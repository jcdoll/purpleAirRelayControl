# purpleAirRelayControl
Control your HVAC hardware based on PurpleAir sensor data to limit wildfire smoke exposure.

Features:
* Open/close a relay based on PurpleAir sensor results
	* Sensor can either be on your local network (free) or use your neighbor's sensor (API key required)
* Use the relay to control your HVAC hardware
	* Control your HRV/ERV/damper
 	* Tested on a Lifebreath 170 ERVD with dry contact controls
* Optionally log the results to a Google Spreadsheet for remote logging
* Optionally monitor and log the results from an indoor sensor
	* Verify that your home air filtering is working as intended

# Microcontroller

This project currently runs on an Arduino board. An ESP32 version is in progress.

## Arduino requirements

* Arduino MKR 1010 (https://store-usa.arduino.cc/products/arduino-mkr-wifi-1010)
* MKR Proto Relay board (https://store-usa.arduino.cc/products/arduino-mkr-relay-proto-shield)
* Three way on-off-on DPDT switch (example: https://www.amazon.com/dp/B07VJ4DXMF)
	* this allows us to select between on/purpleAir/off states without any external resistors
	* this particular example uses screw terminals so no soldering is required

# Instructions

## Microcontroller

### Arduino

* Install the following libraries from in your Arduino IDE
	* Menu: Tools > Manage Libraries
	* Install WifiNINA
	* Install ArduinoHttpClient
	* Install ArduinoJson (not Arduino_JSON!)
	* Install Adafruit SleepyDog
   	* TODO: This is out of date, update from the current code
* Install support for your MKR 1010 board
	* Menu: Tools > Board > Board Manager
	* Install Arduino SAMD Boards
* Select your board
	* Menu: Tools > Board > Arduino SAMD > Arduino MKR WiFi 1010
* Create your personal secrets file
	* copy "arduino_secrets_sample.h" to "arduino_secrets.h" and fill in your details
* Flash Arduino
	* Connect Arduino to your PC
	* Menu: Tools > Port > Select appropriate port
	* Compile (Control+R)
	* Fix any errors or missing dependencies
	* Flash (Control+U)
 
## Install

See the case README for install instructions