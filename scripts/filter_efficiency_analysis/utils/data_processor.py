"""
Data processing utilities for filter efficiency estimation.

This module provides functions for filtering data by time periods and preparing data for analysis.
AQI conversion functions are imported from the dedicated data_conversion module.
"""

import numpy as np
import pandas as pd
from datetime import datetime, time
from typing import Tuple, Optional, Dict, Any
import logging
from utils.data_conversion import aqi_to_pm25

logger = logging.getLogger(__name__)


def pm25_to_aqi(pm25: float) -> float:
    """
    Convert PM2.5 concentration to AQI.
    
    Args:
        pm25: PM2.5 concentration in μg/m³
        
    Returns:
        AQI value
    """
    if pm25 < 0:
        raise ValueError(f"PM2.5 cannot be negative: {pm25}")
    
    # EPA AQI breakpoints for PM2.5 (reversed)
    breakpoints = [
        (0.0, 12.0, 0, 50),
        (12.1, 35.4, 51, 100),
        (35.5, 55.4, 101, 150),
        (55.5, 150.4, 151, 200),
        (150.5, 250.4, 201, 300),
        (250.5, 500.4, 301, 500)
    ]
    
    for pm25_low, pm25_high, aqi_low, aqi_high in breakpoints:
        if pm25_low <= pm25 <= pm25_high:
            # Linear interpolation
            aqi = aqi_low + (pm25 - pm25_low) * (aqi_high - aqi_low) / (pm25_high - pm25_low)
            return round(aqi, 0)
    
    # For values above 500.4 μg/m³
    if pm25 > 500.4:
        logger.warning(f"PM2.5 value {pm25} exceeds AQI scale")
        return 500
    
    raise ValueError(f"PM2.5 value {pm25} outside valid range")


class DataProcessor:
    """
    Main data processing class for filter efficiency estimation.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize data processor with configuration.
        
        Args:
            config: Configuration dictionary from config.yaml
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Calculate building parameters from config
        self.building_params = self._calculate_building_params()
        
    def _calculate_building_params(self) -> Dict[str, float]:
        """Calculate building parameters from configuration."""
        building_config = self.config['building']
        hvac_config = self.config['hvac']
        
        # Convert imperial to metric
        area_sq_ft = building_config['area_sq_ft']
        ceiling_height_ft = building_config['ceiling_height_ft']
        flow_rate_cfm = hvac_config['flow_rate_cfm']
        
        # Calculate volume: area × height × conversion factor
        volume_m3 = area_sq_ft * ceiling_height_ft * 0.0283168  # ft³ to m³
        
        # Calculate filtration rate: CFM × conversion factor
        filtration_rate_m3h = flow_rate_cfm * 1.69901  # CFM to m³/h
        
        # Calculate deposition rate as percentage of volume
        deposition_percent = hvac_config['deposition_rate_percent']
        deposition_rate_m3h = volume_m3 * (deposition_percent / 100.0)
        
        params = {
            'volume': volume_m3,
            'filtration_rate': filtration_rate_m3h,
            'deposition_rate': deposition_rate_m3h
        }
        
        self.logger.info(f"Building parameters: {params}")
        return params
        
    def filter_night_time_data(
        self, 
        df: pd.DataFrame, 
        timestamp_col: str = 'timestamp'
    ) -> pd.DataFrame:
        """
        Filter dataframe to include only night-time data (sealed environment).
        
        Args:
            df: Input dataframe with timestamp column
            timestamp_col: Name of timestamp column
            
        Returns:
            Filtered dataframe containing only night-time data
        """
        analysis_config = self.config['analysis']
        start_hour = analysis_config['night_start_hour']
        end_hour = analysis_config['night_end_hour']
        
        if timestamp_col not in df.columns:
            raise ValueError(f"Timestamp column '{timestamp_col}' not found in dataframe")
        
        # Ensure timestamp is datetime
        df = df.copy()
        df[timestamp_col] = pd.to_datetime(df[timestamp_col])
        
        # Extract hour from timestamp
        df['hour'] = df[timestamp_col].dt.hour
        
        # Filter for night-time hours
        if start_hour > end_hour:  # Spans midnight (e.g., 22:00 to 8:00)
            night_mask = (df['hour'] >= start_hour) | (df['hour'] <= end_hour)
        else:  # Same day (e.g., 2:00 to 6:00)
            night_mask = (df['hour'] >= start_hour) & (df['hour'] <= end_hour)
        
        night_data = df[night_mask].copy()
        if 'hour' in night_data.columns:
            night_data = night_data.drop(columns=['hour'])
        
        # Ensure we return a DataFrame
        assert isinstance(night_data, pd.DataFrame)
        
        self.logger.info(f"Filtered {len(night_data)} night-time records from {len(df)} total records")
        return night_data
    
    def convert_aqi_columns(
        self, 
        df: pd.DataFrame, 
        indoor_aqi_col: str = 'indoor_aqi',
        outdoor_aqi_col: str = 'outdoor_aqi'
    ) -> pd.DataFrame:
        """
        Convert AQI columns to PM2.5 concentrations.
        
        Args:
            df: Input dataframe
            indoor_aqi_col: Name of indoor AQI column
            outdoor_aqi_col: Name of outdoor AQI column
            
        Returns:
            Dataframe with new PM2.5 columns
        """
        df = df.copy()
        
        # Check if PM2.5 columns already exist - if so, skip conversion to avoid corruption
        if 'indoor_pm25' in df.columns and 'outdoor_pm25' in df.columns:
            self.logger.info("PM2.5 columns already exist - skipping AQI conversion")
            return df
        
        # Convert indoor AQI
        if indoor_aqi_col in df.columns:
            df['indoor_pm25'] = df[indoor_aqi_col].apply(
                lambda x: aqi_to_pm25(x) if pd.notna(x) and x >= 0 else np.nan
            )
            self.logger.info(f"Converted {indoor_aqi_col} to indoor_pm25")
        else:
            self.logger.warning(f"Column {indoor_aqi_col} not found in dataframe")
        
        # Convert outdoor AQI
        if outdoor_aqi_col in df.columns:
            df['outdoor_pm25'] = df[outdoor_aqi_col].apply(
                lambda x: aqi_to_pm25(x) if pd.notna(x) and x >= 0 else np.nan
            )
            self.logger.info(f"Converted {outdoor_aqi_col} to outdoor_pm25")
        else:
            self.logger.warning(f"Column {outdoor_aqi_col} not found in dataframe")
        
        return df
    
    def calculate_io_ratio(
        self, 
        df: pd.DataFrame, 
        indoor_col: str = 'indoor_pm25',
        outdoor_col: str = 'outdoor_pm25'
    ) -> pd.DataFrame:
        """
        Calculate indoor/outdoor PM2.5 ratio.
        
        Args:
            df: Input dataframe
            indoor_col: Name of indoor PM2.5 column
            outdoor_col: Name of outdoor PM2.5 column
            
        Returns:
            Dataframe with I/O ratio column added
        """
        df = df.copy()
        
        # Avoid division by zero
        mask = (df[outdoor_col] > 0) & pd.notna(df[outdoor_col]) & pd.notna(df[indoor_col])
        df.loc[mask, 'io_ratio'] = df.loc[mask, indoor_col] / df.loc[mask, outdoor_col]
        
        self.logger.info(f"Calculated I/O ratio for {mask.sum()} valid records")
        return df
    
    def detect_outliers(
        self, 
        df: pd.DataFrame, 
        columns: list,
        method: str = 'iqr'
    ) -> pd.DataFrame:
        """
        Detect and flag outliers in specified columns.
        
        Args:
            df: Input dataframe
            columns: List of columns to check for outliers
            method: Method for outlier detection ('iqr', 'zscore')
            
        Returns:
            Dataframe with outlier flags added
        """
        threshold = self.config['analysis']['outlier_threshold']
        df = df.copy()
        
        for col in columns:
            if col not in df.columns:
                continue
                
            if method == 'iqr':
                Q1 = df[col].quantile(0.25)
                Q3 = df[col].quantile(0.75)
                IQR = Q3 - Q1
                lower_bound = Q1 - threshold * IQR
                upper_bound = Q3 + threshold * IQR
                outlier_mask = (df[col] < lower_bound) | (df[col] > upper_bound)
            
            elif method == 'zscore':
                z_scores = np.abs((df[col] - df[col].mean()) / df[col].std())
                outlier_mask = z_scores > threshold
            
            else:
                raise ValueError(f"Unknown outlier detection method: {method}")
            
            df[f'{col}_outlier'] = outlier_mask
            outlier_count = outlier_mask.sum()
            self.logger.info(f"Detected {outlier_count} outliers in {col} using {method} method")
        
        return df
    
    def prepare_model_data(
        self, 
        df: pd.DataFrame,
        indoor_col: str = 'indoor_pm25',
        outdoor_col: str = 'outdoor_pm25',
        timestamp_col: str = 'timestamp'
    ) -> Dict[str, np.ndarray]:
        """
        Prepare data for model fitting.
        
        Args:
            df: Input dataframe
            indoor_col: Name of indoor PM2.5 column
            outdoor_col: Name of outdoor PM2.5 column
            timestamp_col: Name of timestamp column
            
        Returns:
            Dictionary containing arrays for model fitting
        """
        # Remove outliers and invalid data
        valid_mask = (
            pd.notna(df[indoor_col]) & 
            pd.notna(df[outdoor_col]) & 
            (df[indoor_col] >= 0) & 
            (df[outdoor_col] > 0)
        )
        
        clean_df = df[valid_mask].copy()
        
        if len(clean_df) == 0:
            raise ValueError("No valid data points after filtering")
        
        # Sort by timestamp  
        clean_df = clean_df.sort_values(by=timestamp_col)
        
        # Extract values as numpy arrays
        indoor_values = clean_df[indoor_col].values
        outdoor_values = clean_df[outdoor_col].values
        
        model_data = {
            'timestamps': clean_df[timestamp_col].values,
            'indoor_pm25': indoor_values.astype(float),
            'outdoor_pm25': outdoor_values.astype(float),
            'io_ratio': indoor_values.astype(float) / outdoor_values.astype(float),
            'n_points': len(clean_df)
        }
        
        self.logger.info(f"Prepared {model_data['n_points']} data points for model fitting")
        return model_data 