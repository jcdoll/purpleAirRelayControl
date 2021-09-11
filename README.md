# purpleAirRelayControl
 Control an ERV/HRV and damper based on PurpleAir to limit wildfire smoke exposure


# Arduino requirements

* Arduino MKR 1010 (https://store-usa.arduino.cc/products/arduino-mkr-wifi-1010)
* MKR Proto Relay board (https://store-usa.arduino.cc/products/arduino-mkr-relay-proto-shield)

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
		
		
		* Wire from transformer to 
	
