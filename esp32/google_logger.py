import urequests as requests
import time
import config

class GoogleFormsLogger:
    def __init__(self):
        self.enabled = config.GOOGLE_FORMS_ENABLED
        self.url = config.GOOGLE_FORMS_URL
        self.last_log_time = 0
        
    def log(self, outdoor_aqi, indoor_aqi, switch_state, vent_state, reason):
        # Log data to Google Forms
        if not self.enabled or not self.url:
            return False
            
        try:
            # Prepare form data - field IDs from Arduino implementation
            form_data = {
                'entry.1205406470': str(int(outdoor_aqi)) if outdoor_aqi > 0 else 'N/A',  # Outdoor AQI
                'entry.1516636704': str(int(indoor_aqi)) if indoor_aqi > 0 else 'N/A',   # Indoor AQI
                'entry.937873384': switch_state,                                          # Switch state
                'entry.1558449802': 'ON' if vent_state else 'OFF',                       # Ventilation state
                'entry.589349670': reason                                                 # Reason
            }
            
            # Submit form
            response = requests.post(self.url, data=form_data, timeout=10)
            success = response.status_code == 200 or response.status_code == 302  # 302 is redirect after submit
            response.close()
            
            if success:
                self.last_log_time = time.time()
                if config.DEBUG_MODE:
                    print(f"Logged to Google Forms: Out={outdoor_aqi:.0f}, In={indoor_aqi:.0f}, State={vent_state}")
            else:
                if config.DEBUG_MODE:
                    print(f"Google Forms logging failed: {response.status_code}")
                    
            return success
            
        except Exception as e:
            if config.DEBUG_MODE:
                print(f"Google Forms logging error: {e}")
            return False
    
    def should_log(self, force=False):
        # Check if enough time has passed for next log
        if force:
            return True
            
        current_time = time.time()
        return (current_time - self.last_log_time) >= config.LOG_INTERVAL