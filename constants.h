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
constexpr unsigned long LOCAL_RETRY_DELAY_MS = 500; // Delay between local connection retries within an update cycle
constexpr int MAX_LOCAL_CONNECTION_ATTEMPTS = 3; // Max attempts to connect to local sensor per update cycle

// nuke the session after some maximum uptime to avoid max socket # issues
// note that the resetFunc does not work with the MKR WiFi 1010 but the SleepyDog library does
// after reset you will need to replug in the USB cable (COM port hangs)
// constexpr long MAX_RUN_TIME = 1000L * 60 * 60 * 6;  // Maximum runtime before restart (6 hours)
constexpr long MAX_RUN_TIME = 0;  // Never reset intentionally- the watchdog should cover normal operation

constexpr unsigned long SERIAL_BAUD_RATE = 9600; // Baud rate for Serial communication

// Logging Frequency
constexpr unsigned long GOOGLE_LOG_INTERVAL_MS = 1000 * 60 * 15; // Log every 15 minutes (in milliseconds)

// Pin Definitions
constexpr int PIN_RELAY1 = 1;
constexpr int PIN_RELAY2 = 2;
constexpr int PIN_SWITCH_INPUT1 = A1;  // A1 = 15
constexpr int PIN_SWITCH_INPUT2 = A2;  // A2 = 16

// WiFi Module LED Pins (specific to WiFiNINA)
constexpr int WIFI_LED_R_PIN = 25;
constexpr int WIFI_LED_G_PIN = 26;
constexpr int WIFI_LED_B_PIN = 27;

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
constexpr unsigned long HTTP_CLIENT_RW_TIMEOUT_MS = 5000;    // Timeout for HttpClient read/write operations
constexpr unsigned long WIFI_CONNECT_ATTEMPT_TIMEOUT_MS = 15000; // Timeout for each WiFi.begin() attempt loop
constexpr unsigned long WIFI_CONNECT_RETRY_DELAY_MS = 5000;    // Delay before retrying WiFi.begin()
constexpr unsigned long GOOGLE_FORMS_RESPONSE_TIMEOUT_MS = 5000; // Timeout for Google Forms response
constexpr unsigned long GOOGLE_FORMS_FLUSH_TIMEOUT_MS = 100;     // Timeout for flushing Google Forms client

// Google Form Logging Constants
extern const char* FORM_URL_BASE;
extern const char* FORM_ENTRY_OUTDOOR_AQI;
extern const char* FORM_ENTRY_INDOOR_AQI;
extern const char* FORM_ENTRY_SWITCH_STATE;
extern const char* FORM_ENTRY_VENTILATION_STATE;
extern const char* FORM_ENTRY_REASON;

#endif // CONSTANTS_H 