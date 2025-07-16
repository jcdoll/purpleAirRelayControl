# Display Manager - handles TFT display output
# Extracted from ui_manager.py for better separation of concerns
# Uses software frame buffer to eliminate display flashing

from machine import Pin, SPI
import time
import gc
import config
from utils.error_handling import print_exception, handle_hardware_error
from utils.aqi_colors import get_aqi_color_st7789

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

class DisplayManager:
    def __init__(self):
        self.display = None
        self.tft_power = None
        self.backlight = None
        self.last_update = 0
        self.last_memory_check = 0
        self.update_interval = 1  # seconds
        self.memory_check_interval = 30  # seconds
        
        # Frame buffer for flicker-free updates
        self.frame_buffer = None
        self.buffer_width = 0
        self.buffer_height = 0
        
        if DISPLAY_AVAILABLE and FONT_AVAILABLE:
            self._init_display()
        
        # Initial memory check
        self._check_system_resources()
        
        print("Display Manager: Initialized with software frame buffer")
    
    def _init_display(self):
        """Initialize ST7789 TFT display with frame buffer"""
        try:
            # TFT I2C Power control (required for display)
            if hasattr(config, 'TFT_I2C_POWER'):
                self.tft_power = Pin(config.TFT_I2C_POWER, Pin.OUT)
                self.tft_power.on()
            
            # Backlight control (required for display visibility)
            if hasattr(config, 'TFT_BACKLIGHT'):
                self.backlight = Pin(config.TFT_BACKLIGHT, Pin.OUT)
                self.backlight.on()
            
            # Wait for power to stabilize
            time.sleep(0.2)
            
            # SPI and Display initialization
            spi = SPI(1, baudrate=20000000, polarity=0, phase=0,
                     sck=Pin(config.TFT_SCLK), mosi=Pin(config.TFT_MOSI))
            
            self.display = st7789.ST7789(
                spi, config.TFT_WIDTH, config.TFT_HEIGHT,
                reset=Pin(config.TFT_RST, Pin.OUT),
                dc=Pin(config.TFT_DC, Pin.OUT),
                cs=Pin(config.TFT_CS, Pin.OUT),
                backlight=None,  # We handle backlight separately
                rotation=config.TFT_ROTATION
            )
            
            # Try to create frame buffer
            try:
                # Use config values for display dimensions after rotation
                self.buffer_width = config.TFT_HEIGHT if config.TFT_ROTATION == 1 else config.TFT_WIDTH
                self.buffer_height = config.TFT_WIDTH if config.TFT_ROTATION == 1 else config.TFT_HEIGHT
                buffer_size = self.buffer_width * self.buffer_height * 2  # 2 bytes per pixel
                
                # Only create buffer if we have enough memory
                gc.collect()
                if gc.mem_free() > buffer_size + 50000:  # Leave 50KB safety margin
                    self.frame_buffer = bytearray(buffer_size)
                    print(f"Display Manager: Frame buffer created ({buffer_size} bytes)")
                else:
                    print(f"Display Manager: Insufficient memory for frame buffer, using direct mode")
                    self.frame_buffer = None
                    
            except Exception as e:
                print_exception(e, "Frame buffer creation")
                self.frame_buffer = None
            
            # Clear display
            self.display.fill(st7789.BLACK)
            self.show_message("Display Ready")
            
            print("Display Manager: ST7789 initialized")
            
        except Exception as e:
            handle_hardware_error(e, "ST7789 display")
            self.display = None
    
    def _check_system_resources(self):
        """Check memory and system resources periodically"""
        current_time = time.time()
        if current_time - self.last_memory_check < self.memory_check_interval:
            return
        
        self.last_memory_check = current_time
        
        try:
            gc.collect()
            free_mem = gc.mem_free()
            if free_mem < 20000:  # Less than 20KB free
                print(f"WARNING: Low memory: {free_mem/1024:.1f}KB free")
        except Exception:
            pass
    
    def show_message(self, message, color=None):
        """
        Show a simple text message on display
        Args:
            message: Text to display
            color: Optional color (defaults to white)
        """
        if not self.display:
            return
        
        try:
            if color is None:
                color = st7789.WHITE
            
            self.display.fill(st7789.BLACK)
            
            # Simple centered text
            x = 10
            y = self.buffer_height // 2 - 8
            self.display.text(font8x8, message, x, y, color)
            
        except Exception as e:
            handle_hardware_error(e, "display message")
    
    def show_error(self, message):
        """Show error message in red"""
        self.show_message(message, st7789.RED if DISPLAY_AVAILABLE else None)
    
    def update_display(self, outdoor_aqi, indoor_aqi, vent_controller, wifi_manager):
        """
        Update display with large, readable layout - FLICKER-FREE
        Args:
            outdoor_aqi: Outdoor AQI value
            indoor_aqi: Indoor AQI value  
            vent_controller: VentilationController instance
            wifi_manager: WiFiManager instance
        """
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
                outdoor_color = get_aqi_color_st7789(outdoor_aqi)
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
                indoor_color = get_aqi_color_st7789(indoor_aqi)
            else:
                indoor_text = "---"
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
            
            # Update display from buffer - SINGLE OPERATION, NO FLASHING
            self._flush_buffer()
            
        else:
            # FALLBACK: Direct mode (will cause flashing but still functional)
            self._update_display_direct(outdoor_aqi, indoor_aqi, status)
    
    def _clear_buffer(self):
        """Clear the frame buffer to black"""
        if self.frame_buffer:
            # Fill with black (0x0000 in RGB565)
            for i in range(0, len(self.frame_buffer), 2):
                self.frame_buffer[i] = 0
                self.frame_buffer[i + 1] = 0
    
    def _draw_text_to_buffer(self, text, x, y, scale, color):
        """Draw text to frame buffer (flicker-free)"""
        if not self.frame_buffer or not FONT_AVAILABLE:
            return
        
        for i, char in enumerate(text):
            char_x = x + (i * 8 * scale)
            self._draw_char_to_buffer(char, char_x, y, scale, color)
    
    def _draw_char_to_buffer(self, char, x, y, scale, color):
        """Draw a single character to frame buffer"""
        if not self.frame_buffer or not FONT_AVAILABLE:
            return
        
        # Get character bitmap
        char_code = ord(char)
        if char_code < 32 or char_code > 126:
            char_code = 32
        
        # Font is 8x8 pixels, each character is 8 consecutive bytes
        char_start_index = (char_code - 32) * 8
        
        # Convert color to RGB565 bytes
        color_high = (color >> 8) & 0xFF
        color_low = color & 0xFF
        
        # Draw each pixel to buffer
        for row in range(8):
            byte_data = font8x8.FONT[char_start_index + row]
            for col in range(8):
                if byte_data & (1 << col):
                    for sy in range(scale):
                        for sx in range(scale):
                            pixel_x = x + (7 - col) * scale + sx
                            pixel_y = y + row * scale + sy
                            
                            if (pixel_x >= 0 and pixel_x < self.buffer_width and 
                                pixel_y >= 0 and pixel_y < self.buffer_height):
                                # Calculate buffer index (2 bytes per pixel)
                                buffer_index = ((pixel_y * self.buffer_width) + pixel_x) * 2
                                if buffer_index + 1 < len(self.frame_buffer):
                                    self.frame_buffer[buffer_index] = color_high
                                    self.frame_buffer[buffer_index + 1] = color_low
    
    def _flush_buffer(self):
        """Flush frame buffer to display - SINGLE OPERATION"""
        if not self.frame_buffer or not self.display:
            return
        
        try:
            # This is the magic - single blit operation eliminates flashing
            self.display.blit_buffer(self.frame_buffer, 0, 0, self.buffer_width, self.buffer_height)
        except Exception as e:
            print_exception(e, "Buffer flush")
    
    def _update_display_direct(self, outdoor_aqi, indoor_aqi, status):
        """FALLBACK: Direct display update (will cause flashing)"""
        try:
            self.display.fill(st7789.BLACK)
            
            # Simple layout for fallback mode
            self.display.text(font8x8, "OUT", 20, 10, st7789.WHITE)
            self.display.text(font8x8, "IN", 120, 10, st7789.WHITE)
            
            # AQI values
            outdoor_text = str(int(outdoor_aqi)) if outdoor_aqi >= 0 else "---"
            indoor_text = str(int(indoor_aqi)) if indoor_aqi >= 0 else "---"
            
            outdoor_color = get_aqi_color_st7789(outdoor_aqi) if outdoor_aqi >= 0 else st7789.GRAY
            indoor_color = get_aqi_color_st7789(indoor_aqi) if indoor_aqi >= 0 else st7789.GRAY
            
            self.display.text(font8x8, outdoor_text, 20, 40, outdoor_color)
            self.display.text(font8x8, indoor_text, 120, 40, indoor_color)
            
            # Status
            mode_text = f"Mode: {status['mode']}"
            vent_text = "ON" if status['enabled'] else "OFF"
            vent_color = st7789.GREEN if status['enabled'] else st7789.RED
            
            self.display.text(font8x8, mode_text, 5, 100, st7789.WHITE)
            self.display.text(font8x8, vent_text, 120, 100, vent_color)
            
        except Exception as e:
            handle_hardware_error(e, "direct display update")
    
    def is_available(self):
        """Check if display is available and initialized"""
        return self.display is not None
    
    def cleanup(self):
        """Cleanup display resources"""
        if self.display:
            try:
                self.display.fill(st7789.BLACK)
            except Exception as e:
                print_exception(e, "Display cleanup") 