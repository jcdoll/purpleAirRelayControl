# boot.py - ESP32 MicroPython startup configuration
# This file is executed on every boot (including wake-boot from deepsleep)

import esp
import gc

# Disable debug output to save power and reduce noise
esp.osdebug(None)

# Run garbage collection to free up memory
gc.collect()

# Optional: Set CPU frequency (default is 160MHz, can go up to 240MHz)
# import machine
# machine.freq(240000000)  # 240MHz for better performance

print("Boot sequence complete")