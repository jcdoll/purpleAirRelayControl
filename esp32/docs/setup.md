# MicroPython Setup Guide

## Overview

This guide covers setting up the ESP32-S3 Reverse TFT Feather with MicroPython for the PurpleAir Relay Control project.

## Why MicroPython?

After evaluating Arduino IDE, CircuitPython, and MicroPython, MicroPython is the chosen platform because:

1. Learning Opportunity: Excellent way to learn MicroPython with a real-world project
2. Rapid Development: No compile step, REPL debugging, faster iteration
3. Code Readability: Python syntax is clear and maintainable
4. Excellent Hardware Support: All required components are well-supported
5. Rich Ecosystem: Mature libraries for display, touch, networking, and sensors
6. Easy Debugging: Interactive REPL makes troubleshooting straightforward

## Prerequisites

### Hardware Required
- ESP32-S3 Reverse TFT Feather (Adafruit #5691)
- USB-C cable for programming
- Computer with USB port

### Software Required
- Python 3.7+ installed
- Terminal/Command Prompt access

## Step 1: Prepare Development Environment

### Create Virtual Environment (Recommended)

Linux/Mac:
```bash
python3 -m venv venv
source venv/bin/activate
```

Windows:
```bash
python -m venv venv
venv\Scripts\activate
```

### Install Required Tools
```bash
pip install esptool mpremote
```

## Step 2: Find Your ESP32 Port

### Windows
```powershell
# Method 1: PowerShell command
Get-WmiObject Win32_SerialPort | Select-Object Name, DeviceID, Description

# Method 2: Device Manager
# 1. Press Win+X and select Device Manager
# 2. Expand "Ports (COM & LPT)"
# 3. Look for "USB Serial Device" or "CP210x" or "CH340"
# Common ports: COM3, COM4, COM5
```

### Linux
```bash
ls /dev/ttyUSB* /dev/ttyACM*
# Common ports: /dev/ttyUSB0, /dev/ttyACM0
```

### Mac
```bash
ls /dev/tty.usbserial* /dev/tty.usbmodem*
# Common ports: /dev/tty.usbserial-0001, /dev/tty.usbmodem14101
```

### WSL (Windows Subsystem for Linux)
WSL doesn't have direct USB access. Use Windows COM port from Device Manager and access as `/dev/ttyS3` (for COM3), etc.

## Step 3: Download MicroPython Firmware

### For Adafruit ESP32-S3 TFT Feather with TinyUF2 Bootloader
```bash
# Download UF2 firmware file
wget https://micropython.org/resources/firmware/ESP32_GENERIC_S3-20250415-v1.25.0.uf2
```

### For Generic ESP32-S3 Boards
```bash
# Download BIN firmware file
wget https://micropython.org/resources/firmware/ESP32_GENERIC_S3-20250415-v1.25.0.bin
```

## Step 4: Ensure Correct Bootloader (Adafruit Boards Only)

CRITICAL: Before flashing MicroPython, verify you have the correct TinyUF2 bootloader version.

### Check Bootloader Version
1. Hold BOOT button (D0) and press RESET
2. If `FTHRS3BOOT` drive appears, check bootloader version
3. For MicroPython, you need the single partition bootloader

### Install Correct Bootloader if Needed
If you need to update the bootloader, follow the [Adafruit Factory Reset Guide](https://learn.adafruit.com/esp32-s3-reverse-tft-feather/factory-reset):

Download the correct bootloader:
- For MicroPython: Use `ESP32-S3 Reverse TFT Feather UF2 bootloader 0.33.0 combined.bin` 
- This provides a single 2.8MB firmware partition (required for MicroPython)
- NOT the `combined-ota.bin` version (that's for CircuitPython dual-bank)

Flash bootloader using esptool:
```bash
# Enter ROM bootloader mode first:
# 1. Hold BOOT button and press RESET
# 2. Release RESET, keep holding BOOT until connected
# 3. Release BOOT

# Erase and flash bootloader
esptool --chip esp32s3 --port COM3 erase_flash
esptool --chip esp32s3 --port COM3 write_flash 0x0 tinyuf2-adafruit_feather_esp32s3_tft-0.33.0-combined.bin
```

## Step 5: Flash MicroPython Firmware

### Method A: Using TinyUF2 Bootloader (Adafruit Boards)

After confirming correct bootloader is installed:
1. Hold BOOT button (D0) and press RESET
2. A `FTHRS3BOOT` drive should appear
3. Drag the `.uf2` file onto the drive
4. Board auto-flashes and reboots with MicroPython
5. Press RESET (without BOOT) to exit bootloader mode

### Method B: Using esptool (All Boards)

Erase existing firmware:
```bash
# Linux/Mac
esptool.py --chip esp32s3 --port /dev/ttyUSB0 erase_flash

# Windows
esptool --chip esp32s3 --port COM3 erase_flash
```

Flash MicroPython:
```bash
# For boards WITHOUT bootloader (flash at 0x0)
esptool.py --chip esp32s3 --port /dev/ttyUSB0 write_flash 0x0 ESP32_GENERIC_S3-20250415-v1.25.0.bin

# For boards WITH TinyUF2 bootloader (flash at 0x10000)  
esptool --chip esp32s3 --port COM3 write_flash 0x10000 ESP32_GENERIC_S3-20250415-v1.25.0.bin
```

### Troubleshooting Flash Issues

Connection Problems:
- Hold BOOT button (D0) while running esptool commands
- Keep holding until you see "Connecting..." then release
- Try different baudrates: add `--baud 115200` to esptool command

Flash Size Errors:
- If you see "partition 3 invalid - exceeds flash chip size"
- You have wrong firmware! Generic version is for 8MB flash
- Adafruit ESP32-S3 TFT Feather has 4MB flash - use TinyUF2 method

## Step 6: Verify Installation

### Test MicroPython REPL
```bash
# Connect to board
mpremote connect auto

# Should see MicroPython prompt:
# MicroPython v1.25.0 on 2024-04-15; ESP32-S3 module with ESP32S3
# Type "help()" for more information.
# >>>

# Test basic functionality
>>> print("Hello MicroPython!")
>>> import machine
>>> machine.freq()

# Exit REPL with Ctrl+X
```

## Step 7: Install Required Libraries

### Display Driver
```bash
# Method 1: Using mip (on device)
mpremote exec "import mip; mip.install('github:russhughes/st7789s3_mpy')"

# Method 2: Manual installation (download and copy files)
# Download st7789.py from the repository and copy to /lib/
```

Test Display:
```python
# Quick test script (save as test_display.py)
from machine import Pin, SPI
import st7789
import config

# Configure SPI for display (see hardware.md for pin details)
spi = SPI(1, baudrate=40000000, polarity=0, phase=0, 
          sck=Pin(config.TFT_SCLK), mosi=Pin(config.TFT_MOSI))
display = st7789.ST7789(spi, config.TFT_HEIGHT, config.TFT_WIDTH, 
                       reset=Pin(config.TFT_RST), dc=Pin(config.TFT_DC), cs=Pin(config.TFT_CS))

display.init()
display.fill(st7789.RED)
display.text("Setup Complete!", 10, 10, st7789.WHITE)
```

### Test Hardware Components

For specific pin assignments and hardware details, see [Hardware Documentation](hardware.md).

Hardware test scripts use config.py constants - see [Hardware Documentation](hardware.md) for all pin details.

## Step 8: Deploy Project Code

### Using Deploy Script
```bash
# Clone project repository
git clone <repository-url>
cd purpleAirRelayControl/esp32

# Configure secrets
cp secrets_template.py secrets.py
# Edit secrets.py with your WiFi credentials and API keys

# Deploy all files
python deploy.py
```

### Manual File Transfer
See [Development Guidelines](development.md) for detailed file transfer commands.

## Step 9: Configuration

### Edit Configuration Files
1. Copy `secrets_template.py` to `secrets.py`
2. Edit `secrets.py` with your settings:
   - WiFi SSID and password
   - PurpleAir API key
   - Google Forms logger URL (optional)

### Test Configuration
```bash
# Run configuration test
mpremote run test_config.py
```

## Step 10: Run Project

### Start Main Application
```bash
# Run main application
mpremote run main.py

# Or start with REPL access
mpremote exec "exec(open('main.py').read())"
```

### Expected Behavior
1. WiFi connection established
2. Display shows startup message
3. NeoPixel LED shows status
4. Air quality data retrieved and displayed
5. Ventilation control active based on AQI thresholds

## Development Tools

See [Development Guidelines](development.md) for detailed development workflow and advanced commands.

## Common Issues

### WiFi Connection Problems
- Verify SSID and password in `secrets.py`
- Check signal strength
- Try 2.4GHz network (5GHz not supported)

### Display Not Working
- See [Hardware Documentation](hardware.md) for troubleshooting details

### Memory Issues
- MicroPython has limited RAM
- Use `gc.collect()` periodically
- Avoid large string concatenations
- Check memory usage with `gc.mem_free()`

### Import Errors
- Verify files are uploaded to device
- Check file names match import statements
- Ensure library files are in `/lib/` directory

## Next Steps

After successful setup:
1. Review [Development Guidelines](development.md)
2. Check [Hardware Documentation](hardware.md)
3. Explore the code in the main project files
4. Consider contributing improvements or reporting issues 