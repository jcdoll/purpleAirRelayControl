# Wiring

Two HVAC-side connections plus one one-time soldering step on the relay wing.

1. 24 VAC from the HVAC transformer -> sCharge S39 (powers the Feather over USB-C).
2. Relay FeatherWing dry contact -> the ventilation controller's remote input.

Reference unit: **Honeywell W8150A1001**. Other controllers are similar -- see [Other controllers](#other-controllers).

## Solder jumper for relay control

The Power Relay FeatherWing ships with no pin connected to the relay coil. Bridge the **A0** jumper on the back of the wing. This project's firmware drives A0 (`RELAY_PIN = 18`).

Orient the wing back-side up, silkscreen text right-side up. Screw terminals on your left, Reset button on your right. Two rows of chevron pads:

- bottom row, 6 pads, near the 16-pin header edge
- top row, 5 pads, near the 12-pin header edge

Bottom row, left to right:

```
MOSI   SCK   A5  ..  A2   A1   A0
                                ^
                          bridge this
```

Bridge both halves of the A0 pad with a small solder blob. Bridge nothing else.

If you bridge a different jumper, set `RELAY_PIN` in `esp32/config.py` to the matching GPIO. Pin -> GPIO map for the **ESP32-S3 Reverse TFT Feather** (A0 != GPIO 0 on this board):

| Wing label | GPIO |
|------------|------|
| A0         | 18   |
| A1         | 17   |
| A2         | 16   |
| A5         | 8    |
| SCK        | 36   |
| MOSI       | 35   |
| MISO       | 37   |
| D9         | 9    |
| D10        | 10   |
| D11        | 11   |
| D12        | 12   |
| D13        | 13   |

## Honeywell W8150A1001

The terminal strip has 8 screws labeled top-to-bottom:

| # | Label | Function                         | Used by this project   |
|---|-------|----------------------------------|------------------------|
| 1 | R     | 24 VAC hot from HVAC transformer | yes -- tap for sCharge |
| 2 | C     | 24 VAC common                    | yes -- tap for sCharge |
| 3 | DMP   | Damper output                    | no                     |
| 4 | DMP   | Damper output                    | no                     |
| 5 | AUX   | ERV / Fan output                 | no                     |
| 6 | AUX   | ERV / Fan output                 | no                     |
| 7 | REM   | Timer / Switch input             | yes -- relay COM       |
| 8 | REM   | Timer / Switch input             | yes -- relay NO        |

R, C, AUX, and DMP are already wired when the W8150 is installed. **REM is normally unused** -- it's the input intended for an external timer or wall switch. That's where the relay goes.

### 1. Power (24 VAC -> sCharge)

Tap the existing 24 VAC at R and C. Pigtail with Wago lever-nuts so the W8150 screw terminals don't get disturbed.

```
24 VAC hot     ──┬── R   (W8150 terminal 1)
                 └── one red lead of sCharge

24 VAC common  ──┬── C   (W8150 terminal 2)
                 └── other red lead of sCharge
```

Polarity doesn't matter (sCharge accepts 16-28 VAC). USB-C from the sCharge plugs into the Feather.

### 2. Relay (dry contact -> REM)

The Adafruit Power Relay FeatherWing exposes three screw terminals: NC, COM, NO. Wire COM and NO to the two REM terminals; leave NC unused.

```
Relay COM  ──> W8150 REM (terminal 7)
Relay NO   ──> W8150 REM (terminal 8)
```

REM is a dry-contact input -- not polarity sensitive, no voltage on it. **Do not put 24 VAC across the relay**.

### Firmware behavior

`ventilation.py` boots with the relay GPIO low (coil de-energized -> COM-NO **open** -> REM-REM not shorted -> W8150 in normal mode). When the firmware enables ventilation (manual ON, or PURPLEAIR mode with AQI below threshold) it sets the GPIO high -> coil energized -> COM-NO **closed** -> REM-REM shorted -> W8150 enters override = 100% ventilation.

| Firmware state  | Relay coil   | COM-NO | REM-REM | W8150 mode                       |
|-----------------|--------------|--------|---------|----------------------------------|
| Vent OFF / boot | de-energized | open   | open    | normal (front panel: 50% or off) |
| Vent ON         | energized    | closed | shorted | override (100%)                  |

This is why the wiring uses **NO**, not NC. NC would invert the logic (override active at boot, and whenever the firmware crashes or loses power).

## Other controllers

The pattern generalizes: **find the unit's dry-contact remote / timer / switch input, and wire the relay's COM + NO to it**. Most whole-house ventilation controllers and ERVs have one. Look for terminals labeled `REM`, `REMOTE`, `TIMER`, `SW`, `OVERRIDE`, `BOOST`, or similar.

Before involving the relay, verify with a wire jumper: shorting the two terminals should put the unit into the desired override / boost mode. If it does, the relay drops in.

If your unit has its own 24 VAC transformer, tap that for the sCharge instead of the main HVAC transformer. The sCharge accepts 16-28 VAC (or 6-40 VDC).

If your unit requires switching 24 VAC **to a load** (running a fan or damper directly) rather than closing a logic input, the relay is rated for it (10 A 250 VAC) -- the relay then sits in series with the load. See `case/README.md` for ERV and damper examples from the original Arduino-based design.

When you wire up a new controller, add a section here.
