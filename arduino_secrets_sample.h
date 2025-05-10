#pragma once

// WiFi credentials
const char SECRET_SSID[32] = "your_wifi_ssid";  // Maximum length for SSID
const char SECRET_PASS[64] = "your_wifi_password";  // Maximum length for password

// Purple Air API key (unified for all sensors)
const char SECRET_PURPLE_AIR_API_KEY[64] = "your_purple_air_api_key"; // Optional: leave empty if not using API features

// Purple Air Outdoor sensor IDs
// Example: const int ACTUAL_OUTDOOR_SENSORS[] = {12345, 67890};
// const int* SECRET_OUTDOOR_SENSOR_IDS = ACTUAL_OUTDOOR_SENSORS;
// const int N_OUTDOOR_SENSORS = sizeof(ACTUAL_OUTDOOR_SENSORS)/sizeof(ACTUAL_OUTDOOR_SENSORS[0]);
const int DEFAULT_OUTDOOR_SENSORS[] = {12345, 67890}; // Default example
const int* SECRET_OUTDOOR_SENSOR_IDS = DEFAULT_OUTDOOR_SENSORS;
const int N_OUTDOOR_SENSORS = sizeof(DEFAULT_OUTDOOR_SENSORS)/sizeof(DEFAULT_OUTDOOR_SENSORS[0]);

// Purple Air Indoor sensor IDs
// If you have indoor sensors, define them like this:
// const int ACTUAL_INDOOR_SENSORS[] = {98765};
// const int* SECRET_INDOOR_SENSOR_IDS = ACTUAL_INDOOR_SENSORS;
// const int N_INDOOR_SENSORS = sizeof(ACTUAL_INDOOR_SENSORS)/sizeof(ACTUAL_INDOOR_SENSORS[0]);
// If you have no indoor sensors (or don't want to specify IDs for the local IP):
const int* SECRET_INDOOR_SENSOR_IDS = nullptr;
const int N_INDOOR_SENSORS = 0;

// Local Purple Air server IPs
const char SECRET_OUTDOOR_PURPLE_AIR_IP[16] = "192.168.1.100";  // Optional: e.g. "192.168.1.100", leave empty if not used
const char SECRET_INDOOR_PURPLE_AIR_IP[16] = ""; // Optional: e.g., "192.168.1.101", leave empty if not used

// AQI thresholds for relay control
// if input < lower threshold = enable ventilation
// if input > upper threshold = disable ventilation
// if between, do not change the state
//
// adjust based on the efficiency of your HVAC filter and your personal preferences
// ideally set these limits based on an indoor air quality sensor
const int ENABLE_THRESHOLD = 120;  // Enable ventilation when AQI is below this
const int DISABLE_THRESHOLD = 130; // Disable ventilation when AQI is above this

// Google Form Logging Details (replace with your actual Google Form URL and entry IDs)
// To get these: 
// 1. Create your Google Form with fields for Outdoor AQI, Indoor AQI, Switch State, Ventilation Status, and Reason.
// 2. Click the three dots (More options) -> "Get pre-filled link".
// 3. Fill in sample data and click "Get link" then "COPY LINK".
// 4. Paste the link. It will look like: https://docs.google.com/forms/d/e/YOUR_FORM_ID/viewform?usp=pp_url&entry.xxxx=AQI_VALUE&entry.yyyy=SWITCH_STATE_VALUE&entry.zzzz=VENTILATION_VALUE
//    FORM_URL_BASE will be "https://docs.google.com/forms/d/e/YOUR_FORM_ID/formResponse"
//    The entry.xxxx, entry.yyyy, entry.zzzz will be your entry IDs.
#define SECRET_VALUE_FORM_URL_BASE "https://docs.google.com/forms/d/e/xxxxxxx/formResponse" // TODO: Replace with your Google Form URL
#define SECRET_VALUE_FORM_ENTRY_OUTDOOR_AQI "entry.xxxxxxxxxx" // TODO: Replace with your Outdoor AirQuality entry ID
#define SECRET_VALUE_FORM_ENTRY_INDOOR_AQI "entry.yyyyyyyyyy" // TODO: Replace with your Indoor AirQuality entry ID
#define SECRET_VALUE_FORM_ENTRY_SWITCH_STATE "entry.zzzzzzzzzz" // TODO: Replace with your SwitchState entry ID
#define SECRET_VALUE_FORM_ENTRY_VENTILATION_STATE "entry.wwwwwwwwww" // TODO: Replace with your VentilationState entry ID
#define SECRET_VALUE_FORM_ENTRY_REASON "entry.vvvvvvvvvv" // TODO: Replace with your Reason entry ID
