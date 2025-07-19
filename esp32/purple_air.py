# Hardware tests require MicroPython modules that are not present on the host.
# We use '# type: ignore' to suppress the resulting linting errors.
try:
    import urequests as requests  # type: ignore
except ImportError:
    print("ERROR: urequests module not found! Installing...")
    import mip  # type: ignore

    mip.install('urequests')
    import urequests as requests  # type: ignore

import time

import config


class PurpleAirClient:
    def __init__(self):
        self.api_key = config.PURPLE_AIR_API_KEY
        self.last_outdoor_api_poll = 0
        self.last_outdoor_local_poll = 0
        self.last_indoor_api_poll = 0
        self.last_indoor_local_poll = 0
        self.cached_outdoor_aqi = -1
        self.cached_indoor_aqi = -1

        # Get local sensor IPs from config/secrets
        self.local_outdoor_ips = getattr(config, 'LOCAL_OUTDOOR_SENSOR_IPS', [])
        self.local_indoor_ips = getattr(config, 'LOCAL_INDOOR_SENSOR_IPS', [])

        # Track sensor availability (like Arduino's localSensorAvailable flag)
        self.local_outdoor_available = {}  # IP -> bool
        self.local_indoor_available = {}  # IP -> bool
        for ip in self.local_outdoor_ips:
            self.local_outdoor_available[ip] = False
        for ip in self.local_indoor_ips:
            self.local_indoor_available[ip] = False

    def _is_api_key_configured(self):
        """Check if API key is properly configured"""
        return (
            self.api_key and self.api_key.strip() != "" and len(self.api_key) > 10
        )  # API keys are longer than 10 chars

    def pm25_to_aqi(self, pm25):
        """Convert PM2.5 concentration to AQI using EPA formula - matches Arduino exactly"""
        if pm25 < 0:
            return 0  # Arduino returns 0 for negative values

        # Arduino implementation checks in reverse order (highest first)
        if pm25 > 350.5:
            return self._linear(pm25, 350.5, 500.4, 401.0, 500.0, trim=True)
        if pm25 > 250.5:
            return self._linear(pm25, 250.5, 350.4, 301.0, 400.0, trim=False)
        if pm25 > 150.5:
            return self._linear(pm25, 150.5, 250.4, 201.0, 300.0, trim=False)
        if pm25 > 55.5:
            return self._linear(pm25, 55.5, 150.4, 151.0, 200.0, trim=False)
        if pm25 > 35.5:
            return self._linear(pm25, 35.5, 55.4, 101.0, 150.0, trim=False)
        if pm25 > 12.1:
            return self._linear(pm25, 12.1, 35.4, 51.0, 100.0, trim=False)
        return self._linear(pm25, 0.0, 12.0, 0.0, 50.0, trim=False)

    def _linear(self, pointX, cLow, cHigh, iLow, iHigh, trim=False):
        """Linear interpolation for AQI calculation - matches Arduino exactly"""
        if trim and pointX > cHigh:
            pointX = cHigh
        if trim and pointX < cLow:
            pointX = cLow

        if cHigh == cLow:  # Avoid division by zero
            return iHigh if pointX >= cLow else iLow

        slope = (iHigh - iLow) / (cHigh - cLow)
        aqi = slope * (pointX - cLow) + iLow
        return aqi

    def get_sensor_data_local(self, ip_address, sensor_type='outdoor'):
        """Get sensor data from local network sensor - matches Arduino retry logic"""
        # Arduino tries MAX_LOCAL_CONNECTION_ATTEMPTS times with retry delay
        for attempt in range(1, config.MAX_LOCAL_CONNECTION_ATTEMPTS + 1):
            print(f"  Local sensor attempt {attempt} of {config.MAX_LOCAL_CONNECTION_ATTEMPTS}")

            try:
                url = f"http://{ip_address}/json"
                print(f"    Connecting to {url}...")
                response = requests.get(url, timeout=5)
                print(f"    Response status: {response.status_code}")

                if response.status_code == 200:
                    data = response.json()
                    response.close()

                    # Arduino logic: First check for pm2_5_atm
                    if 'pm2_5_atm' in data:
                        pm25_for_calc = float(data['pm2_5_atm'])
                        if pm25_for_calc >= 0:
                            print("    Using 'pm2_5_atm' from local sensor for AQI calculation.")
                            aqi = int(round(self.pm25_to_aqi(pm25_for_calc)))
                            print(f"    Local data processed. Raw PM2.5: {pm25_for_calc}, Calculated AQI: {aqi}")
                            # Return just the AQI value
                            return aqi
                        else:
                            print(f"    Invalid 'pm2_5_atm' value: {pm25_for_calc}")

                    # Arduino logic: Fall back to pre-calculated pm2.5_aqi
                    elif 'pm2.5_aqi' in data:
                        aqi = int(data['pm2.5_aqi'])
                        if aqi >= 0:
                            print(f"    Using pre-calculated 'pm2.5_aqi' from local sensor: {aqi}")
                            return aqi
                        else:
                            print(f"    Invalid 'pm2.5_aqi' value: {aqi}")

                    print("    No valid PM2.5 or AQI data found in JSON")
                else:
                    print(f"    Error: HTTP {response.status_code}")
                    response.close()

            except OSError as e:
                print(f"    Connection error: {e}")
            except Exception as e:
                print(f"    Error: {type(e).__name__}: {e}")

            # Retry delay (except on last attempt)
            if attempt < config.MAX_LOCAL_CONNECTION_ATTEMPTS:
                print(f"    Waiting {config.LOCAL_RETRY_DELAY_MS}ms before retry...")
                time.sleep(config.LOCAL_RETRY_DELAY_MS / 1000.0)

        print(f"  All {config.MAX_LOCAL_CONNECTION_ATTEMPTS} attempts failed for {ip_address}")
        return -1

    def get_sensor_data_api(self, sensor_id):
        """Get sensor data from PurpleAir API"""
        print(f"  Fetching sensor {sensor_id} from API...")
        try:
            headers = {'X-API-Key': self.api_key}
            url = f"{config.API_BASE_URL}{sensor_id}?fields=pm2.5_10minute"
            print(f"    URL: {url}")

            response = requests.get(url, headers=headers, timeout=10)
            print(f"    Response status: {response.status_code}")

            if response.status_code == 200:
                data = response.json()
                response.close()

                # Extract PM2.5 10-minute average
                sensor_data = data.get('sensor', {})
                pm25 = sensor_data.get('pm2.5_10minute', -1)
                print(f"    PM2.5 (10min avg): {pm25}")

                if pm25 >= 0:  # Accept 0 as valid PM2.5
                    aqi = self.pm25_to_aqi(pm25)
                    print(f"    Calculated AQI: {aqi}")
                    return aqi
                else:
                    print(f"    Invalid PM2.5 value: {pm25}")
            response.close()
        except Exception as e:
            print(f"    API error: {type(e).__name__}: {e}")
        return -1

    def get_multiple_sensors_api(self, sensor_ids):
        """Get average AQI from multiple sensors in one API call (like Arduino does)"""
        if not sensor_ids:
            return -1

        print(f"  Fetching {len(sensor_ids)} sensors from API: {sensor_ids}")
        try:
            headers = {'X-API-Key': self.api_key}
            # Build comma-separated list of sensor IDs (Arduino uses %2C URL encoding)
            sensor_list = "%2C".join(str(id) for id in sensor_ids)  # URL-encoded comma

            # Compose URL in parts to respect the project-wide 120-char limit.
            url = (
                "https://api.purpleair.com/v1/sensors?fields=pm2.5_10minute"
                f"&show_only={sensor_list}&max_age={config.API_MAX_AGE}"
            )
            print(f"    URL: {url}")

            response = requests.get(url, headers=headers, timeout=10)
            print(f"    Response status: {response.status_code}")

            if response.status_code == 200:
                data = response.json()
                response.close()

                # Extract PM2.5 values from all sensors
                pm25_values = []
                for sensor in data.get('data', []):
                    # The API returns data as an array [sensor_id, pm2.5_value]
                    if len(sensor) >= 2 and sensor[1] is not None:
                        print(f"    Sensor {sensor[0]}: PM2.5={sensor[1]}")
                        pm25_values.append(sensor[1])

                if pm25_values:
                    avg_pm25 = sum(pm25_values) / len(pm25_values)
                    print(f"    Average PM2.5: {avg_pm25}")
                    aqi = self.pm25_to_aqi(avg_pm25)
                    print(f"    Calculated AQI: {aqi}")
                    return aqi
            response.close()
        except Exception as e:
            print(f"    API error: {type(e).__name__}: {e}")
        return -1

    def get_outdoor_aqi(self, force_update=False):
        """Get outdoor AQI from configured sensors"""
        current_time = time.time()

        # Try local sensors first if configured
        if config.USE_LOCAL_SENSORS and self.local_outdoor_ips:
            if force_update or (current_time - self.last_outdoor_local_poll) >= config.LOCAL_POLL_INTERVAL:
                print("Outdoor: Polling local sensor(s)...")
                self.last_outdoor_local_poll = current_time
                aqi_values = []

                # Try each outdoor local sensor
                for ip in self.local_outdoor_ips:
                    aqi = self.get_sensor_data_local(ip)
                    if aqi >= 0:  # Accept 0 as valid AQI
                        aqi_values.append(aqi)
                        print(f"  Local sensor {ip}: Success (AQI={aqi})")
                    else:
                        print(f"  Local sensor {ip}: Failed")

                if aqi_values:
                    self.cached_outdoor_aqi = sum(aqi_values) / len(aqi_values)
                    print(f"Outdoor: Local sensor(s) success. Average AQI: {self.cached_outdoor_aqi}")
                    return self.cached_outdoor_aqi
                else:
                    print("Outdoor: All local sensors failed or no valid data.")

        # Fall back to API or use API if no local sensors
        if force_update or (current_time - self.last_outdoor_api_poll) >= config.API_POLL_INTERVAL:
            self.last_outdoor_api_poll = current_time

            # Check if API key is configured before attempting API calls
            if not self._is_api_key_configured():
                if config.DEBUG_MODE:
                    print("Outdoor: Skipping API call - no valid API key configured")
            elif not config.OUTDOOR_SENSOR_IDS:
                print("Outdoor: No sensor IDs configured for API.")
            else:
                print("Outdoor: Polling PurpleAir API...")
                # Make single API call with all sensor IDs (like Arduino does)
                aqi = self.get_multiple_sensors_api(config.OUTDOOR_SENSOR_IDS)
                if aqi >= 0:  # Accept 0 as valid AQI
                    self.cached_outdoor_aqi = aqi
                    print(f"Outdoor: API success. AQI: {aqi}")
                else:
                    print("Outdoor: API failed or no valid data.")

        return self.cached_outdoor_aqi

    def get_indoor_aqi(self, force_update=False):
        """Get indoor AQI from configured sensors"""
        if not config.INDOOR_SENSOR_IDS and not self.local_indoor_ips:
            return -1

        current_time = time.time()

        # Try local sensors first if configured
        if config.USE_LOCAL_SENSORS and self.local_indoor_ips:
            if force_update or (current_time - self.last_indoor_local_poll) >= config.LOCAL_POLL_INTERVAL:
                print("Indoor: Polling local sensor(s)...")
                self.last_indoor_local_poll = current_time
                aqi_values = []

                # Try each indoor local sensor
                for ip in self.local_indoor_ips:
                    aqi = self.get_sensor_data_local(ip)
                    if aqi >= 0:  # Accept 0 as valid AQI
                        aqi_values.append(aqi)
                        print(f"  Local sensor {ip}: Success (AQI={aqi})")
                    else:
                        print(f"  Local sensor {ip}: Failed")

                if aqi_values:
                    self.cached_indoor_aqi = sum(aqi_values) / len(aqi_values)
                    print(f"Indoor: Local sensor(s) success. Average AQI: {self.cached_indoor_aqi}")
                    return self.cached_indoor_aqi
                else:
                    print("Indoor: All local sensors failed or no valid data.")

        # Fall back to API
        if force_update or (current_time - self.last_indoor_api_poll) >= config.API_POLL_INTERVAL:
            self.last_indoor_api_poll = current_time

            # Check if API key is configured before attempting API calls
            if not self._is_api_key_configured():
                if config.DEBUG_MODE:
                    print("Indoor: Skipping API call - no valid API key configured")
            elif not config.INDOOR_SENSOR_IDS:
                print("Indoor: No sensor IDs configured for API.")
            else:
                print("Indoor: Polling PurpleAir API...")
                # Make single API call with all sensor IDs
                aqi = self.get_multiple_sensors_api(config.INDOOR_SENSOR_IDS)
                if aqi >= 0:  # Accept 0 as valid AQI
                    self.cached_indoor_aqi = aqi
                    print(f"Indoor: API success. AQI: {aqi}")
                else:
                    print("Indoor: API failed or no valid data.")

        return self.cached_indoor_aqi

    def log_to_google_forms(self, outdoor_aqi, indoor_aqi, switch_state, vent_state, reason):
        """Log data to Google Forms"""
        if not config.GOOGLE_FORMS_ENABLED or not config.GOOGLE_FORMS_URL:
            return False

        try:
            # Format data for Google Forms
            data = {
                'outdoor_aqi': str(int(outdoor_aqi)) if outdoor_aqi > 0 else 'N/A',
                'indoor_aqi': str(int(indoor_aqi)) if indoor_aqi > 0 else 'N/A',
                'switch_state': switch_state,
                'vent_state': 'ON' if vent_state else 'OFF',
                'reason': reason,
            }

            response = requests.post(config.GOOGLE_FORMS_URL, data=data, timeout=10)
            success = response.status_code == 200
            response.close()
            return success
        except Exception as e:
            if config.DEBUG_MODE:
                print(f"Google Forms logging error: {e}")
            return False
