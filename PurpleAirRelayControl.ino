#include "arduino_secrets.h"
#include "constants.h"
#include "PurpleAirSensor.h"
#include "VentilationControl.h"
#include <SPI.h>
#include <WiFiNINA.h>
#include <ArduinoJson.h>
#include <utility/wifi_drv.h>
#include <Adafruit_SleepyDog.h>
#include <WiFiSSLClient.h>
#include <malloc.h> // Required for mallinfo()

// Example requests
// GET https://api.purpleair.com/v1/sensors?fields=pm2.5_10minute&show_only=62491%2C103888%2C121311%2C70123 HTTP/1.1
// GET https://api.purpleair.com/v1/sensors/62491?fields=pm2.5_10minute HTTP/1.1

// wifi settings
int status = WL_IDLE_STATUS; // initially not connected to wifi
int airQuality = -1; // Initialize to -1 (invalid) until first reading
SwitchState switchState = SwitchState::OFF;

// Global objects
PurpleAirSensor purpleAir(SECRET_PURPLE_AIR_KEY, "api.purpleair.com", HTTPS_PORT, SECRET_PURPLE_AIR_IP, HTTP_PORT);
VentilationControl ventilation; // Assuming this class handles relay control logic

// Timing variables
long lastRestart = 0;
long timeSinceLastRestart = 0;

// Define Google Form Logging Constants (declared as extern in constants.h)
// Values are taken from macros in arduino_secrets.h
const char* FORM_URL_BASE = SECRET_VALUE_FORM_URL_BASE;
const char* FORM_ENTRY_AQI = SECRET_VALUE_FORM_ENTRY_AQI;
const char* FORM_ENTRY_SWITCH_STATE = SECRET_VALUE_FORM_ENTRY_SWITCH_STATE;
const char* FORM_ENTRY_VENTILATION_STATE = SECRET_VALUE_FORM_ENTRY_VENTILATION_STATE;

// WiFi Client for Google Forms
WiFiSSLClient googleFormsClient;

// Variables for logging control
SwitchState previousSwitchState;
bool previousVentilationState = false; // Initialize to a known default
unsigned long lastLogTime = 0;

void setup() {
  delay(1000); // Added delay to potentially help with USB re-enumeration
  // Record startup time
  lastRestart = millis();
  
  // Initialize serial communication
  Serial.begin(9600);
  
  // Initialize components - purpleAir.begin() handles WiFi connection
  purpleAir.begin(); 
  ventilation.begin(); 

  // --- Force initial sensor reading --- 
  // This attempts local first, then API if local fails or isn't configured.
  // It populates currentAQI and sets the initial timestamps.
  // This needs to happen AFTER WiFi is connected by purpleAir.begin()
  purpleAir.forceInitialUpdate(); 
  airQuality = purpleAir.getCurrentAQI(); // Explicitly update global AQI after initial fetch
  // --- End initial reading --- 
  
  // Enable the watchdog with the timeout defined in constants.h
  int countdownMS = Watchdog.enable(WATCHDOG_TIMEOUT_MS); 
  Serial.print("Watchdog enabled with timeout: ");
  Serial.print(countdownMS / 1000); 
  Serial.println("s");

  // enable outputs on relay pins
  pinMode(PIN_RELAY1, OUTPUT);
  pinMode(PIN_RELAY2, OUTPUT);

  // enabled LED control
  WiFiDrv::pinMode(25, OUTPUT);
  WiFiDrv::pinMode(26, OUTPUT);
  WiFiDrv::pinMode(27, OUTPUT);
  
  // enable pullups on digital pins
  pinMode(PIN_SWITCH_INPUT1, INPUT_PULLUP);
  pinMode(PIN_SWITCH_INPUT2, INPUT_PULLUP);

  // --- Initial State Determination & Logging (AFTER WiFi and initial data fetch) ---
  SwitchState initialSwitchState = SwitchState::OFF; // Default
  bool initialVentilationState = false;       // Default
  
  // Check WiFi status before proceeding with state determination that might depend on it indirectly
  // or before attempting a log.
  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("WiFi connected, proceeding with initial state determination for logging.");
    initialSwitchState = getSwitchState();
    // airQuality global variable is populated by purpleAir.forceInitialUpdate() above
    ventilation.update(initialSwitchState, airQuality);
    initialVentilationState = ventilation.getVentilationState();

    Serial.println("Performing initial state log to Google Forms...");
    if (airQuality != -1) { // Also ensure AQI is valid before logging
      logToGoogleForm(airQuality, initialSwitchState, initialVentilationState);
    } else {
      Serial.println("Skipping initial log: AQI is invalid (-1).");
    }
  } else {
    Serial.println("Skipping initial state determination for logging and the log itself: WiFi not connected.");
    // If WiFi is not connected, we might still want to set previous states to something, 
    // or rely on the first successful log in loop() to set them.
    // For now, we'll use the defaults defined above for previousSwitchState and previousVentilationState.
    // This means the first log in loop() will likely trigger due to state change if WiFi connects later.
  }
  
  // Initialize tracking variables for logging logic
  lastLogTime = millis(); // Start timer irrespective of successful initial log
  
  // Use determined states if WiFi was up, otherwise defaults. This ensures first loop log captures any change.
  previousSwitchState = initialSwitchState; 
  previousVentilationState = initialVentilationState;
}

void loop() {
  // Handle system restart
  handleSystemRestart();
  Watchdog.reset(); // Added: Insurance pet at start of loop activities

  // Get switch state
  switchState = getSwitchState();
  Watchdog.reset(); // Added: Insurance pet after switch state
  
  // --- Update Sensor Data ---
  // Call updateAQI() periodically. It handles internal timers for local/API polling.
  Watchdog.reset(); // Added: Pet before potentially long updateAQI call
  bool wasUpdated = purpleAir.updateAQI(); 
  Watchdog.reset(); // Added: Pet after updateAQI call
  
  if (wasUpdated) {
      Serial.println("Sensor data was updated.");
  }
  
  // Get the latest available AQI value from the sensor object
  // This value might be fresh or old, depending on the updateAQI() results
  airQuality = purpleAir.getCurrentAQI(); 

  // Log current known AQI if valid to serial monitor
  if (airQuality != -1) {
    Serial.print("Current known AQI: ");
    Serial.println(airQuality);
  } else {
    Serial.println("Waiting for initial AQI reading...");
  }
  Serial.print("Local sensor available: ");
  Serial.println(purpleAir.isLocalAvailable() ? "Yes" : "No");

  // --- Calculate and display countdown to next check --- 
  unsigned long remainingLocalMs = purpleAir.getTimeUntilNextLocalCheck();
  unsigned long remainingApiMs = purpleAir.getTimeUntilNextApiCheck();

  // Update ventilation state using the VentilationControl class
  // This assumes VentilationControl uses the switchState and the latest airQuality value
  ventilation.update(switchState, airQuality);
  bool currentVentilationState = ventilation.getVentilationState();

  // --- Log data to Google Form based on interval or state change ---
  unsigned long currentTime = millis();
  bool shouldLog = false;
  String logReason = "";

  if (currentTime - lastLogTime >= GOOGLE_LOG_INTERVAL_MS) {
    shouldLog = true;
    logReason = "interval reached";
  }
  if (switchState != previousSwitchState) {
    shouldLog = true;
    logReason = (logReason == "") ? "switch state change" : logReason + ", switch state change";
  }
  if (currentVentilationState != previousVentilationState) {
    shouldLog = true;
    logReason = (logReason == "") ? "ventilation state change" : logReason + ", ventilation state change";
  }

  if (shouldLog && airQuality != -1) {
    Serial.print("Logging to Google Forms. Reason: ");
    Serial.println(logReason);
    logToGoogleForm(airQuality, switchState, currentVentilationState);
    lastLogTime = currentTime;
    previousSwitchState = switchState;
    previousVentilationState = currentVentilationState;
  } else if (shouldLog && airQuality == -1) {
      Serial.println("Logging condition met, but AQI is invalid. Skipping log.");
  }
  Serial.println("");

  delay(LOOP_DELAY);

  // Pet the watchdog at the end of the loop to indicate normal operation.
  Watchdog.reset(); 
}

void handleSystemRestart() {
  timeSinceLastRestart = millis() - lastRestart;
  if (timeSinceLastRestart >= MAX_RUN_TIME) {
    Serial.println("MAX_RUN_TIME reached. Requesting system reset.");
    // The watchdog is already running. Enabling it again with a short timeout
    // will effectively cause a reset. If it were disabled, this would enable it.
    // If it's already enabled with a longer timeout, this shortens it.
    Watchdog.enable(1000); // Force a reset in 1 second
  } else {
    Serial.println(String(timeSinceLastRestart/1000) + "s uptime < " + String(MAX_RUN_TIME/1000) + "s max"); 
  }
}

SwitchState getSwitchState() {
  bool pin1State = digitalRead(PIN_SWITCH_INPUT1); 
  bool pin2State = digitalRead(PIN_SWITCH_INPUT2); 

  if (pin1State && pin2State) {
    Serial.println("SWITCH STATE: purple air");
    return SwitchState::PURPLEAIR;
  } else if (pin1State && !pin2State) { // Pin1 HIGH, Pin2 LOW? -> Now mapped to ON
    Serial.println("SWITCH STATE: on");
    return SwitchState::ON;
  } else if (!pin1State && pin2State) { // Pin1 LOW, Pin2 HIGH? -> Now mapped to OFF
    Serial.println("SWITCH STATE: off");
    return SwitchState::OFF;
  } else {
    Serial.println("ERROR: unknown switch state");
    return SwitchState::OFF; // Default to OFF in case of error
  }
}

// Helper function to convert SwitchState enum to String
String getSwitchStateString(SwitchState state) {
  switch (state) {
    case SwitchState::OFF:
      return "OFF";
    case SwitchState::ON:
      return "ON";
    case SwitchState::PURPLEAIR:
      return "PURPLEAIR";
    default:
      return "UNKNOWN";
  }
}

void logToGoogleForm(int currentAqi, SwitchState currentSwitchState, bool isVentilating) {
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("Google Forms: WiFi not connected. Cannot log data.");
    return;
  }

  char aqiBuffer[12]; // Buffer for AQI string (e.g., "-12345")
  snprintf(aqiBuffer, sizeof(aqiBuffer), "%d", currentAqi);

  char switchStateBuffer[12]; // Buffer for switch state string (e.g., "PURPLEAIR")
  const char* switchStateCString = "";
  switch (currentSwitchState) {
    case SwitchState::OFF:
      switchStateCString = "OFF";
      break;
    case SwitchState::ON:
      switchStateCString = "ON";
      break;
    case SwitchState::PURPLEAIR:
      switchStateCString = "PURPLEAIR";
      break;
    default:
      switchStateCString = "UNKNOWN";
      break;
  }
  strncpy(switchStateBuffer, switchStateCString, sizeof(switchStateBuffer) - 1);
  switchStateBuffer[sizeof(switchStateBuffer) - 1] = '\0'; // Ensure null termination

  char ventilationStateBuffer[4]; // Buffer for ventilation state ("ON" or "OFF")
  strncpy(ventilationStateBuffer, isVentilating ? "ON" : "OFF", sizeof(ventilationStateBuffer) -1);
  ventilationStateBuffer[sizeof(ventilationStateBuffer) - 1] = '\0';

  // Estimate maximum URL length and allocate a buffer.
  // Base URL + ? + entry_aqi=AQI + & + entry_switch=SWITCH + & + entry_vent=VENT
  // Lengths: FORM_URL_BASE (approx 100) + 1 + FORM_ENTRY_AQI (20) + 1 + 5 (aqi) + 1
  // + FORM_ENTRY_SWITCH_STATE (20) + 1 + 10 (switch) + 1
  // + FORM_ENTRY_VENTILATION_STATE (20) + 1 + 3 (vent) + 1 (null terminator)
  // Total roughly: 100 + 1 + 20 + 1 + 5 + 1 + 20 + 1 + 10 + 1 + 20 + 1 + 3 + 1 = ~185. Let's use 256 as a safe buffer.
  char urlBuffer[256];
  snprintf(urlBuffer, sizeof(urlBuffer), "%s?%s=%s&%s=%s&%s=%s",
           FORM_URL_BASE,
           FORM_ENTRY_AQI, aqiBuffer,
           FORM_ENTRY_SWITCH_STATE, switchStateBuffer,
           FORM_ENTRY_VENTILATION_STATE, ventilationStateBuffer);

  Serial.print("Google Forms: Attempting to log data to URL: ");
  Serial.println(urlBuffer);

  Watchdog.reset(); 

  googleFormsClient.stop(); 

  if (googleFormsClient.connect("docs.google.com", HTTPS_PORT)) {
    Serial.println("Google Forms: Connected to docs.google.com");
    
    // Construct GET request line also using a char buffer
    char getRequestBuffer[sizeof(urlBuffer) + 30]; // "GET " + url + " HTTP/1.1" + null
    snprintf(getRequestBuffer, sizeof(getRequestBuffer), "GET %s HTTP/1.1", urlBuffer);
    googleFormsClient.println(getRequestBuffer);
    
    googleFormsClient.println("Host: docs.google.com");
    googleFormsClient.println("Connection: close");
    googleFormsClient.println(); 

    delay(100); 

    unsigned long timeout = millis();
    while (googleFormsClient.available() == 0) {
      if (millis() - timeout > 5000) { 
        Serial.println(">>> Google Forms: Client Timeout waiting for response!");
        googleFormsClient.stop();
        return;
      }
      Watchdog.reset(); // Pet watchdog while waiting for response
    }

    // Read and print only the first line (status line)
    // Still using String here for simplicity of readStringUntil, but it's short-lived.
    // For maximum robustness, this could also be converted to read into a char buffer.
    if (googleFormsClient.available()) {
      String statusLine = googleFormsClient.readStringUntil('\n'); 
      statusLine.trim(); 
      Serial.print("<<< Google Forms Status: ");
      Serial.println(statusLine); 
    }

    googleFormsClient.stop(); 
    Serial.println("Google Forms: Client stopped after response.");

  } else {
    Serial.println("Google Forms: Connection failed!");
  }
  
  if (googleFormsClient.connected()) {
    Serial.println("Google Forms: Stopping client (safeguard check).");
    googleFormsClient.stop();
  }
}
