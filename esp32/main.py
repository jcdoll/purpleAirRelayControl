import time
import machine
import gc
from machine import WDT
import config
from wifi_manager import WiFiManager
from purple_air import PurpleAirClient
from ventilation import VentilationController
from ui_manager import UIManager
from google_logger import GoogleFormsLogger

# Initialize watchdog timer if enabled
if config.WATCHDOG_TIMEOUT > 0:
    wdt = WDT(timeout=config.WATCHDOG_TIMEOUT)
else:
    wdt = None

def initialize_components():
    """Initialize all system components"""
    print("PurpleAir Relay Control - ESP32 MicroPython")
    print("Initializing UI...")
    
    # Initialize UI Manager (handles both display and LED)
    ui = UIManager()
    ui.show_message("Starting up...")
    
    # Initialize WiFi
    ui.set_status_led("wifi_connecting")
    wifi = WiFiManager()
    if not wifi.connect():
        ui.show_error("WiFi Failed!")
        ui.set_status_led("error")
        print(f"Failed to connect to WiFi SSID: {config.WIFI_SSID}")
        time.sleep(5)
        machine.reset()
    ui.set_status_led("wifi_connected")
    print(f"WiFi connected successfully!")
    print(f"  SSID: {config.WIFI_SSID}")
    print(f"  IP: {wifi.get_ip()}")
    print(f"  Signal: {wifi.get_rssi()} dBm")
    
    # Initialize other components
    purple_air = PurpleAirClient()
    ventilation = VentilationController()
    logger = GoogleFormsLogger()
    
    # Show sensor configuration
    print("\nSensor Configuration:")
    print(f"  Outdoor sensors:")
    print(f"    Local IPs: {purple_air.local_outdoor_ips}")
    print(f"    API IDs: {config.OUTDOOR_SENSOR_IDS}")
    print(f"  Indoor sensors:")
    print(f"    Local IPs: {purple_air.local_indoor_ips}")
    print(f"    API IDs: {config.INDOOR_SENSOR_IDS}")
    # Check if API key is properly configured (not just present)
    api_key_valid = (config.PURPLE_AIR_API_KEY and 
                     config.PURPLE_AIR_API_KEY.strip() != "" and
                     len(config.PURPLE_AIR_API_KEY) > 10)
    print(f"  API Key configured: {'Yes' if api_key_valid else 'No'}")
    
    # Force initial sensor reads
    print("\nPerforming initial sensor checks...")
    try:
        outdoor_aqi = purple_air.get_outdoor_aqi(force_update=True)
        indoor_aqi = purple_air.get_indoor_aqi(force_update=True)
        print(f"\nInitial readings: Outdoor AQI={outdoor_aqi}, Indoor AQI={indoor_aqi}")
        
        # Debug check for tuple issues
        print(f"Debug - outdoor_aqi type: {type(outdoor_aqi)}, value: {outdoor_aqi}")
        print(f"Debug - indoor_aqi type: {type(indoor_aqi)}, value: {indoor_aqi}")
    except Exception as e:
        print(f"\nError during initial sensor checks: {type(e).__name__}: {e}")
        import sys
        sys.print_exception(e)
        outdoor_aqi = -1
        indoor_aqi = -1
    
    return ui, wifi, purple_air, ventilation, logger


def main():
    """Main application loop"""
    # Initialize all components
    ui, wifi, purple_air, ventilation, logger = initialize_components()
    
    # State tracking
    error_count = 0
    last_memory_check = 0
    last_status_print = 0
    status_print_interval = 5  # Print status every 5 seconds
    
    # Print initial WiFi info
    if wifi.is_connected():
        print(f"WiFi connected! SSID: {config.WIFI_SSID}")
        print(f"IP Address: {wifi.get_ip()}")
    
    print("System initialized. Starting main loop...")
    ui.show_message("Ready!")
    time.sleep(1)
    
    while True:
        try:
            # Feed watchdog
            if wdt:
                wdt.feed()
            
            # Check WiFi connection
            if not wifi.is_connected():
                ui.set_status_led("wifi_connecting")
                wifi.reconnect()
                if wifi.is_connected():
                    ui.set_status_led("wifi_connected")
                else:
                    ui.set_status_led("error")
            
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
            
            # Update display
            ui.update_display(outdoor_aqi, indoor_aqi, ventilation, wifi)
            
            # Set status LED based on ventilation state
            if ventilation.ventilation_enabled:
                ui.set_status_led("vent_on")
            else:
                ui.set_status_led("vent_off")
            
            # Log data if needed
            if ventilation.should_log() or logger.should_log():
                status = ventilation.get_status()
                logger.log(outdoor_aqi, indoor_aqi, status['mode'], 
                          status['enabled'], status['reason'])
            
            # Memory debugging
            if config.MEMORY_DEBUG and time.time() - last_memory_check > 60:
                last_memory_check = time.time()
                gc.collect()
                free_mem = gc.mem_free()
                used_mem = gc.mem_alloc()
                print(f"Memory - Free: {free_mem/1024:.1f}KB, Used: {used_mem/1024:.1f}KB")
            
            # Print status periodically
            current_time = time.time()
            if current_time - last_status_print >= status_print_interval:
                last_status_print = current_time
                status = ventilation.get_status()
                print(f"[{current_time}] AQI: Outdoor={outdoor_aqi:.1f}, Indoor={indoor_aqi:.1f} | " +
                      f"Mode: {status['mode']} | Ventilation: {'ON' if status['enabled'] else 'OFF'} | " +
                      f"Reason: {status['reason']}")
            
            # Reset error count on successful iteration
            error_count = 0
            
            # Arduino uses 1 second loop delay (LOOP_DELAY = 1000ms)
            time.sleep(1.0)
            
        except KeyboardInterrupt:
            print("\nShutdown requested")
            ui.show_message("Shutting down...")
            ui.set_status_led("off")
            break
            
        except Exception as e:
            error_count += 1
            print(f"\nError in main loop: {type(e).__name__}: {e}")
            
            # Print full stack trace
            import sys
            sys.print_exception(e)
            
            ui.show_error("System Error")
            
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