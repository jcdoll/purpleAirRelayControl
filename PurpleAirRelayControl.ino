#include "arduino_secrets.h"
#include <SPI.h>
#include <WiFiNINA.h>
#include <ArduinoHttpClient.h>
#include <Arduino_JSON.h>
#include <utility/wifi_drv.h>

// limits for bang-bang control of relays
// if input < lower threshold = enable ventilation
// if input > upper threshold = disable ventilation
// if between, do not change the state
// this is a simplest option to add hysteresis to the system and avoid excessive toggling
int ENABLE_THRESHOLD = 30; // lower threshold 
int DISABLE_THRESHOLD = 50; // upper threshold to disable relays

// delay time (ms) after reading purple air, reading switch, and setting relays
int UPDATE_DELAY = 5000; 

// disregard a sensor and move onto the next option if its age is greater than this (minutes)
int MAX_SENSOR_AGE = 10;

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

// read secret info file for wifi connection and purple air sensor id
char ssid[] = SECRET_SSID;
char pass[] = SECRET_PASS; 

// wifi settings
int status = WL_IDLE_STATUS; // initially not connected to wifi
char server[] = "www.purpleair.com";
WiFiClient wifi;
HttpClient client = HttpClient(wifi, server, 80);

// state variables
// ventilation is disabled by default
bool ventilationState = false;
int airQuality = DISABLE_THRESHOLD;
int switchState = SWITCH_STATE_OFF;

void setup() {
	
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
		status = WiFi.begin(ssid, pass);
	}
  Serial.println("WIFI STATUS: connected\n");
}

void loop() {
  switchState = getSwitchState();
  if (switchState == SWITCH_STATE_PURPLEAIR) {
  	airQuality = getAirQuality();
  }
	ventilationState = getVentilationState(switchState, ventilationState, airQuality);
	setRelays(ventilationState);
  
  Serial.println("Waiting ...\n");
	delay(UPDATE_DELAY);
}

int getAirQuality() {
	Serial.println("Requesting data from PurpleAir ...");
  String sensorId;

  for (int i=0; i<sizeof(SECRET_SENSOR_IDS)/sizeof(SECRET_SENSOR_IDS[0]); i++) {
    sensorId = SECRET_SENSOR_IDS[i];
    client.get("/json?show=" + sensorId);
    int statusCode = client.responseStatusCode();
    String response = client.responseBody();

  	if (statusCode == 200) {
  		JSONVar myObject = JSON.parse(response);
  		double PM2p5 = atof(myObject["results"][0]["PM2_5Value"]);
      int sensorAge = myObject["results"][0]["AGE"];

      // Output status to log
  		Serial.println("PURPLE AIR SENSOR (ID: " + String(sensorId) + ", age: " + String(sensorAge) + " minutes): " + String(PM2p5));

      if (sensorAge > MAX_SENSOR_AGE) {
        continue;
      }

      if (PM2p5 > ENABLE_THRESHOLD) {
        Serial.println("WARNING: sensor value is greater than ventilation threshold");
      }

      // Convert to AQI and return
      int aqi = calculateAQI(PM2p5);
      Serial.println("Converted to AQI: " + String(aqi));
  		return aqi;
  	} else {
  		Serial.println("ERROR: failed to access PurpleAir sensor (ID " + String(sensorId) + ")");
  	}
  }

  // We failed to get data from any of the sensors, don't enable the sensor
  Serial.println("ERROR: failed to get data from any sensor option");
  return DISABLE_THRESHOLD;
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
      Serial.println("AIR QUALITY: below enable threshold");
      return true;
    } else if (airQuality >= DISABLE_THRESHOLD) {
      Serial.println("AIR QUALITY: above disable threshold");
      return false;
    } else {
      Serial.println("AIR QUALITY: between thresholds, no change in state");
      return ventilationState;
    }
  }
}

// Calculate AQI from the raw PM2.5 data per EPA limits
int calculateAQI(double pm2p5) {
  const int N = 8;
  bool trim = true;  
  double pmValues[N] =  {0, 12, 35.4, 55.4, 150.4, 250.4, 350.4, 500.4}; // PM2.5
  double aqiValues[N] = {0, 50, 100,  150,  200,   300,   400,   500}; // AQI
  return (int) linearInterpolation(pmValues, aqiValues, N, (double) pm2p5, trim);  
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
