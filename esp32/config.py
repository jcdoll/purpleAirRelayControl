# Configuration for PurpleAir Relay Control System
# ESP32-S3 MicroPython Implementation

# Import secrets from separate file (not in git)
try:
    import secrets as _secrets
except ImportError:
    _secrets = None

# Expose expected names whether or not secrets.py exists so that the rest of
# the code can `import config` unconditionally.
if _secrets is not None:
    WIFI_SSID = getattr(_secrets, "WIFI_SSID", "")
    WIFI_PASSWORD = getattr(_secrets, "WIFI_PASSWORD", "")
    PURPLE_AIR_API_KEY = getattr(_secrets, "PURPLE_AIR_API_KEY", "")
    OUTDOOR_SENSOR_IDS = getattr(_secrets, "OUTDOOR_SENSOR_IDS", [])
    INDOOR_SENSOR_IDS = getattr(_secrets, "INDOOR_SENSOR_IDS", [])
    LOCAL_SENSOR_IPS = getattr(_secrets, "LOCAL_SENSOR_IPS", [])
    GOOGLE_FORMS_URL = getattr(_secrets, "GOOGLE_FORMS_URL", "")
    GOOGLE_FORMS_ENABLED = getattr(_secrets, "GOOGLE_FORMS_ENABLED", False)
    LOCAL_OUTDOOR_SENSOR_IPS = getattr(_secrets, "LOCAL_OUTDOOR_SENSOR_IPS", [])
    LOCAL_INDOOR_SENSOR_IPS = getattr(_secrets, "LOCAL_INDOOR_SENSOR_IPS", [])
else:
    print("ERROR: secrets.py not found!")
    print("Copy secrets_template.py to secrets.py and add your credentials")
    WIFI_SSID = ""
    WIFI_PASSWORD = ""
    PURPLE_AIR_API_KEY = ""
    OUTDOOR_SENSOR_IDS = []
    INDOOR_SENSOR_IDS = []
    LOCAL_SENSOR_IPS = []
    GOOGLE_FORMS_URL = ""
    GOOGLE_FORMS_ENABLED = False
    LOCAL_OUTDOOR_SENSOR_IPS = []
    LOCAL_INDOOR_SENSOR_IPS = []

# Non-secret configuration
WIFI_TIMEOUT = 30  # seconds
USE_LOCAL_SENSORS = True  # Try local network sensors first

# API Configuration (matching Arduino constants.h)
API_POLL_INTERVAL = 1800  # 30 minutes in seconds (PURPLE_AIR_DELAY)
LOCAL_POLL_INTERVAL = 60  # 1 minute in seconds (LOCAL_SENSOR_DELAY)
API_BASE_URL = "https://api.purpleair.com/v1/sensors/"
MAX_LOCAL_CONNECTION_ATTEMPTS = 3  # Retry attempts for local sensors
LOCAL_RETRY_DELAY_MS = 500  # 500ms between retry attempts
API_MAX_AGE = 3600  # Maximum age for API data in seconds

# Ventilation Control
AQI_ENABLE_THRESHOLD = 120  # Enable ventilation below this AQI
AQI_DISABLE_THRESHOLD = 130  # Disable ventilation above this AQI
DEFAULT_STATE = False  # Default relay state on startup
RELAY_MIN_AUTO_SWITCH_INTERVAL = 120  # 2 minutes between automatic state changes

# Hardware Pins (ESP32-S3 Reverse TFT Feather)
# Adafruit Power Relay FeatherWing on A0 (GPIO 8)
RELAY_PIN = 8
SWITCH_PIN = 9
BUTTON_D0 = 0  # BOOT button (pulled HIGH, active LOW)
BUTTON_D1 = 1  # Pulled LOW, active HIGH
BUTTON_D2 = 2  # Pulled LOW, active HIGH

# NeoPixel Configuration (Adafruit ESP32-S3 Reverse TFT Feather specific)
# Note: Pin assignments are specific to this Adafruit board, not generic ESP32-S3
NEOPIXEL_PIN = 33  # Built-in NeoPixel data pin (Adafruit ESP32-S3 Reverse TFT Feather)
NEOPIXEL_POWER_PIN = 21  # NeoPixel power enable (must be HIGH) - WORKING, DON'T CHANGE

# Display Configuration (ST7789 - Adafruit official pins from pinout diagram)
# https://learn.adafruit.com/esp32-s3-reverse-tft-feather/pinouts
TFT_CS = 42  # GPIO42 per official pinout
TFT_RST = 41  # GPIO41 per official pinout
TFT_DC = 40  # GPIO40 per official pinout
TFT_MOSI = 35  # SPI MOSI
TFT_SCLK = 36  # SPI SCLK
TFT_BACKLIGHT = 45  # GPIO45 per official pinout
TFT_I2C_POWER = 7  # GPIO7 per official pinout - I2C and TFT power enable
TFT_WIDTH = 135  # Display width (landscape orientation)
TFT_HEIGHT = 240  # Display height (landscape orientation)
TFT_ROTATION = 1  # Landscape mode (matches original HARDWARE.md)

# Google Forms Logging
GOOGLE_FORMS_URL = ""  # Your Google Forms submission URL
GOOGLE_FORMS_ENABLED = False
LOG_INTERVAL = 900  # 15 minutes in seconds

# System Configuration
# Default watchdog = 16000, disabled (0) to avoid breaking serial transfer during dev
WATCHDOG_TIMEOUT = 0
DEBUG_MODE = True
MEMORY_DEBUG = False
