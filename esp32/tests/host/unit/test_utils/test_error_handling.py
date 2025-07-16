from utils import error_handling


def _good_function(x, y):
    return x + y


def _bad_function(*args, **kwargs):
    raise ValueError("Intentional failure")


def test_safe_execute_success():
    assert error_handling.safe_execute(_good_function, 2, 3) == 5


def test_safe_execute_error_return_default(capsys):
    default = 42
    result = error_handling.safe_execute(_bad_function, context="test", default_return=default)
    captured = capsys.readouterr()
    assert result == default
    # Ensure our standardized error prefix appears in output
    assert "Error: ValueError" in captured.out


def test_handle_network_error_timeout(capsys):
    error_handling.handle_network_error(ValueError("timeout occurred"), operation="fetch")
    captured = capsys.readouterr()
    assert "timeout" in captured.out.lower()
