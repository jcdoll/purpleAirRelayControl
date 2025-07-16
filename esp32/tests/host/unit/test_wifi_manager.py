import importlib

def test_wifi_connect_cycle():
    wifi_manager = importlib.import_module("wifi_manager")
    WM = wifi_manager.WiFiManager()

    # Initially disconnected
    assert WM.is_connected() is False

    assert WM.connect() is True
    assert WM.is_connected() is True
    assert WM.get_ip() == "192.168.0.2"
    assert WM.get_rssi() == -50

    WM.disconnect()
    assert WM.is_connected() is False

    # Reconnect path
    assert WM.reconnect() is True
    assert WM.is_connected() is True 