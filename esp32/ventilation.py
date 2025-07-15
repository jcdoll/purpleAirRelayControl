from machine import Pin
import time
import config

class VentilationController:
    def __init__(self):
        # Initialize relay pins
        self.relay1 = Pin(config.RELAY1_PIN, Pin.OUT)
        self.relay2 = Pin(config.RELAY2_PIN, Pin.OUT)
        
        # Initialize button inputs - these act as the 3-position switch
        self.button_d0 = Pin(config.BUTTON_D0, Pin.IN, Pin.PULL_UP)  # OFF position
        self.button_d1 = Pin(config.BUTTON_D1, Pin.IN, Pin.PULL_UP)  # ON position  
        self.button_d2 = Pin(config.BUTTON_D2, Pin.IN, Pin.PULL_UP)  # PURPLEAIR position
        
        # State tracking
        self.ventilation_enabled = config.DEFAULT_STATE
        self.switch_mode = "PURPLEAIR"  # OFF, ON, PURPLEAIR
        self.last_button_states = [1, 1, 1]  # All HIGH when not pressed
        self.reason = "Startup"
        self.last_log_time = 0
        self.state_changed = True
        
        # Set initial relay state
        self._set_relays(self.ventilation_enabled)
    
    def _set_relays(self, state):
        """Set both relays to the same state (redundancy)"""
        self.relay1.value(1 if state else 0)
        self.relay2.value(1 if state else 0)
        self.ventilation_enabled = state
    
    def read_switch_mode(self):
        """Read button states to determine switch mode"""
        # Buttons D0/D1/D2 represent the 3-position switch
        # When a button is pressed (LOW), that's the active mode
        current_states = [
            self.button_d0.value(),
            self.button_d1.value(), 
            self.button_d2.value()
        ]
        
        # Check if any button state changed
        if current_states != self.last_button_states:
            self.last_button_states = current_states
            self.state_changed = True
            
            # Determine mode based on which button is pressed (LOW)
            if current_states[0] == 0:  # D0 pressed
                self.switch_mode = "OFF"
            elif current_states[1] == 0:  # D1 pressed
                self.switch_mode = "ON"
            elif current_states[2] == 0:  # D2 pressed
                self.switch_mode = "PURPLEAIR"
            # If no button pressed, keep current mode
                
        return self.switch_mode
    
    
    def update(self, outdoor_aqi, indoor_aqi=None):
        """Update ventilation state based on AQI and switch mode"""
        # Read current switch mode
        self.read_switch_mode()
        
        previous_state = self.ventilation_enabled
        previous_reason = self.reason
        
        # Handle switch modes
        if self.switch_mode == "OFF":
            self._set_relays(False)
            self.reason = "Manual OFF"
        elif self.switch_mode == "ON":
            self._set_relays(True)
            self.reason = "Manual ON"
        elif self.switch_mode == "PURPLEAIR":
            # Automatic control based on AQI
            if outdoor_aqi < 0:
                # Keep current state if no valid AQI
                self.reason = "No AQI data"
            elif self.ventilation_enabled:
                # Currently ventilating - check if we should stop
                if outdoor_aqi >= config.AQI_DISABLE_THRESHOLD:
                    self._set_relays(False)
                    self.reason = f"AQI too high ({int(outdoor_aqi)})"
                else:
                    self.reason = f"AQI acceptable ({int(outdoor_aqi)})"
            else:
                # Not ventilating - check if we should start
                if outdoor_aqi <= config.AQI_ENABLE_THRESHOLD:
                    self._set_relays(True)
                    self.reason = f"AQI good ({int(outdoor_aqi)})"
                else:
                    self.reason = f"AQI too high ({int(outdoor_aqi)})"
        
        # Check if state changed
        if previous_state != self.ventilation_enabled or previous_reason != self.reason:
            self.state_changed = True
    
    def should_log(self):
        """Check if we should log data"""
        current_time = time.time()
        
        # Log on state change or every LOG_INTERVAL
        if self.state_changed or (current_time - self.last_log_time) >= config.LOG_INTERVAL:
            self.last_log_time = current_time
            should_log = True
            self.state_changed = False
        else:
            should_log = False
            
        return should_log
    
    def get_status(self):
        """Get current ventilation status"""
        return {
            'enabled': self.ventilation_enabled,
            'mode': self.switch_mode,
            'reason': self.reason,
            'relay1': self.relay1.value(),
            'relay2': self.relay2.value()
        }