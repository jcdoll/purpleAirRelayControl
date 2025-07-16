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


def test_purpleair_control_logic():
    controller = ventilation.VentilationController()
    # Ensure mode is PURPLEAIR
    controller.switch_mode = "PURPLEAIR"

    # AQI good -> should enable
    controller.update(outdoor_aqi=50)
    assert controller.ventilation_enabled is True

    # AQI too high -> should disable
    controller.update(outdoor_aqi=150)
    assert controller.ventilation_enabled is False
