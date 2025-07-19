#!/usr/bin/env python3
"""
Configuration helpers and shared calculation utilities.

This module provides shared functions for building parameter calculations
to ensure consistency between test data generation and analysis.
"""

from typing import Any, Dict


def calculate_infiltration_rate(config: Dict[str, Any]) -> float:
    """
    Calculate infiltration rate from building configuration.

    This is the single source of truth for infiltration calculation,
    used by both Kalman filter and test data generation.

    Args:
        config: Configuration dictionary with building parameters

    Returns:
        Infiltration rate in ACH (air changes per hour)
    """
    building = config.get('building', {})

    # If infiltration_ach is directly provided, use it
    if 'infiltration_ach' in building:
        return building['infiltration_ach']

    # Calculate infiltration based on actual building parameters
    # Get building characteristics
    construction_type = building.get('construction_type', 'average').lower()
    age_years = building.get('age_years', 20)

    # Base infiltration rates by construction type (ACH natural)
    # Based on ASHRAE research and LBNL data
    base_rates = {
        'tight': 0.25,  # Modern tight construction (post-2000)
        'average': 0.5,  # Average construction (1980s-2000s)
        'leaky': 0.8,  # Older leaky construction (pre-1980)
    }
    base_rate = base_rates.get(construction_type, 0.5)

    # Age adjustment factor
    # For buildings newer than 10 years, apply a "new construction bonus"
    # For buildings older than 20 years, apply age penalty
    if age_years <= 10:
        # Modern construction gets tighter values
        age_factor = max(0.7, 1.0 - (10 - age_years) * 0.03)  # Up to 30% tighter for new construction
    elif age_years <= 20:
        # No age adjustment for 10-20 year old buildings
        age_factor = 1.0
    else:
        # 1% increase per year after 20 years (older buildings get leakier)
        age_factor = 1.0 + (age_years - 20) * 0.01
        age_factor = min(2.0, age_factor)  # Cap at 2x base rate

    natural_infiltration_ach = base_rate * age_factor

    # Add ERV (Energy Recovery Ventilator) contribution if enabled
    erv_ach = _calculate_erv_infiltration(config)
    total_infiltration_ach = natural_infiltration_ach + erv_ach

    # Ensure reasonable bounds for total infiltration
    total_infiltration_ach = max(0.1, min(3.0, total_infiltration_ach))  # Higher max to account for ERV

    return total_infiltration_ach


def _calculate_erv_infiltration(config: Dict[str, Any]) -> float:
    """
    Calculate ERV (Energy Recovery Ventilator) contribution to infiltration rate.

    Args:
        config: Configuration dictionary with HVAC and building parameters

    Returns:
        ERV infiltration rate in ACH (air changes per hour)
    """
    hvac = config.get('hvac', {})
    building = config.get('building', {})

    # Check if ERV is enabled
    if not hvac.get('erv_enabled', False):
        return 0.0

    # Get ERV parameters
    erv_cfm = hvac.get('erv_flow_rate_cfm', 0.0)
    runtime_fraction = hvac.get('erv_runtime_fraction', 1.0)

    if erv_cfm <= 0:
        return 0.0

    # Calculate building volume in ft³
    area_sq_ft = building.get('area_sq_ft', 3000)
    ceiling_height_ft = building.get('ceiling_height_ft', 9)
    building_volume_ft3 = area_sq_ft * ceiling_height_ft

    # Convert ERV CFM to ACH
    # CFM = cubic feet per minute
    # ACH = air changes per hour
    # ACH = (CFM × 60 min/hr × runtime_fraction) / building_volume_ft³
    erv_ach = (erv_cfm * 60 * runtime_fraction) / building_volume_ft3

    return erv_ach


def calculate_building_volume_m3(config: Dict[str, Any]) -> float:
    """
    Calculate building volume in cubic meters from config.

    Args:
        config: Configuration dictionary with building parameters

    Returns:
        Building volume in cubic meters
    """
    building = config.get('building', {})

    # Get area in sq ft and height in ft
    area_sq_ft = building.get('area_sq_ft', 3000)  # Default
    height_ft = building.get('ceiling_height_ft', 9)  # Default

    # Calculate volume in cubic feet
    volume_ft3 = area_sq_ft * height_ft

    # Convert to cubic meters (1 ft³ = 0.0283168 m³)
    volume_m3 = volume_ft3 * 0.0283168

    return volume_m3


def get_building_parameters(config: Dict[str, Any]) -> Dict[str, float]:
    """
    Get complete building parameters for analysis.

    Returns a dictionary with all calculated building parameters
    that can be used by both test data generation and analysis.

    Args:
        config: Configuration dictionary

    Returns:
        Dictionary with building parameters including infiltration_ach, volume, etc.
    """
    infiltration_ach = calculate_infiltration_rate(config)
    volume_m3 = calculate_building_volume_m3(config)

    # Calculate other derived parameters
    hvac = config.get('hvac', {})
    flow_rate_cfm = hvac.get('flow_rate_cfm', 1500)

    # Convert CFM to m³/h (1 CFM = 1.699 m³/h)
    filtration_rate_m3h = flow_rate_cfm * 1.699
    filtration_rate_ach = filtration_rate_m3h / volume_m3

    # Deposition rate
    deposition_rate_percent = hvac.get('deposition_rate_percent', 2)
    deposition_rate_ach = deposition_rate_percent / 100.0

    return {
        'infiltration_ach': infiltration_ach,
        'volume_m3': volume_m3,
        'filtration_rate_ach': filtration_rate_ach,
        'filtration_rate_m3h': filtration_rate_m3h,
        'deposition_rate_ach': deposition_rate_ach,
    }
