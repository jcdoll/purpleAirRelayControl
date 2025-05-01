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
