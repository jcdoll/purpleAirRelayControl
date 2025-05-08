#include "PurpleAirSensor.h"
#include "arduino_secrets.h"
#include <Arduino.h>
#include <ArduinoJson.h>
#include <ArduinoHttpClient.h>
#include <WiFiNINA.h> // Ensure WiFi library is included
#include "constants.h" // Include for delay constants
#include <wdt_samd21.h> // Include the library header here too for wdt_reset()
#include <malloc.h> // Required for mallinfo()

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
#endif
}

PurpleAirSensor::PurpleAirSensor(const char* apiKey, const char* server, int port, 
                                const char* localServer, int localPort)
    : apiKey(apiKey), server(server), port(port), 
      localServer(localServer), localPort(localPort),
      lastLocalCheckTime(0), lastApiCheckTime(0), // Initialize timestamps
      currentAQI(-1), // Initialize AQI to an invalid value
      localSensorAvailable(false) {}

void PurpleAirSensor::begin() {
    // Initialize WiFi connection
    Serial.println(F("WIFI STATUS: Attempting to connect..."));
    
    // Outer loop to keep retrying connection indefinitely
    while (WiFi.status() != WL_CONNECTED) {
        Serial.println(F("Initiating WiFi connection attempt..."));
        int status = WiFi.begin(SECRET_SSID, SECRET_PASS);
        if (status != WL_CONNECTED) { // Log if begin immediately fails (though unlikely to be the final status)
            Serial.print(F("WiFi.begin status: ")); Serial.println(status);
        }

        // Inner loop: Wait for connection with a timeout (e.g., 15 seconds)
        unsigned long startAttemptTime = millis();
        while (WiFi.status() != WL_CONNECTED && millis() - startAttemptTime < 15000) {
            Serial.print(".");
            // Use the correct watchdog reset function for the current setup
            wdt_reset(); 
            delay(500); // Wait 500ms between status checks
        }
        Serial.println(); // Newline after dots or connection success

        // Check if the inner loop timed out without connecting
        if (WiFi.status() != WL_CONNECTED) {
            Serial.println(F("WIFI STATUS: Connection failed on this attempt."));
            Serial.println(F("Retrying in 5 seconds..."));
            // Delay for 5 seconds, petting watchdog frequently
            unsigned long retryDelayStart = millis();
            while(millis() - retryDelayStart < 5000) {
                wdt_reset();
                delay(100); // Short delay to allow background tasks/watchdog
            }
        } else {
            // If connected, the outer loop condition will be false next iteration
            Serial.println(F("WIFI STATUS: Connected!"));
        }
        // Ensure watchdog is reset before the next outer loop iteration (retry attempt)
        wdt_reset();
    }
    // Exited the outer loop, means WiFi is connected.
    Serial.println(); // Extra newline for clarity
}

bool PurpleAirSensor::updateAQI() {
    unsigned long currentTime = millis();
    bool updated = false;
    int fetchedAQI = -1;
    bool attemptedLocal = false;
    bool localSucceeded = false;

    // --- Try Local Sensor --- 
    // First check if local server IP is configured (not null and not empty string)
    bool localConfigured = (this->localServer != nullptr && this->localServer[0] != '\0');

    // Check if configured AND if it's time to poll
    if (localConfigured && (currentTime - lastLocalCheckTime >= (unsigned long)LOCAL_SENSOR_DELAY)) {
        attemptedLocal = true;
        Serial.println("Polling local sensor...");
        wdt_reset(); // Use library function
        fetchedAQI = getLocalAirQuality();
        wdt_reset(); // Use library function
        lastLocalCheckTime = currentTime; // Update time of last local check attempt
        
        if (fetchedAQI > 0) {
            Serial.println("Local sensor success.");
            currentAQI = fetchedAQI;
            updated = true;
            localSucceeded = true;
            return updated; // Exit early
        } else {
            // Local sensor failed, proceed to check API below
            Serial.println("Local sensor failed.");
        }
    }

    // --- Try API Sensor --- 
    // Check API only if: 
    // 1) Local wasn't attempted (because not configured or not time yet) OR 
    // 2) Local was attempted but failed
    // AND only if enough time has passed since the last API check.
    if ((!localConfigured || (attemptedLocal && !localSucceeded)) &&
        (currentTime - lastApiCheckTime >= (unsigned long)PURPLE_AIR_DELAY))
    {
        Serial.println("Polling PurpleAir API...");
        wdt_reset(); // Use library function
        fetchedAQI = getAPIAirQuality();
        wdt_reset(); // Use library function
        lastApiCheckTime = currentTime; // Update time of last API check attempt

        if (fetchedAQI > 0) {
             Serial.println("API success.");
             currentAQI = fetchedAQI;
             updated = true;
        } else {
             Serial.println("API failed.");
             // Keep previous currentAQI if API fails
        }
    }

    // Optional: Log if no update occurred during this call 
    if (!updated && !attemptedLocal && localConfigured) {
       // This case means local is configured, but it wasn't time to check it, and it also wasn't time to check API.
       // Add more detailed logging if desired.
       Serial.println("No sensor update: Local configured, but not time for local or API check.");
       Serial.print("  Time until next local check: "); Serial.print(getTimeUntilNextLocalCheck() / 1000); Serial.println("s");
       Serial.print("  Time until next API check: "); Serial.print(getTimeUntilNextApiCheck() / 1000); Serial.println("s");
    } else if (!updated && attemptedLocal && !localSucceeded && localConfigured) {
       // This case means local is configured, was attempted, but failed, AND it wasn't time for API check.
       Serial.println("No sensor update: Local configured, attempted but failed. Not time for API check.");
       Serial.print("  Time until next API check: "); Serial.print(getTimeUntilNextApiCheck() / 1000); Serial.println("s");
    } else if (!updated && !localConfigured) {
       // This case means local wasn't configured, and it wasn't time to check API.
       Serial.println("No sensor update: Local not configured, and not time for API check.");
       Serial.print("  Time until next API check: "); Serial.print(getTimeUntilNextApiCheck() / 1000); Serial.println("s");
    } else if (!updated) {
       Serial.println("No sensor update: Reason not specifically logged, check conditions.");
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
void PurpleAirSensor::forceInitialUpdate() {
    Serial.println("Performing initial sensor data fetch...");
    int fetchedAQI = -1;
    unsigned long currentTime = millis(); // Get current time for timestamping

    // --- Try Local Sensor First --- 
    bool localConfigured = (this->localServer != nullptr && this->localServer[0] != '\0');
    if (localConfigured) {
        Serial.println("Initial check: Polling local sensor...");
        fetchedAQI = getLocalAirQuality(); // Updates localSensorAvailable flag internally
        lastLocalCheckTime = currentTime; // Set timestamp for the first local check

        if (fetchedAQI > 0) {
            Serial.println("Initial check: Local sensor success.");
            currentAQI = fetchedAQI;
            // If local worked, we don't need to check API immediately for the initial fetch
            // Also set the API timestamp so we don't immediately check it in the first loop()
            lastApiCheckTime = currentTime; 
            return; 
        } else {
            Serial.println("Initial check: Local sensor failed.");
            // Proceed to check API as fallback
        }
    } else {
         Serial.println("Initial check: Local sensor not configured.");
         lastLocalCheckTime = currentTime; // Still note the time we would have checked
         // Proceed to check API
    }

    // --- Try API Sensor (if local failed or wasn't configured) ---
    Serial.println("Initial check: Polling PurpleAir API...");
    fetchedAQI = getAPIAirQuality();
    lastApiCheckTime = currentTime; // Set timestamp for the first API check

    if (fetchedAQI > 0) {
         Serial.println("Initial check: API success.");
         currentAQI = fetchedAQI;
    } else {
         Serial.println("Initial check: API failed.");
         // Keep currentAQI as -1 if both fail initially
    }
}

int PurpleAirSensor::getLocalAirQuality() {
    // Reset availability flag before attempt
    localSensorAvailable = false; 
    int resultAQI = 0; // Default to 0 (failure)
    
    Serial.println(F("getLocalAirQuality: --- Start --- "));
    Serial.print(F("Free SRAM (before local request): ")); Serial.println(getFreeMemory());
    
    WiFiClient wifiClient; // Create a WiFiClient instance for this request
    HttpClient localClient = HttpClient(wifiClient, localServer, localPort);
    
    // Log the full URL being used
    char fullUrlBuffer[128]; // Increased buffer size for safety
    snprintf(fullUrlBuffer, sizeof(fullUrlBuffer), "http://%s:%d/json", localServer, localPort);
    Serial.println("Local sensor URL: " + String(fullUrlBuffer)); // OK to use String for immediate print
    
    // Check WiFi status
    if (WiFi.status() != WL_CONNECTED) {
        Serial.println("ERROR: WiFi not connected");
        return 0;
    }
    Serial.println("WiFi status: Connected");
    Serial.print("Local IP: ");
    Serial.println(WiFi.localIP());
    
    Serial.println("Attempting to request data from local sensor using ArduinoHttpClient...");
    localClient.setTimeout(2000); // Wait for up to 2 seconds

    // Send the GET request
    int httpCode = localClient.get("/json"); // Path is fixed, no need to pass fullUrlBuffer if base URL set in client constructor
    // However, ArduinoHttpClient typically takes full path in get() if base URL not part of constructor logic for this specific client object.
    // Assuming get("/json") works because localServer and localPort were used in HttpClient constructor.
    // If it needs the full path, it would be: localClient.get(fullUrlBuffer);
    // For now, let's stick to the original get("/json") if it was working.

    if (httpCode != HTTP_SUCCESS) {
        Serial.print("HTTP GET failed, error: ");
        Serial.println(httpCode); // Print the error code returned by the library
        localClient.stop(); // Close the connection
        return 0;
    }

    // Get the status code
    int statusCode = localClient.responseStatusCode();
    Serial.print("HTTP Status Code: ");
    Serial.println(statusCode);

    if (statusCode == 200) {
        // TEMPORARY TEST: Revert to responseBody() to see if it handles de-chunking
        String response = localClient.responseBody();
        localClient.stop(); // Stop client AFTER getting the body or on error

        DeserializationError error = deserializeJson(doc, response); // Parse from the String

        if (error) {
            Serial.print(F("deserializeJson() failed: "));
            Serial.println(error.f_str());
            Serial.print(F("Free SRAM (after local parse error): ")); Serial.println(getFreeMemory());
            return 0;
        }
        
        double aqi_a = doc["pm2.5_aqi"].as<double>();
        double aqi_b = doc["pm2.5_aqi_b"].as<double>();
        double avg_aqi = (aqi_a + aqi_b) / 2.0;
        
        Serial.println("Local sensor Channel A AQI: " + String(aqi_a));
        Serial.println("Local sensor Channel B AQI: " + String(aqi_b));
        Serial.println("Local sensor Average AQI: " + String(avg_aqi));
        
        resultAQI = (int)avg_aqi;
        if (resultAQI > 0) { // Consider it available only if parse and calculation succeed
            localSensorAvailable = true; 
        }
        Serial.print(F("Free SRAM (after local success): ")); Serial.println(getFreeMemory());
    } else {
        Serial.println("ERROR: failed to access local PurpleAir sensor (Non-200 status)");
        localClient.stop(); // Ensure connection is closed
        Serial.print(F("Free SRAM (after local HTTP error): ")); Serial.println(getFreeMemory());
    }
    return resultAQI; // Return 0 on failure
}

int PurpleAirSensor::getAPIAirQuality() {
    int resultAQI = 0; // Default to 0 (failure)
    Serial.println(F("getAPIAirQuality: --- Start --- "));
    Serial.print(F("Free SRAM (before API request): ")); Serial.println(getFreeMemory());

    WiFiSSLClient wifiSSLClient; // Use WiFiSSLClient for HTTPS for PurpleAir API
    HttpClient client = HttpClient(wifiSSLClient, server, port);
    client.setTimeout(6000); // Set timeout for API client

    // Build the sensor IDs string using char array
    char sensorIdsBuffer[128]; // Max N_SENSORS * (avg_id_length + 3 for %2C) + 1 for null. Adjust size as needed.
    sensorIdsBuffer[0] = '\0'; // Start with an empty string
    for (int i = 0; i < N_SENSORS; i++) {
        char singleIdBuffer[10]; // Buffer for one sensor ID
        snprintf(singleIdBuffer, sizeof(singleIdBuffer), "%d", SECRET_SENSOR_IDS[i]);
        if (i > 0) {
            strncat(sensorIdsBuffer, "%2C", sizeof(sensorIdsBuffer) - strlen(sensorIdsBuffer) - 1);
        }
        strncat(sensorIdsBuffer, singleIdBuffer, sizeof(sensorIdsBuffer) - strlen(sensorIdsBuffer) - 1);
    }

    // Build requestPath using char array
    char requestPathBuffer[256]; // Adjusted size for full path
    snprintf(requestPathBuffer, sizeof(requestPathBuffer), 
             "/v1/sensors?fields=pm2.5_10minute&show_only=%s&max_age=%d", 
             sensorIdsBuffer, MAX_SENSOR_AGE);
    Serial.println("Request Path: " + String(requestPathBuffer)); // OK for print

    // Add header and make the request
    wdt_reset();
    client.beginRequest();
    client.get(requestPathBuffer); // Use the char buffer
    client.sendHeader("X-API-Key", apiKey);
    client.sendHeader("User-Agent", "Arduino/1.0");
    client.endRequest(); // Send the request
    wdt_reset();
    
    // Get the status code
    int statusCode = client.responseStatusCode();
    Serial.print("API HTTP Status Code: ");
    Serial.println(statusCode);

    if (statusCode == 200) {
        // Use responseBody() and parse from String
        String response = client.responseBody();
        client.stop(); // Stop client after getting body

        DeserializationError error = deserializeJson(doc, response); // Parse from String

        if (error) {
            Serial.print(F("deserializeJson() failed: "));
            Serial.println(error.f_str());
            Serial.print(F("Free SRAM (after API parse error): ")); Serial.println(getFreeMemory());
            return 0;
        }
        
        JsonArray data = doc["data"];    
        int n_sensors_found = data.size();
        if (n_sensors_found == 0) {
            Serial.println("ERROR: No sensor data returned from API");
            Serial.print(F("Free SRAM (after API data error): ")); Serial.println(getFreeMemory());
            return 0; // Or handle appropriately
        }
        double PM2p5 = 0;
        int valid_sensor_count = 0;
        
        for (int i = 0; i < n_sensors_found; i++) {
            // Check if the data point is valid before adding
            if (!data[i][1].isNull()) {
              PM2p5 += data[i][1].as<double>();
              valid_sensor_count++;
            } else {
              Serial.print("Warning: Null PM2.5 value for sensor index ");
              Serial.println(i);
            } 
        }
        if (valid_sensor_count > 0) {
             PM2p5 /= valid_sensor_count; // Avoid division by zero
             resultAQI = (int)calculateAQI(PM2p5);
             Serial.println("Average AQI after conversion: " + String(resultAQI));
        } else {
             Serial.println("ERROR: All sensors returned null data from API");
             Serial.print(F("Free SRAM (after API data error): ")); Serial.println(getFreeMemory());
             return 0;
        }
    } else {
        Serial.println("ERROR: failed to access PurpleAir API (Status code: " + String(statusCode) + ")");
        client.stop(); // Ensure client is stopped on non-200 response
        Serial.print(F("Free SRAM (after API HTTP error): ")); Serial.println(getFreeMemory());
        return 0; 
    }

    Serial.print(F("Free SRAM (after API success): ")); Serial.println(getFreeMemory());
    return resultAQI;
}

double PurpleAirSensor::calculateAQI(double pm2p5) {
    const int N = 8;
    bool trim = true;  
    double pmValues[N] = {0, 12, 35.4, 55.4, 150.4, 250.4, 350.4, 500.4};
    double aqiValues[N] = {0, 50, 100, 150, 200, 300, 400, 500};
    return linearInterpolation(pmValues, aqiValues, N, pm2p5, trim);  
}

double PurpleAirSensor::linearInterpolation(double xValues[], double yValues[], int numValues, 
                                          double pointX, bool trim) {
    if (trim) {
        if (pointX <= xValues[0]) return yValues[0];
        if (pointX >= xValues[numValues - 1]) return yValues[numValues - 1];
    }

    int i = 0;
    double rst = 0;
    if (pointX <= xValues[0]) {
        i = 0;
        double t = (pointX - xValues[i]) / (xValues[i + 1] - xValues[i]);
        rst = yValues[i] * (1 - t) + yValues[i + 1] * t;
    } else if (pointX >= xValues[numValues - 1]) {
        double t = (pointX - xValues[numValues - 2]) / (xValues[numValues - 1] - xValues[numValues - 2]);
        rst = yValues[numValues - 2] * (1 - t) + yValues[numValues - 1] * t;
    } else {
        while (pointX >= xValues[i + 1]) i++;
        double t = (pointX - xValues[i]) / (xValues[i + 1] - xValues[i]);
        rst = yValues[i] * (1 - t) + yValues[i + 1] * t;
    }

    return rst;
}

bool PurpleAirSensor::isLocalConfigured() const {
    return (this->localServer != nullptr && this->localServer[0] != '\0');
}

unsigned long PurpleAirSensor::getTimeUntilNextLocalCheck() const {
    unsigned long nextCheckTime = lastLocalCheckTime + (unsigned long)LOCAL_SENSOR_DELAY; // Use constant directly (it's in ms)
    unsigned long currentTime = millis();
    if (nextCheckTime <= currentTime) {
        return 0; // Time has already passed or is now
    } else {
        return nextCheckTime - currentTime;
    }
}

unsigned long PurpleAirSensor::getTimeUntilNextApiCheck() const {
    unsigned long nextCheckTime = lastApiCheckTime + (unsigned long)PURPLE_AIR_DELAY; // Use constant directly (it's in ms)
    unsigned long currentTime = millis();
    if (nextCheckTime <= currentTime) {
        return 0; // Time has already passed or is now
    } else {
        return nextCheckTime - currentTime;
    }
} 