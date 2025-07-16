import importlib
import sys
import types

# ---------------------------------------------------------------------------
# Stub a minimal st7789 module so that display_manager can import it
# ---------------------------------------------------------------------------

st7789_stub = types.ModuleType("st7789py")

# Provide color565 util that converts RGB888 to RGB565


def _color565(r, g, b):
    r5 = (r >> 3) & 0x1F
    g6 = (g >> 2) & 0x3F
    b5 = (b >> 3) & 0x1F
    return (r5 << 11) | (g6 << 5) | b5


# Attach function and a few colour constants used in DisplayManager
st7789_stub.color565 = _color565
st7789_stub.GREEN = _color565(0, 255, 0)
st7789_stub.YELLOW = _color565(255, 255, 0)
st7789_stub.RED = _color565(255, 0, 0)
st7789_stub.PURPLE = _color565(128, 0, 128)
st7789_stub.MAROON = _color565(128, 0, 0)
st7789_stub.GRAY = _color565(128, 128, 128)
st7789_stub.WHITE = _color565(255, 255, 255)

# Inject stub before importing display_manager
sys.modules["st7789py"] = st7789_stub

# Now import / reload display_manager to pick up stub
import display_manager as dm  # noqa: E402

importlib.reload(dm)

from utils import aqi_colors  # noqa: E402


def test_get_aqi_color_st7789_matches_util():
    """Ensure display_manager helper returns same RGB565 as util function."""
    for aqi in [0, 75, 125, 175, 250, 400]:
        expected = aqi_colors.get_aqi_color_565(aqi)
        assert dm.get_aqi_color_st7789(aqi) == expected
