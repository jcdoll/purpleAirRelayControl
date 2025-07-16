import importlib

ventilation = importlib.import_module('ventilation')
purple_air = importlib.import_module('purple_air')

VentilationController = ventilation.VentilationController


def test_end_to_end_decision():
    controller = VentilationController()
    controller.switch_mode = 'PURPLEAIR'

    # High AQI first — ventilation should stay OFF
    controller.update(outdoor_aqi=150)
    assert controller.ventilation_enabled is False

    # Good AQI — ventilation turns ON
    controller.update(outdoor_aqi=50)
    assert controller.ventilation_enabled is True
