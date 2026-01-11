import importlib

# Ensure modules are reloaded with mocks in place
ventilation = importlib.import_module("ventilation")


def test_default_state_from_config():
    controller = ventilation.VentilationController()
    status = controller.get_status()
    assert status["enabled"] == controller.ventilation_enabled


def test_manual_off_on_cycle():
    controller = ventilation.VentilationController()

    # Simulate D1 button press to cycle modes
    # Starting mode is PURPLEAIR

    controller.button_flags[1] = True  # PURPLEAIR -> OFF
    controller.update(outdoor_aqi=0)
    assert controller.switch_mode == "OFF"

    controller.button_flags[1] = True  # OFF -> ON
    controller.update(outdoor_aqi=0)
    assert controller.switch_mode == "ON"
    assert controller.ventilation_enabled is True

    controller.button_flags[1] = True  # ON -> PURPLEAIR
    controller.update(outdoor_aqi=0)
    assert controller.switch_mode == "PURPLEAIR"


def test_purpleair_control_logic(monkeypatch):
    # Mock time.time() to simulate time passing and bypass timing protection
    # Start at 200s so first auto change is allowed (last_auto_change starts at 0)
    import time

    fake_time = [200]

    def mock_time():
        return fake_time[0]

    monkeypatch.setattr(time, "time", mock_time)

    controller = ventilation.VentilationController()
    # Ensure mode is PURPLEAIR
    controller.switch_mode = "PURPLEAIR"

    # AQI good -> should enable
    controller.update(outdoor_aqi=50)
    assert controller.ventilation_enabled is True

    # Advance time past RELAY_MIN_AUTO_SWITCH_INTERVAL (120s)
    fake_time[0] = 400

    # AQI too high -> should disable
    controller.update(outdoor_aqi=150)
    assert controller.ventilation_enabled is False
