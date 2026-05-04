# Persistent settings on the ESP32 filesystem.
#
# Stored in /settings.json. Loaded on boot to override config defaults; updated
# when the user changes runtime values from Home Assistant. Only the keys in
# PERSISTED_KEYS are honoured -- everything else is ignored.

import json

SETTINGS_FILE = "settings.json"
PERSISTED_KEYS = ("AQI_ENABLE_THRESHOLD", "AQI_DISABLE_THRESHOLD")


def load(config_module):
    try:
        with open(SETTINGS_FILE) as f:
            data = json.load(f)
    except OSError:
        return
    except Exception as e:
        print(f"Settings load error: {type(e).__name__}: {e}")
        return
    for key, value in data.items():
        if key in PERSISTED_KEYS and hasattr(config_module, key):
            setattr(config_module, key, value)
            print(f"Loaded {key} = {value}")


def save(name, value, config_module):
    if name not in PERSISTED_KEYS:
        print(f"Settings save: ignoring unknown key {name}")
        return False
    try:
        try:
            with open(SETTINGS_FILE) as f:
                data = json.load(f)
        except OSError:
            data = {}
        data[name] = value
        if hasattr(config_module, name):
            setattr(config_module, name, value)
        with open(SETTINGS_FILE, "w") as f:
            json.dump(data, f)
        print(f"Saved {name} = {value}")
        return True
    except Exception as e:
        print(f"Settings save error: {type(e).__name__}: {e}")
        return False
