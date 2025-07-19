"""
Test step response analysis functionality.
"""

import os
from datetime import datetime, timedelta
from typing import Any, Dict, List, Tuple

import numpy as np
import pandas as pd
import pytest

from models.kalman_filter_tracker import KalmanFilterTracker
from tests.test_utils import create_test_config
from utils.test_data_generator import create_test_data_generator
from utils.visualization import save_test_visualization


def generate_step_test_data(
    filter_efficiency: float, hours_per_step: int = 6, add_disturbances: bool = False, temporal_dynamics: bool = True
) -> Tuple[List[Dict], Dict[str, Any]]:
    """Generate step test data using the canonical generator."""

    # Use test configuration to ensure consistency
    config = create_test_config()
    generator = create_test_data_generator(42, config)

    # Time setup
    total_hours = hours_per_step * 3  # Three steps: low-high-low
    start_time = datetime(2024, 1, 15, 6, 0)  # 6 AM start
    end_time = start_time + timedelta(hours=total_hours)

    # Step levels for outdoor PM2.5
    step_levels = [10.0, 40.0, 10.0]  # low-high-low pattern

    # Generate outdoor data with step pattern
    outdoor_data = generator.generate_outdoor_pm25_series(
        start_date=start_time,
        end_date=end_time,
        pattern="step",
        base_level=25.0,
        step_levels=step_levels,
        hours_per_step=hours_per_step,
    )

    # Sample at 10-minute intervals
    time_index = pd.date_range(start_time, end_time, freq='10min')
    outdoor_timestamps = [t.timestamp() for t in outdoor_data['timestamp']]
    outdoor_values = np.array(outdoor_data['outdoor_pm25'].tolist())
    sampled_outdoor = np.interp([t.timestamp() for t in time_index], outdoor_timestamps, outdoor_values)

    # Building parameters - use generator's calculated values
    building_params = generator.default_building.copy()

    # Calculate indoor concentrations with temporal dynamics
    if temporal_dynamics:
        # Start at steady state for first outdoor level
        initial_indoor = generator.calculate_indoor_pm25_series(
            outdoor_pm25=np.array([step_levels[0]]),
            filter_efficiency=filter_efficiency,
            building_params=building_params,
        )[0]

        indoor_pm25 = generator.calculate_indoor_pm25_series(
            outdoor_pm25=sampled_outdoor,
            filter_efficiency=filter_efficiency,
            building_params=building_params,
            temporal_dynamics=True,
            previous_indoor=initial_indoor,
            dt_hours=10.0 / 60.0,  # 10 minutes
        )
    else:
        indoor_pm25 = generator.calculate_indoor_pm25_series(
            outdoor_pm25=sampled_outdoor, filter_efficiency=filter_efficiency, building_params=building_params
        )

    # Add small disturbances if requested
    if add_disturbances:
        noise = np.random.normal(0, 0.5, len(indoor_pm25))
        indoor_pm25 += noise
        sampled_outdoor += np.random.normal(0, 0.25, len(sampled_outdoor))

    # Ensure positive values
    indoor_pm25 = np.maximum(0.1, indoor_pm25)
    sampled_outdoor = np.maximum(0.1, sampled_outdoor)

    # Create measurements list
    measurements = []
    for i, timestamp in enumerate(time_index):
        # Determine current step
        hour = (timestamp - start_time).total_seconds() / 3600
        if hour < hours_per_step:
            step_name = 'low'
        elif hour < 2 * hours_per_step:
            step_name = 'high'
        else:
            step_name = 'low'

        measurements.append(
            {
                'timestamp': timestamp,
                'outdoor_pm25': float(sampled_outdoor[i]),
                'indoor_pm25': float(indoor_pm25[i]),
                'step': step_name,
            }
        )

    # Scenario info
    scenario_info = {
        'name': f'step_test_eff_{filter_efficiency:.0%}',
        'description': f'Clean step test with {filter_efficiency:.0%} filter efficiency',
        'filter_efficiency': filter_efficiency,
        'hours_per_step': hours_per_step,
        'building_volume_m3': building_params['volume_m3'],
        'hvac_m3h': building_params['hvac_m3h'],
        'infiltration_m3h': building_params['infiltration_ach'] * building_params['volume_m3'],
        'infiltration_ach': building_params['infiltration_ach'],
        'deposition_m3h': building_params['deposition_ach'] * building_params['volume_m3'],
        'total_ach': (
            building_params['infiltration_ach']
            + building_params['hvac_m3h'] / building_params['volume_m3']
            + building_params['deposition_ach']
        ),
        'time_constant_hours': 1.0
        / (
            building_params['infiltration_ach']
            + building_params['hvac_m3h'] / building_params['volume_m3']
            + building_params['deposition_ach']
        ),
    }

    return measurements, scenario_info


# Parametrized test for different filter efficiencies
@pytest.mark.parametrize(
    "filter_efficiency,expected_accuracy",
    [
        (0.30, 0.05),  # 30% efficiency, allow 5% error
        (0.75, 0.05),  # 75% efficiency, allow 5% error
        (0.95, 0.10),  # 95% efficiency, allow 10% error (harder to estimate)
    ],
)
def test_step_analysis_filter_efficiency(filter_efficiency: float, expected_accuracy: float):
    """Test filter efficiency estimation using step changes in outdoor PM2.5."""

    # Generate clean step test data using canonical generator
    measurements, scenario_info = generate_step_test_data(
        filter_efficiency=filter_efficiency, hours_per_step=6, add_disturbances=False, temporal_dynamics=True
    )

    # Convert to DataFrame
    df = pd.DataFrame(measurements)

    # Create Kalman filter tracker
    config = create_test_config()
    tracker = KalmanFilterTracker(config)

    # Process measurements sequentially
    for i in range(len(df)):
        tracker.add_measurement(
            timestamp=df.iloc[i]['timestamp'],
            indoor_pm25=df.iloc[i]['indoor_pm25'],
            outdoor_pm25=df.iloc[i]['outdoor_pm25'],
        )

    # Get final results
    summary = tracker.get_summary_stats()

    # Check estimation accuracy
    estimated_efficiency_pct = summary['current_efficiency_percent']
    if estimated_efficiency_pct is None:
        estimated_efficiency = 0.0
        confidence = 0.0
    else:
        estimated_efficiency = estimated_efficiency_pct / 100.0  # Convert to fraction
        # Calculate confidence from uncertainty (lower uncertainty = higher confidence)
        uncertainty = summary.get('efficiency_uncertainty', 100.0)
        confidence = max(0.0, min(1.0, 1.0 - (uncertainty / 100.0)))  # Normalize to 0-1

    estimation_error = abs(estimated_efficiency - filter_efficiency)

    print(f"\nStep Test Results for {filter_efficiency:.0%} filter:")
    print(f"  True efficiency: {filter_efficiency:.1%}")
    print(f"  Estimated efficiency: {estimated_efficiency:.1%}")
    print(f"  Error: {estimation_error:.1%}")
    print(f"  Confidence: {confidence:.2f}")
    print(f"  Uncertainty: {summary.get('efficiency_uncertainty', 'N/A')}")

    # Create visualization (skip in CI)
    if not os.environ.get('CI'):
        save_test_visualization(
            test_name=f"step_test_eff_{filter_efficiency:.0%}",
            df=df,
            model_results={'kalman': {'model': tracker, 'success': True, 'stats': summary}},
            scenario_info=scenario_info,
            output_dir="test_debug_output",
        )
        print(f"  Debug visualization saved for step_test_eff_{filter_efficiency:.0%}")

    # Assertions
    assert estimation_error <= expected_accuracy, (
        f"Filter efficiency estimation error {estimation_error:.1%} exceeds "
        f"tolerance {expected_accuracy:.1%} for {filter_efficiency:.0%} filter"
    )

    assert confidence >= 0.5, (
        f"Confidence {confidence:.2f} too low for step test "
        f"(uncertainty: {summary.get('efficiency_uncertainty', 'N/A')})"
    )

    # Verify data quality
    assert len(df) >= 30, "Should have sufficient data points"
    assert df['outdoor_pm25'].std() > 5, "Should have significant outdoor variation"


if __name__ == "__main__":
    # Run step tests directly
    print("Running step test analysis...")

    test_efficiencies = [0.30, 0.75, 0.95]

    for efficiency in test_efficiencies:
        print(f"\nTesting {efficiency:.0%} filter efficiency...")
        try:
            test_step_analysis_filter_efficiency(efficiency, 0.1)  # 10% tolerance for direct runs
            print("✓ PASS")
        except Exception as e:
            print(f"✗ FAIL: {e}")

    print("\nStep test analysis complete!")
