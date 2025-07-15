# UI Manager - handles all display and LED feedback
# Bike computer style interface with large, readable numbers

from machine import Pin
import time
import config

# Import display driver and font
try:
    import st7789py as st7789
    DISPLAY_AVAILABLE = True
except ImportError:
    print("Warning: st7789py display driver not found")
    DISPLAY_AVAILABLE = False

try:
    import lib.vga1_8x8 as font8x8
    FONT_AVAILABLE = True
except ImportError:
    print("Warning: vga1_8x8 font not found")
    FONT_AVAILABLE = False

# NeoPixel for status LED
try:
    import neopixel
    LED_AVAILABLE = True
except ImportError:
    print("Warning: neopixel not available")
    LED_AVAILABLE = False

class UIManager:
    def __init__(self):
        self.last_update = 0
        self.update_interval = 1  # seconds
        
        # Initialize NeoPixel
        self.led = None
        self.led_power = None
        if LED_AVAILABLE:
            self._init_led()
        
        # Initialize Display
        self.display = None
        self.tft_power = None
        self.backlight = None
        if DISPLAY_AVAILABLE and FONT_AVAILABLE:
            self._init_display()
        
        print("UIManager initialized")
    
    def _init_led(self):
        """Initialize NeoPixel LED with power management"""
        try:
            # Enable NeoPixel power
            self.led_power = Pin(config.NEOPIXEL_POWER_PIN, Pin.OUT)
            self.led_power.value(1)
            time.sleep(0.1)
            
            self.led = neopixel.NeoPixel(Pin(config.NEOPIXEL_PIN), 1)
            
            # Test flash
            self.led[0] = (10, 0, 0)
            self.led.write()
            time.sleep(0.1)
            self.led[0] = (0, 0, 0)
            self.led.write()
            
            print("  NeoPixel LED initialized")
        except Exception as e:
            print(f"  LED initialization failed: {e}")
            self.led = None
    
    def _init_display(self):
        """Initialize TFT display - simplified, no power pin testing"""
        try:
            from machine import SPI
            
            # Enable display power
            self.tft_power = Pin(config.TFT_I2C_POWER, Pin.OUT)
            self.tft_power.value(1)
            
            # Enable backlight
            self.backlight = Pin(config.TFT_BACKLIGHT, Pin.OUT)
            self.backlight.value(1)
            
            time.sleep(0.2)
            
            # Initialize SPI
            spi = SPI(1, baudrate=20000000, polarity=0, phase=0,
                     sck=Pin(config.TFT_SCLK), mosi=Pin(config.TFT_MOSI))
            
            # Initialize display
            self.display = st7789.ST7789(
                spi, 135, 240,
                reset=Pin(config.TFT_RST, Pin.OUT),
                dc=Pin(config.TFT_DC, Pin.OUT),
                cs=Pin(config.TFT_CS, Pin.OUT),
                rotation=1  # Landscape
            )
            
            self.clear_display()
            print("  TFT display initialized")
            
        except Exception as e:
            print(f"  Display initialization failed: {e}")
            self.display = None
    
    def set_led_color(self, r, g, b):
        """Set status LED color"""
        if self.led:
            self.led[0] = (r, g, b)
            self.led.write()
    
    def set_status_led(self, status):
        """Set LED based on system status"""
        if status == "wifi_connecting":
            self.set_led_color(0, 0, 64)  # Blue
        elif status == "wifi_connected":
            self.set_led_color(64, 64, 0)  # Yellow
        elif status == "vent_on":
            self.set_led_color(0, 64, 0)  # Green
        elif status == "vent_off":
            self.set_led_color(64, 0, 0)  # Red
        elif status == "error":
            self.set_led_color(64, 0, 0)  # Red
        else:
            self.set_led_color(0, 0, 0)  # Off
    
    def clear_display(self):
        """Clear the display"""
        if self.display:
            self.display.fill(st7789.BLACK)
    
    def show_message(self, message, color=None):
        """Show a simple centered message"""
        if not self.display:
            print(f"[Display] {message}")
            return
            
        self.clear_display()
        if color is None:
            color = st7789.WHITE
            
        # Center the message
        msg_width = len(message) * 8
        x = (240 - msg_width) // 2
        y = 60
        self.display.text(font8x8, message, x, y, color)
    
    def show_error(self, message):
        """Show error message in red"""
        self.show_message(message, st7789.RED)
    
    def update_display(self, outdoor_aqi, indoor_aqi, vent_controller, wifi_manager):
        """Update display with large, readable layout"""
        if not self.display:
            return
            
        current_time = time.time()
        if current_time - self.last_update < self.update_interval:
            return
        self.last_update = current_time
        
        self.clear_display()
        
        # Get status
        status = vent_controller.get_status()
        
        # OUT/IN labels (2x scale, 16px high)
        label_y = 10
        self._draw_scaled_text("OUT", 44, label_y, 2, st7789.WHITE)  # Center around x=60
        self._draw_scaled_text("IN", 172, label_y, 2, st7789.WHITE)  # Center around x=180
        
        # Large AQI numbers (4x scale, 32px high) - vertically centered at y=52
        aqi_y = 52
        
        # Outdoor AQI (left side)
        if outdoor_aqi >= 0:
            outdoor_text = str(int(outdoor_aqi))
            outdoor_color = self._get_aqi_color(outdoor_aqi)
        else:
            outdoor_text = "---"
            outdoor_color = st7789.color565(128, 128, 128)  # Gray
        
        # Center outdoor number around x=60
        outdoor_width = len(outdoor_text) * 32  # 4x scale
        outdoor_x = 60 - (outdoor_width // 2)
        self._draw_scaled_text(outdoor_text, outdoor_x, aqi_y, 4, outdoor_color)
        
        # Indoor AQI (right side)
        if indoor_aqi >= 0:
            indoor_text = str(int(indoor_aqi))
            indoor_color = self._get_aqi_color(indoor_aqi)
        else:
            indoor_text = "N/A"
            indoor_color = st7789.color565(128, 128, 128)  # Gray
        
        # Center indoor number around x=180
        indoor_width = len(indoor_text) * 32  # 4x scale
        indoor_x = 180 - (indoor_width // 2)
        self._draw_scaled_text(indoor_text, indoor_x, aqi_y, 4, indoor_color)
        
        # Status indicators (2x scale) - bottom corners
        status_y = 110
        
        # SW state (bottom left) - split color: "SW:" white, mode colored
        self._draw_scaled_text("SW:", 10, status_y, 2, st7789.WHITE)
        
        # Map mode to display text
        if status['mode'] == 'PURPLEAIR':
            mode_text = "AUTO"
            mode_color = st7789.WHITE
        elif status['mode'] == 'ON':
            mode_text = "ON" 
            mode_color = st7789.GREEN
        elif status['mode'] == 'OFF':
            mode_text = "OFF"
            mode_color = st7789.RED
        else:
            mode_text = status['mode']  # Fallback
            mode_color = st7789.WHITE
            
        self._draw_scaled_text(mode_text, 58, status_y, 2, mode_color)  # 10 + (3*16) = 58
        
        # V state (bottom right) - split color: "V:" white, state colored  
        vent_state = "ON" if status['enabled'] else "OFF"
        vent_color = st7789.GREEN if status['enabled'] else st7789.RED
        
        # Right align - calculate x position for "V:" + state
        total_text = f"V:{vent_state}"
        total_width = len(total_text) * 16  # 2x scale = 16px per char
        v_x = 230 - total_width
        
        self._draw_scaled_text("V:", v_x, status_y, 2, st7789.WHITE)
        self._draw_scaled_text(vent_state, v_x + 32, status_y, 2, vent_color)  # +32 for "V:" width
    
    def _draw_scaled_text(self, text, x, y, scale, color):
        """Draw text scaled up by scale factor using repeated character drawing"""
        if not self.display:
            return
            
        current_x = x
        for char in text:
            self._draw_scaled_char(char, current_x, y, scale, color)
            current_x += (8 * scale)
    
    def _draw_scaled_char(self, char, x, y, scale, color):
        """Draw a character scaled up by scaling the actual bitmap"""
        if not self.display:
            return
            
        # Get character bitmap data
        if ord(char) < font8x8.FIRST or ord(char) >= font8x8.LAST:
            return  # Character not in font
        
        char_index = ord(char) - font8x8.FIRST
        char_data_start = char_index * 8
        
        # Draw scaled bitmap
        for row in range(8):
            byte_data = font8x8.FONT[char_data_start + row]
            for col in range(8):
                # Check bits in reverse order since font data is already bit-reversed
                if byte_data & (1 << (7 - col)):  # Pixel is on
                    # Draw scaled pixel as filled rectangle
                    pixel_x = x + (col * scale)
                    pixel_y = y + (row * scale)
                    # Fill scale x scale rectangle for this pixel
                    for sx in range(scale):
                        for sy in range(scale):
                            self.display.pixel(pixel_x + sx, pixel_y + sy, color)
    
    def _get_aqi_color(self, aqi):
        """Get color based on AQI value"""
        if aqi < 0:
            return st7789.color565(128, 128, 128)  # Gray for invalid
        elif aqi <= 50:
            return st7789.color565(0, 255, 0)      # Green - Good
        elif aqi <= 100:
            return st7789.color565(255, 255, 0)    # Yellow - Moderate
        elif aqi <= 150:
            return st7789.color565(255, 165, 0)    # Orange - Unhealthy for sensitive
        elif aqi <= 200:
            return st7789.color565(255, 0, 0)      # Red - Unhealthy
        elif aqi <= 300:
            return st7789.color565(128, 0, 128)    # Purple - Very unhealthy
        else:
            return st7789.color565(128, 0, 0)      # Maroon - Hazardous 