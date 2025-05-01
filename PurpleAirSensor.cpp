#include "PurpleAirSensor.h"
#include "arduino_secrets.h"
#include <Arduino.h>
#include <ArduinoJson.h>
#include <ArduinoHttpClient.h>
#include <WiFiNINA.h> // Ensure WiFi library is included
#include "constants.h" // Include for delay constants

PurpleAirSensor::PurpleAirSensor(const char* apiKey, const char* server, int port, 
                                const char* localServer, int localPort)
    : apiKey(apiKey), server(server), port(port), 
      localServer(localServer), localPort(localPort),
      lastLocalCheckTime(0), lastApiCheckTime(0), // Initialize timestamps
      currentAQI(-1), // Initialize AQI to an invalid value
      localSensorAvailable(false) {}

void PurpleAirSensor::begin() {
    // Initialize WiFi connection
    Serial.println("WIFI STATUS: attempting to connect ...");
    int status = WiFi.begin(SECRET_SSID, SECRET_PASS);

    // Wait for connection with timeout (e.g., 15 seconds)
    unsigned long startAttemptTime = millis();
    while (WiFi.status() != WL_CONNECTED && millis() - startAttemptTime < 15000) {
        Serial.print(".");
        delay(500); // Wait 500ms between status checks
    }
    Serial.println(); // Newline after dots

    // Check connection result
    if (WiFi.status() == WL_CONNECTED) {
        Serial.println("WIFI STATUS: connected\n");
    } else {
        Serial.println("WIFI STATUS: connection failed\n");
        // Optional: Add code here to handle connection failure (e.g., halt, retry later)
        while(true); // Halt execution if connection fails
    }
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
        fetchedAQI = getLocalAirQuality(); // This method updates localSensorAvailable
        lastLocalCheckTime = currentTime; // Update time of last local check attempt
        
        if (fetchedAQI > 0) {
            // Local sensor success
            Serial.println("Local sensor success.");
            currentAQI = fetchedAQI;
            updated = true;
            localSucceeded = true;
            // Successfully updated from local, no need to check API now
            return updated; // Exit early
        } else {
            // Local sensor failed, proceed to check API below
            Serial.println("Local sensor failed.");
        }
    } // End of local sensor check block

    // --- Try API Sensor --- 
    // Check API only if: 
    // 1) Local wasn't attempted (because not configured or not time yet) OR 
    // 2) Local was attempted but failed
    // AND only if enough time has passed since the last API check.
    if ((!attemptedLocal || !localSucceeded) && 
        (currentTime - lastApiCheckTime >= (unsigned long)PURPLE_AIR_DELAY)) 
    {
        Serial.println("Polling PurpleAir API...");
        fetchedAQI = getAPIAirQuality();
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
    } else if (!updated && !localConfigured) {
       // This case means local wasn't configured, and it wasn't time to check API.
       // Add more detailed logging if desired.
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
    
    Serial.println("Requesting data from local PurpleAir sensor...");
    
    WiFiClient wifiClient; // Create a WiFiClient instance for this request
    HttpClient localClient = HttpClient(wifiClient, localServer, localPort);
    
    // Log the full URL being used
    String fullUrl = "http://" + String(localServer) + ":" + String(localPort) + "/json";
    Serial.println("Local sensor URL: " + fullUrl);
    
    // Check WiFi status
    if (WiFi.status() != WL_CONNECTED) {
        Serial.println("ERROR: WiFi not connected");
        return 0;
    }
    Serial.println("WiFi status: Connected");
    Serial.print("Local IP: ");
    Serial.println(WiFi.localIP());
    
    Serial.println("Attempting to request data from local sensor using ArduinoHttpClient...");
    localClient.setTimeout(10000); // 10 second response timeout

    // Send the GET request
    int httpCode = localClient.get("/json");

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
        // Parse response body
        String response = localClient.responseBody();
        localClient.stop(); // Close connection after reading body
        
        DeserializationError error = deserializeJson(doc, response);
        if (error) {
            Serial.print(F("deserializeJson() failed: "));
            Serial.println(error.f_str());
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
    } else {
        Serial.println("ERROR: failed to access local PurpleAir sensor (Non-200 status)");
        localClient.stop(); // Ensure connection is closed
    }
    return resultAQI; // Return 0 on failure
}

int PurpleAirSensor::getAPIAirQuality() {
    int resultAQI = 0; // Default to 0 (failure)
    Serial.println("Requesting data from PurpleAir API using ArduinoHttpClient...");

    WiFiClient wifiClient; // Create a WiFiClient instance for this request
    HttpClient client = HttpClient(wifiClient, server, port);

    // Build the sensor IDs string
    String sensorIds = String(SECRET_SENSOR_IDS[0]);
    for (int i = 1; i < N_SENSORS; i++) {
        sensorIds += "%2C" + String(SECRET_SENSOR_IDS[i]);
    }

    String requestPath = "/v1/sensors?fields=pm2.5_10minute&show_only=" + sensorIds + 
                          "&max_age=" + String(MAX_SENSOR_AGE);
    Serial.println("Request Path: " + requestPath);

    client.setTimeout(10000); // 10 second response timeout

    // Add header and make the request
    client.beginRequest();
    client.get(requestPath);
    client.sendHeader("X-API-Key", apiKey);
    client.sendHeader("User-Agent", "Arduino/1.0");
    client.endRequest(); // Send the request

    // Get the status code
    int statusCode = client.responseStatusCode();
    Serial.print("API HTTP Status Code: ");
    Serial.println(statusCode);
    String response = client.responseBody();
    client.stop(); // Close the connection

    if (statusCode == 200) {
        DeserializationError error = deserializeJson(doc, response);
        if (error) {
            Serial.print(F("deserializeJson() failed: "));
            Serial.println(error.f_str());
            return 0;
        }
        
        JsonArray data = doc["data"];    
        int n_sensors_found = data.size();
        if (n_sensors_found == 0) {
            Serial.println("ERROR: No sensor data returned from API");
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
             return 0;
        }
    } else {
        Serial.println("ERROR: failed to access PurpleAir API (Status code: " + String(statusCode) + ")");
        // Consider previous logic: Maybe return a high value but not if status is e.g. 401 (auth error)
        // For now, return 0 on API error
        return 0; 
    }

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

// --- Getter implementations --- //

bool PurpleAirSensor::isLocalConfigured() const {
    return (this->localServer != nullptr && this->localServer[0] != '\0');
}

unsigned long PurpleAirSensor::getTimeUntilNextLocalCheck() const {
    // Constants are defined in constants.h and are in milliseconds
    // Remove the preprocessor check as it doesn't work well with constexpr
    // #ifndef LOCAL_SENSOR_DELAY
    //     #error "LOCAL_SENSOR_DELAY not defined..." 
    // #endif
    unsigned long nextCheckTime = lastLocalCheckTime + (unsigned long)LOCAL_SENSOR_DELAY; // Use constant directly (it's in ms)
    unsigned long currentTime = millis();
    if (nextCheckTime <= currentTime) {
        return 0; // Time has already passed or is now
    } else {
        return nextCheckTime - currentTime;
    }
}

unsigned long PurpleAirSensor::getTimeUntilNextApiCheck() const {
    // Constants are defined in constants.h and are in milliseconds
    // Remove the preprocessor check
    // #ifndef PURPLE_AIR_DELAY
    //     #error "PURPLE_AIR_DELAY not defined..." 
    // #endif
    unsigned long nextCheckTime = lastApiCheckTime + (unsigned long)PURPLE_AIR_DELAY; // Use constant directly (it's in ms)
    unsigned long currentTime = millis();
    if (nextCheckTime <= currentTime) {
        return 0; // Time has already passed or is now
    } else {
        return nextCheckTime - currentTime;
    }
} 