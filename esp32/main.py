import time
import machine
import gc
from machine import Pin, WDT
import config
from wifi_manager import WiFiManager
from purple_air import PurpleAirClient
from ventilation import VentilationController
from display_ui import DisplayInterface
from google_logger import GoogleFormsLogger

# Initialize watchdog timer if enabled
if config.WATCHDOG_TIMEOUT > 0:
    wdt = WDT(timeout=config.WATCHDOG_TIMEOUT)
else:
    wdt = None

# Initialize NeoPixel for status LED
try:
    import neopixel
    np = neopixel.NeoPixel(Pin(config.NEOPIXEL_PIN), 1)
    LED_AVAILABLE = True
except:
    LED_AVAILABLE = False
    print("NeoPixel not available")

def set_status_led(r, g, b):
    """Set status LED color"""
    if LED_AVAILABLE:
        np[0] = (r, g, b)
        np.write()

def initialize_components():
    """Initialize all system components"""
    print("PurpleAir Relay Control - ESP32 MicroPython")
    print("Initializing components...")
    
    # Initialize display first for user feedback
    display = DisplayInterface()
    display.show_message("Starting up...")
    
    # Initialize WiFi
    set_status_led(0, 0, 64)  # Blue for WiFi connecting
    wifi = WiFiManager()
    if not wifi.connect():
        display.show_error("WiFi Failed!")
        set_status_led(64, 0, 0)  # Red for error
        print(f"Failed to connect to WiFi SSID: {config.WIFI_SSID}")
        time.sleep(5)
        machine.reset()
    set_status_led(64, 64, 0)  # Yellow for connected
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
    print(f"  API Key configured: {'Yes' if config.PURPLE_AIR_API_KEY else 'No'}")
    
    # Force initial sensor reads
    print("\nPerforming initial sensor checks...")
    outdoor_aqi = purple_air.get_outdoor_aqi(force_update=True)
    indoor_aqi = purple_air.get_indoor_aqi(force_update=True)
    print(f"\nInitial readings: Outdoor AQI={outdoor_aqi}, Indoor AQI={indoor_aqi}")
    
    return display, wifi, purple_air, ventilation, logger


def main():
    """Main application loop"""
    # Initialize all components
    display, wifi, purple_air, ventilation, logger = initialize_components()
    
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
    display.show_message("Ready!")
    time.sleep(1)
    
    while True:
        try:
            # Feed watchdog
            if wdt:
                wdt.feed()
            
            # Check WiFi connection
            if not wifi.is_connected():
                set_status_led(0, 0, 64)  # Blue for reconnecting
                wifi.reconnect()
                if wifi.is_connected():
                    set_status_led(64, 64, 0)  # Yellow for connected
                else:
                    set_status_led(64, 0, 0)  # Red for disconnected
            
            # Get AQI data
            outdoor_aqi = purple_air.get_outdoor_aqi()
            indoor_aqi = purple_air.get_indoor_aqi()
            
            # Update ventilation control
            ventilation.update(outdoor_aqi, indoor_aqi)
            
            # Update display
            display.update(outdoor_aqi, indoor_aqi, ventilation, wifi)
            
            # Set status LED based on ventilation state
            if ventilation.ventilation_enabled:
                set_status_led(0, 64, 0)  # Green for ventilating
            else:
                set_status_led(64, 0, 0)  # Red for not ventilating
            
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
            
            # Small delay to prevent tight loop
            time.sleep(0.1)
            
        except KeyboardInterrupt:
            print("\nShutdown requested")
            display.show_message("Shutting down...")
            set_status_led(0, 0, 0)  # Turn off LED
            break
            
        except Exception as e:
            error_count += 1
            print(f"Error in main loop: {e}")
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
        if LED_AVAILABLE:
            # Flash red LED
            for _ in range(5):
                set_status_led(64, 0, 0)
                time.sleep(0.5)
                set_status_led(0, 0, 0)
                time.sleep(0.5)
        machine.reset()