#ifndef VENTILATION_CONTROL_H
#define VENTILATION_CONTROL_H

#include "constants.h"

class VentilationControl {
public:
    VentilationControl();
    
    void begin();
    void update(SwitchState switchState, int airQuality);
    bool getVentilationState() const;
    
private:
    void setRelays(bool ventilate);
    bool getVentilationState(SwitchState switchState, bool currentState, int airQuality);
    
    bool ventilationState;
};

#endif // VENTILATION_CONTROL_H 