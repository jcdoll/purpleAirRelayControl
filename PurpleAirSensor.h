#pragma once

#include <WiFiNINA.h>
#include <ArduinoHttpClient.h>
#include <ArduinoJson.h>
#include "constants.h"

class PurpleAirSensor {
public:
    PurpleAirSensor(const char* sensorName,
                    const char* apiKey, const int* sensorIDs, int numSensors, 
                    const char* apiServerHost, int apiPort, 
                    const char* localServerIP = nullptr, int localServerPort = 80);
    
    void begin();

    // Updates the current AQI based on polling logic. Returns true if a new value was obtained.
    // Takes masterCurrentTime to help synchronize multiple sensor instances.
    // verboseLog controls detailed serial output for this specific call.
    bool updateAQI(unsigned long masterCurrentTime, bool verboseLog = true);

    // Gets the last successfully obtained AQI value.
    int getCurrentAQI() const;

    // Checks if the local sensor has responded successfully recently.
    bool isLocalAvailable() const;

    // Forces an immediate attempt to update AQI, ignoring timers.
    // Takes masterCurrentTime to help synchronize multiple sensor instances.
    void forceInitialUpdate(unsigned long masterCurrentTime);
    
    // Static method for ensuring WiFi is connected
    static bool ensureWiFiConnected();

    // Timing information getters
    bool isLocalConfigured() const;
    unsigned long getTimeUntilNextLocalCheck() const; // Returns milliseconds
    unsigned long getTimeUntilNextApiCheck() const;   // Returns milliseconds
    
private:
    int getLocalAirQuality();
    int getAPIAirQuality();
    double calculateAQI(double pm2p5);
    double linearInterpolation(double cLow, double cHigh, double iLow, double iHigh, double pointX, bool trim);
    
    const char* sensorName;
    const char* apiKey;
    const int* sensorIDs;
    int numSensors;
    const char* apiServerHost;
    int apiPort;
    const char* localServerIP;
    int localServerPort;
    
    static const size_t JSON_DOC_SIZE = 4096;
    static StaticJsonDocument<JSON_DOC_SIZE> doc;
    
    long lastLocalCheckTime; // Timestamp of the last attempt to check local sensor
    long lastApiCheckTime;   // Timestamp of the last attempt to check API
    int currentAQI;          // Last valid AQI reading obtained
    bool localSensorAvailable; // Flag indicating if local sensor responded successfully last time
};
