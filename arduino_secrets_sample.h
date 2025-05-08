#pragma once

// WiFi credentials
const char SECRET_SSID[32] = "your_wifi_ssid";  // Maximum length for SSID
const char SECRET_PASS[64] = "your_wifi_password";  // Maximum length for password

// Purple Air API key
const char SECRET_PURPLE_AIR_KEY[64] = "your_purple_air_api_key";

// Purple Air sensor IDs
const int SECRET_SENSOR_IDS[] = {12345, 67890};  // Array of sensor IDs
const int N_SENSORS = sizeof(SECRET_SENSOR_IDS)/sizeof(SECRET_SENSOR_IDS[0]);  // Number of sensors in the array

// Local Purple Air server IP
const char SECRET_PURPLE_AIR_IP[16] = "192.168.1.100";  // Maximum length for IP address

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
// 1. Create your Google Form with fields for AQI, Switch State, and Ventilation Status.
// 2. Click the three dots (More options) -> "Get pre-filled link".
// 3. Fill in sample data and click "Get link" then "COPY LINK".
// 4. Paste the link. It will look like: https://docs.google.com/forms/d/e/YOUR_FORM_ID/viewform?usp=pp_url&entry.xxxx=AQI_VALUE&entry.yyyy=SWITCH_STATE_VALUE&entry.zzzz=VENTILATION_VALUE
//    FORM_URL_BASE will be "https://docs.google.com/forms/d/e/YOUR_FORM_ID/formResponse"
//    The entry.xxxx, entry.yyyy, entry.zzzz will be your entry IDs.
#define SECRET_VALUE_FORM_URL_BASE "https://docs.google.com/forms/d/e/xxxxxxx/formResponse" // TODO: Replace with your Google Form URL
#define SECRET_VALUE_FORM_ENTRY_AQI "entry.xxxxxxxxxx" // TODO: Replace with your AirQuality entry ID
#define SECRET_VALUE_FORM_ENTRY_SWITCH_STATE "entry.xxxxxxxxxx" // TODO: Replace with your SwitchState entry ID
#define SECRET_VALUE_FORM_ENTRY_VENTILATION_STATE "entry.xxxxxxxxxx" // TODO: Replace with your VentilationState entry ID
#define SECRET_VALUE_FORM_ENTRY_REASON "entry.xxxxxxxxxx" // TODO: Replace with your Reason entry ID
