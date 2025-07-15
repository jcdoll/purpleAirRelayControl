from machine import Pin
import time
import config

class VentilationController:
    def __init__(self):
        # Initialize relay pins
        self.relay1 = Pin(config.RELAY1_PIN, Pin.OUT)
        self.relay2 = Pin(config.RELAY2_PIN, Pin.OUT)
        
        # State tracking
        self.ventilation_enabled = config.DEFAULT_STATE
        self.switch_mode = "PURPLEAIR"  # OFF, ON, PURPLEAIR
        self.mode_order = ["OFF", "ON", "PURPLEAIR"]  # Toggle order for D1
        self.reason = "Startup"
        self.last_log_time = 0
        self.state_changed = True
        
        # Button interrupt handling
        self.button_flags = [False, False, False]  # D0, D1, D2 interrupt flags
        self.last_interrupt_time = [0, 0, 0]  # Debouncing timestamps
        self.debounce_ms = 200  # 200ms debounce period
        
        # Initialize button inputs with interrupts
        self.button_d0 = Pin(config.BUTTON_D0, Pin.IN, Pin.PULL_UP)  # D0: Pull-up, LOW when pressed
        self.button_d1 = Pin(config.BUTTON_D1, Pin.IN, Pin.PULL_DOWN)  # D1: Pull-down, HIGH when pressed
        self.button_d2 = Pin(config.BUTTON_D2, Pin.IN, Pin.PULL_DOWN)  # D2: Pull-down, HIGH when pressed
        
        # Set up hardware interrupts for immediate response
        self.button_d0.irq(trigger=Pin.IRQ_FALLING, handler=self._button0_interrupt)  # Falling edge (press)
        self.button_d1.irq(trigger=Pin.IRQ_RISING, handler=self._button1_interrupt)   # Rising edge (press)
        self.button_d2.irq(trigger=Pin.IRQ_RISING, handler=self._button2_interrupt)   # Rising edge (press)
        
        # Set initial relay state
        self._set_relays(self.ventilation_enabled)
        print("VentilationController initialized with interrupt-driven buttons")
    
    def _button0_interrupt(self, pin):
        """Hardware interrupt handler for D0 button (falling edge = press)"""
        current_time = time.ticks_ms()
        if time.ticks_diff(current_time, self.last_interrupt_time[0]) > self.debounce_ms:
            self.button_flags[0] = True
            self.last_interrupt_time[0] = current_time
    
    def _button1_interrupt(self, pin):
        """Hardware interrupt handler for D1 button (rising edge = press)"""
        current_time = time.ticks_ms()
        if time.ticks_diff(current_time, self.last_interrupt_time[1]) > self.debounce_ms:
            self.button_flags[1] = True
            self.last_interrupt_time[1] = current_time
    
    def _button2_interrupt(self, pin):
        """Hardware interrupt handler for D2 button (rising edge = press)"""
        current_time = time.ticks_ms()
        if time.ticks_diff(current_time, self.last_interrupt_time[2]) > self.debounce_ms:
            self.button_flags[2] = True
            self.last_interrupt_time[2] = current_time
    
    def _set_relays(self, state):
        """Set both relays to the same state (redundancy)"""
        self.relay1.value(1 if state else 0)
        self.relay2.value(1 if state else 0)
        self.ventilation_enabled = state
    
    def read_switch_mode(self):
        """Check for button presses via interrupt flags and handle mode changes"""
        # Check interrupt flags and process button presses
        for i in range(3):
            if self.button_flags[i]:
                self.button_flags[i] = False  # Clear the flag
                self.state_changed = True
                
                if i == 1:  # D1 pressed - toggle between modes
                    current_index = self.mode_order.index(self.switch_mode)
                    next_index = (current_index + 1) % len(self.mode_order)
                    self.switch_mode = self.mode_order[next_index]
                    print(f"D1 pressed: Mode changed to {self.switch_mode}")
                
                elif i == 0:  # D0 pressed - available for other functions
                    print("D0 pressed: Available for future functions")
                
                elif i == 2:  # D2 pressed - available for other functions  
                    print("D2 pressed: Available for future functions")
                
        return self.switch_mode
    
    def update(self, outdoor_aqi, indoor_aqi=None):
        """Update ventilation state based on AQI and switch mode"""
        # Check for button presses (now via interrupts)
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
    
    def get_status(self):
        """Return current status dictionary"""
        return {
            'enabled': self.ventilation_enabled,
            'mode': self.switch_mode,
            'reason': self.reason,
            'state_changed': self.state_changed
        }
    
    def should_log(self):
        """Return True if state has changed and should be logged"""
        if self.state_changed and time.time() - self.last_log_time > config.LOG_INTERVAL:
            self.last_log_time = time.time()
            self.state_changed = False
            return True
        return False