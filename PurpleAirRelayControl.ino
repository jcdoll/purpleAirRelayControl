#include "arduino_secrets.h"
#include "constants.h"
#include "PurpleAirSensor.h"
#include "VentilationControl.h"
#include <SPI.h>
#include <WiFiNINA.h>
#include <ArduinoJson.h>
#include <utility/wifi_drv.h>
#include <Adafruit_SleepyDog.h>

// Example requests
// GET https://api.purpleair.com/v1/sensors?fields=pm2.5_10minute&show_only=62491%2C103888%2C121311%2C70123 HTTP/1.1
// GET https://api.purpleair.com/v1/sensors/62491?fields=pm2.5_10minute HTTP/1.1

// constants
// These seem redundant with constants.h and enum SwitchState
// int SWITCH_STATE_OFF = 0;
// int SWITCH_STATE_PURPLEAIR = 1;
// int SWITCH_STATE_ON = 2;

// define colors for the on board LED - Assuming these are moved to constants.h or used directly
// int COLOR_VENTILATION_ON_1 = 0;
// ... (color definitions removed, assuming they are in constants.h or handled elsewhere)

// wifi settings
int status = WL_IDLE_STATUS; // initially not connected to wifi
// char SERVER[] = "api.purpleair.com"; // Defined in PurpleAirSensor now
// WiFiSSLClient WIFI; // Unused globally now
// HttpClient client = HttpClient(WIFI, SERVER, HTTPS_PORT); // Unused globally now
// HttpClient localClient = HttpClient(WIFI, SECRET_PURPLE_AIR_IP, HTTP_PORT); // Unused globally now

// allocate the memory for the json parsing document
// StaticJsonDocument<2048> doc; // Defined in PurpleAirSensor now

// state variables
// ventilation is enabled by default - This might belong in VentilationControl class?
// bool ventilationState = true; 
int airQuality = -1; // Initialize to -1 (invalid) until first reading
SwitchState switchState = SwitchState::OFF;

// Global objects
PurpleAirSensor purpleAir(SECRET_PURPLE_AIR_KEY, "api.purpleair.com", HTTPS_PORT, SECRET_PURPLE_AIR_IP, HTTP_PORT);
VentilationControl ventilation; // Assuming this class handles relay control logic

// Timing variables
long lastRestart = 0;
long timeSinceLastRestart = 0;
// long lastPurpleAirUpdate = -1; // Obsolete
// long timeSinceLastPurpleAirUpdate; // Obsolete

void setup() {
  // Record startup time
  lastRestart = millis();
  
  // Initialize serial communication
  Serial.begin(9600);
  
  // Initialize components
  purpleAir.begin(); // Handles WiFi connection
  ventilation.begin(); // Call if VentilationControl needs setup

  // --- Force initial sensor reading --- 
  // This attempts local first, then API if local fails or isn't configured.
  // It populates currentAQI and sets the initial timestamps.
  purpleAir.forceInitialUpdate(); 
  // --- End initial reading --- 
  
  // Enable the watchdog with the timeout defined in constants.h
  // If Watchdog.reset() is not called within this period, the system will reset.
  int countdownMS = Watchdog.enable(WATCHDOG_TIMEOUT_MS); 
  Serial.print("Watchdog enabled with timeout: ");
  Serial.print(countdownMS / 1000); 
  Serial.println("s");
  // Watchdog.reset(); // Not strictly needed here if enabled right before loop starts, but safe.

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
}

void loop() {
  // Handle system restart
  handleSystemRestart();
  
  // Get switch state
  switchState = getSwitchState();
  
  // --- Update Sensor Data ---
  // Call updateAQI() periodically. It handles internal timers for local/API polling.
  bool wasUpdated = purpleAir.updateAQI(); 
  if (wasUpdated) {
      Serial.println("Sensor data was updated.");
  }
  
  // Get the latest available AQI value from the sensor object
  // This value might be fresh or old, depending on the updateAQI() results
  airQuality = purpleAir.getCurrentAQI(); 

  // Log current known AQI if valid
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

  if (purpleAir.isLocalConfigured()) {
      Serial.print("Next local check in: ");
      Serial.print(remainingLocalMs / 1000);
      Serial.print("s. ");
      // Also show API countdown as info, as it's the fallback
      Serial.print("(Next API check in: ");
      Serial.print(remainingApiMs / 1000);
      Serial.println("s)");
  } else {
      // Local not configured, only show API countdown
      Serial.print("Next API check in: ");
      Serial.print(remainingApiMs / 1000);
      Serial.println("s.");
  }
  // --- End of countdown block --- 

  // Update ventilation state using the VentilationControl class
  // This assumes VentilationControl uses the switchState and the latest airQuality value
  ventilation.update(switchState, airQuality);

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
