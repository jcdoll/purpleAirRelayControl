# Case and wiring

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
