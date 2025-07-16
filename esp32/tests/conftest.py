import pathlib
import sys
import types
import pytest

# Add esp32 directory to PYTHONPATH so that `import config`, `import utils` works
ESP32_PATH = pathlib.Path(__file__).resolve().parents[1]
if str(ESP32_PATH) not in sys.path:
    sys.path.insert(0, str(ESP32_PATH))

# ---------------------------------------------------------------------------
# Machine module mock (basic Pin implementation sufficient for unit tests)
# ---------------------------------------------------------------------------
class _MockPin:
    OUT = 0
    IN = 1
    PULL_UP = 2
    PULL_DOWN = 3

    IRQ_FALLING = 4
    IRQ_RISING = 8

    def __init__(self, pin_id, mode=None, pull=None):
        self.pin_id = pin_id
        self._value = 0
        self.irq_trigger = None
        self.irq_handler = None

    # Value getter/setter to mimic MicroPython Pin API
    def value(self, v=None):
        if v is None:
            return self._value
        self._value = 1 if v else 0

    # Dummy irq registration
    def irq(self, trigger=None, handler=None):
        self.irq_trigger = trigger
        self.irq_handler = handler

class _MockSPI:
    def __init__(self, *args, **kwargs):
        pass

# Build mock machine module
machine_mock = types.ModuleType("machine")
setattr(machine_mock, "Pin", _MockPin)
setattr(machine_mock, "SPI", _MockSPI)

# Register immediately so imports during test-module import succeed
sys.modules["machine"] = machine_mock

# ---------------------------------------------------------------------------
# Time module extensions (ticks_ms, ticks_diff, sleep_ms) for CPython
# ---------------------------------------------------------------------------
import time as _real_time

def _ticks_ms():
    return int(_real_time.time() * 1000)

def _ticks_diff(new, old):
    return new - old

def _sleep_ms(ms):
    _real_time.sleep(ms / 1000.0)

# Inject into real time module if not present
for name, fn in {"ticks_ms": _ticks_ms, "ticks_diff": _ticks_diff, "sleep_ms": _sleep_ms}.items():
    if not hasattr(_real_time, name):
        setattr(_real_time, name, fn)

# ---------------------------------------------------------------------------
# Auto-applied fixture: patch sys.modules for every test
# ---------------------------------------------------------------------------
@pytest.fixture(autouse=True)
def _patch_machine_module(monkeypatch):
    monkeypatch.setitem(sys.modules, "machine", machine_mock)
    yield 

# ---------------------------------------------------------------------------
# Provide stub for sys.print_exception in CPython
# ---------------------------------------------------------------------------
import traceback as _traceback

if not hasattr(sys, "print_exception"):
    def _print_exception(exc, file=None):  # type: ignore
        _traceback.print_exception(type(exc), exc, exc.__traceback__, file=file or sys.stderr)
    sys.print_exception = _print_exception  # type: ignore 