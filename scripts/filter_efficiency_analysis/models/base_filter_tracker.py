#!/usr/bin/env python3
"""
Base class for filter efficiency tracking models.

This provides a common interface for different tracking approaches
(ratio-based, Kalman filter, etc.) to enable easy comparison and testing.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, Optional

import pandas as pd

from utils.mass_balance import calculate_steady_state_indoor_pm25


class BaseFilterTracker(ABC):
    """Abstract base class for filter efficiency tracking models."""

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the filter tracker.

        Args:
            config: Configuration dictionary containing building and HVAC parameters
        """
        self.config = config
        self.measurements = []
        self.initialized = False

    @abstractmethod
    def add_measurement(self, timestamp: datetime, indoor_pm25: float, outdoor_pm25: float) -> None:
        """
        Add a new measurement to the tracker.

        Args:
            timestamp: When the measurement was taken
            indoor_pm25: Indoor PM2.5 concentration
            outdoor_pm25: Outdoor PM2.5 concentration
        """
        pass

    @abstractmethod
    def get_current_efficiency(self) -> Optional[float]:
        """
        Get the current estimated filter efficiency.

        Returns:
            Current efficiency as a fraction (0.0-1.0), or None if not available
        """
        pass

    @abstractmethod
    def get_efficiency_trend(self, days_back: Optional[int] = None) -> Optional[float]:
        """
        Get the efficiency trend over a specified period.

        Args:
            days_back: Number of days to look back (None for all data)

        Returns:
            Trend in efficiency per month, or None if not available
        """
        pass

    @abstractmethod
    def get_summary_stats(self) -> Dict[str, Any]:
        """
        Get summary statistics about the filter performance.

        Returns:
            Dictionary containing various performance metrics
        """
        pass

    @abstractmethod
    def get_daily_data(self) -> pd.DataFrame:
        """
        Get daily aggregated data for plotting.

        Returns:
            DataFrame with columns: date, timestamp, efficiency, ratio, outdoor_pm25, indoor_pm25
        """
        pass

    def predict_indoor_pm25(self, outdoor_pm25: float, efficiency: Optional[float] = None) -> Optional[float]:
        """
        Predict indoor PM2.5 based on outdoor level and filter efficiency.

        Args:
            outdoor_pm25: Outdoor PM2.5 concentration
            efficiency: Filter efficiency (uses current if None)

        Returns:
            Predicted indoor PM2.5, or None if not possible
        """
        if efficiency is None:
            efficiency = self.get_current_efficiency()

        if efficiency is None:
            return None

        # Check if we have building parameters for accurate calculation
        if self._has_building_params():
            infiltration_rate = self._estimate_infiltration_rate()
            filtration_rate = self._calculate_filtration_rate()
            deposition_rate = self._calculate_deposition_rate()

            # Use canonical PHYSICS.md mass balance function
            return calculate_steady_state_indoor_pm25(
                outdoor_pm25=outdoor_pm25,
                infiltration_rate=infiltration_rate,
                filtration_rate=filtration_rate,
                deposition_rate=deposition_rate,
                filter_efficiency=efficiency,
                indoor_generation=0.0,
            )
        else:
            # Use canonical PHYSICS.md mass balance function with simplified parameters
            return calculate_steady_state_indoor_pm25(
                outdoor_pm25=outdoor_pm25,
                infiltration_rate=0.3,  # Assume 30% infiltration
                filtration_rate=0.7,  # Assume 70% goes through filter
                deposition_rate=0.02,  # Small deposition for PM2.5
                filter_efficiency=efficiency,
                indoor_generation=0.0,
            )

    def _has_building_params(self) -> bool:
        """Check if building parameters are available for calculations."""
        building_config = self.config.get('building', {})
        required_params = ['area_sq_ft', 'ceiling_height_ft']
        return all(param in building_config for param in required_params)

    def _calculate_building_volume(self) -> float:
        """Calculate building volume in cubic feet."""
        building = self.config['building']
        return building['area_sq_ft'] * building['ceiling_height_ft']

    def _calculate_filtration_rate(self) -> float:
        """Calculate air filtration rate in ACH (air changes per hour)."""
        hvac = self.config.get('hvac', {})
        if 'flow_rate_cfm' not in hvac:
            return 1.0  # Default assumption

        volume_cf = self._calculate_building_volume()
        flow_rate_cfh = hvac['flow_rate_cfm'] * 60  # Convert CFM to CFH
        return flow_rate_cfh / volume_cf

    def _calculate_deposition_rate(self) -> float:
        """Calculate particle deposition rate in ACH (air changes per hour)."""
        hvac = self.config.get('hvac', {})
        if 'deposition_rate_percent' not in hvac:
            return 0.02  # Default: 0.02/hr for PM2.5 particles

        # Convert percentage to ACH
        deposition_percent = hvac['deposition_rate_percent']
        return deposition_percent / 100.0

    def _estimate_infiltration_rate(self) -> float:
        """Estimate natural air infiltration rate in ACH based on building parameters."""
        building = self.config.get('building', {})

        # If infiltration_ach is directly provided, use it
        if 'infiltration_ach' in building:
            return building['infiltration_ach']

        # Calculate infiltration based on actual building parameters
        # Get building characteristics
        construction_type = building.get('construction_type', 'tight').lower()  # Default to tight for modern homes
        age_years = building.get('age_years', 4)  # Default to recent construction
        
        # Base infiltration rates by construction type (ACH natural)
        # Based on ASHRAE research and LBNL data
        base_rates = {
            'tight': 0.25,      # Modern tight construction (post-2000)
            'average': 0.5,     # Average construction (1980s-2000s) 
            'leaky': 0.8        # Older leaky construction (pre-1980)
        }
        base_rate = base_rates.get(construction_type, 0.25)
        
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

        # Climate adjustment (optional - can be refined later)
        # Different climates may have different typical construction practices
        
        calculated_ach = base_rate * age_factor
        
        # Ensure reasonable bounds
        calculated_ach = max(0.1, min(1.5, calculated_ach))
        
        return calculated_ach

    def _calculate_building_volume_m3(self) -> float:
        """Calculate building volume in cubic meters from area and height."""
        building = self.config.get('building', {})
        
        # Get area in sq ft and height in ft
        area_sq_ft = building.get('area_sq_ft', 0)
        height_ft = building.get('ceiling_height_ft', 0)
        
        if area_sq_ft <= 0 or height_ft <= 0:
            # Fallback calculation using legacy method
            return self._calculate_building_volume() * 0.0283  # ft³ to m³
        
        # Calculate volume in cubic feet
        volume_ft3 = area_sq_ft * height_ft
        
        # Convert to cubic meters (1 ft³ = 0.0283168 m³)
        volume_m3 = volume_ft3 * 0.0283168
        
        return volume_m3

    def _calculate_infiltration_rate_m3h(self) -> float:
        """Calculate infiltration rate in m³/h from ACH and building volume."""
        infiltration_ach = self._estimate_infiltration_rate()
        volume_m3 = self._calculate_building_volume_m3()
        
        # ACH × Volume = m³/h
        return infiltration_ach * volume_m3

    def get_model_type(self) -> str:
        """Get a string identifier for the model type."""
        return self.__class__.__name__

    def get_measurement_count(self) -> int:
        """Get the total number of measurements."""
        return len(self.measurements)

    def get_date_range(self) -> tuple[Optional[datetime], Optional[datetime]]:
        """Get the date range of measurements."""
        if not self.measurements:
            return None, None

        timestamps = [m['timestamp'] for m in self.measurements]
        return min(timestamps), max(timestamps)
