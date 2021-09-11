# purpleAirRelayControl
 Control an ERV/HRV and damper based on PurpleAir to limit wildfire smoke exposure


# Arduino requirements

* Arduino MKR 1010 (https://store-usa.arduino.cc/products/arduino-mkr-wifi-1010)
* MKR Proto Relay board (https://store-usa.arduino.cc/products/arduino-mkr-relay-proto-shield)
* Three way on-off-on DPDT switch (example: https://www.amazon.com/B07VJ4DXMF)
	* this allows us to select between on/purpleAir/off states without any external resistors
	* this particular example uses screw terminals so no soldering is required
* 3D printed case
	* todo

# Instructions

* Stop git from tracking your secrets file
	* git update-index --skip-worktree arduino_secrets.h
* Edit arduino_secrets.h to include your personal and private info
	* wifi network ssid
	* wifi password
	* PurpleAir id (e.g. 12345)

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
		* A = 5V
		* B = pin 3
		* C = gnd
		* D = gnd
		* E = pin 4
		* F = 5V
		* switch up (force on)
			* AB and DE are connected (B = high, E = low)
		* switch center (purpleAir)
			* nothing connected (B = high, E = high due to internal pull up resistors)
		* switch low (force off)
			* BC and EF are connected (B = low, E = high)

# Operation logic

threshold = 50

if pin3 && ~pin2
	switchState = on
elseif pin1 & pin2
	switchState = purpleAir
elseif ~pin1 && pin2
	switchState = off
else
	log error due to switch problem and set state to off
end

ventilate = (switchState == on) || (switchState == purpleAir && purpleAirSensor < threshold)
	
if ventilate
	pin1 = high
	pin2 = high
	energize relays (open damper and turn on ERV/HRV)
else
	pin1 = low
	pin2 = low
	de-energizerelays (close damper and turn off ERV/HRV)
end
