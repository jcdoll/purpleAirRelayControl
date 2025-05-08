#pragma once

#include <WiFiNINA.h>
#include <ArduinoHttpClient.h>
#include <ArduinoJson.h>
#include "constants.h"

class PurpleAirSensor {
public:
    PurpleAirSensor(const char* apiKey, const char* server, int port, const char* localServer = nullptr, int localPort = 80);
    
    void begin();
    // Updates the current AQI based on polling logic. Returns true if a new value was obtained.
    bool updateAQI();
    // Gets the last successfully obtained AQI value.
    int getCurrentAQI() const;
    // Checks if the local sensor has responded successfully recently.
    bool isLocalAvailable() const;
    // Forces an immediate attempt to update AQI, ignoring timers.
    void forceInitialUpdate();
    
    // Timing information getters
    bool isLocalConfigured() const;
    unsigned long getTimeUntilNextLocalCheck() const; // Returns milliseconds
    unsigned long getTimeUntilNextApiCheck() const;   // Returns milliseconds
    
private:
    int getLocalAirQuality();
    int getAPIAirQuality();
    double calculateAQI(double pm2p5);
    double linearInterpolation(double xValues[], double yValues[], int numValues, double pointX, bool trim);
    
    const char* apiKey;
    const char* server;
    int port;
    const char* localServer;
    int localPort;
    
    static const size_t JSON_DOC_SIZE = 4096;
    StaticJsonDocument<JSON_DOC_SIZE> doc;
    
    long lastLocalCheckTime; // Timestamp of the last attempt to check local sensor
    long lastApiCheckTime;   // Timestamp of the last attempt to check API
    int currentAQI;          // Last valid AQI reading obtained
    bool localSensorAvailable; // Flag indicating if local sensor responded successfully last time
    
    static const long MAX_SENSOR_AGE = 3600; // Max age of sensor data in seconds (1 hour)
};
