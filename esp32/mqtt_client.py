# MQTT client for Home Assistant integration
#
# Best-effort, non-blocking. Publishes state on demand, listens for mode commands,
# auto-reconnects on failure. Failures never propagate -- the main control loop
# always runs whether or not the broker is reachable.
#
# See esp32/docs/home_assistant.md for setup.

import json
import time

import config
from umqtt.simple import MQTTClient

DEVICE_ID = "purpleair_relay"
DEVICE_NAME = "PurpleAir Relay"
DISCOVERY_PREFIX = "homeassistant"
STATE_TOPIC = "purpleair/state"
COMMAND_TOPIC = "purpleair/mode/set"
AVAILABILITY_TOPIC = "purpleair/availability"

VALID_MODES = ("OFF", "ON", "PURPLEAIR")
RECONNECT_INTERVAL_S = 30


class MQTTManager:
    def __init__(self, command_callback=None):
        # command_callback(mode: str) is invoked when a valid mode arrives on COMMAND_TOPIC.
        self.command_callback = command_callback
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
            msg_str = msg_str.strip().upper()
            if topic_str == COMMAND_TOPIC and msg_str in VALID_MODES:
                if self.command_callback:
                    self.command_callback(msg_str)
                    print(f"MQTT command received: mode -> {msg_str}")
            else:
                print(f"MQTT message ignored: topic={topic_str} msg={msg_str}")
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
            self.client.subscribe(COMMAND_TOPIC)
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
        # Home Assistant MQTT discovery payloads. Retained so HA picks them up
        # whenever it (re)connects to the broker.
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
                "command_topic": COMMAND_TOPIC,
                "options": list(VALID_MODES),
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
                "availability_topic": AVAILABILITY_TOPIC,
                "device": device,
            }),
            ("sensor", "indoor_aqi", {
                "name": "Indoor AQI",
                "unique_id": DEVICE_ID + "_indoor_aqi",
                "state_topic": STATE_TOPIC,
                "value_template": "{{ value_json.indoor_aqi }}",
                "state_class": "measurement",
                "availability_topic": AVAILABILITY_TOPIC,
                "device": device,
            }),
            ("sensor", "reason", {
                "name": "Reason",
                "unique_id": DEVICE_ID + "_reason",
                "state_topic": STATE_TOPIC,
                "value_template": "{{ value_json.reason }}",
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

    def publish_state(self, mode, vent_enabled, outdoor_aqi, indoor_aqi, reason):
        if not self.connected:
            return
        payload = {
            "mode": mode,
            "vent": "ON" if vent_enabled else "OFF",
            "outdoor_aqi": int(outdoor_aqi) if outdoor_aqi is not None and outdoor_aqi >= 0 else None,
            "indoor_aqi": int(indoor_aqi) if indoor_aqi is not None and indoor_aqi >= 0 else None,
            "reason": reason,
        }
        try:
            self.client.publish(STATE_TOPIC, json.dumps(payload).encode(), retain=True, qos=0)
        except Exception as e:
            print(f"MQTT publish failed: {type(e).__name__}: {e}")
            self.connected = False

    def check_messages(self):
        # Call from main loop. Non-blocking. Handles reconnect attempts.
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
