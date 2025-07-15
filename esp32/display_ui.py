from machine import Pin, SPI
import time
import config

# Import display driver
try:
    import st7789py as st7789
    DISPLAY_AVAILABLE = True
except ImportError:
    print("Warning: st7789py display driver not found")
    DISPLAY_AVAILABLE = False

class DisplayInterface:
    def __init__(self):
        self.display = None
        self.last_update = 0
        self.update_interval = 1  # seconds
        
        if DISPLAY_AVAILABLE:
            try:
                # Initialize SPI for display
                spi = SPI(1, baudrate=40000000, polarity=0, phase=0,
                         sck=Pin(config.TFT_SCLK), mosi=Pin(config.TFT_MOSI))
                
                # Initialize display
                # Use 135x240 mode with rotation for 240x135 display
                self.display = st7789.ST7789(
                    spi,
                    config.DISPLAY_WIDTH,
                    config.DISPLAY_HEIGHT,
                    reset=Pin(config.TFT_RST, Pin.OUT),
                    dc=Pin(config.TFT_DC, Pin.OUT),
                    cs=Pin(config.TFT_CS, Pin.OUT),
                    rotation=3  # Rotate 270 degrees for landscape
                )
                
                # Note: st7789py doesn't have a separate init() method
                self.clear()
                print("Display initialized successfully")
            except Exception as e:
                print(f"Display initialization error: {e}")
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
            
        # Draw label - text() requires a font, so skip for now
        # TODO: Add font support
        # self.display.text(font, label, 10, y, st7789.WHITE)
        
        # Draw AQI value  
        # aqi_text = "N/A" if aqi < 0 else str(int(aqi))
        # self.display.text(font, aqi_text, 10, y + 15, st7789.WHITE)
        
        # Draw bar
        if aqi >= 0:
            bar_width = min(int(aqi * max_width / 500), max_width)
            bar_color = self.get_aqi_color(aqi)
            self.display.fill_rect(10, y + 30, bar_width, 10, bar_color)
            
            # Draw bar outline
            self.display.rect(10, y + 30, max_width, 10, st7789.WHITE)
    
    def draw_status(self, y, vent_controller):
        """Draw ventilation status"""
        if not self.display:
            return
            
        status = vent_controller.get_status()
        
        # Draw mode - text() requires a font, so using colored rectangles instead
        mode_color = st7789.GREEN if status['mode'] == 'PURPLEAIR' else st7789.YELLOW
        # Mode indicator rectangle
        self.display.fill_rect(10, y, 50, 10, mode_color)
        
        # Draw ventilation state
        vent_color = st7789.GREEN if status['enabled'] else st7789.RED
        # Ventilation status rectangle  
        self.display.fill_rect(70, y, 50, 10, vent_color)
        
        # TODO: Add font support for text display
        # self.display.text(font, f"Mode: {status['mode']}", 10, y, mode_color)
        # self.display.text(font, vent_text, 10, y + 15, vent_color)
        # self.display.text(font, reason_text, 10, y + 30, st7789.WHITE)
    
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
        # TODO: Add font support for title text
        # self.display.text(font, "Air Quality Monitor", 10, 5, st7789.WHITE)
        
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
            
        # Draw colored rectangle to indicate message type
        # Since we can't draw text without fonts, use color coding
        self.display.fill_rect(20, 60, 200, 20, color)
        # TODO: Add font support for message text
        # self.display.text(font, message, x, y, color)
    
    def show_error(self, error_msg):
        """Show error message"""
        self.show_message(error_msg, st7789.RED)