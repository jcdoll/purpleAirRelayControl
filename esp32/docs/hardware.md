# Hardware Documentation

**SINGLE SOURCE OF TRUTH**:
- Pin assignments are defined in `config.py`. This documentation reflects current values but always check `config.py` for authoritative pin definitions.

## ESP32-S3 Reverse TFT Feather Overview

Board: ESP32-S3 Reverse TFT Feather  
Product ID: Adafruit #5691  
URL: https://www.adafruit.com/product/5691

### Core Specifications
- Processor: ESP32-S3 dual-core Tensilica processor @ 240MHz
- Memory: 8MB Flash, 2MB PSRAM
- Display: Built-in 1.14" TFT display (240x135 resolution, ST7789 driver)
- LED: Built-in NeoPixel RGB LED
- Buttons: 3 tactile buttons (D0/BOOT, D1, D2)
- Connectivity: WiFi and Bluetooth 5.0
- GPIO: 21 GPIO pins
- Power: USB-C connector, LiPoly battery connector with charging

### Optional Hardware Components

Network Enhancement:
- External antenna for longer range: https://www.adafruit.com/product/5445

Assembly:
- Header kit: https://www.adafruit.com/product/2886

Relay Options:
- Standard relay (higher power, solder jumper for A0 control): https://www.adafruit.com/product/3191
- Low power latching relay (solder two wires for control): https://www.adafruit.com/product/2923

## Pin Assignments

NOTE: All pin assignments are defined in `config.py`. This documentation shows the current assignments but `config.py` is the authoritative source.

### Project-Specific Pins
```python
# From config.py:
RELAY1_PIN = 5      # Primary ventilation relay
RELAY2_PIN = 6      # Secondary ventilation relay
SWITCH_PIN = 9      # Manual switch input
```

### TFT Display (ST7789)
- Resolution: 135x240 pixels (TFT_WIDTH x TFT_HEIGHT)
- Orientation: Landscape mode with rotation=1 (TFT_ROTATION)
- SPI Pins:
  - MOSI: GPIO 35 (`TFT_MOSI`)
  - SCLK: GPIO 36 (`TFT_SCLK`)
  - CS: GPIO 42 (`TFT_CS`)
  - DC: GPIO 40 (`TFT_DC`)
  - RST: GPIO 41 (`TFT_RST`)
- Backlight: GPIO 45 (`TFT_BACKLIGHT`)
- I2C/TFT Power: GPIO 7 (`TFT_I2C_POWER`) - automatically managed

### NeoPixel RGB LED
- Data Pin: GPIO 33 (`NEOPIXEL_PIN`)
- Power Pin: GPIO 21 (`NEOPIXEL_POWER`)
- IMPORTANT: The NeoPixel power pin MUST be set HIGH for the LED to work

### User Buttons
- D0/BOOT Button:
  - Pin: GPIO 0 (`BUTTON_D0`)
  - Pull: HIGH (10K pull-up)
  - Logic: LOW when pressed
  - Note: Also functions as boot mode selector
  
- D1 Button:
  - Pin: GPIO 1 (`BUTTON_D1`)
  - Pull: LOW (10K pull-down)
  - Logic: HIGH when pressed
  
- D2 Button:
  - Pin: GPIO 2 (`BUTTON_D2`)
  - Pull: LOW (10K pull-down)
  - Logic: HIGH when pressed

### Other Available Pins
- I2C (STEMMA QT):
  - SDA: GPIO 3
  - SCL: GPIO 4
  - Power: GPIO 7 (must be HIGH to enable)
  
- Analog Pins: A0-A5 (GPIO 8, 14, 15, 16, 17, 18)
- Debug TX: GPIO 43
- Battery Voltage: A6 (divided by 2)

## Power Management

### Power Control Examples
```python
from machine import Pin
import config

# Enable NeoPixel power
neopixel_power = Pin(config.NEOPIXEL_POWER_PIN, Pin.OUT)
neopixel_power.value(1)  # Must be HIGH for LED to work

# Control display brightness
backlight = Pin(config.TFT_BACKLIGHT, Pin.OUT)
backlight.value(1)  # Full brightness
```

## MicroPython Hardware Configuration

### SPI Configuration for Display
- Use SPI bus 1 for display
- Maximum baudrate: 40MHz
- Mode: 0 (CPOL=0, CPHA=0)

### Memory Usage Considerations
- Display buffer requires ~64KB
- NeoPixel requires minimal memory
- Font storage adds 10-50KB depending on size

### Boot Behavior
- D0/BOOT button: Hold during reset to enter bootloader
- Normal boot: All pins initialize to default states
- Power pins (NeoPixel, I2C) default to LOW

## Common Hardware Issues

### NeoPixel Not Working
1. Ensure power pin (`config.NEOPIXEL_POWER_PIN`) is set HIGH
2. Check `neopixel` module is installed  
3. Use correct data pin (`config.NEOPIXEL_PIN`)
4. Verify power supply stability

### Display Issues
1. Verify SPI pins match configuration
2. Check display driver installation
3. Ensure proper rotation setting (rotation=3 for landscape)
4. Confirm backlight pin control

### Button Reading Issues
- D0: Check for LOW (pressed) vs HIGH (released)
- D1/D2: Check for HIGH (pressed) vs LOW (released)
- Add debouncing for reliable button detection

### Relay Control Issues
1. Check GPIO pin configuration (OUTPUT mode)
2. Verify relay power requirements
3. Test with multimeter for signal levels
4. Consider using optoisolation for high-power relays

## Hardware References
- [Adafruit Product Page](https://www.adafruit.com/product/5691)
- [Adafruit Learning Guide](https://learn.adafruit.com/esp32-s3-reverse-tft-feather)
- [Pinouts Reference](https://learn.adafruit.com/esp32-s3-reverse-tft-feather/pinouts)
- [ESP32-S3 Technical Reference](https://www.espressif.com/sites/default/files/documentation/esp32-s3_technical_reference_manual_en.pdf) 