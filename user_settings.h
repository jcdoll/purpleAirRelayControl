// aqi limits for relay control
// if input < lower threshold = enable ventilation
// if input > upper threshold = disable ventilation
// if between, do not change the state
//
// adjust based on the efficiency of your HVAC filter and your personal preferences
// ideally set these limits based on an indoor air quality sensor
int ENABLE_THRESHOLD = 120; // lower threshold to enable relays
int DISABLE_THRESHOLD = 130; // upper threshold to disable relays
