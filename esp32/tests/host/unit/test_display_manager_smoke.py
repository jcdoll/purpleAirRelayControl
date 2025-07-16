import importlib

# Dummy VentilationController replacement for status
class _DummyVent:
    def __init__(self):
        self._status = {'enabled': False, 'mode': 'PURPLEAIR', 'reason': 'test'}
    def get_status(self):
        return self._status

class _DummyWiFi:
    def is_connected(self):
        return True
    def get_ip(self):
        return "192.168.0.2"
    def get_rssi(self):
        return -40


def test_display_manager_init_and_update():
    dm = importlib.import_module('display_manager').DisplayManager()

    vent = _DummyVent()
    wifi = _DummyWiFi()

    # Call update_display once; should not raise
    dm.update_display(outdoor_aqi=50, indoor_aqi=25, vent_controller=vent, wifi_manager=wifi)

    # Smoke: show_message should run
    dm.show_message("Test") 