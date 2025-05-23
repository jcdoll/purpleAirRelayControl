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
  
  // Check WiFi status before proceeding with state determination that might depend on it.
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
  wdt_reset();
  unsigned long currentTimeForLoop = millis(); // Use a single millis() call for this loop iteration for consistency

  // Get switch state
  switchState = getSwitchState();
  wdt_reset();
  
  // --- Update Sensor Data ---
  // Call updateAQI() periodically. It handles internal timers for local/API polling.
  unsigned long currentTimeForSensorUpdates = millis(); // Get time once for this loop cycle's updates
  wdt_reset();
  bool outdoorUpdated = outdoorSensor.updateAQI(currentTimeForLoop, false); // Verbose for outdoor sensor
  wdt_reset();
  
  if (outdoorUpdated) {
      Serial.println("Outdoor sensor data was updated.");
      outdoorAirQuality = outdoorSensor.getCurrentAQI(); 
  }
  
  bool indoorUpdated = false; // Initialize
  if (isIndoorSensorEffectivelyConfigured()) {
    indoorUpdated = indoorSensor.updateAQI(currentTimeForLoop, false); // Verbose for indoor sensor
    wdt_reset();
    if (indoorUpdated) {
        Serial.println("Indoor sensor data was updated.");
        indoorAirQuality = indoorSensor.getCurrentAQI();
    }
  }

  bool sensorDataUpdatedThisCycle = outdoorUpdated || indoorUpdated;
  
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

  // --- Log data to Google Form based on interval or state change ---
  // Moved static declaration here, before its first use by the status display or logic
  static bool logDueToIntervalPending = false; 

  // Display time until next Google Forms log interval
  Serial.println(F("--- Google Forms Logger Status ---")); // Corrected to println for the header
  if (logDueToIntervalPending) {
    Serial.println(F("  Interval log: Pending fresh sensor data."));
  } else {
    unsigned long elapsedSinceLastLog = currentTimeForLoop - lastLogTime;
    if (GOOGLE_LOG_INTERVAL_MS > elapsedSinceLastLog) {
      unsigned long remainingLogTimeMs = GOOGLE_LOG_INTERVAL_MS - elapsedSinceLastLog;
      Serial.print(F("  Time until next interval log attempt: ")); 
      Serial.print(remainingLogTimeMs / 1000); 
      Serial.println(F("s"));
    } else {
      // This case should ideally be covered by logDueToIntervalPending becoming true,
      // but as a fallback or for clarity:
      Serial.println(F("  Interval log: Due or pending.")); 
    }
  }

  // Update ventilation state using the VentilationControl class
  ventilation.update(switchState, outdoorAirQuality);
  bool currentVentilationState = ventilation.getVentilationState();

  // Handle all data logging conditions
  handleDataLogging(currentTimeForLoop, sensorDataUpdatedThisCycle, switchState, currentVentilationState);
  Serial.println("");
  delay(LOOP_DELAY);

  // Pet the watchdog at the end of the loop to indicate normal operation.
  wdt_reset();
}

// Function to manage data logging to Google Forms
void handleDataLogging(unsigned long p_currentTimeForLoop, bool p_sensorDataUpdatedThisCycle, SwitchState p_currentSwitchState, bool p_currentVentilationState) {
  static bool logDueToIntervalPending = false; // Persists across loop calls

  // Determine if events occurred this cycle
  bool switchChanged = (p_currentSwitchState != previousSwitchState);
  bool ventChanged = (p_currentVentilationState != previousVentilationState);

  // Check if the logging interval has passed to arm the pending flag
  if (!logDueToIntervalPending && (p_currentTimeForLoop - lastLogTime >= GOOGLE_LOG_INTERVAL_MS)) {
    // Serial.println(F("[LOGIC] Interval elapsed. Setting logDueToIntervalPending = true.")); // Debug removed
    logDueToIntervalPending = true; // Interval is due, arm pending log
  }

  bool performLog = false;
  String logReason = "";

  // Check for event-driven logs first (switch or ventilation changes)
  if (switchChanged) {
    performLog = true;
    logReason = F("switchChange");
  }
  if (ventChanged) {
    performLog = true;
    if (logReason == "") {
      logReason = F("ventChange");
    } else {
      logReason += F("_ventChange");
    }
  }

  // Check for interval-driven log if no event log is already set to fire,
  // and if an interval log is pending and fresh data is available.
  // An event-driven log (if it occurred) can also satisfy a pending interval if fresh data is present,
  // as a successful log of any kind will reset the logDueToIntervalPending flag.
  if (!performLog && logDueToIntervalPending && p_sensorDataUpdatedThisCycle) {
    performLog = true; // Interval log with fresh data
    // logReason remains empty for a pure interval log (or will be event-driven if performLog was already true)
  }
  // Note: If logDueToIntervalPending is true but p_sensorDataUpdatedThisCycle is false,
  // no interval log happens this cycle; it remains pending.

  // Perform the log if any condition was met and outdoor AQI is valid
  if (performLog) {
    if (outdoorAirQuality != -1) {
      Serial.print(F("Logging to Google Forms. Reason: ")); Serial.println(logReason);
      logToGoogleForm(outdoorAirQuality, indoorAirQuality, p_currentSwitchState, p_currentVentilationState, logReason);
      
      lastLogTime = p_currentTimeForLoop; // Reset interval timer on successful log
      if (logDueToIntervalPending) {
          logDueToIntervalPending = false;  // Reset pending flag on successful log
      }
    } else {
      // Log was triggered but outdoor AQI is invalid, so we skip sending to Google Forms.
      // If an interval log was pending, it remains pending because the log attempt failed.
      // lastLogTime is also not updated, so the interval condition will remain met.
      Serial.println(F("Log triggered, but Outdoor AQI is invalid. Skipping Google Forms log."));
    }
  }

  // Update previous states for the next cycle if they changed.
  // This happens regardless of whether a log was successfully sent to ensure changes are acknowledged.
  if (switchChanged) {
    previousSwitchState = p_currentSwitchState;
  }
  if (ventChanged) {
    previousVentilationState = p_currentVentilationState;
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

// Helper function to set the WiFi Module's RGB LED color
// Using analogWrite, assuming 0 is off and 255 is max brightness.
void setWiFiStatusLedColor(int r, int g, int b) {
    WiFiDrv::analogWrite(WIFI_LED_R_PIN, r);
    WiFiDrv::analogWrite(WIFI_LED_G_PIN, g);
    WiFiDrv::analogWrite(WIFI_LED_B_PIN, b);
}

void logToGoogleForm(int currentOutdoorAqi, int currentIndoorAqi, SwitchState currentSwitchState, bool isVentilating, const String& reason) {
  // Ensure WiFi is connected before proceeding
  if (!PurpleAirSensor::ensureWiFiConnected()) {
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
  // switchStateBuffer is now guaranteed to be null-terminated by snprintf
  String tempSwitchStateStr = getSwitchStateString(currentSwitchState);
  snprintf(switchStateBuffer, sizeof(switchStateBuffer), "%s", tempSwitchStateStr.c_str());
  
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

  // Ping Google Docs before attempting to connect
  const char* googleDocsHost = "docs.google.com";
  Serial.print(F("Google Forms: Pinging ")); Serial.print(googleDocsHost); Serial.println(F("..."));
  wdt_reset(); // Reset WDT before potentially blocking operation
  int pingResult = WiFi.ping(googleDocsHost, 1); // Ping once

  if (pingResult >= 0) {
    Serial.print(F("Google Forms: Ping successful. RTT: ")); Serial.print(pingResult); Serial.println(F(" ms"));
    if (googleFormsClient.connect(googleDocsHost, HTTPS_PORT)) {
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

  } else {
    Serial.println("Google Forms: Connection failed!");
    googleFormsClient.stop(); // Add stop() here to reset the client
  }
  } else { // Ping failed
    Serial.print(F("Google Forms: Ping failed to ")); Serial.print(googleDocsHost); Serial.print(F(". Result: ")); Serial.println(pingResult);
    Serial.println(F("Google Forms: Skipping connection attempt."));
    // No need to call googleFormsClient.stop() here if ping failed, as we haven't used the client yet in this attempt after the initial stop().
  }
  
  if (googleFormsClient.connected()) {
    Serial.println("Google Forms: Stopping client (safeguard check).");
    googleFormsClient.stop();
  }
}
