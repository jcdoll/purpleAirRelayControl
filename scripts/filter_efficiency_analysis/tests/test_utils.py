"""
Test utilities for generating mock data and testing filter efficiency analysis.
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, Tuple, Optional
import yaml
import os


def pm25_to_aqi(pm25: float) -> float:
    """Convert PM2.5 concentration to AQI using EPA breakpoints."""
    breakpoints = [
        (0.0, 12.0, 0, 50),      # Good
        (12.1, 35.4, 51, 100),   # Moderate  
        (35.5, 55.4, 101, 150),  # Unhealthy for Sensitive
        (55.5, 150.4, 151, 200), # Unhealthy
        (150.5, 250.4, 201, 300),# Very Unhealthy
        (250.5, 350.4, 301, 400),# Hazardous
        (350.5, 500.4, 401, 500) # Hazardous
    ]
    
    if pm25 <= 0:
        return 0
    
    for c_lo, c_hi, i_lo, i_hi in breakpoints:
        if c_lo <= pm25 <= c_hi:
            return round(((i_hi - i_lo) / (c_hi - c_lo)) * (pm25 - c_lo) + i_lo)
    
    # Above highest breakpoint
    return 500


def generate_realistic_outdoor_pm25(
    start_date: datetime,
    end_date: datetime,
    base_level: float = 15.0,
    daily_variation: float = 5.0,
    weather_events: bool = True,
    random_seed: int = 42
) -> pd.DataFrame:
    """Generate realistic outdoor PM2.5 time series data."""
    np.random.seed(random_seed)
    
    # Create hourly time series
    times = pd.date_range(start_date, end_date, freq='H')
    n_points = len(times)
    
    # Base diurnal pattern (higher during day due to traffic, activity)
    hours = np.array([t.hour for t in times])
    diurnal_pattern = 1.0 + 0.3 * np.sin(2 * np.pi * (hours - 6) / 24)
    
    # Weekly pattern (higher on weekdays)
    weekdays = np.array([t.weekday() for t in times])  # 0=Monday, 6=Sunday
    weekly_pattern = np.where(weekdays < 5, 1.1, 0.9)  # Higher on weekdays
    
    # Seasonal pattern (if data spans multiple months)
    day_of_year = np.array([t.timetuple().tm_yday for t in times])
    seasonal_pattern = 1.0 + 0.2 * np.sin(2 * np.pi * (day_of_year - 80) / 365)
    
    # Combine patterns
    base_pattern = base_level * diurnal_pattern * weekly_pattern * seasonal_pattern
    
    # Add daily random variation
    daily_noise = np.random.normal(0, daily_variation, n_points)
    
    # Add weather events (high pollution episodes)
    if weather_events:
        # Create 2-3 high pollution events
        n_events = max(1, int(len(times) / (24 * 7)))  # ~1 event per week
        for _ in range(n_events):
            event_start = np.random.randint(0, n_points - 48)
            event_duration = np.random.randint(12, 48)  # 12-48 hours
            event_magnitude = np.random.uniform(20, 50)  # Additional PM2.5
            
            # Gaussian decay from event center
            event_times = np.arange(event_start, min(event_start + event_duration, n_points))
            event_center = event_start + event_duration // 2
            event_decay = np.exp(-((event_times - event_center) / (event_duration / 4))**2)
            
            daily_noise[event_times] += event_magnitude * event_decay
    
    # Combine all components
    outdoor_pm25 = np.maximum(1.0, base_pattern + daily_noise)
    
    # Add measurement noise (±15% typical for PM2.5 sensors)
    measurement_noise = np.random.normal(1.0, 0.15, n_points)
    outdoor_pm25 *= measurement_noise
    
    # Ensure non-negative
    outdoor_pm25 = np.maximum(0.1, outdoor_pm25)
    
    return pd.DataFrame({
        'timestamp': times,
        'outdoor_pm25': outdoor_pm25,
        'outdoor_aqi': [pm25_to_aqi(pm) for pm in outdoor_pm25]
    })


def calculate_indoor_pm25(
    outdoor_pm25: np.ndarray,
    filter_efficiency: float,
    infiltration_rate_m3h: float,
    filtration_rate_m3h: float,
    building_volume_m3: float,
    deposition_rate_m3h: float = None,
    indoor_generation: float = 0.0,
    random_seed: int = 42
) -> np.ndarray:
    """Calculate indoor PM2.5 concentrations using mass balance model."""
    np.random.seed(random_seed)
    
    if deposition_rate_m3h is None:
        # Default: 10% of building volume per hour
        deposition_rate_m3h = building_volume_m3 * 0.1
    
    # Steady-state mass balance model
    # C_in = (Q_inf * C_out + Q_gen) / (Q_inf + η * Q_filt + Q_dep)
    numerator = infiltration_rate_m3h * outdoor_pm25 + indoor_generation
    denominator = (infiltration_rate_m3h + 
                   filter_efficiency * filtration_rate_m3h + 
                   deposition_rate_m3h)
    
    indoor_pm25 = numerator / denominator
    
    # Add measurement noise (±15% typical for PM2.5 sensors)
    measurement_noise = np.random.normal(1.0, 0.15, len(outdoor_pm25))
    indoor_pm25 *= measurement_noise
    
    # Ensure non-negative
    indoor_pm25 = np.maximum(0.1, indoor_pm25)
    
    return indoor_pm25


def generate_test_dataset(
    scenario: str = "good_filter",
    days: int = 14,
    start_date: Optional[datetime] = None,
    building_params: Optional[Dict] = None,
    random_seed: int = 42
) -> Tuple[pd.DataFrame, Dict]:
    """Generate a complete test dataset with known parameters."""
    if start_date is None:
        start_date = datetime(2024, 1, 1)
    end_date = start_date + timedelta(days=days)
    
    # Default building parameters (3000 sq ft house)
    if building_params is None:
        area_sq_ft = 3000
        ceiling_height_ft = 9
        flow_rate_cfm = 1500
        
        # Convert to metric
        building_volume_m3 = area_sq_ft * ceiling_height_ft * 0.0283168
        filtration_rate_m3h = flow_rate_cfm * 1.69901
        deposition_rate_m3h = building_volume_m3 * 0.1
    else:
        building_volume_m3 = building_params['volume_m3']
        filtration_rate_m3h = building_params['filtration_rate_m3h']
        deposition_rate_m3h = building_params.get('deposition_rate_m3h', 
                                                 building_volume_m3 * 0.1)
    
    # Define scenario parameters
    scenarios = {
        "good_filter": {
            "filter_efficiency": 0.85,
            "infiltration_ach": 0.6,
            "outdoor_base": 15.0,
            "description": "New high-efficiency filter in well-sealed building"
        },
        "degraded_filter": {
            "filter_efficiency": 0.55,
            "infiltration_ach": 0.8,
            "outdoor_base": 18.0,
            "description": "Partially clogged filter in average building"
        },
        "poor_filter": {
            "filter_efficiency": 0.25,
            "infiltration_ach": 1.2,
            "outdoor_base": 20.0,
            "description": "Old basic filter in leaky building"
        },
        "hepa_filter": {
            "filter_efficiency": 0.97,
            "infiltration_ach": 0.4,
            "outdoor_base": 12.0,
            "description": "HEPA filter in very tight building"
        },
        "high_pollution": {
            "filter_efficiency": 0.75,
            "infiltration_ach": 0.7,
            "outdoor_base": 35.0,
            "description": "Good filter during high pollution period"
        }
    }
    
    if scenario not in scenarios:
        raise ValueError(f"Unknown scenario: {scenario}. Available: {list(scenarios.keys())}")
    
    params = scenarios[scenario]
    
    # Convert infiltration rate to m³/h
    infiltration_rate_m3h = params["infiltration_ach"] * building_volume_m3
    
    # Generate outdoor data
    outdoor_data = generate_realistic_outdoor_pm25(
        start_date=start_date,
        end_date=end_date,
        base_level=params["outdoor_base"],
        daily_variation=params["outdoor_base"] * 0.3,
        weather_events=True,
        random_seed=random_seed
    )
    
    # Calculate indoor concentrations
    indoor_pm25 = calculate_indoor_pm25(
        outdoor_pm25=outdoor_data['outdoor_pm25'].values,
        filter_efficiency=params["filter_efficiency"],
        infiltration_rate_m3h=infiltration_rate_m3h,
        filtration_rate_m3h=filtration_rate_m3h,
        building_volume_m3=building_volume_m3,
        deposition_rate_m3h=deposition_rate_m3h,
        random_seed=random_seed
    )
    
    # Create complete dataset
    dataset = outdoor_data.copy()
    dataset['indoor_pm25'] = indoor_pm25
    dataset['indoor_aqi'] = [pm25_to_aqi(pm) for pm in indoor_pm25]
    
    # True parameters for validation
    true_params = {
        "filter_efficiency": params["filter_efficiency"],
        "infiltration_rate_m3h": infiltration_rate_m3h,
        "infiltration_ach": params["infiltration_ach"],
        "building_volume_m3": building_volume_m3,
        "filtration_rate_m3h": filtration_rate_m3h,
        "deposition_rate_m3h": deposition_rate_m3h,
        "scenario": scenario,
        "description": params["description"]
    }
    
    return dataset, true_params


def create_test_config(
    building_volume_m3: float = 765.0,  # 3000 sq ft * 9 ft
    filtration_rate_m3h: float = 2549.0,  # 1500 CFM
    **overrides
) -> Dict:
    """Create a test configuration dictionary."""
    config = {
        "building": {
            "area_sq_ft": 3000,
            "ceiling_height_ft": 9
        },
        "hvac": {
            "flow_rate_cfm": 1500,
            "deposition_rate_percent": 10
        },
        "analysis": {
            "night_start_hour": 22,
            "night_end_hour": 8,
            "min_data_points": 10,
            "outlier_threshold": 2.0,
            "min_r_squared": 0.5,
            "efficiency_alert_threshold": 0.7
        },
        "google_sheets": {
            "spreadsheet_id": "test_spreadsheet_id",
            "data_sheet": "TestData",
            "results_sheet": "TestResults",
            "columns": {
                "timestamp": "A",
                "indoor_aqi": "B", 
                "outdoor_aqi": "C"
            },
            "header_row": 1,
            "max_rows": 1000
        },
        "schedule": {
            "analysis_window_days": 14,
            "frequency": "daily",
            "keep_results_days": 0
        }
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


def save_test_data_to_csv(
    dataset: pd.DataFrame,
    filepath: str,
    include_pm25: bool = False
) -> None:
    """Save test dataset to CSV file in format similar to Google Sheets export."""
    output_data = dataset[['timestamp', 'indoor_aqi', 'outdoor_aqi']].copy()
    
    if include_pm25:
        output_data['indoor_pm25'] = dataset['indoor_pm25']
        output_data['outdoor_pm25'] = dataset['outdoor_pm25']
    
    # Format timestamp as string (like Google Sheets)
    output_data['timestamp'] = output_data['timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S')
    
    output_data.to_csv(filepath, index=False)


if __name__ == "__main__":
    # Generate sample test datasets
    print("Generating test datasets...")
    
    scenarios = ["good_filter", "degraded_filter", "poor_filter", "hepa_filter"]
    
    for scenario in scenarios:
        print(f"Creating {scenario} dataset...")
        dataset, true_params = generate_test_dataset(
            scenario=scenario,
            days=14,
            random_seed=42
        )
        
        # Save to CSV
        filename = f"test_data_{scenario}.csv"
        save_test_data_to_csv(dataset, filename)
        
        print(f"  True filter efficiency: {true_params['filter_efficiency']:.1%}")
        print(f"  True infiltration rate: {true_params['infiltration_ach']:.2f} ACH")
        print(f"  Saved to: {filename}")
    
    print("Test datasets generated successfully!") 