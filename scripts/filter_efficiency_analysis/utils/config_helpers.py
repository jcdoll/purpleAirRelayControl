"""
Configuration helper functions for filter efficiency analysis.

This module centralizes configuration loading, validation, and building parameter
calculations to eliminate duplication across the codebase.
"""

import logging
from pathlib import Path
from typing import Any, Dict, Optional

import yaml


def load_config(config_path: str) -> Dict[str, Any]:
    """
    Load configuration from YAML file with error handling.

    Args:
        config_path: Path to configuration file

    Returns:
        Configuration dictionary

    Raises:
        FileNotFoundError: If config file doesn't exist
        yaml.YAMLError: If config file is invalid YAML
    """
    config_file = Path(config_path)

    if not config_file.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    try:
        with open(config_file, 'r') as f:
            config = yaml.safe_load(f)

        if config is None:
            raise ValueError(f"Configuration file is empty: {config_path}")

        return config

    except yaml.YAMLError as e:
        raise yaml.YAMLError(f"Invalid YAML in configuration file {config_path}: {e}") from e


def validate_config(config: Dict[str, Any]) -> None:
    """
    Validate configuration structure and required fields.

    Args:
        config: Configuration dictionary

    Raises:
        ValueError: If configuration is invalid
    """
    required_sections = ['building', 'hvac', 'analysis']

    for section in required_sections:
        if section not in config:
            raise ValueError(f"Missing required configuration section: {section}")

    # Validate building parameters
    building = config['building']
    required_building = ['area_sq_ft', 'ceiling_height_ft']
    for param in required_building:
        if param not in building:
            raise ValueError(f"Missing required building parameter: {param}")
        if not isinstance(building[param], (int, float)) or building[param] <= 0:
            raise ValueError(f"Building parameter {param} must be a positive number")

    # Validate HVAC parameters
    hvac = config['hvac']
    required_hvac = ['flow_rate_cfm']
    for param in required_hvac:
        if param not in hvac:
            raise ValueError(f"Missing required HVAC parameter: {param}")
        if not isinstance(hvac[param], (int, float)) or hvac[param] <= 0:
            raise ValueError(f"HVAC parameter {param} must be a positive number")

    # Validate analysis parameters
    analysis = config['analysis']
    required_analysis = ['min_data_points', 'outlier_threshold']
    for param in required_analysis:
        if param not in analysis:
            raise ValueError(f"Missing required analysis parameter: {param}")


def calculate_building_parameters(config: Dict[str, Any]) -> Dict[str, float]:
    """
    Calculate derived building parameters from configuration.

    Args:
        config: Configuration dictionary

    Returns:
        Dictionary containing calculated building parameters
    """
    building = config['building']
    hvac = config['hvac']

    # Basic measurements
    area_sq_ft = building['area_sq_ft']
    ceiling_height_ft = building['ceiling_height_ft']
    flow_rate_cfm = hvac['flow_rate_cfm']

    # Volume calculations
    volume_cf = area_sq_ft * ceiling_height_ft
    volume_m3 = volume_cf * 0.0283168  # ft³ to m³

    # Flow rate conversions
    flow_rate_cfh = flow_rate_cfm * 60  # CFM to CFH
    flow_rate_m3h = flow_rate_cfm * 1.69901  # CFM to m³/h

    # Air change rates
    hvac_ach = flow_rate_cfh / volume_cf
    hvac_ach_m3 = flow_rate_m3h / volume_m3

    # Deposition rate
    deposition_percent = hvac.get('deposition_rate_percent', 2.0)  # Default 2%
    deposition_ach = deposition_percent / 100.0
    deposition_rate_m3h = volume_m3 * deposition_ach

    # Infiltration rate (if specified)
    infiltration_ach = building.get('infiltration_ach', None)
    if infiltration_ach is None:
        # Estimate based on construction
        construction_type = building.get('construction_type', 'average').lower()
        base_rates = {'tight': 0.3, 'average': 0.5, 'leaky': 0.8}
        infiltration_ach = base_rates.get(construction_type, 0.5)

        # Adjust for building age
        age_years = building.get('age_years', 20)
        age_factor = 1.0 + (age_years - 20) * 0.01
        age_factor = max(0.5, min(2.0, age_factor))
        infiltration_ach *= age_factor

    infiltration_rate_m3h = infiltration_ach * volume_m3

    return {
        # Volume
        'volume_cf': volume_cf,
        'volume_m3': volume_m3,
        # Flow rates
        'flow_rate_cfm': flow_rate_cfm,
        'flow_rate_cfh': flow_rate_cfh,
        'flow_rate_m3h': flow_rate_m3h,
        # Air change rates
        'hvac_ach': hvac_ach,
        'hvac_ach_m3': hvac_ach_m3,
        'infiltration_ach': infiltration_ach,
        'deposition_ach': deposition_ach,
        # Volumetric rates
        'infiltration_rate_m3h': infiltration_rate_m3h,
        'deposition_rate_m3h': deposition_rate_m3h,
        # Combined rates
        'total_ach': infiltration_ach + hvac_ach + deposition_ach,
        'time_constant_hours': 1.0 / (infiltration_ach + hvac_ach + deposition_ach),
    }


def setup_logging(
    config: Dict[str, Any], script_name: str = 'filter_analysis', log_level: Optional[str] = None
) -> logging.Logger:
    """
    Set up standardized logging configuration.

    Args:
        config: Configuration dictionary
        script_name: Name for the logger
        log_level: Override log level (DEBUG, INFO, WARNING, ERROR)

    Returns:
        Configured logger
    """
    # Determine log level
    if log_level is None:
        log_level = config.get('logging', {}).get('level', 'INFO')

    # Ensure log_level is a string and valid
    if not isinstance(log_level, str):
        log_level = 'INFO'

    # Configure logging
    logging.basicConfig(
        level=getattr(logging, log_level.upper(), logging.INFO),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        force=True,  # Override any existing configuration
    )

    # Create logger for script
    logger = logging.getLogger(script_name)

    # Log configuration info
    logger.info(f"Logging configured at {log_level} level")

    return logger


def get_default_config() -> Dict[str, Any]:
    """
    Get default configuration for testing and fallback purposes.

    Returns:
        Default configuration dictionary
    """
    return {
        'building': {'area_sq_ft': 3000, 'ceiling_height_ft': 9, 'construction_type': 'average', 'age_years': 20},
        'hvac': {'flow_rate_cfm': 1500, 'deposition_rate_percent': 2.0},
        'analysis': {
            'night_start_hour': 22,
            'night_end_hour': 8,
            'min_data_points': 10,
            'outlier_threshold': 2.0,
            'min_r_squared': 0.5,
            'efficiency_alert_threshold': 0.7,
        },
        'google_sheets': {
            'spreadsheet_id': '',
            'data_sheet': 'Data',
            'results_sheet': 'Results',
            'columns': {'timestamp': 'A', 'indoor_aqi': 'B', 'outdoor_aqi': 'C'},
            'header_row': 1,
            'max_rows': 1000,
        },
        'schedule': {'analysis_window_days': 14, 'frequency': 'daily', 'keep_results_days': 30},
        'alerts': {
            'min_confidence': 0.6,
            'efficiency_thresholds': {'excellent': 0.85, 'good': 0.70, 'declining': 0.50, 'poor': 0.30},
        },
        'logging': {'level': 'INFO'},
    }


def merge_config_with_defaults(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Merge user configuration with defaults, filling in missing values.

    Args:
        config: User configuration dictionary

    Returns:
        Complete configuration with defaults applied
    """
    defaults = get_default_config()

    def deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """Recursively merge dictionaries."""
        result = base.copy()

        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = deep_merge(result[key], value)
            else:
                result[key] = value

        return result

    return deep_merge(defaults, config)


def save_config(config: Dict[str, Any], config_path: str) -> None:
    """
    Save configuration to YAML file.

    Args:
        config: Configuration dictionary
        config_path: Path where to save the configuration
    """
    config_file = Path(config_path)
    config_file.parent.mkdir(parents=True, exist_ok=True)

    with open(config_file, 'w') as f:
        yaml.dump(config, f, indent=2, default_flow_style=False)
