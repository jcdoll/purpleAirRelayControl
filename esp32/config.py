# Configuration for PurpleAir Relay Control System
# ESP32-S3 MicroPython Implementation

# Import secrets from separate file (not in git)
try:
    from secrets import *
except ImportError:
    print("ERROR: secrets.py not found!")
    print("Copy secrets_template.py to secrets.py and add your credentials")
    WIFI_SSID = "NOT_SET"
    WIFI_PASSWORD = "NOT_SET"
    PURPLE_AIR_API_KEY = "NOT_SET"
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

# API Configuration
API_POLL_INTERVAL = 1800  # 30 minutes in seconds
LOCAL_POLL_INTERVAL = 60  # 1 minute in seconds
API_BASE_URL = "https://api.purpleair.com/v1/sensors/"

# Ventilation Control
AQI_ENABLE_THRESHOLD = 120   # Enable ventilation below this AQI
AQI_DISABLE_THRESHOLD = 130  # Disable ventilation above this AQI
DEFAULT_STATE = False        # Default relay state on startup

# Hardware Pins (ESP32-S3 Reverse TFT Feather)
RELAY1_PIN = 5
RELAY2_PIN = 6
SWITCH_PIN = 9
BUTTON_D0 = 0  # BOOT button
BUTTON_D1 = 1
BUTTON_D2 = 2
NEOPIXEL_PIN = 33

# Display Configuration
TFT_CS = 7
TFT_RST = 40
TFT_DC = 39
TFT_MOSI = 35
TFT_SCLK = 36
DISPLAY_WIDTH = 135
DISPLAY_HEIGHT = 240

# Google Forms Logging
GOOGLE_FORMS_URL = ""  # Your Google Forms submission URL
GOOGLE_FORMS_ENABLED = False
LOG_INTERVAL = 900  # 15 minutes in seconds

# System Configuration
WATCHDOG_TIMEOUT = 16000  # milliseconds
DEBUG_MODE = True
MEMORY_DEBUG = False