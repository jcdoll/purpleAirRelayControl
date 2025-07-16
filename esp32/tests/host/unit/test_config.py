import config


def test_core_constants():
    assert config.WIFI_TIMEOUT == 30
    assert config.USE_LOCAL_SENSORS is True
    assert config.API_POLL_INTERVAL == 1800
    assert config.LOCAL_POLL_INTERVAL == 60
    assert config.AQI_ENABLE_THRESHOLD == 120
    assert config.AQI_DISABLE_THRESHOLD == 130
    assert config.DEFAULT_STATE is False
