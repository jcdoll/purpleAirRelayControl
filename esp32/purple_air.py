try:
    import urequests as requests
except ImportError:
    print("ERROR: urequests module not found! Installing...")
    import mip
    mip.install('urequests')
    import urequests as requests

import ujson as json
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
        
    def pm25_to_aqi(self, pm25):
        """Convert PM2.5 concentration to AQI using EPA formula"""
        if pm25 < 0:
            return -1
        elif pm25 <= 12.0:
            return self._linear(pm25, 0, 12.0, 0, 50)
        elif pm25 <= 35.4:
            return self._linear(pm25, 12.1, 35.4, 51, 100)
        elif pm25 <= 55.4:
            return self._linear(pm25, 35.5, 55.4, 101, 150)
        elif pm25 <= 150.4:
            return self._linear(pm25, 55.5, 150.4, 151, 200)
        elif pm25 <= 250.4:
            return self._linear(pm25, 150.5, 250.4, 201, 300)
        elif pm25 <= 350.4:
            return self._linear(pm25, 250.5, 350.4, 301, 400)
        elif pm25 <= 500.4:
            return self._linear(pm25, 350.5, 500.4, 401, 500)
        else:
            return 500
            
    def _linear(self, x, x1, x2, y1, y2):
        """Linear interpolation for AQI calculation"""
        return round(((x - x1) * (y2 - y1) / (x2 - x1)) + y1)
    
    def get_sensor_data_local(self, ip_address):
        """Get sensor data from local network sensor"""
        print(f"  Attempting to fetch AQI from local sensor at {ip_address}")
        try:
            url = f"http://{ip_address}/json"
            print(f"    Connecting to {url}...")
            response = requests.get(url, timeout=5)
            print(f"    Response status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                response.close()
                
                # Extract PM2.5 value (average of two channels)
                pm25_a = data.get('pm2_5_atm', 0)
                pm25_b = data.get('pm2_5_atm_b', 0)
                pm25_avg = (pm25_a + pm25_b) / 2.0
                print(f"    PM2.5 values: A={pm25_a}, B={pm25_b}, Avg={pm25_avg}")
                
                aqi = self.pm25_to_aqi(pm25_avg)
                print(f"    Calculated AQI: {aqi}")
                return aqi
            else:
                print(f"    Error: HTTP {response.status_code}")
            response.close()
        except OSError as e:
            print(f"    Connection error: {e}")
        except Exception as e:
            print(f"    Error: {type(e).__name__}: {e}")
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
                
                if pm25 > 0:
                    aqi = self.pm25_to_aqi(pm25)
                    print(f"    Calculated AQI: {aqi}")
                    return aqi
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
            # Build comma-separated list of sensor IDs
            sensor_list = ','.join(str(id) for id in sensor_ids)
            url = f"https://api.purpleair.com/v1/sensors?show_only={sensor_list}&fields=pm2.5_10minute"
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
                    if aqi > 0:
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
            print("Outdoor: Polling PurpleAir API...")
            self.last_outdoor_api_poll = current_time
            
            # Make single API call with all sensor IDs (like Arduino does)
            if config.OUTDOOR_SENSOR_IDS:
                aqi = self.get_multiple_sensors_api(config.OUTDOOR_SENSOR_IDS)
                if aqi > 0:
                    self.cached_outdoor_aqi = aqi
                    print(f"Outdoor: API success. AQI: {aqi}")
                else:
                    print("Outdoor: API failed or no valid data.")
            else:
                print("Outdoor: No sensor IDs configured for API.")
        
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
                    if aqi > 0:
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
            print("Indoor: Polling PurpleAir API...")
            self.last_indoor_api_poll = current_time
            
            # Make single API call with all sensor IDs
            if config.INDOOR_SENSOR_IDS:
                aqi = self.get_multiple_sensors_api(config.INDOOR_SENSOR_IDS)
                if aqi > 0:
                    self.cached_indoor_aqi = aqi
                    print(f"Indoor: API success. AQI: {aqi}")
                else:
                    print("Indoor: API failed or no valid data.")
            else:
                print("Indoor: No sensor IDs configured for API.")
        
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
                'reason': reason
            }
            
            response = requests.post(config.GOOGLE_FORMS_URL, data=data, timeout=10)
            success = response.status_code == 200
            response.close()
            return success
        except Exception as e:
            if config.DEBUG_MODE:
                print(f"Google Forms logging error: {e}")
            return False