# Status display utilities for ESP32 MicroPython
# Shared status printing and formatting functions

import time


def print_sensor_status(
    outdoor_aqi, indoor_aqi, ventilation_status, reason="Status update"
):
    """
    Print formatted sensor status (extracted from main.py)
    Args:
        outdoor_aqi: Outdoor AQI value (-1 if unavailable)
        indoor_aqi: Indoor AQI value (-1 if unavailable)
        ventilation_status: Dict with 'enabled', 'mode', 'reason' keys
        reason: Reason for status update
    """
    current_time = time.time()

    print(f"[{int(current_time)}] {reason}")
    print(f"  AQI: Outdoor={outdoor_aqi:.1f}, Indoor={indoor_aqi:.1f}")
    print(
        f"  Mode: {ventilation_status['mode']} | Ventilation: {'ON' if ventilation_status['enabled'] else 'OFF'}"
    )
    print(f"  Reason: {ventilation_status['reason']}")


def print_sensor_countdown_timers(purple_air_client):
    """
    Print countdown timers for next sensor checks (extracted from main.py)
    Args:
        purple_air_client: PurpleAirClient instance with timing attributes
    """
    import config

    current_time = time.time()

    print("--- Sensor Check Timers ---")

    # Outdoor sensor timers
    time_until_outdoor_local = max(
        0,
        config.LOCAL_POLL_INTERVAL
        - (current_time - purple_air_client.last_outdoor_local_poll),
    )
    time_until_outdoor_api = max(
        0,
        config.API_POLL_INTERVAL
        - (current_time - purple_air_client.last_outdoor_api_poll),
    )

    print(f"  Outdoor - Time until next local check: {int(time_until_outdoor_local)}s")
    print(f"  Outdoor - Time until next API check: {int(time_until_outdoor_api)}s")

    # Indoor sensor timers (if configured)
    if config.INDOOR_SENSOR_IDS or purple_air_client.local_indoor_ips:
        time_until_indoor_local = max(
            0,
            config.LOCAL_POLL_INTERVAL
            - (current_time - purple_air_client.last_indoor_local_poll),
        )
        time_until_indoor_api = max(
            0,
            config.API_POLL_INTERVAL
            - (current_time - purple_air_client.last_indoor_api_poll),
        )

        print(
            f"  Indoor - Time until next local check: {int(time_until_indoor_local)}s"
        )
        print(f"  Indoor - Time until next API check: {int(time_until_indoor_api)}s")


def print_system_info(wifi_manager=None, memory_info=True):
    """
    Print system status information
    Args:
        wifi_manager: WiFiManager instance (optional)
        memory_info: Whether to include memory usage
    """
    print("--- System Status ---")

    if wifi_manager and wifi_manager.is_connected():
        print(f"  WiFi: Connected")
        print(f"    IP: {wifi_manager.get_ip()}")
        print(f"    Signal: {wifi_manager.get_rssi()} dBm")
    else:
        print(f"  WiFi: Disconnected")

    if memory_info:
        try:
            import gc

            gc.collect()
            free_mem = gc.mem_free()
            used_mem = gc.mem_alloc()
            print(f"  Memory: Free={free_mem/1024:.1f}KB, Used={used_mem/1024:.1f}KB")
        except Exception:
            print(f"  Memory: Information unavailable")


def print_sensor_config(purple_air_client):
    """
    Print sensor configuration summary (extracted from main.py)
    Args:
        purple_air_client: PurpleAirClient instance
    """
    import config

    print("--- Sensor Configuration ---")
    print(f"  Outdoor sensors:")
    print(f"    Local IPs: {purple_air_client.local_outdoor_ips}")
    print(f"    API IDs: {config.OUTDOOR_SENSOR_IDS}")
    print(f"  Indoor sensors:")
    print(f"    Local IPs: {purple_air_client.local_indoor_ips}")
    print(f"    API IDs: {config.INDOOR_SENSOR_IDS}")

    # Check if API key is properly configured
    api_key_valid = (
        config.PURPLE_AIR_API_KEY
        and config.PURPLE_AIR_API_KEY.strip() != ""
        and len(config.PURPLE_AIR_API_KEY) > 10
    )
    print(f"  API Key: {'Configured' if api_key_valid else 'Not configured'}")


def format_aqi_value(aqi_value, decimal_places=1):
    """
    Format AQI value for display
    Args:
        aqi_value: Numeric AQI value
        decimal_places: Number of decimal places
    Returns:
        Formatted string
    """
    if aqi_value < 0:
        return "---"
    return f"{aqi_value:.{decimal_places}f}"


def format_duration(seconds):
    """
    Format duration in seconds to human readable format
    Args:
        seconds: Duration in seconds
    Returns:
        Formatted string (e.g., "2m 30s", "1h 15m")
    """
    if seconds < 60:
        return f"{int(seconds)}s"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        remaining_seconds = int(seconds % 60)
        return f"{minutes}m {remaining_seconds}s"
    else:
        hours = int(seconds // 3600)
        remaining_minutes = int((seconds % 3600) // 60)
        return f"{hours}h {remaining_minutes}m"


def print_startup_banner():
    """Print application startup banner"""
    print("=" * 40)
    print("PurpleAir Relay Control - ESP32 MicroPython")
    print("=" * 40)


def print_separator(char="-", length=40):
    """Print a separator line"""
    print(char * length)
