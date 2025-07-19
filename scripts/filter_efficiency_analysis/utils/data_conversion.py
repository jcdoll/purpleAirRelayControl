"""
Data conversion utilities for filter efficiency analysis.

This module provides standardized functions for converting between different
air quality measurement units and validating data quality.
"""

import logging
from datetime import datetime
from typing import List, Optional, Tuple, Union

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


def aqi_to_pm25(aqi: Union[float, np.ndarray]) -> Union[float, np.ndarray]:
    """
    Convert Air Quality Index (AQI) to PM2.5 concentration in μg/m³.

    Based on EPA AQI calculation: https://www.airnow.gov/aqi/aqi-calculator/

    Args:
        aqi: Air Quality Index value(s)

    Returns:
        PM2.5 concentration(s) in μg/m³

    Raises:
        ValueError: If AQI contains negative values
    """
    # EPA AQI breakpoints for PM2.5
    # (AQI_low, AQI_high, PM25_low, PM25_high)
    breakpoints = [
        (0, 50, 0.0, 12.0),  # Good
        (50, 100, 12.0, 35.4),  # Moderate
        (100, 150, 35.4, 55.4),  # Unhealthy for Sensitive
        (150, 200, 55.4, 150.4),  # Unhealthy
        (200, 300, 150.4, 250.4),  # Very Unhealthy
        (300, 500, 250.4, 500.4),  # Hazardous
    ]

    def convert_single_aqi(aqi_val: float) -> float:
        """Convert a single AQI value."""
        if aqi_val < 0:
            raise ValueError(f"AQI cannot be negative: {aqi_val}")

        if aqi_val > 500:
            logger.warning(f"AQI value {aqi_val} exceeds typical range")
            return 500.4  # Maximum PM2.5 for AQI 500

        for aqi_low, aqi_high, pm25_low, pm25_high in breakpoints:
            if aqi_low <= aqi_val <= aqi_high:
                # Linear interpolation
                pm25 = pm25_low + (aqi_val - aqi_low) * (pm25_high - pm25_low) / (aqi_high - aqi_low)
                return round(pm25, 2)

        # Should not reach here if breakpoints are complete
        raise ValueError(f"AQI value {aqi_val} outside valid range")

    # Handle both scalar and array inputs
    if isinstance(aqi, (int, float)):
        return convert_single_aqi(float(aqi))
    elif isinstance(aqi, np.ndarray):
        return np.array(
            [convert_single_aqi(float(val)) if not np.isnan(val) else np.nan for val in aqi.flatten()]
        ).reshape(aqi.shape)
    else:
        # Try to convert to array and process
        aqi_array = np.asarray(aqi)
        return np.array(
            [convert_single_aqi(float(val)) if not np.isnan(val) else np.nan for val in aqi_array.flatten()]
        ).reshape(aqi_array.shape)


def pm25_to_aqi(pm25: Union[float, np.ndarray]) -> Union[int, np.ndarray]:
    """
    Convert PM2.5 concentration to Air Quality Index (AQI).

    Args:
        pm25: PM2.5 concentration(s) in μg/m³

    Returns:
        AQI value(s)
    """
    # EPA AQI breakpoints for PM2.5
    # (PM25_low, PM25_high, AQI_low, AQI_high)
    breakpoints = [
        (0.0, 12.0, 0, 50),  # Good
        (12.0, 35.4, 50, 100),  # Moderate
        (35.4, 55.4, 100, 150),  # Unhealthy for Sensitive
        (55.4, 150.4, 150, 200),  # Unhealthy
        (150.4, 250.4, 200, 300),  # Very Unhealthy
        (250.4, 350.4, 300, 400),  # Hazardous
        (350.4, 500.4, 400, 500),  # Hazardous
    ]

    def convert_single_pm25(pm25_val: float) -> int:
        """Convert a single PM2.5 value."""
        if pm25_val <= 0:
            return 0

        for pm25_low, pm25_high, aqi_low, aqi_high in breakpoints:
            if pm25_low <= pm25_val <= pm25_high:
                # Linear interpolation
                aqi = ((aqi_high - aqi_low) / (pm25_high - pm25_low)) * (pm25_val - pm25_low) + aqi_low
                return round(aqi)

        # Above highest breakpoint
        return 500

    # Handle both scalar and array inputs
    if isinstance(pm25, (int, float)):
        return convert_single_pm25(float(pm25))
    elif isinstance(pm25, np.ndarray):
        return np.array(
            [convert_single_pm25(float(val)) if not np.isnan(val) else np.nan for val in pm25.flatten()]
        ).reshape(pm25.shape)
    else:
        # Try to convert to array and process
        pm25_array = np.asarray(pm25)
        return np.array(
            [convert_single_pm25(float(val)) if not np.isnan(val) else np.nan for val in pm25_array.flatten()]
        ).reshape(pm25_array.shape)


def convert_aqi_dataframe_columns(
    df: pd.DataFrame,
    indoor_aqi_col: str = 'indoor_aqi',
    outdoor_aqi_col: str = 'outdoor_aqi',
    indoor_pm25_col: str = 'indoor_pm25',
    outdoor_pm25_col: str = 'outdoor_pm25',
) -> pd.DataFrame:
    """
    Convert AQI columns to PM2.5 concentrations in a DataFrame.

    Args:
        df: Input dataframe
        indoor_aqi_col: Name of indoor AQI column
        outdoor_aqi_col: Name of outdoor AQI column
        indoor_pm25_col: Name for new indoor PM2.5 column
        outdoor_pm25_col: Name for new outdoor PM2.5 column

    Returns:
        Dataframe with new PM2.5 columns
    """
    df = df.copy()

    # Convert indoor AQI
    if indoor_aqi_col in df.columns:
        df[indoor_pm25_col] = df[indoor_aqi_col].apply(lambda x: aqi_to_pm25(x) if pd.notna(x) and x >= 0 else np.nan)
        logger.info(f"Converted {indoor_aqi_col} to {indoor_pm25_col}")
    else:
        logger.warning(f"Column {indoor_aqi_col} not found in dataframe")

    # Convert outdoor AQI
    if outdoor_aqi_col in df.columns:
        df[outdoor_pm25_col] = df[outdoor_aqi_col].apply(lambda x: aqi_to_pm25(x) if pd.notna(x) and x >= 0 else np.nan)
        logger.info(f"Converted {outdoor_aqi_col} to {outdoor_pm25_col}")
    else:
        logger.warning(f"Column {outdoor_aqi_col} not found in dataframe")

    return df


def validate_measurement_data(
    indoor_pm25: Union[float, List[float], np.ndarray],
    outdoor_pm25: Union[float, List[float], np.ndarray],
    timestamp: Optional[Union[datetime, List[datetime]]] = None,
) -> Tuple[bool, str]:
    """
    Validate measurement data for quality and consistency.

    Args:
        indoor_pm25: Indoor PM2.5 concentration(s)
        outdoor_pm25: Outdoor PM2.5 concentration(s)
        timestamp: Optional timestamp(s)

    Returns:
        Tuple of (is_valid, error_message)
    """
    # Convert to arrays for easier handling
    indoor_array = np.asarray(indoor_pm25)
    outdoor_array = np.asarray(outdoor_pm25)

    # Check for negative values
    if np.any(indoor_array < 0):
        return False, "Indoor PM2.5 values cannot be negative"

    if np.any(outdoor_array < 0):
        return False, "Outdoor PM2.5 values cannot be negative"

    # Check for unreasonably high values (>1000 μg/m³)
    if np.any(indoor_array > 1000):
        return False, "Indoor PM2.5 values exceed reasonable range (>1000 μg/m³)"

    if np.any(outdoor_array > 1000):
        return False, "Outdoor PM2.5 values exceed reasonable range (>1000 μg/m³)"

    # Check for indoor > outdoor by unreasonable amounts (suggests measurement error)
    if indoor_array.shape == outdoor_array.shape:
        ratio = indoor_array / (outdoor_array + 0.1)  # Add small value to avoid division by zero
        if np.any(ratio > 5.0):  # Indoor should rarely be >5x outdoor
            return False, "Indoor PM2.5 significantly exceeds outdoor (ratio >5x)"

    # Check for too many zero or very low values
    indoor_low_count = np.sum(indoor_array < 1.0)
    if indoor_low_count / len(indoor_array) > 0.8:  # >80% very low values
        return False, "Too many very low indoor PM2.5 readings (<1 μg/m³)"

    return True, "Data validation passed"


def calculate_indoor_outdoor_ratio(
    indoor_pm25: Union[float, np.ndarray], outdoor_pm25: Union[float, np.ndarray], min_outdoor: float = 1.0
) -> Union[float, np.ndarray]:
    """
    Calculate indoor/outdoor PM2.5 ratio with safety checks.

    Args:
        indoor_pm25: Indoor PM2.5 concentration(s)
        outdoor_pm25: Outdoor PM2.5 concentration(s)
        min_outdoor: Minimum outdoor value to avoid division by zero

    Returns:
        Indoor/outdoor ratio(s)
    """
    # Ensure outdoor values are above minimum
    outdoor_safe = np.maximum(outdoor_pm25, min_outdoor)

    # Calculate ratio
    ratio = indoor_pm25 / outdoor_safe

    # Cap extreme ratios (likely measurement errors)
    ratio = np.minimum(ratio, 10.0)  # Max ratio of 10:1

    return ratio


def clean_timestamp_data(
    df: pd.DataFrame,
    timestamp_col: str = 'timestamp',
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
) -> pd.DataFrame:
    """
    Clean and validate timestamp data in a DataFrame.

    Args:
        df: Input dataframe
        timestamp_col: Name of timestamp column
        start_date: Optional start date for filtering
        end_date: Optional end date for filtering

    Returns:
        Cleaned dataframe with valid timestamps
    """
    df = df.copy()

    # Convert timestamp to datetime
    df[timestamp_col] = pd.to_datetime(df[timestamp_col], errors='coerce')

    # Remove rows with invalid timestamps
    initial_count = len(df)
    df = df.dropna(subset=[timestamp_col])

    if len(df) < initial_count:
        logger.warning(f"Removed {initial_count - len(df)} rows with invalid timestamps")

    # Filter by date range if provided
    if start_date is not None:
        mask = df[timestamp_col] >= start_date
        df = df.loc[mask].copy()

    if end_date is not None:
        mask = df[timestamp_col] <= end_date
        df = df.loc[mask].copy()

    # Remove duplicates (keep last)
    df = df.drop_duplicates(subset=[timestamp_col], keep='last').copy()

    return df


def is_nighttime(timestamp: datetime, night_start_hour: int = 22, night_end_hour: int = 8) -> bool:
    """
    Check if a timestamp falls during nighttime hours.

    Args:
        timestamp: Timestamp to check
        night_start_hour: Hour when night period starts (24-hour format)
        night_end_hour: Hour when night period ends (24-hour format)

    Returns:
        True if timestamp is during nighttime
    """
    hour = timestamp.hour

    if night_start_hour > night_end_hour:
        # Night period crosses midnight (e.g., 22:00 to 08:00)
        return hour >= night_start_hour or hour < night_end_hour
    else:
        # Night period within same day
        return night_start_hour <= hour < night_end_hour


def filter_nighttime_data(
    df: pd.DataFrame, timestamp_col: str = 'timestamp', night_start_hour: int = 22, night_end_hour: int = 8
) -> pd.DataFrame:
    """
    Filter DataFrame to include only nighttime measurements.

    Args:
        df: Input dataframe
        timestamp_col: Name of timestamp column
        night_start_hour: Hour when night period starts
        night_end_hour: Hour when night period ends

    Returns:
        Filtered dataframe with only nighttime data
    """
    df = df.copy()

    # Ensure timestamp column exists and is datetime
    if timestamp_col not in df.columns:
        raise ValueError(f"Column {timestamp_col} not found in dataframe")

    df[timestamp_col] = pd.to_datetime(df[timestamp_col])

    # Apply nighttime filter
    night_mask = df[timestamp_col].apply(lambda ts: is_nighttime(ts, night_start_hour, night_end_hour))

    night_data = df.loc[night_mask].copy()

    # Ensure we return a DataFrame
    assert isinstance(night_data, pd.DataFrame)

    logger.info(f"Filtered to {len(night_data)} nighttime measurements " f"from {len(df)} total measurements")

    return night_data
