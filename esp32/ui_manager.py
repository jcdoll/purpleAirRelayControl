# UI Manager - handles all display and LED feedback
# Simple UI with large, readable numbers
# Uses software frame buffer to eliminate display flashing

from machine import Pin
import time
import gc
import os
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
        self.last_memory_check = 0
        self.update_interval = 1  # seconds
        self.memory_check_interval = 30  # seconds
        
        # Frame buffer for flicker-free updates
        self.frame_buffer = None
        self.buffer_width = 0
        self.buffer_height = 0
        
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
        
        # Initial memory check
        self._check_system_resources()
        
        print("UIManager initialized with software frame buffer")
    
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
        """Initialize TFT display with software frame buffer"""
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
            
            # Set up frame buffer dimensions (after rotation)
            # rotation=1 means landscape: 240x135
            self.buffer_width = 240
            self.buffer_height = 135
            
            # Create software frame buffer (width * height * 2 bytes for RGB565)
            buffer_size = self.buffer_width * self.buffer_height * 2
            print(f"  Creating frame buffer: {buffer_size} bytes ({buffer_size//1024}KB)")
            
            try:
                self.frame_buffer = bytearray(buffer_size)
                print(f"  Frame buffer allocated successfully")
            except MemoryError:
                print("  ERROR: Not enough memory for frame buffer - falling back to direct drawing")
                self.frame_buffer = None
            
            self._clear_buffer()
            self._flush_buffer()
            print("  TFT display initialized with frame buffer")
            
        except Exception as e:
            print(f"  Display initialization failed: {e}")
            self.display = None
            self.frame_buffer = None
    
    def _check_system_resources(self):
        """Check and report system memory and storage"""
        current_time = time.time()
        if current_time - self.last_memory_check < self.memory_check_interval:
            return
        
        self.last_memory_check = current_time
        
        # Memory check
        gc.collect()  # Force garbage collection first
        free_ram = gc.mem_free()
        used_ram = gc.mem_alloc()
        total_ram = free_ram + used_ram
        
        print(f"[Memory] Free: {free_ram//1024}KB, Used: {used_ram//1024}KB, Total: {total_ram//1024}KB")
        
        # Flash storage check
        try:
            statvfs = os.statvfs('/')
            block_size = statvfs[0]  # f_bsize
            total_blocks = statvfs[2]  # f_blocks  
            free_blocks = statvfs[3]  # f_bavail
            
            total_flash = total_blocks * block_size
            free_flash = free_blocks * block_size
            used_flash = total_flash - free_flash
            
            print(f"[Flash] Free: {free_flash//1024}KB, Used: {used_flash//1024}KB, Total: {total_flash//1024}KB")
            
            # Warn if running low
            if free_ram < 50000:  # Less than 50KB
                print("WARNING: Low RAM available!")
            if free_flash < 100000:  # Less than 100KB
                print("WARNING: Low flash storage available!")
                
        except Exception as e:
            print(f"[Flash] Could not check storage: {e}")
    
    def _clear_buffer(self):
        """Clear the software frame buffer (fill with black)"""
        if self.frame_buffer:
            # Fill with black (0x0000 in RGB565)
            for i in range(0, len(self.frame_buffer), 2):
                self.frame_buffer[i] = 0x00
                self.frame_buffer[i + 1] = 0x00
    
    def _color565_to_bytes(self, color565):
        """Convert RGB565 color to high/low bytes"""
        return (color565 >> 8) & 0xFF, color565 & 0xFF
    
    def _draw_pixel_to_buffer(self, x, y, color565):
        """Draw a single pixel to the frame buffer"""
        if not self.frame_buffer or x < 0 or x >= self.buffer_width or y < 0 or y >= self.buffer_height:
            return
        
        # Calculate buffer position (2 bytes per pixel for RGB565)
        pos = (y * self.buffer_width + x) * 2
        if pos + 1 < len(self.frame_buffer):
            high_byte, low_byte = self._color565_to_bytes(color565)
            self.frame_buffer[pos] = high_byte
            self.frame_buffer[pos + 1] = low_byte
    
    def _draw_char_to_buffer(self, char, x, y, scale, color565):
        """Draw a single character to the frame buffer"""
        if not FONT_AVAILABLE or not self.frame_buffer:
            return
        
        # Get character bitmap from font
        char_code = ord(char)
        if char_code < 32 or char_code > 126:
            char_code = 32  # Space for unknown characters
        
        # Font is 8x8 pixels, each character is 8 consecutive bytes in flat array
        char_start_index = (char_code - 32) * 8
        
        # Draw each pixel of the character
        for row in range(8):
            byte_data = font8x8.FONT[char_start_index + row]
            for col in range(8):
                if byte_data & (1 << col):  # Pixel is set
                    # Draw scaled pixel
                    for sy in range(scale):
                        for sx in range(scale):
                            pixel_x = x + (7 - col) * scale + sx  # Reverse col for correct orientation
                            pixel_y = y + row * scale + sy
                            self._draw_pixel_to_buffer(pixel_x, pixel_y, color565)
    
    def _draw_text_to_buffer(self, text, x, y, scale, color565):
        """Draw text to the frame buffer"""
        if not self.frame_buffer:
            return
        
        current_x = x
        for char in text:
            self._draw_char_to_buffer(char, current_x, y, scale, color565)
            current_x += (8 * scale)
    
    def _flush_buffer(self):
        """Copy the entire frame buffer to the display - single hardware operation"""
        if self.display and self.frame_buffer:
            # Single hardware write - NO FLASHING!
            self.display.blit_buffer(self.frame_buffer, 0, 0, self.buffer_width, self.buffer_height)
        elif self.display:
            # Fallback if no frame buffer
            self.display.fill(st7789.BLACK)
    
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
        """Clear the display using frame buffer"""
        if self.frame_buffer:
            self._clear_buffer()
            self._flush_buffer()
        elif self.display:
            self.display.fill(st7789.BLACK)
    
    def show_message(self, message, color=None):
        """Show a simple centered message using frame buffer"""
        if not self.display:
            print(f"[Display] {message}")
            return
        
        if color is None:
            color = st7789.WHITE
        
        if self.frame_buffer:
            # Use frame buffer - no flashing
            self._clear_buffer()
            
            # Center the message
            msg_width = len(message) * 8
            x = (self.buffer_width - msg_width) // 2
            y = 60
            
            self._draw_text_to_buffer(message, x, y, 1, color)
            self._flush_buffer()
        else:
            # Fallback to direct drawing
            self.display.fill(st7789.BLACK)
            msg_width = len(message) * 8
            x = (240 - msg_width) // 2
            y = 60
            self.display.text(font8x8, message, x, y, color)
    
    def show_error(self, message):
        """Show error message in red"""
        self.show_message(message, st7789.RED)
    
    def update_display(self, outdoor_aqi, indoor_aqi, vent_controller, wifi_manager):
        """Update display with large, readable layout - FLICKER-FREE"""
        if not self.display:
            return
            
        current_time = time.time()
        if current_time - self.last_update < self.update_interval:
            return
        self.last_update = current_time
        
        # Check system resources periodically
        self._check_system_resources()
        
        # Get status
        status = vent_controller.get_status()
        
        if self.frame_buffer:
            # FRAME BUFFER MODE - NO FLASHING!
            self._clear_buffer()
            
            # OUT/IN labels (2x scale, 16px high)
            label_y = 10
            self._draw_text_to_buffer("OUT", 44, label_y, 2, st7789.WHITE)
            self._draw_text_to_buffer("IN", 172, label_y, 2, st7789.WHITE)
            
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
            self._draw_text_to_buffer(outdoor_text, outdoor_x, aqi_y, 4, outdoor_color)
            
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
            self._draw_text_to_buffer(indoor_text, indoor_x, aqi_y, 4, indoor_color)
            
            # Status indicators (2x scale) - bottom corners
            status_y = 110
            
            # SW state (bottom left)
            self._draw_text_to_buffer("SW:", 10, status_y, 2, st7789.WHITE)
            
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
                mode_text = status['mode']
                mode_color = st7789.WHITE
                
            self._draw_text_to_buffer(mode_text, 58, status_y, 2, mode_color)
            
            # V state (bottom right)
            vent_state = "ON" if status['enabled'] else "OFF"
            vent_color = st7789.GREEN if status['enabled'] else st7789.RED
            
            # Right align
            total_text = f"V:{vent_state}"
            total_width = len(total_text) * 16  # 2x scale = 16px per char
            v_x = 230 - total_width
            
            self._draw_text_to_buffer("V:", v_x, status_y, 2, st7789.WHITE)
            self._draw_text_to_buffer(vent_state, v_x + 32, status_y, 2, vent_color)
            
            # SINGLE HARDWARE UPDATE - NO FLASHING!
            self._flush_buffer()
            
        else:
            # FALLBACK MODE - direct drawing (will flash)
            self.clear_display()
            self._draw_scaled_text("OUT", 44, 10, 2, st7789.WHITE)
            # ... (rest of fallback implementation)
    
    def _get_aqi_color(self, aqi):
        """Get color based on AQI value - RGB565 format"""
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
    
    def _draw_scaled_text(self, text, x, y, scale, color):
        """FALLBACK: Draw text scaled up - will cause flashing"""
        if not self.display:
            return
            
        current_x = x
        for char in text:
            self._draw_scaled_char(char, current_x, y, scale, color)
            current_x += (8 * scale)
    
    def _draw_scaled_char(self, char, x, y, scale, color):
        """FALLBACK: Draw a single character scaled up - will cause flashing"""
        if not self.display or not FONT_AVAILABLE:
            return
        
        # Get character bitmap
        char_code = ord(char)
        if char_code < 32 or char_code > 126:
            char_code = 32
        
        # Font is 8x8 pixels, each character is 8 consecutive bytes in flat array
        char_start_index = (char_code - 32) * 8
        
        # Draw each pixel scaled up - each call causes flashing
        for row in range(8):
            byte_data = font8x8.FONT[char_start_index + row]
            for col in range(8):
                if byte_data & (1 << col):
                    for sy in range(scale):
                        for sx in range(scale):
                            pixel_x = x + (7 - col) * scale + sx
                            pixel_y = y + row * scale + sy
                            # Direct pixel draw - causes flashing
                            if (pixel_x >= 0 and pixel_x < self.display.width() and 
                                pixel_y >= 0 and pixel_y < self.display.height()):
                                self.display.pixel(pixel_x, pixel_y, color) 