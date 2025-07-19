"""
Canonical mass balance calculations based on PHYSICS.md

This module provides the single source of truth for all mass balance calculations
to ensure consistency across test data generation, Kalman filter, and other components.

The mass balance explicitly accounts for:
- Natural building infiltration (Q_inf) 
- ERV mechanical ventilation (Q_erv) - bypasses filter
- Total outdoor air infiltration = Q_inf + Q_erv
"""

from typing import Any, Dict, Union

import numpy as np


def calculate_steady_state_indoor_pm25(
    outdoor_pm25: Union[float, np.ndarray],
    infiltration_rate: float,
    filtration_rate: float,
    deposition_rate: float,
    filter_efficiency: float,
    indoor_generation: float = 0.0,
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
    infiltration_rate: float, filtration_rate: float, deposition_rate: float, filter_efficiency: float
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
    io_ratio: float, infiltration_rate: float, filtration_rate: float, deposition_rate: float
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
    return max(0.0, efficiency)  # Allow efficiency > 100% to indicate model issues


def calculate_infiltration_components(config: Dict[str, Any]) -> Dict[str, float]:
    """
    Calculate natural infiltration and ERV contributions separately.

    Args:
        config: Configuration dictionary with building and HVAC parameters

    Returns:
        Dictionary with 'natural_ach', 'erv_ach', and 'total_ach' components
    """
    from utils.config_helpers import _calculate_erv_infiltration, calculate_infiltration_rate

    # Calculate total infiltration (includes ERV)
    total_ach = calculate_infiltration_rate(config)

    # Calculate ERV-only contribution
    erv_ach = _calculate_erv_infiltration(config)

    # Natural infiltration is the difference
    natural_ach = total_ach - erv_ach

    return {'natural_ach': natural_ach, 'erv_ach': erv_ach, 'total_ach': total_ach}


def calculate_steady_state_indoor_pm25_with_erv(
    outdoor_pm25: Union[float, np.ndarray],
    natural_infiltration_rate: float,
    erv_infiltration_rate: float,
    filtration_rate: float,
    deposition_rate: float,
    filter_efficiency: float,
    indoor_generation: float = 0.0,
) -> float:
    """
    Calculate steady-state indoor PM2.5 with explicit ERV consideration.

    PHYSICS.md canonical equation with ERV:
    C_in = ((Q_inf + Q_erv) * C_out + Q_gen) / (Q_inf + Q_erv + Q_filt * η + Q_dep)

    Args:
        outdoor_pm25: Outdoor PM2.5 concentration (μg/m³)
        natural_infiltration_rate: Natural building infiltration (m³/h or ACH)
        erv_infiltration_rate: ERV mechanical ventilation (m³/h or ACH)
        filtration_rate: HVAC filtration rate (m³/h or ACH)
        deposition_rate: Natural deposition rate (m³/h or ACH)
        filter_efficiency: Filter efficiency (0-1)
        indoor_generation: Indoor particle generation rate (μg/h or μg/m³·h)

    Returns:
        Indoor PM2.5 concentration (μg/m³) as float

    Note:
        ERV air bypasses the HVAC filter, so it's treated as unfiltered outdoor air.
        All rates must use consistent units (either all m³/h or all ACH).
    """
    # Total outdoor air infiltration (both natural and ERV)
    total_infiltration_rate = natural_infiltration_rate + erv_infiltration_rate

    numerator = total_infiltration_rate * outdoor_pm25 + indoor_generation
    denominator = total_infiltration_rate + filtration_rate * filter_efficiency + deposition_rate

    result = numerator / denominator
    return float(result)


def calculate_indoor_outdoor_ratio_with_erv(
    natural_infiltration_rate: float,
    erv_infiltration_rate: float,
    filtration_rate: float,
    deposition_rate: float,
    filter_efficiency: float,
) -> float:
    """
    Calculate steady-state indoor/outdoor ratio with explicit ERV consideration.

    Args:
        natural_infiltration_rate: Natural building infiltration (ACH)
        erv_infiltration_rate: ERV mechanical ventilation (ACH)
        filtration_rate: HVAC filtration rate (ACH)
        deposition_rate: Natural deposition rate (ACH)
        filter_efficiency: Filter efficiency (0-1)

    Returns:
        Indoor/outdoor PM2.5 ratio
    """
    total_infiltration_rate = natural_infiltration_rate + erv_infiltration_rate

    return total_infiltration_rate / (total_infiltration_rate + filtration_rate * filter_efficiency + deposition_rate)


def solve_filter_efficiency_from_ratio_with_erv(
    io_ratio: float,
    natural_infiltration_rate: float,
    erv_infiltration_rate: float,
    filtration_rate: float,
    deposition_rate: float,
) -> float:
    """
    Solve for filter efficiency given indoor/outdoor ratio with explicit ERV.

    Inverse of the mass balance equation with ERV:
    η = ((Q_inf + Q_erv) - ratio * (Q_inf + Q_erv + Q_dep)) / (ratio * Q_filt)

    Args:
        io_ratio: Indoor/outdoor PM2.5 ratio
        natural_infiltration_rate: Natural building infiltration (ACH)
        erv_infiltration_rate: ERV mechanical ventilation (ACH)
        filtration_rate: HVAC filtration rate (ACH)
        deposition_rate: Natural deposition rate (ACH)

    Returns:
        Filter efficiency (0-1)
    """
    total_infiltration_rate = natural_infiltration_rate + erv_infiltration_rate

    numerator = total_infiltration_rate - io_ratio * (total_infiltration_rate + deposition_rate)
    denominator = io_ratio * filtration_rate

    if denominator <= 0:
        return 0.0

    efficiency = numerator / denominator
    return max(0.0, efficiency)  # Allow efficiency > 100% to indicate model issues
