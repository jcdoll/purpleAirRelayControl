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
String sensor_id = SECRET_SENSOR_ID;

// wifi settings
int status = WL_IDLE_STATUS; // initially not connected to wifi
char server[] = "www.purpleair.com";
WiFiClient wifi;
HttpClient client = HttpClient(wifi, server, 80);

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
  bool ventilationState = false;
  int airQuality = 0;
  int switchState = SWITCH_STATE_OFF;
  
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
 
	client.get("/json?show=" + sensor_id);
	int statusCode = client.responseStatusCode();
	String response = client.responseBody();

	if (statusCode == 200) {
		JSONVar myObject = JSON.parse(response);
		int PM2_5 = atoi(myObject["results"][0]["PM2_5Value"]);

    Serial.print("PURPLE AIR SENSOR VALUE: ");
		Serial.println(PM2_5);

    if (PM2_5 > ENABLE_THRESHOLD) {
      Serial.println("WARNING: sensor value is greater than ventilation threshold");
    }
		return PM2_5;
	} else {
		Serial.println("ERROR: failed to access PurpleAir");
	}
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
    } else if (airQuality > DISABLE_THRESHOLD) {
      Serial.println("AIR QUALITY: above disable threshold");
      return false;
    } else {
      Serial.println("AIR QUALITY: between thresholds, no change in state");
      return ventilationState;
    }
  }
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
