# boot.py - ESP32 MicroPython startup configuration
# This file is executed on every boot (including wake-boot from deepsleep)

import gc
import time

import esp

# Disable debug output to save power and reduce noise
esp.osdebug(None)

# Run garbage collection to free up memory
gc.collect()

# Give system time to stabilize
time.sleep(0.5)

print("Boot sequence complete")

# DO NOT auto-import main to prevent boot loops
# Comment this out to stop auto-running main.py
# import main
