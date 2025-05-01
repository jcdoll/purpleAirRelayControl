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
    WiFiDrv::pinMode(25, OUTPUT);
    WiFiDrv::pinMode(26, OUTPUT);
    WiFiDrv::pinMode(27, OUTPUT);
    
    // Enable pullups on digital pins
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
    } else {
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
        Serial.println("VENTILATION STATE: on");
        WiFiDrv::analogWrite(25, LEDColors::VENTILATION_ON[0]);
        WiFiDrv::analogWrite(26, LEDColors::VENTILATION_ON[1]);
        WiFiDrv::analogWrite(27, LEDColors::VENTILATION_ON[2]);
    } else {
        Serial.println("VENTILATION STATE: off");    
        WiFiDrv::analogWrite(25, LEDColors::VENTILATION_OFF[0]);
        WiFiDrv::analogWrite(26, LEDColors::VENTILATION_OFF[1]);
        WiFiDrv::analogWrite(27, LEDColors::VENTILATION_OFF[2]);
    }
    
    digitalWrite(PIN_RELAY1, ventilate);
    digitalWrite(PIN_RELAY2, ventilate);
} 