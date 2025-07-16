from utils import status_display


def test_format_aqi_value():
    assert status_display.format_aqi_value(42.123, 1) == "42.1"
    assert status_display.format_aqi_value(-1) == "---"


def test_format_duration():
    assert status_display.format_duration(45) == "45s"
    assert status_display.format_duration(125) == "2m 5s"
    assert status_display.format_duration(3720) == "1h 2m"
