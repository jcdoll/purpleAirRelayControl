import gc
import time

import config
import machine
import settings
from display_manager import DisplayManager
from google_logger import GoogleFormsLogger
from led_manager import LEDManager
from machine import WDT
from mqtt_client import MQTTManager
from purple_air import PurpleAirClient
from ventilation import VentilationController
from wifi_manager import WiFiManager

from utils.status_display import (
    print_sensor_config,
    print_sensor_countdown_timers,
    print_sensor_status,
    print_startup_banner,
)


def iso_utc_now():
    # ISO 8601 UTC timestamp -- HA timestamp-class sensors expect this format.
    # Returns None if the system clock is unset (NTP not synced yet).
    t = time.gmtime()
    if t[0] < 2024:
        return None
    return f"{t[0]:04d}-{t[1]:02d}-{t[2]:02d}T{t[3]:02d}:{t[4]:02d}:{t[5]:02d}+00:00"


def sync_ntp():
    try:
        import ntptime
        ntptime.settime()
        print(f"NTP sync ok: {iso_utc_now()}")
    except Exception as e:
        print(f"NTP sync failed: {type(e).__name__}: {e}")

# Initialize watchdog timer if enabled
if config.WATCHDOG_TIMEOUT > 0:
    wdt = WDT(timeout=config.WATCHDOG_TIMEOUT)
else:
    wdt = None


def initialize_components():
    """Initialize all system components"""
    print_startup_banner()
    settings.load(config)
    print("Initializing display and LED...")

    # Initialize Display and LED Managers (split from UIManager)
    display = DisplayManager()
    led = LEDManager()
    display.show_message("Starting up...")

    # Initialize WiFi
    led.set_status_led("wifi_connecting")
    wifi = WiFiManager()
    if not wifi.connect():
        display.show_error("WiFi Failed!")
        led.set_status_led("error")
        print(f"Failed to connect to WiFi SSID: {config.WIFI_SSID}")
        time.sleep(5)
        machine.reset()
    led.set_status_led("wifi_connected")
    print("WiFi connected successfully!")
    print(f"  SSID: {config.WIFI_SSID}")
    print(f"  IP: {wifi.get_ip()}")
    print(f"  Signal: {wifi.get_rssi()} dBm")

    # Set the system clock so timestamp-class HA entities work
    sync_ntp()

    # Initialize other components
    purple_air = PurpleAirClient()
    ventilation = VentilationController()
    logger = GoogleFormsLogger()

    # Show sensor configuration using utility function
    print_sensor_config(purple_air)

    # Force initial sensor reads
    print("\nPerforming initial sensor checks...")
    try:
        outdoor_aqi = purple_air.get_outdoor_aqi(force_update=True)
        indoor_aqi = purple_air.get_indoor_aqi(force_update=True)
        print(f"\nInitial readings: Outdoor AQI={outdoor_aqi}, Indoor AQI={indoor_aqi}")
    except Exception as e:
        print(f"\nError during initial sensor checks: {type(e).__name__}: {e}")
        import sys

        sys.print_exception(e)
        outdoor_aqi = -1
        indoor_aqi = -1

    return display, led, wifi, purple_air, ventilation, logger


# Status printing functions now available from utils.status_display
# print_sensor_countdown_timers, print_sensor_status, print_sensor_config, print_startup_banner


def main():
    """Main application loop"""
    # Initialize all components
    display, led, wifi, purple_air, ventilation, logger = initialize_components()

    # Force-refresh flag toggled by the HA "Refresh AQI" button
    refresh_requested = [False]

    def on_refresh():
        refresh_requested[0] = True

    # MQTT for Home Assistant remote control (best-effort, never blocks main loop)
    mqtt = MQTTManager(
        mode_callback=ventilation.set_mode,
        threshold_callback=lambda name, value: settings.save(name, value, config),
        refresh_callback=on_refresh,
    )
    if mqtt.is_enabled():
        mqtt.connect()

    # State tracking for event-based logging
    error_count = 0
    last_memory_check = 0
    last_countdown_display = 0
    countdown_display_interval = 30  # Show countdown every 30 seconds

    # Track previous values for change detection
    prev_outdoor_aqi = None
    prev_indoor_aqi = None
    prev_vent_state = None
    prev_mode = None
    prev_thr_enable = None
    prev_thr_disable = None
    last_aqi_update = None

    # Print initial WiFi info
    if wifi.is_connected():
        print(f"WiFi connected! SSID: {config.WIFI_SSID}")
        print(f"IP Address: {wifi.get_ip()}")

    print("System initialized. Starting main loop...")
    display.show_message("Ready!")
    time.sleep(1)

    while True:
        try:
            # Feed watchdog
            if wdt:
                wdt.feed()

            # Check WiFi connection
            if not wifi.is_connected():
                led.set_status_led("wifi_connecting")
                wifi.reconnect()
                if wifi.is_connected():
                    led.set_status_led("wifi_connected")
                else:
                    led.set_status_led("error")

            # Get AQI data (force_update if HA Refresh button was pressed)
            force = refresh_requested[0]
            refresh_requested[0] = False
            outdoor_aqi = purple_air.get_outdoor_aqi(force_update=force)
            indoor_aqi = purple_air.get_indoor_aqi(force_update=force)

            # Ensure AQI values are numbers, not tuples
            if isinstance(outdoor_aqi, tuple):
                print(f"WARNING: outdoor_aqi is tuple: {outdoor_aqi}")
                outdoor_aqi = outdoor_aqi[0] if outdoor_aqi else -1
            if isinstance(indoor_aqi, tuple):
                print(f"WARNING: indoor_aqi is tuple: {indoor_aqi}")
                indoor_aqi = indoor_aqi[0] if indoor_aqi else -1

            # Update ventilation control
            ventilation.update(outdoor_aqi, indoor_aqi)
            current_status = ventilation.get_status()

            # Refresh the last-update timestamp on any successful AQI read
            if outdoor_aqi >= 0 or indoor_aqi >= 0:
                ts = iso_utc_now()
                if ts:
                    last_aqi_update = ts

            # EVENT-BASED LOGGING: Check for changes
            sensor_data_changed = outdoor_aqi != prev_outdoor_aqi or indoor_aqi != prev_indoor_aqi
            vent_state_changed = current_status['enabled'] != prev_vent_state
            mode_changed = current_status['mode'] != prev_mode
            threshold_changed = (config.AQI_ENABLE_THRESHOLD != prev_thr_enable
                                 or config.AQI_DISABLE_THRESHOLD != prev_thr_disable)

            # Print status on any change (like Arduino event-based logging)
            if sensor_data_changed:
                print_sensor_status(
                    outdoor_aqi,
                    indoor_aqi,
                    ventilation.get_status(),
                    "Sensor data updated",
                )

            if vent_state_changed:
                print_sensor_status(
                    outdoor_aqi,
                    indoor_aqi,
                    ventilation.get_status(),
                    "Ventilation state changed",
                )

            if mode_changed:
                print_sensor_status(outdoor_aqi, indoor_aqi, ventilation.get_status(), "Mode changed")

            # Publish state to MQTT on any change
            if sensor_data_changed or vent_state_changed or mode_changed or threshold_changed:
                mqtt.publish_state(
                    current_status['mode'],
                    current_status['enabled'],
                    outdoor_aqi,
                    indoor_aqi,
                    current_status['reason'],
                    aqi_enable_threshold=config.AQI_ENABLE_THRESHOLD,
                    aqi_disable_threshold=config.AQI_DISABLE_THRESHOLD,
                    last_update=last_aqi_update,
                )

            # Service MQTT (process incoming commands, reconnect if needed)
            mqtt.check_messages()

            # Update display
            display.update_display(outdoor_aqi, indoor_aqi, ventilation, wifi)

            # Set status LED based on ventilation state
            if ventilation.ventilation_enabled:
                led.set_status_led("vent_on")
            else:
                led.set_status_led("vent_off")

            # Log data if needed (event-based)
            if ventilation.should_log() or logger.should_log():
                status = ventilation.get_status()
                logger.log(
                    outdoor_aqi,
                    indoor_aqi,
                    status['mode'],
                    status['enabled'],
                    status['reason'],
                )

            # Memory debugging
            if config.MEMORY_DEBUG and time.time() - last_memory_check > 60:
                last_memory_check = time.time()
                gc.collect()
                free_mem = gc.mem_free()
                used_mem = gc.mem_alloc()
                print(f"Memory - Free: {free_mem/1024:.1f}KB, Used: {used_mem/1024:.1f}KB")

            # Show countdown timers periodically (like Arduino does)
            current_time = time.time()
            if current_time - last_countdown_display >= countdown_display_interval:
                last_countdown_display = current_time
                print_sensor_countdown_timers(purple_air)

            # Update previous values for next iteration
            prev_outdoor_aqi = outdoor_aqi
            prev_indoor_aqi = indoor_aqi
            prev_vent_state = current_status['enabled']
            prev_mode = current_status['mode']
            prev_thr_enable = config.AQI_ENABLE_THRESHOLD
            prev_thr_disable = config.AQI_DISABLE_THRESHOLD

            # Reset error count on successful iteration
            error_count = 0

            # Arduino uses 1 second loop delay (LOOP_DELAY = 1000ms)
            time.sleep(1.0)

        except KeyboardInterrupt:
            print("\nShutdown requested")
            display.show_message("Shutting down...")
            led.set_status_led("off")
            break

        except Exception as e:
            error_count += 1
            print(f"\nError in main loop: {type(e).__name__}: {e}")

            # Print full stack trace
            import sys

            sys.print_exception(e)

            display.show_error("System Error")

            if error_count > 10:
                print("Too many errors, resetting...")
                time.sleep(5)
                machine.reset()

            time.sleep(1)


# Run main application
if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Fatal error: {e}")
        machine.reset()
