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

# Initialize NeoPixel for status LED with proper power management
neopixel_power = None
tft_power = None
backlight = None
LED_AVAILABLE = False

try:
    # NeoPixel setup for Adafruit ESP32-S3 Reverse TFT Feather (requires power pin)
    print("Setting up NeoPixel...")
    
    # Enable NeoPixel power (required for Adafruit ESP32-S3 Reverse TFT Feather)
    neopixel_power = Pin(config.NEOPIXEL_POWER_PIN, Pin.OUT)
    neopixel_power.value(1)  # Enable power
    time.sleep(0.1)  # Allow power to stabilize
    
    import neopixel
    np = neopixel.NeoPixel(Pin(config.NEOPIXEL_PIN), 1)
    
    # Test the LED
    np[0] = (10, 0, 0)  # Dim red test
    np.write()
    time.sleep(0.2)
    np[0] = (0, 0, 0)
    np.write()
    
    LED_AVAILABLE = True
    print("  NeoPixel initialized successfully (Adafruit ESP32-S3 Reverse TFT Feather)")
        
except Exception as e:
    LED_AVAILABLE = False
    print(f"NeoPixel initialization error: {e}")

# Initialize Display with proper power management
try:
    print("Setting up Display...")
    
    # Set up display power pins
    for tft_power_pin in [7, 21]:  # Try different power pin options
        try:
            print(f"  Trying TFT power pin GPIO {tft_power_pin}...")
            tft_power = Pin(tft_power_pin, Pin.OUT)
            tft_power.value(1)  # Enable TFT power
            time.sleep(0.2)
            
            # Set up backlight
            try:
                backlight = Pin(config.TFT_BACKLIGHT, Pin.OUT)
                backlight.value(1)  # Enable backlight
                print(f"  Backlight enabled on GPIO {config.TFT_BACKLIGHT}")
            except:
                print("  Backlight setup failed, continuing without it...")
            
            # Initialize display with power management
            from display_ui import DisplayInterface
            display = DisplayInterface()
            
            if display.display is not None:
                print(f"  Display working with power pin GPIO {tft_power_pin}")
                break
            else:
                print(f"  Display failed with power pin GPIO {tft_power_pin}")
                continue
                
        except Exception as e:
            print(f"  Failed with TFT power pin GPIO {tft_power_pin}: {e}")
            continue
    else:
        # If all power pins failed, create dummy display
        print("  Creating dummy display (no hardware display available)")
        class DummyDisplay:
            def show_message(self, msg):
                print(f"[Display] {msg}")
            def show_error(self, msg):
                print(f"[Display Error] {msg}")
            def update(self, *args):
                pass
            def clear(self):
                pass
        display = DummyDisplay()
        
except Exception as e:
    print(f"Display initialization error: {e}")
    # Create dummy display as fallback
    class DummyDisplay:
        def show_message(self, msg):
            print(f"[Display] {msg}")
        def show_error(self, msg):
            print(f"[Display Error] {msg}")
        def update(self, *args):
            pass
        def clear(self):
            pass
    display = DummyDisplay()

def set_status_led(r, g, b):
    """Set status LED color"""
    if LED_AVAILABLE:
        print(f"Setting LED to RGB({r}, {g}, {b})")
        np[0] = (r, g, b)
        np.write()
    else:
        print(f"LED not available - would set RGB({r}, {g}, {b})")

def initialize_components():
    """Initialize all system components"""
    print("PurpleAir Relay Control - ESP32 MicroPython")
    print("Initializing other components...")
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
            display.update(outdoor_aqi, indoor_aqi, ventilation, wifi)
            
            # Set status LED based on ventilation state
            if ventilation.ventilation_enabled:
                if not hasattr(ventilation, '_last_led_state') or ventilation._last_led_state != 'green':
                    set_status_led(0, 64, 0)  # Green for ventilating
                    ventilation._last_led_state = 'green'
            else:
                if not hasattr(ventilation, '_last_led_state') or ventilation._last_led_state != 'red':
                    set_status_led(64, 0, 0)  # Red for not ventilating
                    ventilation._last_led_state = 'red'
            
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
            display.show_message("Shutting down...")
            set_status_led(0, 0, 0)  # Turn off LED
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
        if LED_AVAILABLE:
            # Flash red LED
            for _ in range(5):
                set_status_led(64, 0, 0)
                time.sleep(0.5)
                set_status_led(0, 0, 0)
                time.sleep(0.5)
        machine.reset()