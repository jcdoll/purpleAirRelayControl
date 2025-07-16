
from utils import aqi_colors

# ---------------------------------------------------------------------------
# Helper to convert RGB888 to RGB565 for expectation comparison
# ---------------------------------------------------------------------------


def rgb888_to_565(r, g, b):
    r5 = (r >> 3) & 0x1F
    g6 = (g >> 2) & 0x3F
    b5 = (b >> 3) & 0x1F
    return (r5 << 11) | (g6 << 5) | b5


def test_category_boundaries():
    # Exact boundary checks
    assert aqi_colors.get_aqi_category(-1) == "invalid"
    assert aqi_colors.get_aqi_category(0) == "good"
    assert aqi_colors.get_aqi_category(50) == "good"
    assert aqi_colors.get_aqi_category(51) == "moderate"
    assert aqi_colors.get_aqi_category(100) == "moderate"
    assert aqi_colors.get_aqi_category(101) == "unhealthy_sensitive"
    assert aqi_colors.get_aqi_category(150) == "unhealthy_sensitive"
    assert aqi_colors.get_aqi_category(151) == "unhealthy"
    assert aqi_colors.get_aqi_category(200) == "unhealthy"
    assert aqi_colors.get_aqi_category(201) == "very_unhealthy"
    assert aqi_colors.get_aqi_category(300) == "very_unhealthy"
    assert aqi_colors.get_aqi_category(301) == "hazardous"


def test_rgb_and_565_consistency():
    # Iterate over representative AQI values across categories
    for aqi in [0, 75, 125, 175, 250, 400]:
        rgb = aqi_colors.get_aqi_color_rgb(aqi)
        rgb565_expected = rgb888_to_565(*rgb)
        assert aqi_colors.get_aqi_color_565(aqi) == rgb565_expected


def test_color_names():
    # Spot-check a couple of values
    assert aqi_colors.get_aqi_color_name(25) == "green"
    assert aqi_colors.get_aqi_color_name(125) == "orange"
