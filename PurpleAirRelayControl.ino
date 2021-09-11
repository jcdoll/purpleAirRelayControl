#include "arduino_secrets.h"
#include <WiFiNINA.h>
#include <ArduinoHttpClient.h>
#include <Arduino_JSON.h>

// Constants
int ENABLE_THRESHOLD = 50; // threshold to enable relays (units = PM2.5 μg/m3)
int UPDATE_DELAY = 10000; // delay time after reading purple air, reading switch, and setting relays

int SWITCH_STATE_OFF = 0;
int SWITCH_STATE_PURPLEAIR = 1;
int SWITCH_STATE_ON = 2;

int PIN_RELAY1 = 1;
int PIN_RELAY2 = 2;
int PIN_SWITCH_INPUT1 = 3;
int PIN_SWITCH_INPUT2 = 4;

// secret info
char ssid[] = SECRET_SSID;
char pass[] = SECRET_PASS;
String sensor_id = SECRET_SENSOR_ID;

int status = WL_IDLE_STATUS;
char server[] = "www.purpleair.com";
WiFiClient wifi;
HttpClient client = HttpClient(wifi, server, 80);

void setup() {
	
	// enable outputs on relay pins
	pinMode(PIN_RELAY1, OUTPUT);
	pinMode(PIN_RELAY2, OUTPUT);

	// enable pullups on digital pins
	pinMode(PIN_SWITCH_INPUT1, INPUT_PULLUP);
	pinMode(PIN_SWITCH_INPUT2, INPUT_PULLUP);

	// connect to wifi
	Serial.begin(9600);
	while (status != WL_CONNECTED) {
		Serial.print("Attempting to connect to Network named: ");
		Serial.println(ssid);
		status = WiFi.begin(ssid, pass);
	}
}

void loop() {
	int airQuality = getAirQuality();
	int switchState = getSwitchState();
	bool ventilationState = getVentilationState(switchState, airQuality);
	setRelays(ventilationState);
	delay(UPDATE_DELAY);
}

int getAirQuality() {
	Serial.println("Requesting data from PurpleAir... ");
	client.get("/json?show=" + sensor_id);
	int statusCode = client.responseStatusCode();
	String response = client.responseBody();

	if (statusCode == 200) {
		JSONVar myObject = JSON.parse(response);
		int PM2_5 = atoi(myObject["results"][0]["PM2_5Value"]);
		Serial.println(PM2_5);
		return PM2_5
	} else {
		Serial.println("error accessing PurpleAir");
	}
}

int getSwitchState() {
	if (digitalRead(PIN_SWITCH_INPUT1) && ~digitalRead(PIN_SWITCH_INPUT2)) {
		return SWITCH_STATE_ON;
	} else if (digitalRead(PIN_SWITCH_INPUT1) && digitalRead(PIN_SWITCH_INPUT2)) {
		return SWITCH_STATE_PURPLEAIR;
	} else {
		if (~digitalRead(PIN_SWITCH_INPUT1) && ~digitalRead(PIN_SWITCH_INPUT2)) {
			Serial.println("ERROR: unknown switch state");
		}
		return SWITCH_STATE_OFF;
	}
}

bool getVentilationState(int switchState, int airQuality) {
	return (switchState == SWITCH_STATE_ON) || (switchState == SWITCH_STATE_PURPLEAIR && airQuality < threshold);
}

void setRelays(bool ventilate) {
	digitalWrite(PIN_RELAY1, ventilate);
	digitalWrite(PIN_RELAY2, ventilate);
}
