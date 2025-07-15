# ESP32 MicroPython Implementation Setup

This guide covers setting up the ESP32-S3 Reverse TFT Feather with the PurpleAir Relay Control MicroPython implementation.

## Hardware Requirements

- **ESP32-S3 Reverse TFT Feather** (Adafruit #5691)
- **2x Relays** for ventilation control
- **Manual override switch** (optional)
- **Wiring:**
  - Relay 1: GPIO 5
  - Relay 2: GPIO 6
  - Manual Switch: GPIO 9
  - Built-in buttons: D0 (GPIO 0), D1 (GPIO 1), D2 (GPIO 2)

## Software Setup

### 1. Prepare Your ESP32-S3 Board

```bash
# IMPORTANT: Adafruit ESP32-S3 Reverse TFT Feather (4MB) requires special setup
# The generic MicroPython firmware expects 8MB flash and won't work on 4MB boards

# Step 1a: For Adafruit ESP32-S3 TFT Feather ONLY - Install TinyUF2 bootloader
# This provides proper 4MB partition layout
# Download from: https://learn.adafruit.com/adafruit-esp32-s3-tft-feather/factory-reset
# Get: tinyuf2-adafruit_feather_esp32s3_tft-0.33.0-combined.bin

# Flash the bootloader (Adafruit boards only):
esptool --chip esp32s3 --port COM3 write-flash 0x0 tinyuf2-adafruit_feather_esp32s3_tft-0.33.0-combined.bin

# Verify bootloader installation:
# 1. Hold BOOT (D0) and press RESET
# 2. A FTHRS3BOOT drive should appear
# 3. Press RESET (without BOOT) to exit bootloader mode

# Step 1b: Download MicroPython firmware
# For Adafruit boards with TinyUF2, download the UF2 file:
Invoke-WebRequest -Uri "https://micropython.org/resources/firmware/ESP32_GENERIC_S3-20250415-v1.25.0.uf2" -OutFile "ESP32_GENERIC_S3-20250415-v1.25.0.uf2"

# For boards without bootloader, download the BIN file:
Invoke-WebRequest -Uri "https://micropython.org/resources/firmware/ESP32_GENERIC_S3-20250415-v1.25.0.bin" -OutFile "ESP32_GENERIC_S3-20250415-v1.25.0.bin"
```

### 2. Flash MicroPython Firmware
```bash
# Create virtual environment (recommended)
# For Mac/Linux:
python3 -m venv venv
source venv/bin/activate

# For Windows:
python -m venv venv
venv\Scripts\activate

# Install esptool
pip install esptool

# Find your ESP32 port
# For WSL:
# WSL doesn't have direct USB access. Use Windows COM port:
# 1. Open Windows Device Manager
# 2. Look under "Ports (COM & LPT)" for your ESP32
# 3. Use the COM port directly (e.g., COM3, COM4)
# Or in Windows PowerShell: Get-PnpDevice -Class Ports

# For Linux (native):
ls /dev/ttyUSB* /dev/ttyACM*
# Common ports: /dev/ttyUSB0, /dev/ttyACM0

# For Mac:
ls /dev/tty.usbserial* /dev/tty.usbmodem*
# Common ports: /dev/tty.usbserial-0001, /dev/tty.usbmodem14101

# For Windows (native):
# In PowerShell (as Administrator):
Get-WmiObject Win32_SerialPort | Select-Object Name, DeviceID, Description
# Or check Device Manager:
# 1. Press Win+X and select Device Manager
# 2. Expand "Ports (COM & LPT)"
# 3. Look for "USB Serial Device" or "CP210x" or "CH340"
# Common ports: COM3, COM4, COM5
#
# PS C:\Windows\System32> Get-WmiObject Win32_SerialPort | Select-Object Name, DeviceID, Description

# Name                                       DeviceID Description
# ----                                       -------- -----------
# Standard Serial over Bluetooth link (COM7) COM7     Standard Serial over Bluetooth link
# Standard Serial over Bluetooth link (COM8) COM8     Standard Serial over Bluetooth link
# USB Serial Device (COM3)                   COM3     USB Serial Device
# --> device is on COM3

# Erase flash (replace PORT with your actual port)
# Note: Windows uses 'esptool' without '.py'
# Examples:
esptool.py --chip esp32s3 --port /dev/ttyUSB0 erase-flash # Linux
esptool.py --chip esp32s3 --port /dev/tty.usbserial-0001 erase-flash # Mac
esptool --chip esp32s3 --port COM3 erase-flash # Windows Powershell
esptool.exe --chip esp32s3 --port COM3 erase-flash # Windows CMD

# Flash MicroPython (use your port from above)
# IMPORTANT: For ESP32-S3 boards, you may need to specify flash size and mode
# Note: flash options go AFTER write-flash command

# If you get "Failed to connect" errors:
# The ESP32-S3 Reverse TFT Feather has 3 buttons: D0, D1, D2
# D0 is the BOOT button (leftmost button)
# Hold down D0 while running the command
# Keep holding until you see "Connecting..." then release

# Flashing depends on whether you have a bootloader:

# Option A: No bootloader (bare ESP32) - flash at 0x0:
esptool.py --chip esp32s3 --port PORT write-flash 0x0 ESP32_GENERIC_S3-20250415-v1.25.0.bin # Linux/Mac
esptool --chip esp32s3 --port COM5 write-flash 0x0 ESP32_GENERIC_S3-20250415-v1.25.0.bin # Windows

# Option B: With TinyUF2 bootloader (Adafruit boards) - use UF2 file:
# 1. Enter bootloader: Hold BOOT (D0) and press RESET
# 2. FTHRS3BOOT drive appears
# 3. Drag ESP32_GENERIC_S3-20250415-v1.25.0.uf2 onto the drive
# 4. Board auto-flashes and reboots with MicroPython

# Alternative: Use esptool with BIN file at offset 0x10000:
esptool --chip esp32s3 --port COM3 write-flash 0x10000 ESP32_GENERIC_S3-20250415-v1.25.0.bin

# ERROR: If you see "partition 3 invalid - exceeds flash chip size"
# You have the wrong firmware! The generic version is for 8MB flash.
# You MUST download a 4MB-specific version.

# After flashing completes:
# 1. Wait 5-10 seconds for the board to reset
# 2. The serial port may briefly disconnect/reconnect
# 3. Then proceed to step 2
# 4. Re-check the serial port, it probably has changed

# Sample output
(venv) PS D:\Documents\GitHub\personal\purpleAirRelayControl\esp32> esptool --chip esp32s3 --port COM3 write-flash 0x0 ESP32_GENERIC_S3-20250415-v1.25.0.bin
esptool v5.0.0
Connected to ESP32-S3 on COM3:
Chip type:          ESP32-S3 (QFN56) (revision v0.1)
Features:           Wi-Fi, BT 5 (LE), Dual Core + LP Core, 240MHz, Embedded Flash 4MB (XMC), Embedded PSRAM 2MB (AP_3v3)
Crystal frequency:  40MHz
USB mode:           USB-Serial/JTAG
MAC:                64:e8:33:73:cd:9c

Stub flasher running.

Configuring flash size...
Flash will be erased from 0x00000000 to 0x00198fff...
Wrote 1673008 bytes (1096502 compressed) at 0x00000000 in 17.0 seconds (786.1 kbit/s).
```

### 2. Install mpremote

```bash
# Ensure virtual environment is activated (see step 1)
pip install mpremote

# Verify installation
mpremote --help
```

### 3. Install Required Libraries

Since the ESP32 needs internet to use mip, we'll download the display driver on your PC and transfer it:

```bash
# Download libraries on your PC and transfer them
# This avoids needing WiFi on the ESP32

# Create lib directory locally and on ESP32
mkdir lib -ErrorAction SilentlyContinue  # Windows PowerShell
# mkdir -p lib  # Linux/Mac

# IMPORTANT: MicroPython v1.23+ added 4MB support for ESP32-S3
# Per v1.23 release notes: "boards/ESP32_GENERIC_S3: add 4MiB partitioning board variant"
# However, the generic firmware may still use 8MB partitions

# If you see "Flash size: 0MB" or filesystem errors:

# Option 1: Look for a 4MB-specific build variant
# Check if there's a specific FLASH_4M variant in the downloads
# The generic build might default to 8MB partitions

# Option 2: Use CircuitPython instead
# https://circuitpython.org/board/adafruit_feather_esp32s3_reverse_tft/
# CircuitPython is designed specifically for this Adafruit board

# Option 3: Build MicroPython from source with 4MB config
# The 4MB support exists but may need specific build configuration

# Test if filesystem works - paste these commands one at a time:

import os
from flashbdev import bdev

# First try to unmount
try:
    os.umount('/')
except:
    pass

# Now try to format and mount
try:
    os.VfsLfs2.mkfs(bdev)
    print("Format complete")
    os.mount(os.VfsLfs2(bdev), '/')
    print("Mounted!")
    os.mkdir('/lib')
    print("Created /lib")
    print(os.listdir('/'))
except Exception as e:
    print(f"Error: {e}")

# After connecting with mpremote, verify your setup - paste this entire block:

import os
import esp
print(f"Flash size: {esp.flash_size()/1024/1024:.1f}MB")
print(f"Files: {os.listdir('/')}")
try:
    os.mkdir('/lib')
    print("Created /lib successfully!")
except:
    print("/lib already exists or error")
print(f"Files after: {os.listdir('/')}")

# You should see 4.0MB or similar (not 0MB)
# Exit REPL with Ctrl+X

# Download the ST7789 display driver (pure Python version)
# This driver works but without font support initially
# Windows PowerShell:
Invoke-WebRequest -Uri "https://raw.githubusercontent.com/russhughes/st7789py_mpy/master/lib/st7789py.py" -OutFile "lib/st7789py.py"

# Linux/Mac/WSL:
wget https://raw.githubusercontent.com/russhughes/st7789py_mpy/master/lib/st7789py.py -P lib/

# Note: The display will show colored bars instead of text until fonts are added
# The system works fine without the display - NeoPixel LED shows status:
# - Blue: WiFi connecting
# - Yellow: WiFi connected
# - Green: Ventilation ON
# - Red: Ventilation OFF/error

# Deploy all files with the provided script:
python deploy.py          # Auto-detect port
python deploy.py COM5     # Specify port

# The deploy script will:
# 1. Upload the display driver library
# 2. Upload all Python files
# 3. Reset the board
# 4. Show you how to monitor output

# Manual deployment (if needed):
mpremote connect COM5 cp lib/st7789.mpy :lib/st7789.mpy + cp *.py : + reset
```

### 4. Configure Your Settings

```bash
# Copy the template and add your credentials
cp secrets_template.py secrets.py

# Edit secrets.py with your private settings:
# - WiFi credentials
# - PurpleAir API key
# - Sensor IDs
# - Google Forms URL (optional)

# The secrets.py file is gitignored and won't be committed
```

Example secrets.py:
```python
# WiFi Configuration
WIFI_SSID = "MyHomeWiFi"
WIFI_PASSWORD = "MySecurePassword"

# PurpleAir Configuration
PURPLE_AIR_API_KEY = "12345678-1234-1234-1234-123456789012"
OUTDOOR_SENSOR_IDS = [123456, 123457]
INDOOR_SENSOR_IDS = [123458]

# Local sensors (optional)
LOCAL_SENSOR_IPS = ["192.168.1.100"]

# Google Forms (optional)
GOOGLE_FORMS_URL = "https://docs.google.com/forms/d/e/YOUR_FORM_ID/formResponse"
GOOGLE_FORMS_ENABLED = True
```

### 5. Upload Files to ESP32

```bash
# Upload all files at once (Linux/Mac)
mpremote connect /dev/ttyUSB0 cp *.py :

# Upload all files at once (Windows)
mpremote connect COM3 cp *.py :

# Or upload files individually
mpremote connect COM3 cp boot.py :boot.py
mpremote connect COM3 cp main.py :main.py
mpremote connect COM3 cp config.py :config.py
mpremote connect COM3 cp wifi_manager.py :wifi_manager.py
mpremote connect COM3 cp purple_air.py :purple_air.py
mpremote connect COM3 cp ventilation.py :ventilation.py
mpremote connect COM3 cp display_ui.py :display_ui.py
mpremote connect COM3 cp google_logger.py :google_logger.py

# List files on device to verify
mpremote connect COM3 ls
```

### 6. Test the System

```bash
# Reset the board and enter REPL (Linux/Mac)
mpremote connect /dev/ttyUSB0 reset
mpremote connect /dev/ttyUSB0 repl

# Reset the board and enter REPL (Windows)
mpremote connect COM3 reset
mpremote connect COM3 repl

# Monitor output without entering REPL
mpremote connect COM3 run --no-follow

# Useful mpremote commands:
# - Ctrl+C: Interrupt running program (use if no prompt appears)
# - Ctrl+D: Soft reset (restarts MicroPython) - DO NOT press physical RESET button
# - Ctrl+X: Exit mpremote
# - If no prompt: Press Enter, then Ctrl+C to interrupt

# IMPORTANT: Never press physical RESET while connected with mpremote
# It breaks the serial connection. Use Ctrl+D for soft reset instead
```

## Usage

### Button Controls

The three buttons act as a 3-position switch:
- **D0 (BOOT)**: OFF mode - Ventilation always OFF
- **D1**: ON mode - Ventilation always ON  
- **D2**: PURPLEAIR mode - Automatic control based on AQI

### Display Information

The TFT display shows:
- Current outdoor AQI with color-coded bar
- Current indoor AQI (if configured)
- Ventilation status (ON/OFF)
- Current mode (PURPLEAIR/ON/OFF)
- WiFi connection status
- Status reason

### LED Status

The built-in NeoPixel LED indicates:
- **Blue**: Connecting to WiFi
- **Yellow**: WiFi connected
- **Green**: Ventilation ON
- **Red**: Ventilation OFF or error

### Operating Modes

1. **PURPLEAIR Mode** (Automatic):
   - Ventilation controlled by AQI thresholds
   - Enables when outdoor AQI < 120
   - Disables when outdoor AQI > 130

2. **Manual ON Mode**:
   - Ventilation always ON
   - Ignores AQI readings

3. **Manual OFF Mode**:
   - Ventilation always OFF
   - Ignores AQI readings

## Recovery Procedures

### Complete Board Recovery (If Bootloader/Firmware Corrupted)

If your ESP32-S3 board stops responding to MicroPython commands or shows filesystem corruption, you may need to completely restore the bootloader and firmware. This can happen if:

- The filesystem becomes corrupted
- Wrong firmware was flashed
- The TinyUF2 bootloader was accidentally overwritten
- You see errors like "The filesystem appears to be corrupted"

**Recovery Steps:**

1. **Put board in bootloader mode:**
   - Hold down **BOOT button (D0)** 
   - Press and release **RESET button**
   - Release **BOOT button**
   - Board should now be in bootloader mode

2. **Flash TinyUF2 bootloader:**
   ```bash
   esptool --chip esp32s3 --port COM3 write_flash 0x0 tinyuf2-adafruit_feather_esp32s3_tft-0.33.0-combined.bin
   ```

3. **Flash MicroPython firmware (choose Option A or B):**

   **Option A: UF2 drag-and-drop method (PREFERRED)**
   ```bash
   # 1. TinyUF2 drive should already be mounted as FTHRS3BOOT
   # 2. Check what drive letter it mounted as:
   Get-Volume | Where-Object {$_.FileSystemLabel -like "*TinyUF2*" -or $_.FileSystemLabel -like "*FEATHERS3*"}
   
   # 3. Copy/drag the UF2 file to the mounted drive:
   Copy-Item ESP32_GENERIC_S3-20250415-v1.25.0.uf2 F:\
   # (Replace F:\ with your actual drive letter)
   
   # 4. Board will automatically flash and reboot into MicroPython
   # 5. The FTHRS3BOOT drive should disappear when successful
   ```

   **Option B: Command line with .bin file (NOT RECOMMENDED)**
   ```bash
   # NOTE: This method does not work properly with TinyUF2 bootloader
   # The board may remain in bootloader mode instead of booting MicroPython
   # Use Option A instead for TinyUF2 boards
   
   # Put board back into bootloader mode for esptool:
   # - Hold down BOOT button (D0)
   # - Press and release RESET button  
   # - Release BOOT button
   
   # Flash MicroPython at offset 0x10000 (after TinyUF2 bootloader)
   esptool --chip esp32s3 --port COM3 write_flash 0x10000 ESP32_GENERIC_S3-20250415-v1.25.0.bin
   ```

4. **Verify recovery:**
   ```bash
   # The FTHRS3BOOT drive should disappear after successful UF2 flash
   # Board will reboot into MicroPython (COM port may change)
   
   # Connect with auto-detection:
   mpremote connect auto
   
   # Or specify port (check Device Manager for current port):
   mpremote connect COM5
   
   # You should see MicroPython prompt:
   # MicroPython v1.25.0 on 2025-04-15; Generic ESP32S3 module with ESP32S3
   # Type "help()" for more information.
   # >>>
   ```

5. **Useful mpremote commands:**
   ```bash
   # Connect to REPL
   mpremote connect auto          # Auto-detect port
   mpremote connect COM5          # Specific port
   
   # REPL control commands (while connected):
   # Ctrl-C: Interrupt running program
   # Ctrl-D: Soft reboot (restarts MicroPython)
   # Ctrl-X: Exit shell and disconnect
   ```

6. **Redeploy your application:**
   ```bash
   # Copy secrets file and deploy application
   python deploy.py              # Auto-detect port
   python deploy.py COM5         # Specific port
   ```

**Notes:**
- Option A (UF2 method) is the proper way to work with TinyUF2 bootloader
- Option B (esptool) does not work correctly with TinyUF2 and is not recommended
- After recovery, you'll need to redeploy all your application files
- The COM port number may change during the recovery process (COM3 → COM5 in this example)
- Use `mpremote connect auto` for automatic port detection

## Troubleshooting

### "failed to access COM3 (it may be in use by another program)"

This error occurs when the serial port is locked by another application. Common causes:

1. **Serial Monitor/Terminal Open**
- Close any serial terminal programs (PuTTY, Tera Term, Arduino Serial Monitor)
- Close Arduino IDE if open
- Close Thonny if running

2. **Previous mpremote Session**
- Check Task Manager for stuck python/mpremote processes
- Kill any orphaned processes:
```powershell
# Find processes using the port
Get-Process | Where-Object {$_.ProcessName -match "python|mpremote"}

# Or use Resource Monitor to find what's using COM3
resmon.exe
# Go to CPU tab -> Associated Handles -> Search for "COM3"
```

3. **Windows Serial Port Lock**
- Unplug and replug the ESP32
- Wait 5-10 seconds before reconnecting
- Try a different USB port

4. **Quick Fixes**
```powershell
# Option 1: Force close all Python processes
taskkill /F /IM python.exe

# Option 2: Restart in PowerShell
# Close all terminals, unplug ESP32, wait 5 seconds, replug

# Option 3: Use Device Manager
# Right-click COM3 -> Disable -> Enable
```

5. **Check What's Using the Port**
```powershell
# PowerShell command to check serial ports
[System.IO.Ports.SerialPort]::getportnames()

# Check if port is accessible
$port = new-Object System.IO.Ports.SerialPort COM3
$port.Open()
$port.Close()
```

6. **Alternative Solutions**
- Try using `--no-exclusive` flag (if available in your mpremote version)
- Use a different terminal/PowerShell window
- Restart your computer (last resort)

### "Failed to connect to ESP32-S3: Invalid head of packet"

This happens when MicroPython is running and using the serial port. Solutions:

1. **Hold BOOT button while connecting**:
   - Hold down the BOOT button (D0) on your ESP32-S3
   - While holding BOOT, run the esptool command
   - Keep holding until you see "Connecting..."
   - Release when it starts erasing

2. **Reset into bootloader mode**:
   - Press and hold BOOT button
   - Press and release RESET button
   - Release BOOT button
   - Now run esptool command

3. **If already in REPL**:
   ```python
   # In REPL, put it in raw mode
   import machine
   machine.bootloader()
   # Board will disconnect, then run esptool
   ```

4. **Alternative: Use lower baud rate**:
   ```bash
   esptool --chip esp32s3 --port COM5 --baud 115200 erase-flash
   ```

### "Cannot configure port" Error
- Wrong baud rate - ESP32-S3 typically uses 115200
- Driver issues - Reinstall USB-to-Serial drivers
- Bad USB cable - Try a different cable (data cable, not charge-only)

### ESP32 Not Detected
- Install CP210x or CH340 drivers
- Check Windows Device Manager for driver errors
- Try different USB port (USB 2.0 ports sometimes work better)

### mpremote Hangs
- Press Ctrl+C to interrupt
- Press Ctrl+X to exit
- Kill the process if frozen

### Display Not Working
- Verify ST7789 driver is installed: `import st7789`
- Check SPI pin connections in config.py
- Try reducing SPI baudrate to 20000000

### WiFi Connection Issues
- Check credentials in config.py
- Ensure 2.4GHz network (5GHz not supported)
- Monitor serial output for error messages

### AQI Data Not Updating
- Verify API key is correct
- Check sensor IDs are valid
- Test API manually: https://api.purpleair.com/v1/sensors/{sensor_id}

### Memory Issues
- Enable MEMORY_DEBUG in config.py to monitor usage
- Normal usage: ~50-70KB free memory
- If low, try disabling features (display, logging)

## Development Tips

### Main Development Loop

The typical development workflow is:

```bash
# 1. Make code changes in your editor

# 2. Deploy to ESP32
python deploy.py COM5

# 3. Connect to REPL and monitor output
mpremote connect COM5 repl

# 4. Soft reset to see boot sequence (Ctrl+D)
# You'll see:
# - Boot messages
# - WiFi connection with IP address
# - System initialization
# - Status updates every 5 seconds

# 5. To stop and check state: Ctrl+C
# 6. To exit mpremote: Ctrl+X
```

### Testing with mpremote

```bash
# Enter REPL for interactive testing
mpremote connect COM3 repl

# Test individual components in REPL:
>>> from wifi_manager import WiFiManager
>>> wifi = WiFiManager()
>>> wifi.connect()

>>> from purple_air import PurpleAirClient
>>> pa = PurpleAirClient()
>>> print(pa.get_outdoor_aqi())

>>> from ventilation import VentilationController
>>> vent = VentilationController()
>>> print(vent.get_status())

# Run a specific file
mpremote connect COM3 run test_script.py

# Execute commands directly
mpremote connect COM3 exec "import gc; print(f'Free: {gc.mem_free()}')"

# Mount local directory for live editing
mpremote connect COM3 mount .
# Now you can edit files locally and run them on device
```

### Debugging
- Set `DEBUG_MODE = True` in config.py
- Use `print()` statements for debugging
- Monitor memory with `gc.mem_free()`

### Performance Optimization
- Display updates limited to 1Hz
- API polling: 30 minutes (configurable)
- Local sensor polling: 1 minute (configurable)

## Future Enhancements

- [ ] Web interface for configuration
- [ ] Historical data graphing on display
- [ ] OTA (Over-The-Air) updates
- [ ] Data export to SD card
- [ ] Mobile app integration