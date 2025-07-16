import gc
import time

import config
import machine
from display_manager import DisplayManager
from google_logger import GoogleFormsLogger
from led_manager import LEDManager
from machine import WDT
from purple_air import PurpleAirClient
from utils.status_display import (
    print_sensor_config,
    print_sensor_countdown_timers,
    print_sensor_status,
    print_startup_banner,
)
from ventilation import VentilationController
from wifi_manager import WiFiManager

# Initialize watchdog timer if enabled
if config.WATCHDOG_TIMEOUT > 0:
    wdt = WDT(timeout=config.WATCHDOG_TIMEOUT)
else:
    wdt = None


def initialize_components():
    """Initialize all system components"""
    print_startup_banner()
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

            # Get AQI data
            outdoor_aqi = purple_air.get_outdoor_aqi()
            indoor_aqi = purple_air.get_indoor_aqi()

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

            # EVENT-BASED LOGGING: Check for changes
            sensor_data_changed = (
                outdoor_aqi != prev_outdoor_aqi or indoor_aqi != prev_indoor_aqi
            )
            vent_state_changed = current_status['enabled'] != prev_vent_state
            mode_changed = current_status['mode'] != prev_mode

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
                print_sensor_status(
                    outdoor_aqi, indoor_aqi, ventilation.get_status(), "Mode changed"
                )

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
                print(
                    f"Memory - Free: {free_mem/1024:.1f}KB, Used: {used_mem/1024:.1f}KB"
                )

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
