# secrets.py - Private configuration (DO NOT COMMIT)
# Copy this file to secrets.py and fill in your values

# WiFi Configuration
WIFI_SSID = "YOUR_WIFI_SSID"
WIFI_PASSWORD = "YOUR_WIFI_PASSWORD"

# PurpleAir Configuration
PURPLE_AIR_API_KEY = "YOUR_API_KEY"

# Sensor IDs
OUTDOOR_SENSOR_IDS = [12345, 67890]  # Your outdoor sensor IDs
INDOOR_SENSOR_IDS = [11111]          # Your indoor sensor IDs (optional, leave empty if none)

# Local sensor IPs (optional) - for direct HTTP access on local network
# IMPORTANT: These must be in the same order as OUTDOOR_SENSOR_IDS
LOCAL_OUTDOOR_SENSOR_IPS = []  # e.g., ["192.168.1.100", "192.168.1.101"]
LOCAL_INDOOR_SENSOR_IPS = []   # e.g., ["192.168.1.102"]

# Google Forms (optional)
GOOGLE_FORMS_URL = ""  # Your Google Forms submission URL
GOOGLE_FORMS_ENABLED = False