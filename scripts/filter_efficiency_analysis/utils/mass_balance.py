"""
Canonical mass balance calculations based on PHYSICS.md

This module provides the single source of truth for all mass balance calculations
to ensure consistency across test data generation, Kalman filter, and other components.
"""

import numpy as np
from typing import Union


def calculate_steady_state_indoor_pm25(
    outdoor_pm25: Union[float, np.ndarray],
    infiltration_rate: float,
    filtration_rate: float, 
    deposition_rate: float,
    filter_efficiency: float,
    indoor_generation: float = 0.0
) -> float:
    """
    Calculate steady-state indoor PM2.5 concentration using PHYSICS.md mass balance equation.
    
    PHYSICS.md canonical equation:
    C_in = (Q_inf * C_out + Q_gen) / (Q_inf + Q_filt * η + Q_dep)
    
    Args:
        outdoor_pm25: Outdoor PM2.5 concentration (μg/m³)
        infiltration_rate: Air infiltration rate (m³/h or ACH)
        filtration_rate: HVAC filtration rate (m³/h or ACH)
        deposition_rate: Natural deposition rate (m³/h or ACH) 
        filter_efficiency: Filter efficiency (0-1)
        indoor_generation: Indoor particle generation rate (μg/h or μg/m³·h)
        
    Returns:
        Indoor PM2.5 concentration (μg/m³) as float
        
    Note:
        All rates must use consistent units (either all m³/h or all ACH).
        For ACH units, indoor_generation should be in μg/m³·h.
    """
    numerator = infiltration_rate * outdoor_pm25 + indoor_generation
    denominator = infiltration_rate + filtration_rate * filter_efficiency + deposition_rate
    
    result = numerator / denominator
    
    # Always return float
    return float(result)


def calculate_indoor_outdoor_ratio(
    infiltration_rate: float,
    filtration_rate: float,
    deposition_rate: float, 
    filter_efficiency: float
) -> float:
    """
    Calculate steady-state indoor/outdoor ratio with no indoor generation.
    
    Args:
        infiltration_rate: Air infiltration rate (ACH)
        filtration_rate: HVAC filtration rate (ACH)
        deposition_rate: Natural deposition rate (ACH)
        filter_efficiency: Filter efficiency (0-1)
        
    Returns:
        Indoor/outdoor PM2.5 ratio
    """
    return infiltration_rate / (infiltration_rate + filtration_rate * filter_efficiency + deposition_rate)


def solve_filter_efficiency_from_ratio(
    io_ratio: float,
    infiltration_rate: float,
    filtration_rate: float,
    deposition_rate: float
) -> float:
    """
    Solve for filter efficiency given indoor/outdoor ratio.
    
    Inverse of the mass balance equation:
    η = (Q_inf - ratio * (Q_inf + Q_dep)) / (ratio * Q_filt)
    
    Args:
        io_ratio: Indoor/outdoor PM2.5 ratio
        infiltration_rate: Air infiltration rate (ACH)
        filtration_rate: HVAC filtration rate (ACH) 
        deposition_rate: Natural deposition rate (ACH)
        
    Returns:
        Filter efficiency (0-1)
    """
    numerator = infiltration_rate - io_ratio * (infiltration_rate + deposition_rate)
    denominator = io_ratio * filtration_rate
    
    if denominator <= 0:
        return 0.0
        
    efficiency = numerator / denominator
    return max(0.0, min(1.0, efficiency))  # Clamp to [0, 1] 