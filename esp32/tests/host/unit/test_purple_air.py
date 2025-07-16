import math
import importlib
import json
from pathlib import Path

import config

# Utility simple response for requests_stub
class _SimpleResp:
    def __init__(self, status_code=200, data=None):
        self.status_code = status_code
        self._data = data or {}

    def json(self):
        return self._data

    def close(self):
        pass


# ---------------------------------------------------------------------------
# Algorithmic tests (no HTTP required)
# ---------------------------------------------------------------------------
def test_pm25_to_aqi_breakpoints():
    PurpleAirClient = importlib.import_module("purple_air").PurpleAirClient
    client = PurpleAirClient()
    cases = [
        (0.0, 0),
        (12.0, 50),
        (35.4, 100),
        (55.4, 150),
        (150.4, 200),
        (250.4, 300),
        (350.4, 400),
        (500.4, 500),
    ]
    for pm25, expected in cases:
        aqi = client.pm25_to_aqi(pm25)
        assert math.isclose(aqi, expected, abs_tol=1)


# ---------------------------------------------------------------------------
# Network-related tests using requests_stub fixture
# ---------------------------------------------------------------------------
def test_get_sensor_data_local_success(requests_stub):
    # Register response *before* importing module so it uses the stub
    ip = "1.2.3.4"
    local_url = f"http://{ip}/json"  # exact path used in client

    sample_file = Path(__file__).resolve().parents[3] / "tests" / "test.json"
    data = json.loads(sample_file.read_text())

    requests_stub.set_response(local_url, _SimpleResp(200, data))

    purple_air = importlib.import_module("purple_air")
    importlib.reload(purple_air)
    client = purple_air.PurpleAirClient()

    pm25 = data.get("pm2_5_atm", 0)
    expected_aqi = int(round(client.pm25_to_aqi(pm25)))

    assert client.get_sensor_data_local(ip) == expected_aqi


def test_get_sensor_data_api_success(requests_stub):
    sensor_id = 123
    api_url = f"{config.API_BASE_URL}{sensor_id}?fields=pm2.5_10minute"
    pm25 = 35.4
    response_body = {"sensor": {"pm2.5_10minute": pm25}}
    requests_stub.set_response(api_url, _SimpleResp(200, response_body))

    purple_air = importlib.import_module("purple_air")
    importlib.reload(purple_air)
    client = purple_air.PurpleAirClient()
    client.api_key = "dummy"

    expected_aqi = client.pm25_to_aqi(pm25)
    assert math.isclose(client.get_sensor_data_api(sensor_id), expected_aqi, abs_tol=0.1)


def test_get_multiple_sensors_api_average(requests_stub):
    ids = [1, 2, 3]
    sensor_list = "%2C".join(str(i) for i in ids)
    api_url = (
        "https://api.purpleair.com/v1/sensors?fields=pm2.5_10minute"
        f"&show_only={sensor_list}&max_age={config.API_MAX_AGE}"
    )
    pm_values = [10, 20, 30]
    response_body = {"data": [[ids[i], pm_values[i]] for i in range(3)]}
    requests_stub.set_response(api_url, _SimpleResp(200, response_body))

    purple_air = importlib.import_module("purple_air")
    importlib.reload(purple_air)
    client = purple_air.PurpleAirClient()
    client.api_key = "dummy"

    avg_pm = sum(pm_values) / len(pm_values)
    expected_aqi = client.pm25_to_aqi(avg_pm)
    assert math.isclose(client.get_multiple_sensors_api(ids), expected_aqi, abs_tol=0.1) 