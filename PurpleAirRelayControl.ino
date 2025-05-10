#include "arduino_secrets.h"
#include "constants.h"
#include "PurpleAirSensor.h"
#include "VentilationControl.h"
#include <SPI.h>
#include <WiFiNINA.h>
#include <ArduinoJson.h>
#include <utility/wifi_drv.h>
#include <wdt_samd21.h>      // Include the new library
#include <WiFiSSLClient.h>
#include <malloc.h> // Required for mallinfo()

// Example requests
// GET https://api.purpleair.com/v1/sensors?fields=pm2.5_10minute&show_only=62491%2C103888%2C121311%2C70123 HTTP/1.1
// GET https://api.purpleair.com/v1/sensors/62491?fields=pm2.5_10minute HTTP/1.1

// wifi settings
int status = WL_IDLE_STATUS; // initially not connected to wifi
int outdoorAirQuality = -1; // For outdoor sensor
int indoorAirQuality = -1;  // For indoor sensor
SwitchState switchState = SwitchState::OFF;

// WDTZero MyWatchDog; // Removing WDTZero object

// Global objects
// Outdoor Sensor
PurpleAirSensor outdoorSensor(
    "Outdoor", // Sensor Name
    SECRET_PURPLE_AIR_API_KEY,
    SECRET_OUTDOOR_SENSOR_IDS,
    N_OUTDOOR_SENSORS,
    "api.purpleair.com", HTTPS_PORT,
    SECRET_OUTDOOR_PURPLE_AIR_IP, HTTP_PORT
);

// Indoor Sensor - conditionally configured
PurpleAirSensor indoorSensor(
    "Indoor", // Sensor Name
    SECRET_PURPLE_AIR_API_KEY,
    SECRET_INDOOR_SENSOR_IDS,
    N_INDOOR_SENSORS,
    "api.purpleair.com", HTTPS_PORT,
    SECRET_INDOOR_PURPLE_AIR_IP, HTTP_PORT
);

VentilationControl ventilation; // Assuming this class handles relay control logic

// Timing variables
long lastRestart = 0;
long timeSinceLastRestart = 0;

// Define Google Form Logging Constants (declared as extern in constants.h)
// Values are taken from macros in arduino_secrets.h
const char* FORM_URL_BASE = SECRET_VALUE_FORM_URL_BASE;
const char* FORM_ENTRY_OUTDOOR_AQI = SECRET_VALUE_FORM_ENTRY_OUTDOOR_AQI;
const char* FORM_ENTRY_INDOOR_AQI = SECRET_VALUE_FORM_ENTRY_INDOOR_AQI;
const char* FORM_ENTRY_SWITCH_STATE = SECRET_VALUE_FORM_ENTRY_SWITCH_STATE;
const char* FORM_ENTRY_VENTILATION_STATE = SECRET_VALUE_FORM_ENTRY_VENTILATION_STATE;
const char* FORM_ENTRY_REASON = SECRET_VALUE_FORM_ENTRY_REASON;

// WiFi Client for Google Forms
WiFiSSLClient googleFormsClient;

// Variables for logging control
SwitchState previousSwitchState;
bool previousVentilationState = false; // Initialize to a known default
unsigned long lastLogTime = 0;

// Helper to check if indoor sensor configuration seems valid enough to use
bool isIndoorSensorEffectivelyConfigured() {
    // Considered configured if it has an API key (the unified one) and sensor IDs, OR a local IP.
    bool hasApiConfig = (SECRET_PURPLE_AIR_API_KEY != nullptr && SECRET_PURPLE_AIR_API_KEY[0] != '\0' && N_INDOOR_SENSORS > 0);
    bool hasLocalConfig = (SECRET_INDOOR_PURPLE_AIR_IP != nullptr && SECRET_INDOOR_PURPLE_AIR_IP[0] != '\0');
    return hasApiConfig || hasLocalConfig;
}

void setup() {
  delay(1000); // Added delay to potentially help with USB re-enumeration
  // Record startup time
  lastRestart = millis();
  
  // Initialize serial communication
  Serial.begin(SERIAL_BAUD_RATE);

  // Enable the watchdog using the wdt_samd21 library
  wdt_init(WDT_CONFIG_PER_16K); // Initialize WDT for ~16 seconds timeout
  Serial.println(F("wdt_samd21 watchdog initialized (~16s timeout)."));
  
  // Initialize components - purpleAir.begin() handles WiFi connection
  outdoorSensor.begin(); 
  ventilation.begin(); 

  // --- Force initial sensor reading --- 
  // This attempts local first, then API if local fails or isn't configured.
  // It populates currentAQI and sets the initial timestamps.
  // This needs to happen AFTER WiFi is connected by purpleAir.begin()
  unsigned long setupTime = millis(); // Get time once for initial updates
  outdoorSensor.forceInitialUpdate(setupTime); 
  outdoorAirQuality = outdoorSensor.getCurrentAQI(); // Explicitly update global AQI after initial fetch
  
  if (isIndoorSensorEffectivelyConfigured()) {
    // indoorSensor.begin(); // Not strictly needed if WiFi already up by outdoorSensor
    indoorSensor.forceInitialUpdate(setupTime);
    indoorAirQuality = indoorSensor.getCurrentAQI();
  }
  
  // enable outputs on relay pins
  pinMode(PIN_RELAY1, OUTPUT);
  pinMode(PIN_RELAY2, OUTPUT);

  // enabled LED control
  WiFiDrv::pinMode(WIFI_LED_R_PIN, OUTPUT);
  WiFiDrv::pinMode(WIFI_LED_G_PIN, OUTPUT);
  WiFiDrv::pinMode(WIFI_LED_B_PIN, OUTPUT);
  
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

    // Ventilation control based on outdoor air quality
    ventilation.update(initialSwitchState, outdoorAirQuality); 
    initialVentilationState = ventilation.getVentilationState();

    Serial.println(F("Performing initial state log to Google Forms..."));
    // Log if at least outdoor AQI is valid. Indoor might be -1.
    if (outdoorAirQuality != -1) { 
      logToGoogleForm(outdoorAirQuality, indoorAirQuality, initialSwitchState, initialVentilationState, F("initialBoot"));
    } else {
      Serial.println(F("Skipping initial log: Outdoor AQI is invalid (-1)."));
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
  wdt_reset();

  // Get switch state
  switchState = getSwitchState();
  wdt_reset();
  
  // --- Update Sensor Data ---
  // Call updateAQI() periodically. It handles internal timers for local/API polling.
  unsigned long currentTimeForSensorUpdates = millis(); // Get time once for this loop cycle's updates
  wdt_reset();
  bool outdoorUpdated = outdoorSensor.updateAQI(currentTimeForSensorUpdates, true); // Verbose for outdoor sensor
  wdt_reset();
  
  if (outdoorUpdated) {
      Serial.println("Outdoor sensor data was updated.");
      outdoorAirQuality = outdoorSensor.getCurrentAQI(); 
  }
  
  if (isIndoorSensorEffectivelyConfigured()) {
    bool indoorUpdated = indoorSensor.updateAQI(currentTimeForSensorUpdates, true); // Verbose for indoor sensor
    wdt_reset();
    if (indoorUpdated) {
        Serial.println("Indoor sensor data was updated.");
        indoorAirQuality = indoorSensor.getCurrentAQI();
    }
  }
  
  // Log current known AQIs if valid to serial monitor
  if (outdoorAirQuality != -1) {
    Serial.print("Current Outdoor AQI: "); Serial.println(outdoorAirQuality);
  } else {
    Serial.println("Waiting for initial Outdoor AQI reading...");
  }
  if (isIndoorSensorEffectivelyConfigured()) {
    if (indoorAirQuality != -1) {
        Serial.print("Current Indoor AQI: "); Serial.println(indoorAirQuality);
    } else {
        Serial.println("Waiting for initial Indoor AQI reading...");
    }
    Serial.print("Indoor Local sensor available: ");
    Serial.println(indoorSensor.isLocalAvailable() ? "Yes" : "No");
  }
  Serial.print("Outdoor Local sensor available: ");
  Serial.println(outdoorSensor.isLocalAvailable() ? "Yes" : "No");

  // Display countdown timers using the sensor's internal logic (which now uses synchronized timestamps)
  Serial.println(F("--- Sensor Check Timers ---"));
  Serial.print(F("  Time until next local check: ")); Serial.print(outdoorSensor.getTimeUntilNextLocalCheck() / 1000); Serial.println(F("s"));
  Serial.print(F("  Time until next API check: ")); Serial.print(outdoorSensor.getTimeUntilNextApiCheck() / 1000); Serial.println(F("s"));

  // Update ventilation state using the VentilationControl class
  // This assumes VentilationControl uses the switchState and the latest airQuality value
  ventilation.update(switchState, outdoorAirQuality);
  bool currentVentilationState = ventilation.getVentilationState();

  // --- Log data to Google Form based on interval or state change ---
  unsigned long currentTime = millis();
  bool shouldLog = false;
  String logReason = "";

  if (currentTime - lastLogTime >= GOOGLE_LOG_INTERVAL_MS) {
    shouldLog = true;
    logReason = F(""); // Leave reason empty for interval-based logging
  }

  if (switchState != previousSwitchState) {
    shouldLog = true;
    if (logReason == "") {
        logReason = F("switchChange");
    } else {
        logReason += F("_switchChange");
    }
  }

  if (currentVentilationState != previousVentilationState) {
    shouldLog = true;
    if (logReason == "") {
        logReason = F("ventChange");
    } else {
        logReason += F("_ventChange");
    }
  }

  // Log if condition met AND outdoor AQI is valid. Indoor AQI can be -1.
  if (shouldLog && outdoorAirQuality != -1) {
    Serial.print(F("Logging to Google Forms. Reason: ")); Serial.println(logReason);
    logToGoogleForm(outdoorAirQuality, indoorAirQuality, switchState, currentVentilationState, logReason);
    lastLogTime = currentTime;
    previousSwitchState = switchState;
    previousVentilationState = currentVentilationState;
  } else if (shouldLog && outdoorAirQuality == -1) {
      Serial.println("Logging condition met, but Outdoor AQI is invalid. Skipping log.");
  }
  Serial.println("");

  delay(LOOP_DELAY);

  // Pet the watchdog at the end of the loop to indicate normal operation.
  wdt_reset();
}

void handleSystemRestart() {
  timeSinceLastRestart = millis() - lastRestart;
  if (MAX_RUN_TIME > 0) { 
    if (timeSinceLastRestart >= MAX_RUN_TIME) {
      Serial.println(F("MAX_RUN_TIME reached. Requesting system reset."));
      // TODO: If there are any problems here consider using the WDT library instead.
      NVIC_SystemReset(); // Standard ARM CMSIS call for a software reset
    } else {
      Serial.println(String(timeSinceLastRestart/1000) + F("s uptime < ") + String(MAX_RUN_TIME/1000) + F("s max")); 
    }
  }
}

SwitchState getSwitchState() {
  bool pin1State = digitalRead(PIN_SWITCH_INPUT1); 
  bool pin2State = digitalRead(PIN_SWITCH_INPUT2); 

  if (pin1State && pin2State) {
    Serial.println("SWITCH STATE: PURPLE AIR");
    return SwitchState::PURPLEAIR;
  } else if (pin1State && !pin2State) { // Pin1 HIGH, Pin2 LOW? -> Now mapped to ON
    Serial.println("SWITCH STATE: ON");
    return SwitchState::ON;
  } else if (!pin1State && pin2State) { // Pin1 LOW, Pin2 HIGH? -> Now mapped to OFF
    Serial.println("SWITCH STATE: OFF");
    return SwitchState::OFF;
  } else {
    Serial.println("ERROR: UNKNOWN SWITCH STATE (DEFAULT TO OFF)");
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

void logToGoogleForm(int currentOutdoorAqi, int currentIndoorAqi, SwitchState currentSwitchState, bool isVentilating, const String& reason) {
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println(F("Google Forms: WiFi not connected. Cannot log data."));
    return;
  }

  char outdoorAqiBuffer[12];
  snprintf(outdoorAqiBuffer, sizeof(outdoorAqiBuffer), "%d", currentOutdoorAqi);
  
  char indoorAqiBuffer[12];
  // Handle case where indoor AQI might be invalid (-1), log as empty or a placeholder.
  // Google Forms usually treats empty strings fine.
  if (currentIndoorAqi == -1) {
    snprintf(indoorAqiBuffer, sizeof(indoorAqiBuffer), ""); 
  } else {
    snprintf(indoorAqiBuffer, sizeof(indoorAqiBuffer), "%d", currentIndoorAqi);
  }

  char switchStateBuffer[12]; 
  // Use snprintf for safer string copying into the buffer
  String tempSwitchStateStr = getSwitchStateString(currentSwitchState);
  snprintf(switchStateBuffer, sizeof(switchStateBuffer), "%s", tempSwitchStateStr.c_str());
  // switchStateBuffer is now guaranteed to be null-terminated by snprintf

  char ventilationStateBuffer[4]; 
  strncpy(ventilationStateBuffer, isVentilating ? "ON" : "OFF", sizeof(ventilationStateBuffer) -1);
  ventilationStateBuffer[sizeof(ventilationStateBuffer) - 1] = '\\0';

  // Increased buffer for two AQI entries
  char urlBuffer[300]; 
  snprintf(urlBuffer, sizeof(urlBuffer), "%s?%s=%s&%s=%s&%s=%s&%s=%s&%s=%s",
           FORM_URL_BASE,
           FORM_ENTRY_OUTDOOR_AQI, outdoorAqiBuffer,
           FORM_ENTRY_INDOOR_AQI, indoorAqiBuffer,
           FORM_ENTRY_SWITCH_STATE, switchStateBuffer,
           FORM_ENTRY_VENTILATION_STATE, ventilationStateBuffer,
           FORM_ENTRY_REASON, reason.c_str());

  Serial.print(F("Google Forms: Attempting to log data to URL: "));
  Serial.println(urlBuffer);

  googleFormsClient.stop(); 

  if (googleFormsClient.connect("docs.google.com", HTTPS_PORT)) {
    Serial.println("Google Forms: Connected to docs.google.com");
    
    char getRequestBuffer[sizeof(urlBuffer) + 30]; 
    snprintf(getRequestBuffer, sizeof(getRequestBuffer), "GET %s HTTP/1.1", urlBuffer);
    googleFormsClient.println(getRequestBuffer);
    
    googleFormsClient.println("Host: docs.google.com");
    googleFormsClient.println("Connection: close");
    googleFormsClient.println(); 

    delay(100); 

    unsigned long timeout = millis();
    while (googleFormsClient.available() == 0) {
      if (millis() - timeout > GOOGLE_FORMS_RESPONSE_TIMEOUT_MS) {
        Serial.println(">>> Google Forms: Client Timeout waiting for response!");
        googleFormsClient.stop();
        return;
      }
      wdt_reset();
    }

    if (googleFormsClient.available()) {
      String statusLine = googleFormsClient.readStringUntil('\n'); 
      statusLine.trim(); 
      Serial.print("<<< Google Forms Status: ");
      Serial.println(statusLine); 

      // Consume any remaining data from the client to clear the buffer
      unsigned long flushTimeout = millis();
      while (googleFormsClient.available() && (millis() - flushTimeout < GOOGLE_FORMS_FLUSH_TIMEOUT_MS)) {
          googleFormsClient.read(); // Read and discard byte
          wdt_reset(); // Pet watchdog while flushing
      }
    }

    googleFormsClient.stop(); 
    // Serial.println("Google Forms: Client stopped after response.");

  } else {
    Serial.println("Google Forms: Connection failed!");
  }
  
  if (googleFormsClient.connected()) {
    Serial.println("Google Forms: Stopping client (safeguard check).");
    googleFormsClient.stop();
  }
}
