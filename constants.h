#ifndef CONSTANTS_H
#define CONSTANTS_H
#include <Arduino.h>

// Timing Constants

// delay time of the main loop (msec)
// it will only check for switch changes after waiting this long
constexpr int LOOP_DELAY = 1000;  // Main loop delay in milliseconds

// only get data from sensors that have reported data recently, default = 60 minutes (sec)
constexpr int MAX_SENSOR_AGE = 60 * 60;  // Maximum sensor age in seconds

// delay time between purple air requests to avoid API blacklist
// note: purple air is considering adding API pricing, so monitor this setting closely
constexpr int PURPLE_AIR_DELAY = 1000 * 60 * 20;  // Minimum delay between API checks (20 min)
constexpr int LOCAL_SENSOR_DELAY = 1000 * 60;  // Check local sensor every (1 min)

// Watchdog timer timeout in milliseconds. 
// The system will reset if Watchdog.reset() is not called within this period.
// Ensure LOOP_DELAY is significantly shorter than this value.
constexpr int WATCHDOG_TIMEOUT_MS = 16000; // 16 seconds

// nuke the session after some maximum uptime to avoid max socket # issues
// note that the resetFunc does not work with the MKR WiFi 1010 but the SleepyDog library does
// after reset you will need to replug in the USB cable (COM port hangs)
constexpr long MAX_RUN_TIME = 1000L * 60 * 60 * 12;  // Maximum runtime before restart (12 hours)

// Pin Definitions
constexpr int PIN_RELAY1 = 1;
constexpr int PIN_RELAY2 = 2;
constexpr int PIN_SWITCH_INPUT1 = A1;  // A1 = 15
constexpr int PIN_SWITCH_INPUT2 = A2;  // A2 = 16

// LED Colors
struct LEDColors {
    static constexpr int VENTILATION_ON[3] = {0, 50, 0};
    static constexpr int VENTILATION_OFF[3] = {50, 0, 0};
};

// Switch States
enum class SwitchState {
    OFF = 0,
    PURPLEAIR = 1,
    ON = 2
};

// Network Settings
constexpr int HTTPS_PORT = 443;
constexpr int HTTP_PORT = 80;

// Google Form Logging Constants
extern const char* FORM_URL_BASE;
extern const char* FORM_ENTRY_AQI;
extern const char* FORM_ENTRY_SWITCH_STATE;
extern const char* FORM_ENTRY_VENTILATION_STATE;

// Logging Frequency
constexpr unsigned long GOOGLE_LOG_INTERVAL_MS = 1000 * 60 * 15; // Log every 15 minutes (in milliseconds)

#endif // CONSTANTS_H 