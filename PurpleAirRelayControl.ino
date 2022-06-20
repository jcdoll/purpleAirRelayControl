#include "arduino_secrets.h"
#include <SPI.h>
#include <WiFiNINA.h>
#include <ArduinoHttpClient.h>
#include <ArduinoJson.h>
#include <utility/wifi_drv.h>

// Example requests
// GET https://api.purpleair.com/v1/sensors?fields=pm2.5_10minute&show_only=62491%2C103888%2C121311%2C70123 HTTP/1.1
// GET https://api.purpleair.com/v1/sensors/62491?fields=pm2.5_10minute HTTP/1.1

// limits for bang-bang control of relays
// if input < lower threshold = enable ventilation
// if input > upper threshold = disable ventilation
// if between, do not change the state
// this is a simplest option to add hysteresis to the system and avoid excessive toggling
int ENABLE_THRESHOLD = 30; // lower threshold 
int DISABLE_THRESHOLD = 50; // upper threshold to disable relays

// delay time of the main loop (msec)
// it will only check for switch changes after waiting this long
int LOOP_DELAY = 1000;

// delay time between purple air requests to avoid API blacklist, default = 5 min (msec)
int PURPLE_AIR_DELAY = 300000;
long int lastPurpleAirUpdate = -1; // init negative so that we check the first time
long int timeSinceLastPurpleAirUpdate;

// only get data from sensors that have reported data recently, default = 60 minutes (sec)
int MAX_SENSOR_AGE = 3600;

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
char SSID[] = SECRET_SSID;
char WIFI_PASSWORD[] = SECRET_PASS;
char API_KEY[] = "1A37BB5C-E051-11EC-8561-42010A800005";
int N_SENSORS = sizeof(SECRET_SENSOR_IDS)/sizeof(SECRET_SENSOR_IDS[0]);

// wifi settings
int status = WL_IDLE_STATUS; // initially not connected to wifi
char SERVER[] = "api.purpleair.com";
int HTTPS_PORT = 443;
WiFiSSLClient WIFI;
HttpClient client = HttpClient(WIFI, SERVER, HTTPS_PORT);

// allocate the memory for the document
StaticJsonDocument<2048> doc;

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
		status = WiFi.begin(SSID, WIFI_PASSWORD);
	}
  Serial.println("WIFI STATUS: connected\n");
}

void loop() {
  switchState = getSwitchState();
  if (switchState == SWITCH_STATE_PURPLEAIR) {
    timeSinceLastPurpleAirUpdate = millis() - lastPurpleAirUpdate;
    if (lastPurpleAirUpdate < 0 || timeSinceLastPurpleAirUpdate > PURPLE_AIR_DELAY) {
      lastPurpleAirUpdate = millis();
      airQuality = getAirQuality();
    } else {
      Serial.println("Too soon to check Purple Air again: " + String(timeSinceLastPurpleAirUpdate/1000) + "s elapsed < " + String(PURPLE_AIR_DELAY/1000) + "s required");
    }
  }
	ventilationState = getVentilationState(switchState, ventilationState, airQuality);
	setRelays(ventilationState);
  
  Serial.println("Waiting for loop delay\n");
	delay(LOOP_DELAY);
}

int getAirQuality() {
	Serial.println("Requesting data from PurpleAir ...");

  // Build request string from multiple sensors (e.g. 1234%2C5678%2C5555)
  String sensorIds;
  sensorIds = SECRET_SENSOR_IDS[0];
  for (int i = 1; i < N_SENSORS; i++) {
    sensorIds += "%2C" + SECRET_SENSOR_IDS[i];
  }

  // Generate request string
  String requestString = "/v1/sensors?fields=pm2.5,pm2.5_10minute&show_only=" + sensorIds + "&max_age=" + MAX_SENSOR_AGE;
  Serial.println("Request: " + requestString);

  // Send request including header
  // TODO: Move API key to secrets file if it is abused, otherwise keep it here to simplify new user setup
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
    double sensorCurrentReading;
    double sensorAvgReading;
    double PM2p5 = 0;
    Serial.println();
    for (int i = 0; i < n_sensors_found; i++) {
      sensorId = data[i][0];
      sensorCurrentReading = data[i][1];
      sensorAvgReading = data[i][2];
      
      Serial.println("Sensor: " + String(sensorId));
      Serial.println("Raw PM2.5: " + String(sensorCurrentReading));
      Serial.println("10-min avg: " + String(sensorAvgReading));
      Serial.println();
      PM2p5 += sensorAvgReading;
    }
    PM2p5 /= N_SENSORS;
    Serial.println("Average PM2.5 across " + String(n_sensors_found) + " sensors: " + String(PM2p5));
    
    if (PM2p5 > ENABLE_THRESHOLD) {
      Serial.println("WARNING: sensor value is greater than ventilation threshold");
    }

    // Convert to AQI and return
    double aqi = calculateAQI(PM2p5);

    // Output summary
    Serial.println("Converted to AQI: " + String(aqi));
		return aqi;
	} else {
		Serial.println("ERROR: failed to access PurpleAir");
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
