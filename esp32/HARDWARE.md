# ESP32-S3 Reverse TFT Feather Hardware Documentation

## Board Overview
- **Product**: Adafruit ESP32-S3 Reverse TFT Feather
- **Product ID**: 5691
- **Processor**: ESP32-S3 dual-core Tensilica processor @ 240MHz
- **Memory**: 8MB Flash, 2MB PSRAM
- **Display**: Built-in 1.14" 240x135 Color TFT (ST7789)
- **LED**: Built-in NeoPixel RGB LED
- **Buttons**: 3 user buttons (D0/BOOT, D1, D2)
- **Connectivity**: WiFi, Bluetooth LE
- **Power**: USB-C, LiPoly battery connector with charging

## Pin Assignments

### NeoPixel LED
- **Data Pin**: GPIO 33 (`board.NEOPIXEL` in CircuitPython)
- **Power Pin**: GPIO 21 (`NEOPIXEL_POWER`)
- **IMPORTANT**: The NeoPixel power pin MUST be set HIGH for the LED to work
- **Library**: `neopixel` module required

### TFT Display (ST7789)
- **Resolution**: 240x135 pixels
- **Orientation**: Landscape mode with rotation=3
- **SPI Pins**:
  - **MOSI**: GPIO 35 (`board.TFT_MOSI`)
  - **SCLK**: GPIO 36 (`board.TFT_SCLK`)
  - **CS**: GPIO 7 (`board.TFT_CS`)
  - **DC**: GPIO 39 (`board.TFT_DC`)
  - **RST**: GPIO 40 (`board.TFT_RST`)
- **Backlight**: GPIO 45 (`board.TFT_BACKLIGHT`)
- **Power Pin**: `TFT_I2C_POWER` (automatically managed)

### User Buttons
- **D0/BOOT Button**:
  - **Pin**: GPIO 0
  - **Pull**: HIGH (10K pull-up)
  - **Logic**: LOW when pressed
  - **Note**: Also functions as boot mode selector
  
- **D1 Button**:
  - **Pin**: GPIO 1
  - **Pull**: LOW (10K pull-down)
  - **Logic**: HIGH when pressed
  
- **D2 Button**:
  - **Pin**: GPIO 2
  - **Pull**: LOW (10K pull-down)
  - **Logic**: HIGH when pressed

### Relay Control Pins
- **Relay 1**: GPIO 5
- **Relay 2**: GPIO 6
- **Switch Input**: GPIO 9

### Other Important Pins
- **I2C (STEMMA QT)**:
  - **SDA**: GPIO 3
  - **SCL**: GPIO 4
  - **Power**: GPIO 7 (must be HIGH to enable)
  
- **Analog Pins**: A0-A5 (GPIO 8, 14, 15, 16, 17, 18)
- **Debug TX**: GPIO 43
- **Battery Voltage**: A6 (divided by 2)

## Power Management

### NeoPixel Power Control
```python
# Enable NeoPixel power
neopixel_power = Pin(34, Pin.OUT)
neopixel_power.value(1)  # Must be HIGH for LED to work
```

### Display Backlight Control
```python
# Control display brightness
backlight = Pin(45, Pin.OUT)
backlight.value(1)  # Full brightness
```

## MicroPython Considerations

### SPI Configuration
- Use SPI bus 1 for display
- Maximum baudrate: 40MHz
- Mode: 0 (CPOL=0, CPHA=0)

### Memory Usage
- Display buffer requires ~64KB
- NeoPixel requires minimal memory
- Font storage adds 10-50KB depending on size

### Boot Behavior
- D0/BOOT button: Hold during reset to enter bootloader
- Normal boot: All pins initialize to default states
- Power pins (NeoPixel, I2C) default to LOW

## Common Issues and Solutions

### NeoPixel Not Working
1. Ensure GPIO 34 (power pin) is set HIGH
2. Check `neopixel` module is installed
3. Use correct pin (GPIO 33)

### Display Issues
1. Verify SPI pins match configuration
2. Check display driver installation
3. Ensure proper rotation setting

### Button Reading
- D0: Check for LOW (pressed) vs HIGH (released)
- D1/D2: Check for HIGH (pressed) vs LOW (released)

## References
- [Adafruit Product Page](https://www.adafruit.com/product/5691)
- [Adafruit Learning Guide](https://learn.adafruit.com/esp32-s3-reverse-tft-feather)
- [Pinouts Reference](https://learn.adafruit.com/esp32-s3-reverse-tft-feather/pinouts)