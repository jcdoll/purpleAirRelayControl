# purpleAirRelayControl
 Control an ERV/HRV and/or damper based on PurpleAir to limit wildfire smoke exposure.


# Arduino requirements

* Arduino MKR 1010 (https://store-usa.arduino.cc/products/arduino-mkr-wifi-1010)
* MKR Proto Relay board (https://store-usa.arduino.cc/products/arduino-mkr-relay-proto-shield)
* Three way on-off-on DPDT switch (example: https://www.amazon.com/B07VJ4DXMF)
	* this allows us to select between on/purpleAir/off states without any external resistors
	* this particular example uses screw terminals so no soldering is required
* 3D printed case
	* todo

# Instructions

* Install the following libraries from in your Arduino IDE (Tools > Manage Libraries)
	* WifiNINA
	* ArduinoHttpClient
	* Arduino_JSON
* Stop git from tracking your secrets file
	* git update-index --skip-worktree arduino_secrets.h
* Edit arduino_secrets.h to include your personal and private info
	* wifi network ssid
	* wifi password
	* PurpleAir id (e.g. 12345)
* 3d print case
	* 0.3 mm layer height
	* include supports
* Install
	* compile and upload code to the arduino
	* attach arduino to the case with M3x8 screws
	* attach the switch to the case using included screws/washers
	* wire the switch to the board (see below)
	* wire the relay outputs to whatever you are controlling
	* attach the case nearby your HRV/ERV and/or damper using your preferred method (drywall fasteners, adhesive, etc)
	* connect a powered micro usb cable to the arduino
	* test on/off/purpleair functionality

# Electronics

Switching hardware:
* ERV
	* Any HRV/ERV with dry contact controls (tested on Lifebreath 170 ERVD)
* Damper
	* Any 24VAC damper
		* Suncourt Adjustable Motorized Damper, Closed, 6" (includes 24 VAC transformer)
		* Honeywell EARD6TZ Round Fresh Air Damper, 6"
	* 24 VAC transformer to provider power
* Wiring
	* Relay1
		* COM = ERV contact 1 (e.g. Lifebreath ON)
		* NO = ERV contact 2 (e.g. Lifebreath LO or HI)
		* Open -> do nothing
		* Closed -> connect two ERV contacts
		* Ensure that ERV is in standby mode (e.g. Lifebreath set to fan speed 0 or short the RED/ON contacts, see manual)
	* Relay2
		* COM = Damper contact 1
		* NO = 24 VAC transformer
		* Connect the other transformer lead to damper contact 2
		* Open -> do nothing
		* Closed -> close circuit to provide 24 VAC to damper
	* Switch
		* ABC / DEF on each side from top to bottom
		* A = GND
		* B = pin 3
		* C = NC (no connection)
		* D = NC
		* E = pin 4
		* F = GND
		* switch up (force on)
			* B = GND
			* E = NC (pulled high)
		* switch middle (purple air)
			* B = NC (pulled high)
			* E = NC (pulled high)
		* switch low (off)
			* B = NC (pulled high)
			* E = grounded
