# LED Manager - handles status LED feedback via NeoPixel
# Extracted from ui_manager.py for better separation of concerns

from machine import Pin
import config
from utils.error_handling import print_exception, handle_hardware_error

# NeoPixel for status LED
try:
    import neopixel
    LED_AVAILABLE = True
except ImportError:
    print("Warning: neopixel not available")
    LED_AVAILABLE = False

class LEDManager:
    def __init__(self):
        self.led = None
        self.led_power = None
        
        if LED_AVAILABLE:
            self._init_led()
    
    def _init_led(self):
        """Initialize NeoPixel LED with proper power management"""
        try:
            # Power management for NeoPixel (critical on Adafruit boards)
            self.led_power = Pin(config.NEOPIXEL_POWER_PIN, Pin.OUT)
            self.led_power.on()  # Must be HIGH for NeoPixel to work
            
            # Initialize NeoPixel
            self.led = neopixel.NeoPixel(Pin(config.NEOPIXEL_PIN), 1)
            self.led[0] = (0, 0, 0)  # Start with LED off
            self.led.write()
            
            print("LED Manager: NeoPixel initialized")
            
        except Exception as e:
            handle_hardware_error(e, "NeoPixel LED")
            self.led = None
            self.led_power = None
    
    def set_status_led(self, status):
        """
        Set status LED color based on system state
        Args:
            status: Status string (wifi_connecting, wifi_connected, vent_on, vent_off, error, off)
        """
        if not self.led:
            return
        
        try:
            # Status color mapping
            colors = {
                'off': (0, 0, 0),           # Black (off)
                'wifi_connecting': (255, 165, 0),  # Orange (connecting)
                'wifi_connected': (0, 0, 255),     # Blue (connected)
                'vent_on': (0, 255, 0),     # Green (ventilation running)
                'vent_off': (255, 255, 0),  # Yellow (ventilation off)
                'error': (255, 0, 0),       # Red (error state)
            }
            
            color = colors.get(status, (128, 0, 128))  # Purple for unknown status
            self.led[0] = color
            self.led.write()
            
        except Exception as e:
            handle_hardware_error(e, "NeoPixel status update")
    
    def set_custom_color(self, r, g, b):
        """
        Set LED to custom RGB color
        Args:
            r, g, b: RGB values (0-255)
        """
        if not self.led:
            return
        
        try:
            self.led[0] = (r, g, b)
            self.led.write()
        except Exception as e:
            handle_hardware_error(e, "NeoPixel color set")
    
    def flash_led(self, color=(255, 255, 255), duration_ms=100):
        """
        Flash LED briefly (for notifications)
        Args:
            color: RGB tuple for flash color
            duration_ms: Flash duration in milliseconds
        """
        if not self.led:
            return
        
        try:
            import time
            
            # Save current color
            original_color = tuple(self.led[0])
            
            # Flash
            self.led[0] = color
            self.led.write()
            time.sleep_ms(duration_ms)
            
            # Restore
            self.led[0] = original_color
            self.led.write()
            
        except Exception as e:
            handle_hardware_error(e, "NeoPixel flash")
    
    def is_available(self):
        """Check if LED is available and initialized"""
        return self.led is not None
    
    def cleanup(self):
        """Turn off LED and cleanup resources"""
        if self.led:
            try:
                self.led[0] = (0, 0, 0)
                self.led.write()
            except Exception as e:
                print_exception(e, "LED cleanup") 