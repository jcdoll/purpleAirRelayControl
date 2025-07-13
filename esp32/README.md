# purpleAirRelayControl ESP32-S3 Implementation
Control your HVAC hardware based on PurpleAir sensor data using ESP32-S3 Reverse TFT Feather with integrated display and touch interface.

## Hardware: ESP32-S3 Reverse TFT Feather

**Board:** ESP32-S3 Reverse TFT Feather  
https://www.adafruit.com/product/5691

**Features:**
- ESP32-S3 dual-core processor (240 MHz)
- Built-in 1.14" TFT display (240x135 resolution)
- Three tactile buttons (D0, D1, D2)
- WiFi and Bluetooth 5.0
- 8MB Flash, 2MB PSRAM
- 21 GPIO pins
- Built-in USB-C connector

**Optional Hardware:**
- External antenna for longer range: https://www.adafruit.com/product/5445
- Header kit: https://www.adafruit.com/product/2886

**Relay Options:**
- Standard relay (higher power, solder jumper for A0 control): https://www.adafruit.com/product/3191
- Low power latching relay (solder two wires for control): https://www.adafruit.com/product/2923

## Platform: MicroPython

After evaluating Arduino IDE, CircuitPython, and MicroPython, MicroPython is the chosen platform for this project because:

1. **Learning Opportunity**: Excellent way to learn MicroPython with a real-world project
2. **Rapid Development**: No compile step, REPL debugging, faster iteration
3. **Code Readability**: Python syntax is clear and maintainable
4. **Excellent Hardware Support**: All required components are well-supported
5. **Rich Ecosystem**: Mature libraries for display, touch, networking, and sensors
6. **Easy Debugging**: Interactive REPL makes troubleshooting straightforward

While Arduino IDE and CircuitPython would also be acceptable solutions, MicroPython provides the best balance of learning value and development efficiency for this project.

## Getting Started with MicroPython

### 1. Flash MicroPython Firmware

```bash
# Download firmware
wget https://micropython.org/resources/firmware/ESP32_GENERIC_S3-20241025-v1.25.0.bin

# Flash firmware (Windows users: use esptool.exe)
esptool.py --chip esp32s3 --port COM3 erase_flash
esptool.py --chip esp32s3 --port COM3 write_flash 0x0 ESP32_GENERIC_S3-20241025-v1.25.0.bin
```

### 2. Install Development Tools

```bash
pip install thonny  # IDE with excellent MicroPython support
# or
pip install ampy    # Command-line file transfer tool
```

### 3. Hardware Configuration

**Pin Definitions for ESP32-S3 Reverse TFT Feather:**

```python
# Built-in TFT Display
TFT_CS = 7
TFT_RST = 40
TFT_DC = 39
TFT_MOSI = 35
TFT_SCLK = 36

# Tactile Buttons
BUTTON_D0 = 0  # Also BOOT button
BUTTON_D1 = 1
BUTTON_D2 = 2

# Relay Control
RELAY1_PIN = 5
RELAY2_PIN = 6

# Manual Switch Input
SWITCH_PIN = 9

# Status LED (built-in NeoPixel)
NEOPIXEL_PIN = 33
```

### 4. Required Libraries

**Display & Graphics:**
```python
import mip
mip.install("github:russhughes/st7789s3_mpy")  # Optimized display driver
# or
mip.install("github:russhughes/s3lcd")          # Alternative with framebuffer
```

**Button Input:**
```python
from machine import Pin  # Built-in for button handling
```

**Networking (Built-in):**
```python
import network    # WiFi management
import urequests  # HTTP client
import ujson      # JSON parser
```

### 5. Test Basic Display

```python
# Quick test to verify display works
from machine import Pin, SPI
import st7789

# Configure SPI for display
spi = SPI(1, baudrate=40000000, polarity=0, phase=0, 
          sck=Pin(36), mosi=Pin(35))
display = st7789.ST7789(spi, 240, 135, 
                       reset=Pin(40), dc=Pin(39), cs=Pin(7))

display.init()
display.fill(st7789.RED)
display.text("Hello World!", 10, 10, st7789.WHITE)
```

## MicroPython Implementation Plan

### Project Structure

```
/
├── main.py              # Main application loop
├── config.py            # Configuration settings
├── purple_air.py        # PurpleAir API client
├── ventilation.py       # Relay control logic
├── display_ui.py        # Touch display interface
├── wifi_manager.py      # WiFi connection management
└── lib/
    ├── st7789.py        # Display driver
    ├── ft6x06.py        # Touch driver
    └── urequests.py     # HTTP client
```

### Development Phases

**Phase 1: Core Functionality**
- WiFi connection management
- PurpleAir API integration
- Basic relay control
- Simple display output

**Phase 2: Display Interface**
- Button interface implementation
- Real-time air quality display
- Basic UI controls

**Phase 3: Advanced Features**
- Button-based configuration
- Data logging and graphs
- Enhanced user interface
- Error handling and recovery

### Example Implementation

```python
# main.py - Core application structure
import time
import machine
from purple_air import PurpleAirClient
from ventilation import VentilationController
from display_ui import DisplayInterface
from wifi_manager import WiFiManager

# Initialize components
wifi = WiFiManager()
purple_air = PurpleAirClient(api_key="your_key")
ventilation = VentilationController(relay_pins=[5, 6])
display = DisplayInterface()

# Initialize buttons
from machine import Pin
button_d0 = Pin(0, Pin.IN, Pin.PULL_UP)  # BOOT button
button_d1 = Pin(1, Pin.IN, Pin.PULL_UP)
button_d2 = Pin(2, Pin.IN, Pin.PULL_UP)

# Main loop
while True:
    # Update air quality data
    outdoor_aqi = purple_air.get_outdoor_aqi()
    indoor_aqi = purple_air.get_indoor_aqi()
    
    # Update display
    display.update_readings(outdoor_aqi, indoor_aqi)
    
    # Handle button input
    if not button_d0.value():  # Button pressed (active low)
        ventilation.handle_manual_override("button_0")
    if not button_d1.value():
        ventilation.handle_manual_override("button_1")
    if not button_d2.value():
        ventilation.handle_manual_override("button_2")
    
    # Update ventilation based on readings
    ventilation.update(outdoor_aqi, indoor_aqi)
    
    # Log data if needed
    if time.time() % 900 == 0:  # Every 15 minutes
        purple_air.log_data(outdoor_aqi, indoor_aqi, ventilation.state)
    
    time.sleep(1)
```

## Migration from Arduino Version

The MicroPython version will include these enhancements over the Arduino implementation:

1. **Interactive Development:**
   - REPL-based debugging and testing
   - Live code modification without recompiling
   - Easier experimentation and learning

2. **Button Control Interface:**
   - Real-time air quality display
   - Three-button controls for manual override
   - System status visualization
   - Historical data graphs

3. **Enhanced User Experience:**
   - Visual feedback for all operations
   - Button-based configuration
   - Error status display
   - Network status indicators

4. **Python Advantages:**
   - More readable and maintainable code
   - Rich standard library
   - Easy JSON and HTTP handling
   - Excellent debugging experience

## Hardware Support Status

### ✅ **Fully Supported Components**

**ESP32-S3 Features:**
- Official MicroPython firmware (v1.25.0)
- Auto-detection of PSRAM (2MB on your board)
- Built-in WiFi and Bluetooth support
- Full GPIO, I2C, SPI, PWM capabilities

**Display (ST7789):**
- `russhughes/st7789s3_mpy` - C-based driver optimized for ESP32-S3
- `russhughes/s3lcd` - ESP_LCD based with framebuffer support
- Advanced features: JPEG/PNG display, multiple fonts, graphics primitives

**Button Interface:**
- Built-in `machine.Pin` support for button handling
- Three tactile buttons (D0, D1, D2) with pull-up resistors
- Simple and reliable input method

**Networking:**
- `urequests` for HTTP/HTTPS API calls
- `ujson` for JSON parsing
- `network` module for WiFi management
- All PurpleAir API functionality supported

### ⚠️ **Minor Considerations**

**Performance:**
- Python is ~3-5x slower than C for intensive graphics operations
- Higher memory usage (~50KB more RAM overhead)
- Sufficient performance for air quality monitoring and HVAC control

**Development Notes:**
- `machine.bootloader()` has known issues on ESP32-S3 (requires physical reset)
- No impact on normal operation, only affects development workflow

## Alternative Platforms

### Arduino IDE
**Pros:**
- Maximum performance (compiled C code)
- Extensive library ecosystem
- Easy migration from existing Arduino code
- Lower memory usage

**Cons:**
- Compile-test-debug cycle slows development
- Less readable C syntax
- Steeper learning curve for beginners

### CircuitPython
**Pros:**
- Python syntax with hardware abstraction
- Beginner-friendly
- Good for rapid prototyping

**Cons:**
- Limited ESP32-S3 support
- Smaller ecosystem compared to MicroPython
- Performance limitations

### ESP-IDF
**Pros:**
- Maximum performance and features
- Full access to ESP32 capabilities
- Professional development framework

**Cons:**
- Very steep learning curve
- Complex setup and configuration
- Overkill for this project

## Why MicroPython for This Project

**Learning Value:**
- Excellent introduction to MicroPython ecosystem
- Real-world project with practical applications
- Covers networking, hardware control, and user interfaces

**Development Efficiency:**
- REPL makes experimentation easy
- No compile step speeds up iteration
- Python's readability aids debugging and maintenance

**Project Suitability:**
- All required hardware is well-supported
- Performance is sufficient for air quality monitoring
- Rich ecosystem of libraries and examples

**Future Expansion:**
- Easy to add new features and sensors
- Simple to modify thresholds and behaviors
- Excellent foundation for learning embedded Python

This project provides an excellent opportunity to learn MicroPython while building a useful HVAC control system with modern touch display interface.
