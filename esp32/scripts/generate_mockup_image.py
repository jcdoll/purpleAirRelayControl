# Generate PNG image mockup of the display layout
# Creates actual image file for review without needing ESP32 hardware

from PIL import Image, ImageDraw, ImageFont
import sys
import os

# Add the esp32 directory to path so we can import the font
sys.path.append('../')
try:
    import lib.vga1_8x8 as font8x8
except ImportError:
    print("Error: Cannot import font. Run this from the project root or ensure esp32/lib/vga1_8x8.py exists.")
    sys.exit(1)

class ImageMockup:
    def __init__(self, width=240, height=135):
        self.width = width
        self.height = height
        self.img = Image.new('RGB', (width, height), color='black')
        self.draw = ImageDraw.Draw(self.img)
        
        # Colors (RGB values matching ST7789 colors)
        self.colors = {
            'white': (255, 255, 255),
            'black': (0, 0, 0),
            'red': (255, 0, 0),
            'green': (0, 255, 0),
            'yellow': (255, 255, 0),
            'orange': (255, 165, 0),
            'purple': (128, 0, 128),
            'maroon': (128, 0, 0),
            'gray': (128, 128, 128),
        }
    
    def _get_aqi_color(self, aqi):
        """Get color name based on AQI value"""
        if aqi <= 50:
            return 'green'      # Good
        elif aqi <= 100:
            return 'yellow'     # Moderate
        elif aqi <= 150:
            return 'orange'     # Unhealthy for sensitive
        elif aqi <= 200:
            return 'red'        # Unhealthy
        elif aqi <= 300:
            return 'purple'     # Very unhealthy
        else:
            return 'maroon'     # Hazardous
    
    def _draw_scaled_char(self, char, x, y, scale, color_name):
        """Draw a character scaled up by scale factor"""
        if ord(char) < font8x8.FIRST or ord(char) >= font8x8.LAST:
            return x + (8 * scale)
        
        color = self.colors[color_name]
        
        # Get character data from font
        char_index = ord(char) - font8x8.FIRST
        char_data_start = char_index * 8
        
        for row in range(8):
            byte_data = font8x8.FONT[char_data_start + row]
            for col in range(8):
                if byte_data & (1 << col):  # Pixel is on
                    # Draw scaled pixel as filled rectangle
                    pixel_x = x + (col * scale)
                    pixel_y = y + (row * scale)
                    self.draw.rectangle([
                        pixel_x, pixel_y, 
                        pixel_x + scale - 1, pixel_y + scale - 1
                    ], fill=color)
        
        return x + (8 * scale)
    
    def _draw_scaled_text(self, text, x, y, scale, color_name):
        """Draw text scaled up by scale factor"""
        current_x = x
        for char in text:
            current_x = self._draw_scaled_char(char, current_x, y, scale, color_name)
        return current_x
    
    def generate_layout(self, outdoor_aqi=140, indoor_aqi=36, sw_mode="AUTO", vent_state="ON"):
        """Generate the mockup layout"""
        # Clear background
        self.img = Image.new('RGB', (self.width, self.height), color='black')
        self.draw = ImageDraw.Draw(self.img)
        
        # OUT/IN labels (2x scale, 16px high)
        label_y = 10
        out_label_x = 60   # Left side for OUT
        in_label_x = 180   # Right side for IN
        
        self._draw_scaled_text("OUT", out_label_x, label_y, 2, 'white')
        self._draw_scaled_text("IN", in_label_x, label_y, 2, 'white')
        
        # Large AQI numbers (4x scale, 32px high)
        aqi_y = 35
        
        # Outdoor AQI (left side)
        outdoor_text = str(int(outdoor_aqi)) if outdoor_aqi >= 0 else "---"
        outdoor_color = self._get_aqi_color(outdoor_aqi) if outdoor_aqi >= 0 else 'white'
        
        # Calculate centering for 3-digit numbers (each char is 32px wide at 4x scale)
        outdoor_width = len(outdoor_text) * 32
        outdoor_x = 60 - (outdoor_width // 2)  # Center around x=60
        
        self._draw_scaled_text(outdoor_text, outdoor_x, aqi_y, 4, outdoor_color)
        
        # Indoor AQI (right side)
        if indoor_aqi >= 0:
            indoor_text = str(int(indoor_aqi))
            indoor_color = self._get_aqi_color(indoor_aqi)
        else:
            indoor_text = "N/A"
            indoor_color = 'gray'
        
        indoor_width = len(indoor_text) * 32
        indoor_x = 180 - (indoor_width // 2)  # Center around x=180
        
        self._draw_scaled_text(indoor_text, indoor_x, aqi_y, 4, indoor_color)
        
        # Status indicators (2x scale, 16px high) - bottom corners
        status_y = 110
        
        # SW state (bottom left)
        sw_text = f"SW:{sw_mode}"
        sw_color = 'green' if sw_mode == "AUTO" else 'yellow'
        self._draw_scaled_text(sw_text, 10, status_y, 2, sw_color)
        
        # VENT state (bottom right)
        vent_text = f"VENT:{vent_state}"
        vent_color = 'green' if vent_state == "ON" else 'red'
        # Right align - calculate x position
        vent_width = len(vent_text) * 16  # 2x scale = 16px per char
        vent_x = 230 - vent_width
        self._draw_scaled_text(vent_text, vent_x, status_y, 2, vent_color)
    
    def save_image(self, filename):
        """Save the mockup as PNG file"""
        self.img.save(filename)
        print(f"Mockup saved as: {filename}")

def generate_mockups():
    """Generate multiple mockup scenarios"""
    scenarios = [
        (140, 36, "AUTO", "ON", "unhealthy_out_good_in_auto_on"),
        (85, -1, "AUTO", "OFF", "moderate_out_no_in_auto_off_with_na"),
        (250, 180, "OFF", "OFF", "very_unhealthy_both_manual_off"),
        (35, 28, "ON", "ON", "good_both_manual_on"),
    ]
    
    for outdoor, indoor, sw, vent, filename_suffix in scenarios:
        mockup = ImageMockup()
        mockup.generate_layout(outdoor, indoor, sw, vent)
        mockup.save_image(f"display_mockup_{filename_suffix}.png")

if __name__ == "__main__":
    generate_mockups() 