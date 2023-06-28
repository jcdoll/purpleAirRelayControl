#include "arduino_secrets.h"
#include "user_settings.h" // settings that users are likely to adjust
#include <SPI.h>
#include <WiFiNINA.h>
#include <ArduinoHttpClient.h>
#include <ArduinoJson.h>
#include <utility/wifi_drv.h>
#include <Adafruit_SleepyDog.h>

// Example requests
// GET https://api.purpleair.com/v1/sensors?fields=pm2.5_10minute&show_only=62491%2C103888%2C121311%2C70123 HTTP/1.1
// GET https://api.purpleair.com/v1/sensors/62491?fields=pm2.5_10minute HTTP/1.1

// delay time of the main loop (msec)
// it will only check for switch changes after waiting this long
int LOOP_DELAY = 1000;

// only get data from sensors that have reported data recently, default = 60 minutes (sec)
int MAX_SENSOR_AGE = 60*60;

// delay time between purple air requests to avoid API blacklist, default = 10 min (msec)
// note: purple air is considering adding API pricing, so monitor this setting closely
int PURPLE_AIR_DELAY = 1000*60*10;
long int lastPurpleAirUpdate = -1; // init negative so that we check the first time
long int timeSinceLastPurpleAirUpdate;

// nuke the session after some maximum uptime to avoid max socket # issues
// note that the resetFunc does not work with the MKR WiFi 1010 but the SleepyDog library does
// after reset you will need to replug in the USB cable (COM port hangs)
long int lastRestart;
long int timeSinceLastRestart;
long int MAX_RUN_TIME = 1000*60*60*24; // every 24 hours (in msec)

// constants
int SWITCH_STATE_OFF = 0;
int SWITCH_STATE_PURPLEAIR = 1;
int SWITCH_STATE_ON = 2;

int PIN_RELAY1 = 1; // relay 1 control is hardwired to digital pin 1 on the relay board
int PIN_RELAY2 = 2; // relay 2 control is hardwired to digital pin 2 on the relay board
int PIN_SWITCH_INPUT1 = A1; // use A1 because it is a screw terminal on the relay board
int PIN_SWITCH_INPUT2 = A2; // use A2 because it is a screw terminal on the relay board

// define colors for the on board LED
int COLOR_VENTILATION_ON_1 = 0;
int COLOR_VENTILATION_ON_2 = 50;
int COLOR_VENTILATION_ON_3 = 0;

int COLOR_VENTILATION_OFF_1 = 50;
int COLOR_VENTILATION_OFF_2 = 0;
int COLOR_VENTILATION_OFF_3 = 0;

// read secret info file for wifi connection, purple air sensor ids, and purple air api key
char SSID[] = SECRET_SSID;
char WIFI_PASSWORD[] = SECRET_PASS;
char API_KEY[] = SECRET_PURPLE_AIR_KEY;
int N_SENSORS = sizeof(SECRET_SENSOR_IDS)/sizeof(SECRET_SENSOR_IDS[0]);

// wifi settings
int status = WL_IDLE_STATUS; // initially not connected to wifi
char SERVER[] = "api.purpleair.com";
int HTTPS_PORT = 443;
WiFiSSLClient WIFI;
HttpClient client = HttpClient(WIFI, SERVER, HTTPS_PORT);

// allocate the memory for the json parsing document
StaticJsonDocument<2048> doc;

// state variables
// ventilation is enabled by default
bool ventilationState = true;
int airQuality = DISABLE_THRESHOLD;
int switchState = SWITCH_STATE_OFF;

void setup() {
  // record startup time
  lastRestart = millis();
  
	// enable outputs on relay pins
	pinMode(PIN_RELAY1, OUTPUT);
	pinMode(PIN_RELAY2, OUTPUT);

  // enabled LED control
  WiFiDrv::pinMode(25, OUTPUT);
  WiFiDrv::pinMode(26, OUTPUT);
  WiFiDrv::pinMode(27, OUTPUT);
  
	// enable pullups on digital pins
	pinMode(PIN_SWITCH_INPUT1, INPUT_PULLUP);
	pinMode(PIN_SWITCH_INPUT2, INPUT_PULLUP);

	// connect to wifi
	Serial.begin(9600);
	while (status != WL_CONNECTED) {
		Serial.println("WIFI STATUS: attempting to connect ...");
		status = WiFi.begin(SSID, WIFI_PASSWORD);
	}
  Serial.println("WIFI STATUS: connected\n");

  // reset the watchdog once after wifi is setup
  Watchdog.reset();
}

void loop() {
  // provide guidance re: when the controller will restart
  // restart is handled automatically by the watchdog
  timeSinceLastRestart = millis() - lastRestart;
  if (timeSinceLastRestart < MAX_RUN_TIME) {
    Serial.println(String(timeSinceLastRestart/1000) + "s uptime < " + String(MAX_RUN_TIME/1000) + "s max");
  } else {
    int countdownMS = Watchdog.enable(1000);
    Serial.println("Resetting in 1 second");
  }

  // Get switch state and ping Purple Air if necessary
  switchState = getSwitchState();
  if (switchState == SWITCH_STATE_PURPLEAIR) {
    timeSinceLastPurpleAirUpdate = millis() - lastPurpleAirUpdate; // subtract here to avoid overflow issue

    // check purple air if our lastUpdate time is negative or we've waited long enough
    if (lastPurpleAirUpdate < 0 || timeSinceLastPurpleAirUpdate > PURPLE_AIR_DELAY) {
      lastPurpleAirUpdate = millis();
      airQuality = getAirQuality();
    } else {
      Serial.println("Waiting to refresh sensor data: " + String(timeSinceLastPurpleAirUpdate/1000) + "s elapsed < " + String(PURPLE_AIR_DELAY/1000) + "s required");
    }
  } else {
      // If we are ON or OFF, reset the last purple air update timer
      // This allows us to force a requery by toggling off/on and then back
      lastPurpleAirUpdate = -1;
  }

  // update ventilation state based on switch and/or AQI
	ventilationState = getVentilationState(switchState, ventilationState, airQuality);
	setRelays(ventilationState);

  Serial.println("");
	delay(LOOP_DELAY);
}

int getAirQuality() {
  double aqi = 0;
	Serial.println("Requesting data from PurpleAir ...");

  // Build request string from multiple sensors (e.g. 1234%2C5678%2C5555)
  String sensorIds;
  sensorIds = SECRET_SENSOR_IDS[0];
  for (int i = 1; i < N_SENSORS; i++) {
    sensorIds += "%2C" + SECRET_SENSOR_IDS[i];
  }

  // Generate request string
  // Field 1 = 10 minute average PM2.5
  // We convert to AQI later
  String requestString = "/v1/sensors?fields=pm2.5_10minute&show_only=" + sensorIds + "&max_age=" + MAX_SENSOR_AGE;
  Serial.println("Request: " + requestString);

  // Send request including header
  client.beginRequest();
  client.get(requestString);
  client.sendHeader("X-API-Key", API_KEY);
  client.endRequest();
    
  int statusCode = client.responseStatusCode();
  String response = client.responseBody();

  // Print response
  Serial.println("Status:" + String(statusCode));
  Serial.println("Response:");
  Serial.println(response + "\n");

	if (statusCode == 200) {
    // Deserialize results
    DeserializationError error = deserializeJson(doc, response);
    if (error) {
      Serial.print(F("deserializeJson() failed: "));
      Serial.println(error.f_str());
    }
    JsonArray data = doc["data"];    

    // Check things
    int n_sensors_found = data.size();
    Serial.println("Expected sensors: " + String(N_SENSORS));
    Serial.println("Actual sensors found: " + String(n_sensors_found));
    
    // Calculate the average PM2.5 and output the raw data to the log
    int sensorId;
    double sensorAvgReading;
    double PM2p5 = 0;
    Serial.println();
    for (int i = 0; i < n_sensors_found; i++) {
      sensorId = data[i][0];
      sensorAvgReading = data[i][1];
      
      Serial.println("Sensor: " + String(sensorId));
      Serial.println("10-min avg: " + String(sensorAvgReading));
      Serial.println();
      PM2p5 += sensorAvgReading;
    }
    PM2p5 /= N_SENSORS;
    Serial.println("Average raw PM2.5 across " + String(n_sensors_found) + " sensors: " + String(PM2p5));

    // Convert to AQI
    aqi = calculateAQI(PM2p5);
    Serial.println("Average AQI after conversion: " + String(aqi));
    Serial.println("NOTE: THIS MAY BE DIFFERENT THAN THE PURPLE AIR MAP DUE TO AQI CONVERSION DIFFERENCES");    
	} else {
		Serial.println("ERROR: failed to access PurpleAir");
    aqi = 2*DISABLE_THRESHOLD;
	}

  return aqi;
}

int getSwitchState() {
  // pos1 = off (inputX high)
  // pos2 = purple air (both inputs high)
  // pos3 = on (inputX high)
  
  if (digitalRead(PIN_SWITCH_INPUT1) && digitalRead(PIN_SWITCH_INPUT2)) {
    Serial.println("SWITCH STATE: purple air");
    return SWITCH_STATE_PURPLEAIR;
  } else if (digitalRead(PIN_SWITCH_INPUT1) && ~digitalRead(PIN_SWITCH_INPUT2)) {
    Serial.println("SWITCH STATE: on");
		return SWITCH_STATE_ON;
	} else if (~digitalRead(PIN_SWITCH_INPUT1) && digitalRead(PIN_SWITCH_INPUT2)) {
    Serial.println("SWITCH STATE: off");
    return SWITCH_STATE_OFF;
	} else {
		Serial.println("ERROR: unknown switch state");
	}
}

bool getVentilationState(int switchState, bool ventilationState, int airQuality) {
  if (switchState == SWITCH_STATE_ON) {
    return true;
  } else if (switchState == SWITCH_STATE_OFF) {
    return false;
  } else {
    if (airQuality < ENABLE_THRESHOLD) {
      Serial.println("AQI is below the enable threshold -> ventilate");
      return true;
    } else if (airQuality >= DISABLE_THRESHOLD) {
      Serial.println("AQI is above the disable threshold -> shut it down");
      return false;
    } else {
      Serial.println("AQI is between our limits -> no change in state");
      return ventilationState;
    }
  }
}

// Calculate AQI from the raw PM2.5 data per EPA limits
double calculateAQI(double pm2p5) {
  const int N = 8;
  bool trim = true;  
  double pmValues[N] =  {0, 12, 35.4, 55.4, 150.4, 250.4, 350.4, 500.4}; // PM2.5
  double aqiValues[N] = {0, 50, 100,  150,  200,   300,   400,   500}; // AQI
  return (double) linearInterpolation(pmValues, aqiValues, N, (double) pm2p5, trim);  
}

double linearInterpolation(double xValues[], double yValues[], int numValues, double pointX, bool trim) {
    if (trim)
  {
    if (pointX <= xValues[0]) return yValues[0];
    if (pointX >= xValues[numValues - 1]) return yValues[numValues - 1];
  }

  auto i = 0;
  double rst = 0;
  if (pointX <= xValues[0])
  {
    i = 0;
    auto t = (pointX - xValues[i]) / (xValues[i + 1] - xValues[i]);
    rst = yValues[i] * (1 - t) + yValues[i + 1] * t;
  }
  else if (pointX >= xValues[numValues - 1])
  {
    auto t = (pointX - xValues[numValues - 2]) / (xValues[numValues - 1] - xValues[numValues - 2]);
    rst = yValues[numValues - 2] * (1 - t) + yValues[numValues - 1] * t;
  }
  else
  {
    while (pointX >= xValues[i + 1]) i++;
    auto t = (pointX - xValues[i]) / (xValues[i + 1] - xValues[i]);
    rst = yValues[i] * (1 - t) + yValues[i + 1] * t;
  }

  return rst;
}

void setRelays(bool ventilate) {
  if (ventilate) {
    Serial.println("VENTILATION STATE: on");
    WiFiDrv::analogWrite(25, COLOR_VENTILATION_ON_1);
    WiFiDrv::analogWrite(26, COLOR_VENTILATION_ON_2);
    WiFiDrv::analogWrite(27, COLOR_VENTILATION_ON_3);
  } else {
    Serial.println("VENTILATION STATE: off");    
    WiFiDrv::analogWrite(25, COLOR_VENTILATION_OFF_1);
    WiFiDrv::analogWrite(26, COLOR_VENTILATION_OFF_2);
    WiFiDrv::analogWrite(27, COLOR_VENTILATION_OFF_3);
  }
  
	digitalWrite(PIN_RELAY1, ventilate);
	digitalWrite(PIN_RELAY2, ventilate);
}
