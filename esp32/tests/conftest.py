import json as _std_json
import pathlib
import sys
import time as _real_time
import traceback as _traceback
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


def _ticks_ms():
    return int(_real_time.time() * 1000)


def _ticks_diff(new, old):
    return new - old


def _sleep_ms(ms):
    _real_time.sleep(ms / 1000.0)


# Inject into real time module if not present
for name, fn in {
    "ticks_ms": _ticks_ms,
    "ticks_diff": _ticks_diff,
    "sleep_ms": _sleep_ms,
}.items():
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

if not hasattr(sys, "print_exception"):

    def _print_exception(exc, file=None):  # type: ignore
        _traceback.print_exception(type(exc), exc, exc.__traceback__, file=file or sys.stderr)

    sys.print_exception = _print_exception  # type: ignore


# ---------------------------------------------------------------------------
# requests / urequests stub to simulate HTTP responses
# ---------------------------------------------------------------------------
class _FakeResponse:
    def __init__(self, status_code=200, json_data=None):
        self.status_code = status_code
        self._json_data = json_data or {}

    def json(self):
        return self._json_data

    def close(self):
        pass


class _RequestsStub(types.ModuleType):
    def __init__(self):
        super().__init__("requests")
        # store mapping of prefix -> response
        self._responses = {}

    def set_response(self, url_prefix: str, response: _FakeResponse):
        """Register a response to any GET that starts with url_prefix."""
        self._responses[url_prefix] = response

    # alias for convenience
    def set_json(self, url_prefix: str, json_dict, status_code: int = 200):
        self.set_response(url_prefix, _FakeResponse(status_code, json_dict))

    def get(self, url, *args, **kwargs):
        for prefix, resp in self._responses.items():
            if url.startswith(prefix):
                return resp
        return _FakeResponse(status_code=404)


# Fixture installs stub and yields helper to set responses
@pytest.fixture
def requests_stub(monkeypatch):
    stub = _RequestsStub()
    # Make both 'requests' and 'urequests' point to the same stub
    monkeypatch.setitem(sys.modules, "requests", stub)
    monkeypatch.setitem(sys.modules, "urequests", stub)
    yield stub


# ---------------------------------------------------------------------------
# Make time.sleep a no-op for faster tests (can be overridden per test)
# ---------------------------------------------------------------------------
@pytest.fixture(autouse=True)
def _fast_sleep(monkeypatch):
    monkeypatch.setattr(_real_time, "sleep", lambda s: None)
    yield


# Ensure basic stub for urequests and mip modules BEFORE any esp32 imports
if "urequests" not in sys.modules:
    sys.modules["urequests"] = types.ModuleType("urequests")
    setattr(
        sys.modules["urequests"],
        "get",
        lambda *a, **k: (_FakeResponse(status_code=404)),
    )

if "mip" not in sys.modules:
    mip_stub = types.ModuleType("mip")

    def _install(pkg):
        # no-op for tests
        return None

    mip_stub.install = _install  # type: ignore[attr-defined]
    sys.modules["mip"] = mip_stub

if "ujson" not in sys.modules:
    ujson_stub = types.ModuleType("ujson")
    setattr(ujson_stub, 'loads', _std_json.loads)
    setattr(ujson_stub, 'dumps', _std_json.dumps)
    setattr(ujson_stub, 'dumpsb', lambda obj: _std_json.dumps(obj).encode())
    setattr(ujson_stub, 'load', _std_json.load)
    setattr(ujson_stub, 'dump', _std_json.dump)
    sys.modules["ujson"] = ujson_stub


# ---------------------------------------------------------------------------
# network WLAN stub for WiFiManager tests
# ---------------------------------------------------------------------------
class _MockWLAN:
    STA_IF = 0

    def __init__(self, iface):
        self.active_state = False
        self._connected = False
        self._ip = "192.168.0.2"
        self._rssi = -50

    def active(self, state=None):
        if state is None:
            return self.active_state
        self.active_state = state

    def connect(self, ssid, password):
        # instantly connect
        self._connected = True

    def isconnected(self):
        return self._connected

    def ifconfig(self):
        return (self._ip, "255.255.255.0", "192.168.0.1", "8.8.8.8")

    def status(self, arg="rssi"):
        if arg == 'rssi':
            return self._rssi
        return None

    def disconnect(self):
        self._connected = False


network_stub = types.ModuleType("network")
setattr(network_stub, "WLAN", _MockWLAN)
setattr(network_stub, "STA_IF", _MockWLAN.STA_IF)

sys.modules["network"] = network_stub

# ---------------------------------------------------------------------------
# st7789py display driver stub and font stub
# ---------------------------------------------------------------------------


def _rgb565(r, g, b):
    r5 = (r >> 3) & 0x1F
    g6 = (g >> 2) & 0x3F
    b5 = (b >> 3) & 0x1F
    return (r5 << 11) | (g6 << 5) | b5


class _StubST7789:
    BLACK = _rgb565(0, 0, 0)
    WHITE = _rgb565(255, 255, 255)
    RED = _rgb565(255, 0, 0)
    GREEN = _rgb565(0, 255, 0)
    YELLOW = _rgb565(255, 255, 0)
    PURPLE = _rgb565(128, 0, 128)
    MAROON = _rgb565(128, 0, 0)
    GRAY = _rgb565(128, 128, 128)

    def __init__(self, *args, **kwargs):
        pass

    def fill(self, color):
        pass

    def text(self, *args, **kwargs):
        pass

    def blit_buffer(self, *args, **kwargs):
        pass

    @staticmethod
    def color565(r, g, b):
        return _rgb565(r, g, b)


st7789_stub = types.ModuleType("st7789py")
# expose constants and class
for attr in dir(_StubST7789):
    if not attr.startswith("__"):
        setattr(st7789_stub, attr, getattr(_StubST7789, attr))
setattr(st7789_stub, "ST7789", _StubST7789)

sys.modules["st7789py"] = st7789_stub

# Font stub: lib.vga1_8x8.FONT (768 zeros)
lib_stub = types.ModuleType("lib")
font_mod = types.ModuleType("vga1_8x8")
setattr(font_mod, "FONT", [0] * (96 * 8))
lib_stub.vga1_8x8 = font_mod  # type: ignore[attr-defined]
sys.modules["lib"] = lib_stub
sys.modules["lib.vga1_8x8"] = font_mod

# Ensure config has PURPLE_AIR_API_KEY for tests running without secrets.py
try:
    import config as _cfg

    if not hasattr(_cfg, "PURPLE_AIR_API_KEY"):
        setattr(_cfg, "PURPLE_AIR_API_KEY", "")
except ImportError:
    pass
