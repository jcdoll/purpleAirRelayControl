"""
Test utilities for filter efficiency analysis.

This module provides essential test configuration and AQI conversion functions.
All test data generation now uses the canonical generator in utils/test_data_generator.py.
"""

from typing import Dict

import pandas as pd

# Import conversion functions from canonical module


def create_test_config(
    building_volume_m3: float = 765.0, filtration_rate_m3h: float = 2549.0, **overrides  # 3000 sq ft * 9 ft  # 1500 CFM
) -> Dict:
    """Create a test configuration dictionary."""
    config = {
        "building": {
            "area_sq_ft": 3000,
            "ceiling_height_ft": 9,
            "construction_type": "average",  # Will calculate infiltration_ach = 0.5
            "age_years": 20,  # Will calculate infiltration_ach = 0.5
        },
        "hvac": {
            "flow_rate_cfm": 1500,
            "deposition_rate_percent": 2,  # Updated to match config.yaml (0.02/hr for PM2.5)
        },
        "kalman_filter": {
            "day_confidence_multiplier": 0.5,
            "night_confidence_multiplier": 2.0,
            "min_indoor_pm25_for_learning": 10.0,
            "min_outdoor_pm25_for_learning": 30.0,
        },
        "analysis": {
            "night_start_hour": 22,
            "night_end_hour": 8,
            "min_data_points": 10,
            "outlier_threshold": 2.0,
            "min_r_squared": 0.5,
            "efficiency_alert_threshold": 0.7,
        },
        "google_sheets": {
            "spreadsheet_id": "test_spreadsheet_id",
            "data_sheet": "TestData",
            "results_sheet": "TestResults",
            "columns": {"timestamp": "A", "indoor_aqi": "B", "outdoor_aqi": "C"},
            "header_row": 1,
            "max_rows": 1000,
        },
        "schedule": {"analysis_window_days": 14, "frequency": "daily", "keep_results_days": 0},
        "alerts": {
            "min_confidence": 0.6,
            "efficiency_thresholds": {"excellent": 0.85, "good": 0.70, "declining": 0.50, "poor": 0.30},
        },
    }

    # Apply any overrides
    def deep_update(base_dict, update_dict):
        for key, value in update_dict.items():
            if isinstance(value, dict) and key in base_dict:
                deep_update(base_dict[key], value)
            else:
                base_dict[key] = value

    deep_update(config, overrides)
    return config


def save_test_data_to_csv(dataset: pd.DataFrame, filepath: str, include_pm25: bool = False) -> None:
    """Save test dataset to CSV file in format similar to Google Sheets export."""
    output_data = dataset[['timestamp', 'indoor_aqi', 'outdoor_aqi']].copy()

    if include_pm25:
        output_data['indoor_pm25'] = dataset['indoor_pm25']
        output_data['outdoor_pm25'] = dataset['outdoor_pm25']

    # Format timestamp as string (like Google Sheets)
    output_data['timestamp'] = [ts.strftime('%Y-%m-%d %H:%M:%S') for ts in output_data['timestamp']]

    output_data.to_csv(filepath, index=False)


if __name__ == "__main__":
    # Generate sample test datasets using canonical generator
    print("Use utils.test_data_generator.generate_standard_test_dataset() for test data generation")
    print("Legacy wrapper functions have been removed - use the canonical generator directly")
