# Home Assistant integration

Optional remote-control / monitoring path. The ESP32 publishes its state and accepts commands over MQTT, and Home Assistant auto-discovers the device. Combined with Tailscale, this gives remote control without exposing anything to the public internet.

Architecture:

```
ESP32 ──MQTT──> Mosquitto broker ──MQTT──> Home Assistant
                  (on Unraid)                  (on Unraid)
```

## Prerequisites

- Home Assistant reachable on your LAN (any install method works; this guide assumes Unraid).
- An MQTT broker. The steps below set up Mosquitto on Unraid as a Docker container.
- ESP32 firmware with MQTT publish/subscribe enabled (see firmware notes at the bottom).

## 1. Install the Mosquitto broker on Unraid

Install **eclipse-mosquitto** via Community Apps. Defaults are fine:

- Port `1883` (MQTT) bound to the host
- Bind-mounts: `/mosquitto/config`, `/mosquitto/data`, `/mosquitto/log` to a path under `/mnt/user/appdata/mosquitto/`

The official image ships **without** a default config file. The container will enter a restart loop on first start until you provide one.

### Create a minimal config (no auth)

This works for a trusted LAN. Anonymous access is fine as long as port `1883` is **not** exposed to the internet.

From the Unraid shell:

```bash
docker stop mosquitto

cat > /mnt/user/appdata/mosquitto/config/mosquitto.conf <<'EOF'
listener 1883
allow_anonymous true
persistence true
persistence_location /mosquitto/data/
log_dest file /mosquitto/log/mosquitto.log
EOF

# eclipse-mosquitto runs as UID 1883 inside the container
chown -R 1883:1883 /mnt/user/appdata/mosquitto

docker start mosquitto
docker logs mosquitto --tail 20
```

A clean start prints `mosquitto version 2.x.x running` and stays up.

### Optional: enable username/password auth

If you'd rather not run anonymously, create a password file with a one-shot container (avoids the "container restarting" race):

```bash
docker run --rm -it \
  -v /mnt/user/appdata/mosquitto/config:/mosquitto/config \
  eclipse-mosquitto:latest \
  mosquitto_passwd -c /mosquitto/config/passwd <USERNAME>

chown 1883:1883 /mnt/user/appdata/mosquitto/config/passwd
```

Replace the config with:

```bash
cat > /mnt/user/appdata/mosquitto/config/mosquitto.conf <<'EOF'
listener 1883
allow_anonymous false
password_file /mosquitto/config/passwd
persistence true
persistence_location /mosquitto/data/
log_dest file /mosquitto/log/mosquitto.log
EOF

docker restart mosquitto
docker logs mosquitto --tail 20
```

### Sanity test

From the Unraid host, publish a test message to your own broker:

```bash
docker run --rm eclipse-mosquitto:latest \
  mosquitto_pub -h <UNRAID_IP> -p 1883 -t test/hello -m world
```

(Add `-u <USERNAME> -P <PASSWORD>` if you enabled auth.) No error printed = broker is up.

## 2. Add the MQTT integration to Home Assistant

1. **Settings → Devices & Services → Add Integration → MQTT**.
2. **Broker**: Unraid host IP (the one Mosquitto is bound to).
3. **Port**: `1883`.
4. **Username / Password**: leave blank for anonymous, or use what you set in the optional step above.
5. **Discovery prefix**: `homeassistant` (the default — leave it).
6. Submit. The integration shows "Connected" once it reaches the broker.

No YAML edits needed; entities will appear automatically once the ESP32 publishes its discovery payloads.

## 3. ESP32 firmware

The firmware reads MQTT broker info from `secrets.py` (see `secrets_template.py`):

```python
MQTT_BROKER = ""        # Unraid host IP, e.g. "192.168.1.10"
MQTT_PORT = 1883
MQTT_USER = ""          # blank for anonymous
MQTT_PASSWORD = ""      # blank for anonymous
```

On boot the ESP32:

1. Connects to WiFi.
2. Connects to the broker.
3. Publishes a Home Assistant MQTT discovery payload under `homeassistant/...` for each entity it exposes.
4. Publishes its current state on `purpleair/state`.
5. Subscribes to `purpleair/mode/set` for remote mode changes.

Entities that appear in Home Assistant after first boot:

| Entity                                       | Type          | Direction  | Notes                                                                              |
|----------------------------------------------|---------------|------------|------------------------------------------------------------------------------------|
| `select.purpleair_relay_mode`                | select        | read/write | `OFF` / `ON` / `PURPLEAIR` -- same modes as the D1 button                          |
| `binary_sensor.purpleair_relay_ventilation`  | binary_sensor | read       | actual relay state                                                                 |
| `sensor.purpleair_relay_outdoor_aqi`         | sensor        | read       | latest outdoor AQI (device_class `aqi`, unit `AQI`)                                |
| `sensor.purpleair_relay_indoor_aqi`          | sensor        | read       | latest indoor AQI                                                                  |
| `sensor.purpleair_relay_reason`              | sensor        | read       | human-readable reason for the current state                                        |
| `sensor.purpleair_relay_last_aqi_update`     | sensor        | read       | timestamp of the last successful PurpleAir poll (diagnostic)                       |
| `number.purpleair_relay_aqi_enable_threshold`| number        | read/write | AQI below which ventilation turns ON in PURPLEAIR mode (config; persisted)         |
| `number.purpleair_relay_aqi_disable_threshold`| number       | read/write | AQI at/above which ventilation turns OFF in PURPLEAIR mode (config; persisted)     |
| `button.purpleair_relay_refresh_aqi`         | button        | write      | Force an immediate PurpleAir poll                                                  |

Threshold values are persisted to `/settings.json` on the ESP32 filesystem and survive reboot.

If MQTT is misconfigured or unreachable the ESP32 keeps running normally -- MQTT is best-effort and never blocks the main control loop.

## Using it in Home Assistant

After the device shows up under **Settings -> Devices & services -> MQTT -> 1 device -> PurpleAir Relay**, you have three things you'll want to do regularly:

### Change the mode (remote control)

Two ways:

1. **From the device page**: Settings -> Devices & services -> MQTT -> 1 device -> PurpleAir Relay. The "Controls" section shows the **Mode** dropdown. Click it, pick `OFF` / `ON` / `PURPLEAIR`. The change reaches the firmware in <1 s.
2. **From a dashboard** (much faster after setup, see below).

### View the AQI history graph

Recorder + statistics are on by default in HA, so the AQI sensors are already being logged. To view:

- Sidebar -> **History**. Filter by entity `sensor.purpleair_relay_outdoor_aqi` (and the indoor one). Pick a date range top-right.
- Or sidebar -> **Statistics** for hourly aggregated charts going back further.

To pin a graph to a dashboard, see the next section.

### Build a one-card dashboard

Most useful starting point:

1. Sidebar -> **Overview** (the default dashboard). Top-right three-dot menu -> **Edit dashboard** -> **Add card**.
2. Pick **Entities**, then add: `select.purpleair_relay_mode`, `binary_sensor.purpleair_relay_ventilation`, `sensor.purpleair_relay_outdoor_aqi`, `sensor.purpleair_relay_indoor_aqi`, `sensor.purpleair_relay_reason`.
3. **Add card** -> **History graph**. Add the two AQI sensors. Set "Hours to show" to 168 for a week's view.
4. (Optional) **Add card** -> **Statistics graph**. Add the AQI sensors with period "hour" or "day" for longer-term trend.

Save. You can now glance at the dashboard, change the mode, and see AQI trends in one place. The mobile app reuses the same dashboard.

### Tune the AQI thresholds without re-flashing

`number.purpleair_relay_aqi_enable_threshold` and `..._aqi_disable_threshold` show as sliders in the device page. Change them and the firmware:

1. Saves the new value to `/settings.json` on the ESP32.
2. Reloads the value into `config.AQI_ENABLE_THRESHOLD` / `config.AQI_DISABLE_THRESHOLD` immediately.
3. The next ventilation update uses the new threshold.

The values persist across reboots. To revert to the firmware defaults, delete `/settings.json` on the device (`mpremote rm settings.json`).

Keep `enable < disable`. Hysteresis prevents the relay from chattering near the threshold.

### Force an AQI refresh

`button.purpleair_relay_refresh_aqi` triggers an immediate poll of the PurpleAir API and the local sensors, bypassing the normal poll interval. Useful for testing or after a known AQI change in your area.

### Set up an automation

Example: text yourself when outdoor AQI exceeds 150.

1. Settings -> **Automations & scenes** -> **+ Create automation** -> **Create new automation**.
2. Trigger -> **State** -> Entity `sensor.purpleair_relay_outdoor_aqi`, "Above" 150.
3. Action -> pick a notify service (mobile app, email, etc).
4. Save.

Other useful patterns: switch mode to `OFF` between 22:00 and 06:00; switch to `PURPLEAIR` otherwise; trigger a fan based on the indoor AQI.

## Verification

1. After flashing the firmware, watch `docker logs mosquitto -f` on Unraid. You should see `New client connected from <ESP32_IP>` within ~10 seconds of boot.
2. In Home Assistant, **Settings → Developer tools → MQTT** tab → under **Listen to a topic**, enter `purpleair/state` (or `#` to see everything) → **Start listening**. State updates should appear on every change.
3. The auto-discovered device shows up under **Settings → Devices & Services → MQTT** as `purpleair_relay`.

## Remote access via Tailscale

With Tailscale on both your Unraid box and your phone/laptop, the Home Assistant mobile app and web UI work from anywhere — no port forwarding, no exposed services. The MQTT broker stays on the trusted Tailnet only.

## Troubleshooting

**Mosquitto container in a restart loop**
- Almost always a missing or unreadable config. Check `docker logs mosquitto --tail 20`.
- File ownership: contents of `/mnt/user/appdata/mosquitto/` must be readable by UID `1883`.

**HA shows "Failed to connect" when adding the integration**
- Wrong host IP, wrong port, or anonymous access not enabled in the broker.
- Test from the Unraid host first with `mosquitto_pub` (see Sanity test above).

**Entities never appear in HA**
- Use the **Listen to a topic** tool in HA with `homeassistant/#` to confirm the discovery payloads are arriving.
- If `purpleair/state` is publishing but `homeassistant/...` payloads aren't, the discovery prefix on the ESP32 doesn't match what HA is configured for.

**ESP32 never connects to the broker**
- WiFi up? Check the device serial console.
- Broker IP reachable from the ESP32's subnet? Some Unraid networking setups put Docker containers on a separate subnet.
