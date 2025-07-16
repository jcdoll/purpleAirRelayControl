# AQI color mapping utilities for ESP32 MicroPython
# Centralized AQI color logic used across display and visualization modules

# AQI color thresholds and RGB values
AQI_THRESHOLDS = [
    (50, "good"),
    (100, "moderate"),
    (150, "unhealthy_sensitive"),
    (200, "unhealthy"),
    (300, "very_unhealthy"),
    (float('inf'), "hazardous"),
]


def get_aqi_category(aqi_value):
    """
    Get AQI category name based on AQI value
    Args:
        aqi_value: Numeric AQI value
    Returns:
        String category name
    """
    if aqi_value < 0:
        return "invalid"

    for threshold, category in AQI_THRESHOLDS:
        if aqi_value <= threshold:
            return category

    return "hazardous"


def get_aqi_color_rgb(aqi_value):
    """
    Get RGB color tuple for AQI value
    Args:
        aqi_value: Numeric AQI value
    Returns:
        (r, g, b) tuple with values 0-255
    """
    category = get_aqi_category(aqi_value)

    color_map = {
        "good": (0, 255, 0),  # Green
        "moderate": (255, 255, 0),  # Yellow
        "unhealthy_sensitive": (255, 165, 0),  # Orange
        "unhealthy": (255, 0, 0),  # Red
        "very_unhealthy": (128, 0, 128),  # Purple
        "hazardous": (128, 0, 0),  # Maroon
        "invalid": (128, 128, 128),  # Gray
    }

    return color_map.get(category, (128, 128, 128))


def get_aqi_color_565(aqi_value):
    """
    Get 16-bit color value for ST7789 display (RGB565 format)
    Args:
        aqi_value: Numeric AQI value
    Returns:
        16-bit RGB565 color value
    """
    r, g, b = get_aqi_color_rgb(aqi_value)

    # Convert RGB888 to RGB565
    # R: 5 bits (shift right 3), G: 6 bits (shift right 2), B: 5 bits (shift right 3)
    r5 = (r >> 3) & 0x1F
    g6 = (g >> 2) & 0x3F
    b5 = (b >> 3) & 0x1F

    return (r5 << 11) | (g6 << 5) | b5


def get_aqi_color_name(aqi_value):
    """
    Get human-readable color name for AQI value
    Args:
        aqi_value: Numeric AQI value
    Returns:
        String color name
    """
    category = get_aqi_category(aqi_value)

    color_names = {
        "good": "green",
        "moderate": "yellow",
        "unhealthy_sensitive": "orange",
        "unhealthy": "red",
        "very_unhealthy": "purple",
        "hazardous": "maroon",
        "invalid": "gray",
    }

    return color_names.get(category, "gray")
