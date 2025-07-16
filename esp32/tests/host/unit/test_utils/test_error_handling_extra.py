from utils import error_handling


def test_handle_hardware_error_pin(capsys):
    error_handling.handle_hardware_error(ValueError("pin invalid"), component="display")
    captured = capsys.readouterr()
    assert "Pin configuration error" in captured.out


def test_handle_hardware_error_i2c(capsys):
    error_handling.handle_hardware_error(RuntimeError("I2C bus"), component="sensor")
    captured = capsys.readouterr()
    assert "Communication error" in captured.out


def test_print_exception_context(capsys):
    try:
        raise KeyError("missing")
    except KeyError as e:
        error_handling.print_exception(e, context="unit")
    captured = capsys.readouterr()
    assert "unit - Error: KeyError" in captured.out
