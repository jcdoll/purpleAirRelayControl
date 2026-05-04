# MQTT client for Home Assistant integration
#
# Best-effort, non-blocking. Publishes state on demand, listens for commands,
# auto-reconnects on failure. Failures never propagate -- the main control loop
# always runs whether or not the broker is reachable.
#
# See esp32/docs/home_assistant.md for setup + usage.

import json
import time

import config
from umqtt.simple import MQTTClient

DEVICE_ID = "purpleair_relay"
DEVICE_NAME = "PurpleAir Relay"
DISCOVERY_PREFIX = "homeassistant"

STATE_TOPIC = "purpleair/state"
AVAILABILITY_TOPIC = "purpleair/availability"

CMD_MODE_TOPIC      = "purpleair/mode/set"
CMD_REFRESH_TOPIC   = "purpleair/refresh/press"
CMD_THR_ENABLE_TOPIC  = "purpleair/threshold_enable/set"
CMD_THR_DISABLE_TOPIC = "purpleair/threshold_disable/set"

VALID_MODES = ("OFF", "ON", "PURPLEAIR")
RECONNECT_INTERVAL_S = 30


class MQTTManager:
    def __init__(self, mode_callback=None, threshold_callback=None, refresh_callback=None):
        # Callbacks (all optional):
        #   mode_callback(mode_str)             -- new mode requested
        #   threshold_callback(name, int_value) -- threshold change requested
        #   refresh_callback()                  -- force-refresh button pressed
        self.mode_callback = mode_callback
        self.threshold_callback = threshold_callback
        self.refresh_callback = refresh_callback
        self.client = None
        self.connected = False
        self.last_connect_attempt = 0

    def is_enabled(self):
        return bool(getattr(config, "MQTT_BROKER", ""))

    def _build_client(self):
        user = getattr(config, "MQTT_USER", "") or None
        password = getattr(config, "MQTT_PASSWORD", "") or None
        return MQTTClient(
            client_id=DEVICE_ID,
            server=config.MQTT_BROKER,
            port=getattr(config, "MQTT_PORT", 1883),
            user=user,
            password=password,
            keepalive=60,
        )

    def _on_message(self, topic, msg):
        try:
            topic_str = topic.decode() if isinstance(topic, (bytes, bytearray)) else topic
            msg_str = msg.decode() if isinstance(msg, (bytes, bytearray)) else msg
            msg_str = msg_str.strip()

            if topic_str == CMD_MODE_TOPIC:
                mode = msg_str.upper()
                if mode in VALID_MODES and self.mode_callback:
                    self.mode_callback(mode)
                    print(f"MQTT cmd: mode -> {mode}")
            elif topic_str == CMD_THR_ENABLE_TOPIC and self.threshold_callback:
                self.threshold_callback("AQI_ENABLE_THRESHOLD", int(float(msg_str)))
            elif topic_str == CMD_THR_DISABLE_TOPIC and self.threshold_callback:
                self.threshold_callback("AQI_DISABLE_THRESHOLD", int(float(msg_str)))
            elif topic_str == CMD_REFRESH_TOPIC and self.refresh_callback:
                self.refresh_callback()
                print("MQTT cmd: refresh")
            else:
                print(f"MQTT msg ignored: topic={topic_str} msg={msg_str}")
        except Exception as e:
            print(f"MQTT message handler error: {type(e).__name__}: {e}")

    def connect(self):
        if not self.is_enabled():
            return False
        try:
            self.client = self._build_client()
            self.client.set_last_will(AVAILABILITY_TOPIC, b"offline", retain=True, qos=0)
            self.client.set_callback(self._on_message)
            self.client.connect()
            for topic in (CMD_MODE_TOPIC, CMD_THR_ENABLE_TOPIC,
                          CMD_THR_DISABLE_TOPIC, CMD_REFRESH_TOPIC):
                self.client.subscribe(topic)
            self.client.publish(AVAILABILITY_TOPIC, b"online", retain=True, qos=0)
            self.connected = True
            print(f"MQTT connected to {config.MQTT_BROKER}:{getattr(config, 'MQTT_PORT', 1883)}")
            self._publish_discovery()
            return True
        except Exception as e:
            print(f"MQTT connect failed: {type(e).__name__}: {e}")
            self.connected = False
            self.client = None
            return False

    def _publish_discovery(self):
        device = {
            "identifiers": [DEVICE_ID],
            "name": DEVICE_NAME,
            "model": "ESP32-S3 Reverse TFT Feather",
            "manufacturer": "DIY",
        }
        entities = [
            ("select", "mode", {
                "name": "Mode",
                "unique_id": DEVICE_ID + "_mode",
                "state_topic": STATE_TOPIC,
                "value_template": "{{ value_json.mode }}",
                "command_topic": CMD_MODE_TOPIC,
                "options": list(VALID_MODES),
                "icon": "mdi:fan",
                "availability_topic": AVAILABILITY_TOPIC,
                "device": device,
            }),
            ("binary_sensor", "vent", {
                "name": "Ventilation",
                "unique_id": DEVICE_ID + "_vent",
                "state_topic": STATE_TOPIC,
                "value_template": "{{ value_json.vent }}",
                "payload_on": "ON",
                "payload_off": "OFF",
                "device_class": "running",
                "availability_topic": AVAILABILITY_TOPIC,
                "device": device,
            }),
            ("sensor", "outdoor_aqi", {
                "name": "Outdoor AQI",
                "unique_id": DEVICE_ID + "_outdoor_aqi",
                "state_topic": STATE_TOPIC,
                "value_template": "{{ value_json.outdoor_aqi }}",
                "state_class": "measurement",
                "device_class": "aqi",
                "unit_of_measurement": "AQI",
                "icon": "mdi:weather-windy",
                "availability_topic": AVAILABILITY_TOPIC,
                "device": device,
            }),
            ("sensor", "indoor_aqi", {
                "name": "Indoor AQI",
                "unique_id": DEVICE_ID + "_indoor_aqi",
                "state_topic": STATE_TOPIC,
                "value_template": "{{ value_json.indoor_aqi }}",
                "state_class": "measurement",
                "device_class": "aqi",
                "unit_of_measurement": "AQI",
                "icon": "mdi:home-thermometer",
                "availability_topic": AVAILABILITY_TOPIC,
                "device": device,
            }),
            ("sensor", "reason", {
                "name": "Reason",
                "unique_id": DEVICE_ID + "_reason",
                "state_topic": STATE_TOPIC,
                "value_template": "{{ value_json.reason }}",
                "icon": "mdi:information-outline",
                "availability_topic": AVAILABILITY_TOPIC,
                "device": device,
            }),
            ("sensor", "last_update", {
                "name": "Last AQI Update",
                "unique_id": DEVICE_ID + "_last_update",
                "state_topic": STATE_TOPIC,
                "value_template": "{{ value_json.last_update }}",
                "device_class": "timestamp",
                "entity_category": "diagnostic",
                "availability_topic": AVAILABILITY_TOPIC,
                "device": device,
            }),
            ("number", "threshold_enable", {
                "name": "AQI Enable Threshold",
                "unique_id": DEVICE_ID + "_threshold_enable",
                "state_topic": STATE_TOPIC,
                "value_template": "{{ value_json.aqi_enable_threshold }}",
                "command_topic": CMD_THR_ENABLE_TOPIC,
                "min": 0,
                "max": 500,
                "step": 5,
                "mode": "slider",
                "device_class": "aqi",
                "unit_of_measurement": "AQI",
                "icon": "mdi:fan-plus",
                "entity_category": "config",
                "availability_topic": AVAILABILITY_TOPIC,
                "device": device,
            }),
            ("number", "threshold_disable", {
                "name": "AQI Disable Threshold",
                "unique_id": DEVICE_ID + "_threshold_disable",
                "state_topic": STATE_TOPIC,
                "value_template": "{{ value_json.aqi_disable_threshold }}",
                "command_topic": CMD_THR_DISABLE_TOPIC,
                "min": 0,
                "max": 500,
                "step": 5,
                "mode": "slider",
                "device_class": "aqi",
                "unit_of_measurement": "AQI",
                "icon": "mdi:fan-off",
                "entity_category": "config",
                "availability_topic": AVAILABILITY_TOPIC,
                "device": device,
            }),
            ("button", "refresh", {
                "name": "Refresh AQI",
                "unique_id": DEVICE_ID + "_refresh",
                "command_topic": CMD_REFRESH_TOPIC,
                "icon": "mdi:refresh",
                "entity_category": "config",
                "availability_topic": AVAILABILITY_TOPIC,
                "device": device,
            }),
        ]
        for component, slug, payload in entities:
            topic = f"{DISCOVERY_PREFIX}/{component}/{DEVICE_ID}/{slug}/config"
            try:
                self.client.publish(topic, json.dumps(payload).encode(), retain=True, qos=0)
            except Exception as e:
                print(f"MQTT discovery publish failed for {slug}: {type(e).__name__}: {e}")
                self.connected = False
                return
        print("MQTT discovery published")

    def publish_state(self, mode, vent_enabled, outdoor_aqi, indoor_aqi, reason,
                      aqi_enable_threshold=None, aqi_disable_threshold=None,
                      last_update=None):
        if not self.connected:
            return
        payload = {
            "mode": mode,
            "vent": "ON" if vent_enabled else "OFF",
            "outdoor_aqi": int(outdoor_aqi) if outdoor_aqi is not None and outdoor_aqi >= 0 else None,
            "indoor_aqi": int(indoor_aqi) if indoor_aqi is not None and indoor_aqi >= 0 else None,
            "reason": reason,
            "aqi_enable_threshold": aqi_enable_threshold,
            "aqi_disable_threshold": aqi_disable_threshold,
            "last_update": last_update,
        }
        try:
            self.client.publish(STATE_TOPIC, json.dumps(payload).encode(), retain=True, qos=0)
        except Exception as e:
            print(f"MQTT publish failed: {type(e).__name__}: {e}")
            self.connected = False

    def check_messages(self):
        if not self.is_enabled():
            return
        if not self.connected:
            now = time.time()
            if now - self.last_connect_attempt >= RECONNECT_INTERVAL_S:
                self.last_connect_attempt = now
                self.connect()
            return
        try:
            self.client.check_msg()
        except Exception as e:
            print(f"MQTT check_msg failed: {type(e).__name__}: {e}")
            self.connected = False
