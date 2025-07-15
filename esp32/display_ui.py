from machine import Pin, SPI
import time
import config

# Import display driver and font
try:
    import st7789py as st7789
    DISPLAY_AVAILABLE = True
except ImportError:
    print("Warning: st7789py display driver not found")
    DISPLAY_AVAILABLE = False

# Import font (character mirroring fix applied directly to vga1_8x8)
try:
    import lib.vga1_8x8 as font8x8
    FONT_AVAILABLE = True
    print("Using corrected font for proper character display")
except ImportError:
    print("Warning: vga1_8x8 font not found")
    FONT_AVAILABLE = False

class DisplayInterface:
    def __init__(self):
        self.display = None
        self.last_update = 0
        self.update_interval = 1  # seconds
        
        if DISPLAY_AVAILABLE and FONT_AVAILABLE:
            try:
                print("Initializing DisplayInterface...")
                
                # Initialize SPI for display with lower baudrate for stability
                print(f"Initializing SPI: SCK={config.TFT_SCLK}, MOSI={config.TFT_MOSI}")
                spi = SPI(1, baudrate=20000000, polarity=0, phase=0,
                         sck=Pin(config.TFT_SCLK), mosi=Pin(config.TFT_MOSI))
                
                # Initialize display with correct dimensions and rotation
                # Rotation 1 is landscape with buttons on left side (CONFIRMED WORKING)
                print(f"Initializing display: 135x240, rotation=1 (buttons on left)")
                print(f"  RST={config.TFT_RST}, DC={config.TFT_DC}, CS={config.TFT_CS}")
                self.display = st7789.ST7789(
                    spi,
                    135,  # width (correct for ESP32-S3 Reverse TFT Feather)
                    240,  # height (correct for ESP32-S3 Reverse TFT Feather)
                    reset=Pin(config.TFT_RST, Pin.OUT),
                    dc=Pin(config.TFT_DC, Pin.OUT),
                    cs=Pin(config.TFT_CS, Pin.OUT),
                    rotation=1  # Landscape with buttons on left side (TESTED AND WORKING)
                )
                
                print("Clearing display...")
                self.clear()
                
                # Test the display with a simple pattern
                print("Testing display with color pattern...")
                self.display.fill_rect(0, 0, 60, 30, st7789.RED)
                self.display.fill_rect(60, 0, 60, 30, st7789.GREEN)
                self.display.fill_rect(120, 0, 60, 30, st7789.BLUE)
                self.display.fill_rect(180, 0, 60, 30, st7789.WHITE)
                time.sleep(1)
                self.clear()
                
                print("Display initialized successfully")
            except Exception as e:
                print(f"Display initialization error: {e}")
                self.display = None
        else:
            print("Display not available (missing hardware or font support)")
            self.display = None
    
    def clear(self):
        """Clear the display"""
        if self.display:
            self.display.fill(st7789.BLACK)
    
    def get_aqi_color(self, aqi):
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
    
    def draw_aqi_bar(self, y, label, aqi, max_width=200):
        """Draw AQI bar with label"""
        if not self.display:
            return
            
        # Draw label
        if FONT_AVAILABLE:
            self.display.text(font8x8, label, 10, y, st7789.WHITE)
        
        # Draw AQI value  
        aqi_text = "N/A" if aqi < 0 else str(int(aqi))
        if FONT_AVAILABLE:
            self.display.text(font8x8, aqi_text, 10, y + 12, st7789.WHITE)
        
        # Draw bar
        if aqi >= 0:
            bar_width = min(int(aqi * max_width / 500), max_width)
            bar_color = self.get_aqi_color(aqi)
            self.display.fill_rect(10, y + 25, bar_width, 10, bar_color)
            
            # Draw bar outline
            self.display.rect(10, y + 25, max_width, 10, st7789.WHITE)
    
    def draw_status(self, y, vent_controller):
        """Draw ventilation status"""
        if not self.display:
            return
            
        status = vent_controller.get_status()
        
        # Draw mode
        mode_color = st7789.GREEN if status['mode'] == 'PURPLEAIR' else st7789.YELLOW
        if FONT_AVAILABLE:
            self.display.text(font8x8, f"Mode: {status['mode']}", 10, y, mode_color)
        else:
            # Fallback: Mode indicator rectangle
            self.display.fill_rect(10, y, 50, 10, mode_color)
        
        # Draw ventilation state
        vent_color = st7789.GREEN if status['enabled'] else st7789.RED
        vent_text = "Vent: ON" if status['enabled'] else "Vent: OFF"
        if FONT_AVAILABLE:
            self.display.text(font8x8, vent_text, 10, y + 12, vent_color)
        else:
            # Fallback: Ventilation status rectangle  
            self.display.fill_rect(70, y, 50, 10, vent_color)
        
        # Draw reason (truncate if too long)
        reason_text = status['reason'][:28]  # Max ~28 chars at 8 pixels wide
        if FONT_AVAILABLE:
            self.display.text(font8x8, reason_text, 10, y + 24, st7789.WHITE)
    
    def draw_network_status(self, wifi_manager):
        """Draw network status in corner"""
        if not self.display:
            return
            
        if wifi_manager.is_connected():
            # Draw WiFi status indicator (green rectangle)
            self.display.fill_rect(220, 5, 15, 10, st7789.GREEN)
        else:
            # Draw WiFi disconnected indicator (red rectangle)
            self.display.fill_rect(220, 5, 15, 10, st7789.RED)
    
    def update(self, outdoor_aqi, indoor_aqi, vent_controller, wifi_manager):
        """Update the entire display"""
        if not self.display:
            return
            
        current_time = time.time()
        if current_time - self.last_update < self.update_interval:
            return
            
        self.last_update = current_time
        
        # Clear display
        self.clear()
        
        # Draw title bar (swap dimensions for rotated display)
        self.display.fill_rect(0, 0, 240, 20, st7789.BLUE)
        if FONT_AVAILABLE:
            self.display.text(font8x8, "Air Quality Monitor", 10, 6, st7789.WHITE)
        
        # Draw network status
        self.draw_network_status(wifi_manager)
        
        # Draw outdoor AQI
        self.draw_aqi_bar(25, "Outdoor", outdoor_aqi, 180)
        
        # Draw indoor AQI if available
        if indoor_aqi >= 0:
            self.draw_aqi_bar(70, "Indoor", indoor_aqi, 180)
            status_y = 115
        else:
            status_y = 70
        
        # Draw ventilation status
        self.draw_status(status_y, vent_controller)
    
    def show_message(self, message, color=None):
        """Show a simple message on the display"""
        if not self.display:
            return
            
        self.clear()
        if color is None:
            color = st7789.WHITE
            
        if FONT_AVAILABLE:
            # Center the message
            msg_width = len(message) * 8
            x = (240 - msg_width) // 2
            y = 60
            self.display.text(font8x8, message, x, y, color)
        else:
            # Fallback: Draw colored rectangle to indicate message type
            self.display.fill_rect(20, 60, 200, 20, color)
    
    def show_error(self, error_msg):
        """Show error message"""
        self.show_message(error_msg, st7789.RED)