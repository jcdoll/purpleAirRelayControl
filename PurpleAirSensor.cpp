#include "PurpleAirSensor.h"
#include "arduino_secrets.h"
#include <Arduino.h>
#include <ArduinoJson.h>
#include <ArduinoHttpClient.h>
#include <WiFiNINA.h> // Ensure WiFi library is included
#include <WiFiSSLClient.h> // Added for WiFiSSLClient
#include "constants.h" // Include for delay constants
#include <wdt_samd21.h> // Include the library header here too for wdt_reset()
#include <malloc.h> // Required for mallinfo()
#include <StreamUtils.h> // Include StreamUtils library

// Extern declaration for the LED control function in PurpleAirRelayControl.ino
extern void setWiFiStatusLedColor(int r, int g, int b);

// Definition for the static JsonDocument
StaticJsonDocument<PurpleAirSensor::JSON_DOC_SIZE> PurpleAirSensor::doc;

// Static constant for API sensor ID separator (comma)
static const char* API_SENSOR_SEPARATOR = "%2C";

// Attempt to declare sbrk with C linkage at global scope for this file
extern "C" {
    char* sbrk(int incr);
}

// Forward declaration for getFreeMemory()
int getFreeMemory();

// Function to get free memory
int getFreeMemory() {
  char stackVariable; // Get a variable on the stack
  void* currentStackPointer = (void*)&stackVariable;

#if defined(ARDUINO_SAMD_MKRWIFI1010) || defined(ARDUINO_SAMD_NANO_33_IOT) || defined(ARDUINO_SAMD_ZERO) || defined(ARDUINO_SAMD_MKRZERO) || defined(ARDUINO_SAMD_MKR1000) || defined(ARDUINO_SAMD_GEMMA_M0) || defined(ARDUINO_SAMD_TRINKET_M0)
  // For SAMD boards, free memory is the space between the current stack pointer and the top of the heap.
  // extern "C" char* sbrk(int incr); // Moved to global scope
  void* heapEnd = sbrk(0); // Current top of the heap.
  if (heapEnd == (void*)-1) { // sbrk can return -1 on error, though unlikely with 0.
      return -1; // Indicate error
  }
  return (char*)currentStackPointer - (char*)heapEnd;
#else
  return -1; // Fallback for other architectures, or implement specific logic
#endif
}

// Implementation of the static WiFi connection helper
bool PurpleAirSensor::ensureWiFiConnected() {
    if (WiFi.status() == WL_CONNECTED) {
        return true;
    }

    Serial.println(F("WIFI STATUS: Not connected. Attempting to connect/reconnect..."));
    setWiFiStatusLedColor(0, 0, 50); // Set LED to BLUE (R=0, G=0, B=50)
    
    // Loop to attempt connection, similar to original begin() logic
    // This will loop indefinitely until connection or WDT reset
    while (WiFi.status() != WL_CONNECTED) {
        Serial.println(F("Initiating WiFi connection attempt..."));
        WiFi.disconnect(); // Explicitly disconnect before trying to connect
        delay(100); // Short delay after disconnect
        int status = WiFi.begin(SECRET_SSID, SECRET_PASS);
        // Log status immediately after begin call for diagnostics
        Serial.print(F("WiFi.begin status code: ")); Serial.println(status);
        // Note: WL_CONNECTED might not be immediate, status from begin() can be misleading for final state.

        unsigned long startAttemptTime = millis();
        while (WiFi.status() != WL_CONNECTED && millis() - startAttemptTime < WIFI_CONNECT_ATTEMPT_TIMEOUT_MS) {
            Serial.print(".");
            wdt_reset(); 
            delay(500); // Wait 500ms between status checks
        }
        Serial.println(); // Newline after dots or connection success

        if (WiFi.status() != WL_CONNECTED) {
            Serial.println(F("WIFI STATUS: Connection failed on this attempt."));
            Serial.print(F("Retrying in ")); Serial.print(WIFI_CONNECT_RETRY_DELAY_MS / 1000); Serial.println(F(" seconds..."));
            unsigned long retryDelayStart = millis();
            while(millis() - retryDelayStart < WIFI_CONNECT_RETRY_DELAY_MS) {
                wdt_reset();
                delay(100); // Short delay to allow background tasks/watchdog
            }
        } else {
            Serial.println(F("WIFI STATUS: Connected!"));
            Serial.print(F("IP Address: ")); Serial.println(WiFi.localIP());
            Serial.print(F("Signal Strength (RSSI): ")); Serial.print(WiFi.RSSI()); Serial.println(F(" dBm"));
            setWiFiStatusLedColor(50, 50, 0); // Set LED to YELLOW (R=50, G=50, B=0) upon connection
            // No need to return true here, loop condition will handle exit
        }
        wdt_reset(); // Ensure watchdog is reset before the next outer loop iteration (retry attempt)
    }
    // Exited the while loop, so WiFi.status() == WL_CONNECTED
    // The LED would have been set to YELLOW in the 'else' block above if connection was just made.
    // If WiFi was already connected at the function's start, the LED state was not touched by this function.
    return true; 
}

PurpleAirSensor::PurpleAirSensor(const char* sensorName,
                                const char* apiKey, const int* sensorIDs, int numSensors,
                                const char* apiServerHost, int apiPort,
                                const char* localServerIP, int localServerPort)
    : sensorName(sensorName),
      apiKey(apiKey), sensorIDs(sensorIDs), numSensors(numSensors),
      apiServerHost(apiServerHost), apiPort(apiPort),
      localServerIP(localServerIP), localServerPort(localServerPort),
      lastLocalCheckTime(0), lastApiCheckTime(0),
      currentAQI(-1),
      localSensorAvailable(false) {}

void PurpleAirSensor::begin() {
    // Initialize WiFi connection by ensuring it's connected.
    Serial.println(F("PurpleAirSensor::begin() called. Ensuring WiFi is connected..."));
    ensureWiFiConnected(); // This will loop until connected or WDT reset
    Serial.println(F("PurpleAirSensor::begin(): WiFi connection process complete."));
    Serial.println(); // Extra newline for clarity
}

bool PurpleAirSensor::updateAQI(unsigned long masterCurrentTime, bool verboseLog) {
    bool updated = false;
    int fetchedAQI = -1;
    bool attemptedLocal = false;
    bool localSucceeded = false;

    if (isLocalConfigured() && (masterCurrentTime - lastLocalCheckTime >= (unsigned long)LOCAL_SENSOR_DELAY)) {
        attemptedLocal = true;
        Serial.print(this->sensorName); Serial.println(F(": Polling local sensor..."));
        wdt_reset();
        fetchedAQI = getLocalAirQuality();
        wdt_reset();
        lastLocalCheckTime = masterCurrentTime; // Use masterCurrentTime
        
        if (fetchedAQI >= 0) { 
            Serial.print(this->sensorName); Serial.println(F(": Local sensor success."));
            currentAQI = fetchedAQI;
            updated = true;
            localSucceeded = true; 
            // If local succeeds, update API check time too, so it doesn't immediately follow
            // if its PURPLE_AIR_DELAY was also met. This maintains the local-first preference effectively.
            lastApiCheckTime = masterCurrentTime; 
            return updated; 
        } else {
            Serial.print(this->sensorName); Serial.println(F(": Local sensor failed or no valid data."));
            localSensorAvailable = false; 
        }
    }

    bool apiConfigured = (this->apiKey != nullptr && this->apiKey[0] != '\0' && this->numSensors > 0);

    if (apiConfigured && (!isLocalConfigured() || (attemptedLocal && !localSucceeded)) &&
        (masterCurrentTime - lastApiCheckTime >= (unsigned long)PURPLE_AIR_DELAY))
    {
        Serial.print(this->sensorName); Serial.println(F(": Polling PurpleAir API..."));
        wdt_reset();
        fetchedAQI = getAPIAirQuality();
        wdt_reset();
        lastApiCheckTime = masterCurrentTime; // Use masterCurrentTime

        if (fetchedAQI >= 0) { 
             Serial.print(this->sensorName); Serial.println(F(": API success."));
             currentAQI = fetchedAQI;
             updated = true;
        } else {
             Serial.print(this->sensorName); Serial.println(F(": API failed or no valid data."));
        }
    }
    
    if (!updated && verboseLog) {
        Serial.print(this->sensorName); Serial.println(F(": No sensor data updated in this cycle."));
        bool apiConfiguredForLog = (this->apiKey != nullptr && this->apiKey[0] != '\0' && this->numSensors > 0);
        if (isLocalConfigured()) {
             Serial.print(this->sensorName); Serial.print(F(":  Time since last local check: ")); Serial.print((masterCurrentTime - lastLocalCheckTime) / 1000); Serial.println("s");
        }
        if (apiConfiguredForLog) {
            Serial.print(this->sensorName); Serial.print(F(":  Time since last API check: ")); Serial.print((masterCurrentTime - lastApiCheckTime) / 1000); Serial.println("s");
        }
    }
    return updated;
}

int PurpleAirSensor::getCurrentAQI() const {
    return currentAQI;
}

bool PurpleAirSensor::isLocalAvailable() const {
    return localSensorAvailable;
}

// Forces an immediate fetch, bypassing normal timers. Called once at startup.
void PurpleAirSensor::forceInitialUpdate(unsigned long masterCurrentTime) {
    Serial.print(this->sensorName); Serial.println(F(": Performing initial sensor data fetch..."));
    int fetchedAQI = -1;

    if (isLocalConfigured()) {
        Serial.print(this->sensorName); Serial.println(F(": Initial check: Polling local sensor..."));
        fetchedAQI = getLocalAirQuality(); 
        lastLocalCheckTime = masterCurrentTime; // Use masterCurrentTime

        if (fetchedAQI >= 0) { 
            Serial.print(this->sensorName); Serial.println(F(": Initial check: Local sensor success."));
            currentAQI = fetchedAQI;
            lastApiCheckTime = masterCurrentTime; // Use masterCurrentTime
            return; 
        } else {
            Serial.print(this->sensorName); Serial.println(F(": Initial check: Local sensor failed or no valid data."));
            localSensorAvailable = false; 
        }
    } else {
         Serial.print(this->sensorName); Serial.println(F(": Initial check: Local sensor not configured."));
         lastLocalCheckTime = masterCurrentTime; // Use masterCurrentTime
         localSensorAvailable = false;
    }

    bool apiConfigured = (this->apiKey != nullptr && this->apiKey[0] != '\0' && this->numSensors > 0);
    if (apiConfigured) {
        Serial.print(this->sensorName); Serial.println(F(": Initial check: Polling PurpleAir API..."));
        fetchedAQI = getAPIAirQuality();
        lastApiCheckTime = masterCurrentTime; // Use masterCurrentTime

        if (fetchedAQI >= 0) { 
             Serial.print(this->sensorName); Serial.println(F(": Initial check: API success."));
             currentAQI = fetchedAQI;
        } else {
             Serial.print(this->sensorName); Serial.println(F(": Initial check: API failed or no valid data."));
        }
    } else {
        Serial.print(this->sensorName); Serial.println(F(": Initial check: API not configured (no key or no sensor IDs)."));
        lastApiCheckTime = masterCurrentTime; // Use masterCurrentTime
    }
}

int PurpleAirSensor::getLocalAirQuality() {
    if (!ensureWiFiConnected()) {
        Serial.print(this->sensorName); Serial.println(F(": getLocalAirQuality: WiFi not connected. Aborting."));
        localSensorAvailable = false; // Ensure this is false if we can't even check
        return -1;
    }

    // Reset availability flag before attempt
    localSensorAvailable = false;
    int resultAQI = -1; // Default to -1 (failure/no data)

    if (!isLocalConfigured()) {
        Serial.print(this->sensorName); Serial.println(F(": getLocalAirQuality: Local sensor not configured (IP address missing)."));
        return -1;
    }

    for (int attempt = 1; attempt <= MAX_LOCAL_CONNECTION_ATTEMPTS; ++attempt) {
        Serial.print(this->sensorName); Serial.print(F(": Local sensor attempt "));
        Serial.print(attempt);
        Serial.print(F(" of "));
        Serial.println(MAX_LOCAL_CONNECTION_ATTEMPTS);

        Serial.print(this->sensorName); Serial.print(F(": Free SRAM (before local request, attempt "));
        Serial.print(attempt);
        Serial.print(F("): "));
        Serial.println(getFreeMemory());

        wdt_reset(); // Pet watchdog at the start of each attempt

        Serial.print(this->sensorName); Serial.print(F(": Pinging local sensor at "));
        Serial.print(this->localServerIP);
        Serial.print(F("... "));
        int pingResult = WiFi.ping(this->localServerIP);
        wdt_reset(); // Pet watchdog after ping attempt

        if (pingResult >= 0) { // A non-negative result indicates success (RTT in ms)
            Serial.print(F(" success. RTT: "));
            Serial.print(pingResult);
            Serial.println(F(" ms"));
        } else {
            Serial.print(F(" failed. Result code: "));
            Serial.println(pingResult);
            // If ping fails, skip the connect and treat as a failed attempt for this cycle
            if (attempt < MAX_LOCAL_CONNECTION_ATTEMPTS) {
                Serial.print(this->sensorName); Serial.print(F(": Waiting for retry delay (after ping fail): ")); Serial.print(LOCAL_RETRY_DELAY_MS); Serial.println(F(" ms"));
                unsigned long delayStart = millis();
                while(millis() - delayStart < LOCAL_RETRY_DELAY_MS) {
                    wdt_reset();
                    delay(50);
                }
            }
            continue; // Next attempt or exit if max attempts reached
        }

        WiFiClient wifiClient; // Create the WiFiClient for this attempt
        int currentAttemptAQI = -1; 

        Serial.print(this->sensorName); Serial.print(F(": Attempting to connect to local sensor at http://"));
        Serial.print(this->localServerIP);
        Serial.print(F(":"));
        Serial.print(this->localServerPort);
        Serial.println(F("/json"));

        wdt_reset(); 
        if (wifiClient.connect(this->localServerIP, this->localServerPort)) {
            Serial.print(this->sensorName); Serial.println(F(": connection successful."));
            wdt_reset();

            // Proceed with HTTP GET and JSON parsing
            HttpClient localClient = HttpClient(wifiClient, this->localServerIP, this->localServerPort);
            localClient.setTimeout(HTTP_CLIENT_RW_TIMEOUT_MS); // Timeout for read/write after connection

            // Proceed with GET request
            int httpCode = localClient.get("/json"); // HttpClient uses the already connected wifiClient
            if (httpCode == HTTP_SUCCESS) {
                doc.clear();
                DeserializationError error;

                // Skip headers to get to the body
                localClient.skipResponseHeaders();
                
                // Serial.print(this->sensorName); Serial.println(F(": assuming chunked response."));
                ChunkDecodingStream dechunkedStream(wifiClient);
                error = deserializeJson(doc, dechunkedStream);

                if (error) {
                    Serial.print(this->sensorName); Serial.print(F(": deserializeJson() failed for local data: "));
                    Serial.println(error.c_str());
                } else {
                    // Simplified JSON parsing logic for local sensor data
                    currentAttemptAQI = -1; // Default to -1 for this attempt
                    double pm25_for_calc = -1.0;
                    bool found_preferred_pm_value = false;

                    if (doc.is<JsonObject>()) {
                        JsonObject root = doc.as<JsonObject>();

                        if (root.containsKey("pm2_5_atm")) { // Directly check for the key with underscore
                            pm25_for_calc = root["pm2_5_atm"].as<double>();
                            if (pm25_for_calc >= 0) {
                                Serial.print(this->sensorName); Serial.println(F(": Using 'pm2_5_atm' from local sensor for AQI calculation."));
                                found_preferred_pm_value = true;
                            } else {
                                Serial.print(this->sensorName); Serial.print(F(": Invalid 'pm2_5_atm' value: ")); Serial.println(pm25_for_calc);
                                pm25_for_calc = -1.0;
                            }
                        }
                        
                        // If a preferred raw PM2.5 value was found and is valid, calculate AQI
                        if (found_preferred_pm_value) {
                            currentAttemptAQI = static_cast<int>(round(calculateAQI(pm25_for_calc)));
                            localSensorAvailable = true;
                            Serial.print(this->sensorName); Serial.print(F(": Local data processed. Raw PM2.5: ")); Serial.print(pm25_for_calc);
                            Serial.print(F(", Calculated AQI: ")); Serial.println(currentAttemptAQI);
                        } 

                        // If no pm2.5 value, fall back to sensor's pre-calculated 'pm2.5_aqi'
                        else if (root.containsKey("pm2.5_aqi")) {
                            currentAttemptAQI = root["pm2.5_aqi"].as<int>();
                            if (currentAttemptAQI >= 0) {
                                localSensorAvailable = true;
                                Serial.print(this->sensorName); Serial.print(F(": Using pre-calculated 'pm2.5_aqi' from local sensor: ")); Serial.println(currentAttemptAQI);
                            } else {
                                Serial.print(this->sensorName); Serial.print(F(": Invalid pre-calculated 'pm2.5_aqi' value: ")); Serial.println(currentAttemptAQI);
                                currentAttemptAQI = -1; // Mark as invalid
                            }
                        } else {
                            Serial.print(this->sensorName); Serial.println(F(": No suitable PM2.5 data or pre-calculated AQI found in local JSON object."));
                        }
                    } else {
                        Serial.print(this->sensorName); Serial.println(F(": Local JSON response was not a single object as expected. Cannot parse."));
                    }
                }
            } else {
                Serial.print(this->sensorName); Serial.print(F(": HTTP GET request to local sensor failed, code: "));
                Serial.println(httpCode);
            }
            
            localClient.stop(); // IMPORTANT: Stop the HttpClient to properly close connection and release resources for this attempt.

            if (currentAttemptAQI >= 0) {
                localSensorAvailable = true; // Mark as available only on final success of an attempt
                Serial.print(this->sensorName); Serial.print(F(": Free SRAM (after local success, attempt "));
                Serial.print(attempt);
                Serial.print(F("): "));
                Serial.println(getFreeMemory());
                return currentAttemptAQI; // Successfully got data in this attempt
            }
            
            // If not successful, and not the last attempt, delay before retrying
            if (attempt < MAX_LOCAL_CONNECTION_ATTEMPTS) {
                Serial.print(this->sensorName); Serial.print(F(": Delaying for "));
                Serial.print(LOCAL_RETRY_DELAY_MS);
                Serial.println(F("ms before next local attempt..."));
                unsigned long delayStart = millis();
                while(millis() - delayStart < LOCAL_RETRY_DELAY_MS) {
                    wdt_reset(); 
                    delay(50); 
                }
            }
        } else {
            Serial.println(F("WiFiClient.connect() failed."));
            wdt_reset();
            // No need to call stop() if connect returned 0/false immediately
            if (attempt < MAX_LOCAL_CONNECTION_ATTEMPTS) {
                Serial.print(this->sensorName); Serial.print(F(": Waiting for retry delay (after connect fail): ")); Serial.print(LOCAL_RETRY_DELAY_MS); Serial.println(F(" ms"));
                unsigned long delayStart = millis();
                while(millis() - delayStart < LOCAL_RETRY_DELAY_MS) {
                    wdt_reset();
                    delay(50);
                }
            }
            continue; // Try next attempt
        }
    } // End of retry loop

    localSensorAvailable = false; // Ensure this is explicitly false if all attempts failed
    Serial.println(F("All local sensor attempts failed."));
    Serial.print(this->sensorName); Serial.print(F(": Free SRAM (after all local attempts failed): ")); Serial.println(getFreeMemory());
    return -1; // Return -1 if all attempts failed
}

int PurpleAirSensor::getAPIAirQuality() {
    if (!ensureWiFiConnected()) {
        Serial.print(this->sensorName); Serial.println(F(": getAPIAirQuality: WiFi not connected. Aborting."));
        return -1;
    }

    int resultAQI = -1;

    if (this->apiKey == nullptr || this->apiKey[0] == '\0') {
        Serial.print(this->sensorName); Serial.println(F(": getAPIAirQuality: API key is missing."));
        return -1;
    }
    if (this->numSensors == 0) {
        Serial.print(this->sensorName); Serial.println(F(": getAPIAirQuality: No sensor IDs provided for API call."));
        return -1;
    }

    Serial.print(this->sensorName); Serial.println(F(": getAPIAirQuality: --- Start ---"));
    Serial.print(this->sensorName); Serial.println(F(": Free SRAM (before API request): ")); Serial.println(getFreeMemory());

    WiFiSSLClient secureClient; 
    HttpClient apiClient = HttpClient(secureClient, this->apiServerHost, this->apiPort);
    apiClient.setTimeout(HTTP_CLIENT_RW_TIMEOUT_MS);

    // Define a buffer for the API path
    char apiPathBuffer[200]; // Increased buffer size for safety
    strcpy(apiPathBuffer, "/v1/sensors?fields=pm2.5_10minute&show_only=");

    for (int i = 0; i < this->numSensors; ++i) {
        char sensorIdStr[8]; // Buffer for one sensor ID (e.g., 123456 + null)
        snprintf(sensorIdStr, sizeof(sensorIdStr), "%d", this->sensorIDs[i]);
        
        // Ensure there's space before concatenating sensor ID
        if (strlen(apiPathBuffer) + strlen(sensorIdStr) < sizeof(apiPathBuffer) -1) { // -1 for null terminator
            strncat(apiPathBuffer, sensorIdStr, sizeof(apiPathBuffer) - strlen(apiPathBuffer) - 1);
        } else {
            Serial.println(F("API path buffer too small for sensor ID!"));
            // Handle error: maybe return -1 or skip this API call
            return -1; 
        }

        if (i < this->numSensors - 1) {
            // Ensure there's space for separator
            if (strlen(apiPathBuffer) + strlen(API_SENSOR_SEPARATOR) < sizeof(apiPathBuffer) -1) {
                 strncat(apiPathBuffer, API_SENSOR_SEPARATOR, sizeof(apiPathBuffer) - strlen(apiPathBuffer) - 1);
            } else {
                Serial.println(F("API path buffer too small for separator!"));
                return -1; // Handle error
            }
        }
    }
    
    // Append max_age parameter
    char maxAgeStr[20]; // Buffer for "&max_age=XXXXX"
    snprintf(maxAgeStr, sizeof(maxAgeStr), "&max_age=%d", MAX_SENSOR_AGE);
    if (strlen(apiPathBuffer) + strlen(maxAgeStr) < sizeof(apiPathBuffer) -1) {
        strncat(apiPathBuffer, maxAgeStr, sizeof(apiPathBuffer) - strlen(apiPathBuffer) - 1);
    } else {
        Serial.println(F("API path buffer too small for max_age parameter!"));
        // Handle error: maybe return -1 or skip this API call
        return -1;
    }

    // Ensure watchdog is reset before making network calls that might take time
    wdt_reset();

    Serial.print(this->sensorName); Serial.print(F(": API Request Path: ")); Serial.println(apiPathBuffer);

    Serial.print(this->sensorName); Serial.print(F(": Attempting Full API Request URL: https://"));
    Serial.print(this->apiServerHost);
    Serial.println(apiPathBuffer);

    apiClient.beginRequest();
    apiClient.get(apiPathBuffer);
    apiClient.sendHeader("X-API-Key", this->apiKey); 
    apiClient.sendHeader(HTTP_HEADER_CONTENT_TYPE, "application/json");
    apiClient.endRequest();

    int httpCode = apiClient.responseStatusCode();

    if (httpCode == 200) {
        doc.clear(); 
        DeserializationError error;

        // Skip headers to get to the body
        apiClient.skipResponseHeaders();

        // API calls now deserialize directly from secureClient
        error = deserializeJson(doc, secureClient); 

        if (error) {
            Serial.print(this->sensorName); Serial.print(F(": deserializeJson() failed for API data: "));
            Serial.println(error.c_str());
            apiClient.stop(); // Stop client before returning
            return -1;
        }

        // --- New parsing logic for "fields" and "data" arrays ---
        if (!doc.containsKey("fields") || !doc["fields"].is<JsonArray>() || 
            !doc.containsKey("data") || !doc["data"].is<JsonArray>()) {
            Serial.println(F("API JSON response missing 'fields' or 'data' array, or they are not arrays."));
            apiClient.stop(); // Stop client before returning
            return -1;
        }

        JsonArray fieldsArray = doc["fields"].as<JsonArray>();
        JsonArray dataArray = doc["data"].as<JsonArray>();

        int pm25_10m_idx = -1;
        int sensor_idx_idx = -1; // To potentially identify which sensor reading it is, if needed later

        for (int i = 0; i < fieldsArray.size(); i++) {
            if (fieldsArray[i].is<const char*>()) { // Check type before strcmp
                if (strcmp(fieldsArray[i].as<const char*>(), "pm2.5_10minute") == 0) {
                    pm25_10m_idx = i;
                }
                if (strcmp(fieldsArray[i].as<const char*>(), "sensor_index") == 0) {
                    sensor_idx_idx = i;
                }
            }
        }

        if (pm25_10m_idx == -1) {
            Serial.print(this->sensorName); Serial.println(F(": Could not find 'pm2.5_10minute' in API 'fields' array."));
            apiClient.stop(); // Stop client before returning
            return -1;
        }

        double totalPM25 = 0;
        int validSensorCount = 0;

        for (JsonVariant sensor_data_row_variant : dataArray) {
            if (!sensor_data_row_variant.is<JsonArray>()) {
                Serial.println(F("Item in 'data' is not an array. Skipping."));
                continue;
            }
            JsonArray sensor_data_row = sensor_data_row_variant.as<JsonArray>();

            // Ensure the row has enough elements for the pm2.5_10minute index
            if (pm25_10m_idx >= sensor_data_row.size()) {
                Serial.println(F("Sensor data row is too short for pm2.5_10minute index. Skipping."));
                continue;
            }

            JsonVariant pm25_variant = sensor_data_row[pm25_10m_idx];
            if (!pm25_variant.is<float>() && !pm25_variant.is<double>() && !pm25_variant.is<int>()) {
                Serial.println(F("PM2.5 value in data row is not a number. Skipping."));
                continue;
            }

            double pm25_value = pm25_variant.as<double>();
            if (pm25_value < 0) { 
                Serial.println(F("Warning: API PM2.5 value is negative. Treating as invalid for this sensor."));
                continue; 
            }
            totalPM25 += pm25_value;
            validSensorCount++;
        }
        // --- End new parsing logic ---

        if (validSensorCount > 0) {
            double avgPM25 = totalPM25 / validSensorCount;
            resultAQI = static_cast<int>(round(calculateAQI(avgPM25)));
            Serial.print(this->sensorName); Serial.print(F(": API: Avg PM2.5: ")); Serial.print(avgPM25);
            Serial.print(F(", Calculated AQI: ")); Serial.println(resultAQI);
        } else {
            Serial.println(F("API: No valid sensor data found."));
            resultAQI = -1; // No valid data from API
        }

    } else {
        Serial.print(this->sensorName); Serial.print(F(": API request failed, HTTP code: ")); Serial.println(httpCode);
        resultAQI = -1;
    }
    apiClient.stop();
    Serial.print(this->sensorName); Serial.print(F(": Free SRAM (after API request): ")); Serial.println(getFreeMemory());
    Serial.print(this->sensorName); Serial.println(F(": getAPIAirQuality: --- End ---"));
    return resultAQI;
}

double PurpleAirSensor::calculateAQI(double pm2p5) {
    if (pm2p5 < 0) return 0; 

    // Using U.S. EPA PM2.5 AQI calculation breakpoints
    if (pm2p5 > 350.5) return linearInterpolation(350.5, 500.4, 401.0, 500.0, pm2p5, true);
    if (pm2p5 > 250.5) return linearInterpolation(250.5, 350.4, 301.0, 400.0, pm2p5, false);
    if (pm2p5 > 150.5) return linearInterpolation(150.5, 250.4, 201.0, 300.0, pm2p5, false);
    if (pm2p5 > 55.5)  return linearInterpolation(55.5, 150.4, 151.0, 200.0, pm2p5, false);
    if (pm2p5 > 35.5)  return linearInterpolation(35.5, 55.4, 101.0, 150.0, pm2p5, false);
    if (pm2p5 > 12.1)  return linearInterpolation(12.1, 35.4, 51.0, 100.0, pm2p5, false);
    return linearInterpolation(0.0, 12.0, 0.0, 50.0, pm2p5, false); // Covers 0 <= pm2p5 <= 12.0
}

double PurpleAirSensor::linearInterpolation(double cLow, double cHigh, double iLow, double iHigh, 
                                          double pointX, bool trim) {
    if (trim && pointX > cHigh) pointX = cHigh; 
    if (trim && pointX < cLow) pointX = cLow; // Also trim to lower bound if specified

    if (cHigh == cLow) { // Avoid division by zero if concentrations are the same
        // If pointX is at or above cLow (which equals cHigh), use iHigh. Otherwise, iLow.
        // This handles cases where the range is a single point.
        return (pointX >= cLow) ? iHigh : iLow;
    }

    double slope = (iHigh - iLow) / (cHigh - cLow);
    double aqi = slope * (pointX - cLow) + iLow;
    
    return aqi;
}

bool PurpleAirSensor::isLocalConfigured() const {
    return (this->localServerIP != nullptr && this->localServerIP[0] != '\0');
}

unsigned long PurpleAirSensor::getTimeUntilNextLocalCheck() const {
    if (!isLocalConfigured()) return (unsigned long)LOCAL_SENSOR_DELAY; // Or some max value
    long timePassed = millis() - lastLocalCheckTime;
    if (timePassed >= (long)LOCAL_SENSOR_DELAY) return 0;
    return (unsigned long)LOCAL_SENSOR_DELAY - timePassed;
}

unsigned long PurpleAirSensor::getTimeUntilNextApiCheck() const {
    // API check depends on API key and sensor IDs being present
    bool apiConfigured = (this->apiKey != nullptr && this->apiKey[0] != '\0' && this->numSensors > 0);
    if (!apiConfigured) return (unsigned long)PURPLE_AIR_DELAY; // Or some max value

    long timePassed = millis() - lastApiCheckTime;
    if (timePassed >= (long)PURPLE_AIR_DELAY) return 0;
    return (unsigned long)PURPLE_AIR_DELAY - timePassed;
} 