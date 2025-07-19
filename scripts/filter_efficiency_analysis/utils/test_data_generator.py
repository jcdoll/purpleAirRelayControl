"""
Canonical test data generator for filter efficiency analysis.

This module provides the single source of truth for all test data generation
to ensure consistency across test files and eliminate code duplication.
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from utils.data_conversion import pm25_to_aqi
from utils.mass_balance import calculate_steady_state_indoor_pm25


class FilterTestDataGenerator:
    """Canonical test data generator for all filter efficiency tests."""

    def __init__(self, random_seed: int = 42, config: Optional[Dict[str, Any]] = None):
        """Initialize with consistent random seed for reproducibility."""
        self.random_seed = random_seed
        np.random.seed(random_seed)

        # Use provided config or create default
        if config is None:
            config = {
                'building': {
                    'area_sq_ft': 3000,
                    'ceiling_height_ft': 9,
                    'construction_type': 'average',
                    'age_years': 20,
                },
                'hvac': {
                    'flow_rate_cfm': 1500,
                    'deposition_rate_percent': 2,
                },
            }

        self.config = config

        # Calculate building parameters using shared functions
        from utils.config_helpers import get_building_parameters

        params = get_building_parameters(config)

        # Standard building parameters used across all tests
        self.default_building = {
            'area_sq_ft': config['building']['area_sq_ft'],
            'ceiling_height_ft': config['building']['ceiling_height_ft'],
            'flow_rate_cfm': config['hvac']['flow_rate_cfm'],
            'volume_m3': params['volume_m3'],
            'hvac_m3h': params['filtration_rate_m3h'],
            'infiltration_ach': params['infiltration_ach'],  # Now calculated from config
            'deposition_ach': params['deposition_rate_ach'],
        }

    def generate_outdoor_pm25_series(
        self, start_date: datetime, end_date: datetime, pattern: str = "realistic", base_level: float = 15.0, **kwargs
    ) -> pd.DataFrame:
        """
        Generate outdoor PM2.5 time series with various patterns.

        Args:
            start_date: Start datetime
            end_date: End datetime
            pattern: Type of pattern ('realistic', 'step', 'constant', 'sinusoidal')
            base_level: Base PM2.5 level
            **kwargs: Additional pattern-specific parameters

        Returns:
            DataFrame with timestamp and outdoor_pm25 columns
        """
        # Create 5-minute interval time series (realistic sensor frequency)
        times = pd.date_range(start_date, end_date, freq='5min')
        len(times)

        if pattern == "realistic":
            return self._generate_realistic_outdoor(times, base_level, **kwargs)
        elif pattern == "step":
            return self._generate_step_outdoor(times, base_level, **kwargs)
        elif pattern == "constant":
            return self._generate_constant_outdoor(times, base_level, **kwargs)
        elif pattern == "sinusoidal":
            return self._generate_sinusoidal_outdoor(times, base_level, **kwargs)
        else:
            raise ValueError(f"Unknown pattern: {pattern}")

    def _generate_realistic_outdoor(
        self,
        times: pd.DatetimeIndex,
        base_level: float,
        daily_variation: float = 8.0,  # Increased from 5.0 for more variation
        weather_events: bool = True,
        **kwargs,
    ) -> pd.DataFrame:
        """Generate realistic outdoor PM2.5 with diurnal, weekly, and weather patterns."""
        n_points = len(times)

        # Base diurnal pattern (higher during day due to traffic, activity)
        hours = np.array([t.hour for t in times])
        diurnal_pattern = 1.0 + 0.4 * np.sin(2 * np.pi * (hours - 6) / 24)  # Increased amplitude

        # Weekly pattern (higher on weekdays)
        weekdays = np.array([t.weekday() for t in times])  # 0=Monday, 6=Sunday
        weekly_pattern = np.where(weekdays < 5, 1.2, 0.8)  # Increased contrast

        # Seasonal pattern (if data spans multiple months)
        day_of_year = np.array([t.timetuple().tm_yday for t in times])
        seasonal_pattern = 1.0 + 0.2 * np.sin(2 * np.pi * (day_of_year - 80) / 365)

        # Combine patterns
        base_pattern = base_level * diurnal_pattern * weekly_pattern * seasonal_pattern

        # Add daily random variation
        daily_noise = np.random.normal(0, daily_variation, n_points)

        # Add weather events (high pollution episodes) - longer and more frequent
        if weather_events:
            n_events = max(2, int(len(times) / (24 * 4)))  # ~1 event every 4 days instead of weekly
            for _ in range(n_events):
                event_start = np.random.randint(0, max(1, n_points - 96))  # Ensure room for longer events
                event_duration = np.random.randint(48, 96)  # 2-4 days instead of 12-48 hours
                event_magnitude = np.random.uniform(30, 80)  # Higher magnitude: 30-80 instead of 20-50

                # Gaussian decay from event center with longer tail
                event_times = np.arange(event_start, min(event_start + event_duration, n_points))
                event_center = event_start + event_duration // 2
                event_decay = np.exp(-(((event_times - event_center) / (event_duration / 3)) ** 2))  # Broader spread

                daily_noise[event_times] += event_magnitude * event_decay

        # Combine all components
        outdoor_pm25 = np.maximum(2.0, base_pattern + daily_noise)  # Higher minimum

        # Add measurement noise (±5% instead of 15% for modern sensors)
        measurement_noise = np.random.normal(1.0, 0.05, n_points)  # Reduced from 0.15
        outdoor_pm25 *= measurement_noise

        # Ensure non-negative with higher minimum
        outdoor_pm25 = np.maximum(1.0, outdoor_pm25)

        return pd.DataFrame({'timestamp': times, 'outdoor_pm25': outdoor_pm25})

    def _generate_step_outdoor(
        self,
        times: pd.DatetimeIndex,
        base_level: float,
        step_levels: Optional[List[float]] = None,
        hours_per_step: int = 6,
        **kwargs,
    ) -> pd.DataFrame:
        """Generate step pattern outdoor PM2.5."""
        if step_levels is None:
            step_levels = [base_level * 0.5, base_level * 2.0, base_level * 0.5]  # low-high-low

        n_points = len(times)
        outdoor_pm25 = np.zeros(n_points)

        hours_elapsed = 0
        for i, _ in enumerate(times):
            step_index = min(hours_elapsed // hours_per_step, len(step_levels) - 1)
            outdoor_pm25[i] = step_levels[step_index]
            hours_elapsed += 1

        return pd.DataFrame({'timestamp': times, 'outdoor_pm25': outdoor_pm25})

    def _generate_constant_outdoor(
        self, times: pd.DatetimeIndex, base_level: float, noise_level: float = 0.1, **kwargs
    ) -> pd.DataFrame:
        """Generate constant outdoor PM2.5 with optional noise."""
        n_points = len(times)

        if noise_level > 0:
            noise = np.random.normal(1.0, noise_level, n_points)
            outdoor_pm25 = base_level * noise
        else:
            outdoor_pm25 = np.full(n_points, base_level)

        outdoor_pm25 = np.maximum(0.1, outdoor_pm25)

        return pd.DataFrame({'timestamp': times, 'outdoor_pm25': outdoor_pm25})

    def _generate_sinusoidal_outdoor(
        self, times: pd.DatetimeIndex, base_level: float, amplitude: float = 10.0, period_days: float = 7.0, **kwargs
    ) -> pd.DataFrame:
        """Generate sinusoidal outdoor PM2.5."""
        # Calculate hours from start
        start_time = times[0]
        hours_from_start = [(t - start_time).total_seconds() / 3600 for t in times]

        # Generate sinusoidal pattern
        outdoor_pm25 = base_level + amplitude * np.sin(2 * np.pi * np.array(hours_from_start) / (period_days * 24))
        outdoor_pm25 = np.maximum(0.1, outdoor_pm25)

        return pd.DataFrame({'timestamp': times, 'outdoor_pm25': outdoor_pm25})

    def calculate_indoor_pm25_series(
        self,
        outdoor_pm25: np.ndarray,
        filter_efficiency: float,
        building_params: Optional[Dict] = None,
        temporal_dynamics: bool = False,
        previous_indoor: Optional[float] = None,
        dt_hours: float = 1.0,
    ) -> np.ndarray:
        """
        Calculate indoor PM2.5 series using canonical mass balance.

        Args:
            outdoor_pm25: Array of outdoor PM2.5 values
            filter_efficiency: Filter efficiency (0-1)
            building_params: Building parameters (uses defaults if None)
            temporal_dynamics: Whether to include temporal dynamics
            previous_indoor: Previous indoor concentration for dynamics
            dt_hours: Time step in hours

        Returns:
            Array of indoor PM2.5 values
        """
        if building_params is None:
            building_params = self.default_building.copy()

        # Convert to volumetric rates
        infiltration_rate = building_params['infiltration_ach'] * building_params['volume_m3']
        deposition_rate = building_params['deposition_ach'] * building_params['volume_m3']

        if temporal_dynamics and previous_indoor is not None:
            # Include exponential approach to steady state
            total_ach = (
                building_params['infiltration_ach']
                + building_params['hvac_m3h'] / building_params['volume_m3']
                + building_params['deposition_ach']
            )

            indoor_pm25 = np.zeros_like(outdoor_pm25)
            current_indoor = previous_indoor

            for i, outdoor_val in enumerate(outdoor_pm25):
                # Calculate steady state
                steady_state = calculate_steady_state_indoor_pm25(
                    outdoor_pm25=outdoor_val,
                    infiltration_rate=infiltration_rate,
                    filtration_rate=building_params['hvac_m3h'],
                    deposition_rate=deposition_rate,
                    filter_efficiency=filter_efficiency,
                    indoor_generation=0.0,
                )

                # Exponential approach
                alpha = 1 - np.exp(-total_ach * dt_hours)
                current_indoor = current_indoor + alpha * (steady_state - current_indoor)
                indoor_pm25[i] = current_indoor
        else:
            # Steady state calculation for each point
            indoor_pm25 = np.array(
                [
                    calculate_steady_state_indoor_pm25(
                        outdoor_pm25=outdoor_val,
                        infiltration_rate=infiltration_rate,
                        filtration_rate=building_params['hvac_m3h'],
                        deposition_rate=deposition_rate,
                        filter_efficiency=filter_efficiency,
                        indoor_generation=0.0,
                    )
                    for outdoor_val in outdoor_pm25
                ]
            )

        return indoor_pm25

    def add_measurement_noise(
        self,
        values: np.ndarray,
        noise_type: str = "gaussian",
        noise_level: float = 0.05,  # Reduced from 0.15 to 0.05 for better signal quality
    ) -> np.ndarray:
        """Add measurement noise to values."""
        if noise_type == "gaussian":
            noise = np.random.normal(1.0, noise_level, len(values))
            return values * noise
        elif noise_type == "uniform":
            noise = np.random.uniform(1 - noise_level, 1 + noise_level, len(values))
            return values * noise
        else:
            raise ValueError(f"Unknown noise type: {noise_type}")

    def generate_complete_dataset(
        self,
        scenario: str,
        days: int = 14,
        start_date: Optional[datetime] = None,
        building_params: Optional[Dict] = None,
        custom_params: Optional[Dict] = None,
    ) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Generate a complete test dataset for a given scenario.

        Args:
            scenario: Scenario name or type
            days: Number of days of data
            start_date: Start date (defaults to 2024-01-01)
            building_params: Building parameters (uses defaults if None)
            custom_params: Custom scenario parameters

        Returns:
            Tuple of (dataset DataFrame, true parameters dict)
        """
        if start_date is None:
            # Use recent dates for realistic mock data (ending today)
            end_date = datetime.now().replace(hour=23, minute=59, second=59, microsecond=0)
            start_date = end_date - timedelta(days=days)
        else:
            end_date = start_date + timedelta(days=days)

        if building_params is None:
            building_params = self.default_building.copy()

        # Define built-in scenarios
        scenarios = {
            "good_filter": {
                "filter_efficiency": 0.85,
                "infiltration_ach": 0.6,
                "outdoor_pattern": "realistic",
                "outdoor_base": 30.0,  # Increased from 15.0 for better signal
                "description": "High-efficiency filter in well-sealed building",
            },
            "degraded_filter": {
                "filter_efficiency": 0.55,
                "infiltration_ach": 0.8,
                "outdoor_pattern": "realistic",
                "outdoor_base": 35.0,  # Increased from 18.0 for better signal
                "description": "Partially degraded filter in average building",
            },
            "poor_filter": {
                "filter_efficiency": 0.25,
                "infiltration_ach": 1.2,
                "outdoor_pattern": "realistic",
                "outdoor_base": 40.0,  # Increased from 20.0 for better signal
                "description": "Poor filter in leaky building",
            },
            "hepa_filter": {
                "filter_efficiency": 0.97,
                "infiltration_ach": 0.4,
                "outdoor_pattern": "realistic",
                "outdoor_base": 25.0,  # Increased from 12.0 for better signal
                "description": "HEPA filter in very tight building",
            },
            "step_test": {
                "filter_efficiency": 0.75,
                "infiltration_ach": 0.5,
                "outdoor_pattern": "step",
                "outdoor_base": 25.0,
                "step_levels": [10.0, 40.0, 10.0],
                "hours_per_step": 6,
                "description": "Clean step test for validation",
            },
            "constant_test": {
                "filter_efficiency": 0.70,
                "infiltration_ach": 0.5,
                "outdoor_pattern": "constant",
                "outdoor_base": 20.0,
                "description": "Constant outdoor conditions",
            },
        }

        if scenario in scenarios:
            params = scenarios[scenario].copy()
        else:
            # Custom scenario
            params = custom_params or {
                "filter_efficiency": 0.75,
                "infiltration_ach": 0.5,
                "outdoor_pattern": "realistic",
                "outdoor_base": 15.0,
                "description": f"Custom scenario: {scenario}",
            }

        # Allow building_params to override scenario parameters
        if 'filter_efficiency' in building_params:
            params['filter_efficiency'] = building_params['filter_efficiency']

        # For scenarios, allow scenario-specific infiltration rates to override config
        # This preserves scenario testing while maintaining config consistency for normal use
        if scenario in scenarios and 'infiltration_ach' in params:
            building_params['infiltration_ach'] = params['infiltration_ach']
        # Otherwise, building_params contains the correctly calculated infiltration_ach from config

        # Generate outdoor data
        outdoor_data = self.generate_outdoor_pm25_series(
            start_date=start_date,
            end_date=end_date,
            pattern=params['outdoor_pattern'],
            base_level=params['outdoor_base'],
            **{k: v for k, v in params.items() if k.startswith('step_') or k.startswith('hours_')},
        )

        # Calculate indoor concentrations
        indoor_pm25 = self.calculate_indoor_pm25_series(
            outdoor_pm25=np.array(outdoor_data['outdoor_pm25'].tolist()),
            filter_efficiency=params['filter_efficiency'],
            building_params=building_params,
            temporal_dynamics=params.get('temporal_dynamics', False),
        )

        # Add measurement noise
        indoor_pm25_noisy = self.add_measurement_noise(np.array(indoor_pm25))
        outdoor_pm25_noisy = self.add_measurement_noise(np.array(outdoor_data['outdoor_pm25'].tolist()))

        # Create complete dataset
        dataset = pd.DataFrame(
            {
                'timestamp': outdoor_data['timestamp'],
                'outdoor_pm25': outdoor_pm25_noisy,
                'indoor_pm25': indoor_pm25_noisy,
                'outdoor_aqi': [pm25_to_aqi(pm) for pm in outdoor_pm25_noisy],
                'indoor_aqi': [pm25_to_aqi(pm) for pm in indoor_pm25_noisy],
            }
        )

        # Calculate true parameters
        infiltration_rate_m3h = building_params['infiltration_ach'] * building_params['volume_m3']
        deposition_rate_m3h = building_params['deposition_ach'] * building_params['volume_m3']

        true_params = {
            "filter_efficiency": params["filter_efficiency"],
            "infiltration_rate_m3h": infiltration_rate_m3h,
            "infiltration_ach": params["infiltration_ach"],
            "building_volume_m3": building_params['volume_m3'],
            "filtration_rate_m3h": building_params['hvac_m3h'],
            "deposition_rate_m3h": deposition_rate_m3h,
            "scenario": scenario,
            "description": params["description"],
        }

        return dataset, true_params


# Convenience functions for direct use
def create_test_data_generator(
    random_seed: int = 42, config: Optional[Dict[str, Any]] = None
) -> FilterTestDataGenerator:
    """Create a FilterTestDataGenerator instance."""
    return FilterTestDataGenerator(random_seed, config)


def generate_standard_test_dataset(
    scenario: str, days: int = 14, random_seed: int = 42, config: Optional[Dict[str, Any]] = None
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """Generate a standard test dataset using the canonical generator."""
    generator = FilterTestDataGenerator(random_seed, config)
    return generator.generate_complete_dataset(scenario, days)
