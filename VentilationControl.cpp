#include "VentilationControl.h"
#include "arduino_secrets.h"
#include "constants.h"
#include <Arduino.h>
#include <utility/wifi_drv.h>

VentilationControl::VentilationControl() : ventilationState(true) {}

void VentilationControl::begin() {
    // Enable outputs on relay pins
    pinMode(PIN_RELAY1, OUTPUT);
    pinMode(PIN_RELAY2, OUTPUT);

    // Enable LED control
    WiFiDrv::pinMode(WIFI_LED_R_PIN, OUTPUT);
    WiFiDrv::pinMode(WIFI_LED_G_PIN, OUTPUT);
    WiFiDrv::pinMode(WIFI_LED_B_PIN, OUTPUT);
    
    // Enable pullups on digital pins
    // This is critical for the switch inputs to work properly
    pinMode(PIN_SWITCH_INPUT1, INPUT_PULLUP);
    pinMode(PIN_SWITCH_INPUT2, INPUT_PULLUP);
}

void VentilationControl::update(SwitchState switchState, int airQuality) {
    ventilationState = getVentilationState(switchState, ventilationState, airQuality);
    setRelays(ventilationState);
}

bool VentilationControl::getVentilationState() const {
    return ventilationState;
}

bool VentilationControl::getVentilationState(SwitchState switchState, bool currentState, int airQuality) {
    if (switchState == SwitchState::ON) {
        return true;
    } else if (switchState == SwitchState::OFF) {
        return false;
    } else { // PURPLEAIR mode
        if (airQuality == -1) {
            Serial.println("AQI is invalid (-1) -> maintaining current ventilation state for PURPLEAIR mode.");
            return currentState; // Maintain current state if AQI is unknown
        }
        if (airQuality < ENABLE_THRESHOLD) {
            Serial.println("AQI is below the enable threshold -> ventilate");
            return true;
        } else if (airQuality >= DISABLE_THRESHOLD) {
            Serial.println("AQI is above the disable threshold -> shut it down");
            return false;
        } else {
            Serial.println("AQI is between our limits -> no change in state");
            return currentState;
        }
    }
}

void VentilationControl::setRelays(bool ventilate) {
    if (ventilate) {
        Serial.println("VENTILATION STATE: ON");
        WiFiDrv::analogWrite(WIFI_LED_R_PIN, LEDColors::VENTILATION_ON[0]);
        WiFiDrv::analogWrite(WIFI_LED_G_PIN, LEDColors::VENTILATION_ON[1]);
        WiFiDrv::analogWrite(WIFI_LED_B_PIN, LEDColors::VENTILATION_ON[2]);
    } else {
        Serial.println("VENTILATION STATE: OFF");    
        WiFiDrv::analogWrite(WIFI_LED_R_PIN, LEDColors::VENTILATION_OFF[0]);
        WiFiDrv::analogWrite(WIFI_LED_G_PIN, LEDColors::VENTILATION_OFF[1]);
        WiFiDrv::analogWrite(WIFI_LED_B_PIN, LEDColors::VENTILATION_OFF[2]);
    }
    
    digitalWrite(PIN_RELAY1, ventilate);
    digitalWrite(PIN_RELAY2, ventilate);
} 