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

## ESP32

In progress


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

### ESP32

TODO
 
## Case

The case is optional if you have another mounting method.

* Generate STLs
	* install OpenSCAD if necessary
	* run exportSTLs.bat in this repository
* Print box and shelf
	* print external perimeters first for dimensional accuracy
	* recommended settings: 0.3 mm layer height, 15% infill, slow enough perimeters to avoid overextruded corners

## Installation

* Fill box
	* attach arduino to the case with M3x4 screws (or longer if you have washers available)
		* the fasteners should self tap the holes if your printer is accurate
		* don't overtighten or you will strip the plastic
	* attach the switch to the case using included screws/washers
	* wire the switch to the board (see below)
	* wire the relay outputs to whatever you are controlling
* Attach wall mount
	* install the wall mount (holds box) to a nearby wall using your preferred method (drywall fasteners, adhesive, etc)
* Wiring
	* run wires from your HVAC equipment to the Arduino mounting location
	* i'd recommend using a quick disconnect (e.g. Wago) between the HVAC equipment and the Arduino to allow for easy box removal
	* connect a powered micro usb cable to the Arduino
* Test
	* confirm that your HVAC equipment is controlled appropriately with the switch in the on/off/purpleair positions

## Switch wiring

We are using a three-way on-off-on switch. The two middle pins go to the microcontroller. Depending on the switch position they are either NC (pulled high) or grounded. This allows the microcontroller to monitor the state of the switch.

| Pin | Connection | Pin | Connection |
|-----|------------|-----|------------|
| A   | GND        | D   | NC         |
| B   | A2 (pin 3) | E   | A1 (pin 4) |
| C   | NC         | F   | GND        |


## HVAC wiring

* Example ERV setup
	* COM = ERV contact 1 (e.g. Lifebreath ON)
	* NO = ERV contact 2 (e.g. Lifebreath LO or HI)
	* Notes
 		* Open relay -> do nothing
   		* Closed relay -> short two ERV contacts
	* Ensure that ERV is in standby mode (e.g. Lifebreath set to fan speed 0 or short the RED/ON contacts, see manual)
* Example damper setup (not tested)
	* COM = Damper contact 1
	* NO = 24 VAC transformer
	* Connect the other transformer lead to damper contact 2
 	* Notes
  		* Relay is in series with the damper
		* Open relay -> no power to damper
		* Closed relay -> 24VAC to damper (ensure that your relay is properly rated)
  		* Ensure that you have a NC damper
