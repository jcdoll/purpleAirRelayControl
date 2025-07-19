"""
Integration tests for the KalmanFilterTracker using the analysis pipeline.
"""

import os
from datetime import datetime

import pandas as pd
import pytest
from analyze_filter_performance import FilterEfficiencyAnalyzer

from models.kalman_filter_tracker import KalmanFilterTracker
from tests.test_utils import create_test_config
from utils.test_data_generator import create_test_data_generator
from utils.visualization import save_test_visualization


class MockSheetsClient:
    """Mock Google Sheets client for testing."""

    def __init__(self, dataset: pd.DataFrame):
        self.dataset = dataset

    def read_sensor_data(self, days_back: int) -> pd.DataFrame:
        return self.dataset


@pytest.mark.parametrize(
    "scenario, true_efficiency, expected_range",
    [
        ("good_filter", 0.85, (0.75, 0.95)),
        ("degraded_filter", 0.60, (0.50, 0.70)),
        ("poor_filter", 0.40, (0.30, 0.50)),
        ("hepa_filter", 0.97, (0.90, 1.0)),
    ],
)
def test_kalman_tracker_raw_data(scenario, true_efficiency, expected_range):
    """Test KalmanFilterTracker directly with raw data (no night-time filtering)."""

    # Create config and generator for custom scenario
    config = create_test_config()
    generator = create_test_data_generator(42, config)

    # Create custom building params with the desired filter efficiency
    building_params = generator.default_building.copy()
    building_params['filter_efficiency'] = true_efficiency

    # Generate data with custom parameters, not pre-defined scenarios
    # This ensures the Kalman filter gets data consistent with its config
    dataset, true_params = generator.generate_complete_dataset(
        scenario="custom", days=14, building_params=building_params
    )

    # Test Kalman filter with the SAME config used for data generation
    tracker = KalmanFilterTracker(config)

    # Feed all data points directly to tracker
    for i in range(len(dataset)):
        row = dataset.iloc[i]
        try:
            timestamp = pd.Timestamp(row['timestamp']).to_pydatetime()
            if not isinstance(timestamp, datetime):
                continue  # Skip invalid timestamps
        except (ValueError, TypeError):
            continue  # Skip invalid timestamps

        tracker.add_measurement(
            timestamp=timestamp,
            indoor_pm25=float(row['indoor_pm25']),
            outdoor_pm25=float(row['outdoor_pm25']),
        )

    # Get results
    estimated_efficiency = tracker.get_current_efficiency()

    # Create automatic visualization for debugging (skip in CI)
    if not os.environ.get('CI'):
        test_name = f"raw_{scenario}_eff_{true_efficiency:.0%}"
        scenario_info = {
            'name': scenario,
            'filter_efficiency': true_efficiency,
            'description': f'Raw Algorithm Test: {scenario} (True: {true_efficiency:.0%})',
        }
        model_results = {'kalman': {'model': tracker, 'success': True}}

        try:
            save_test_visualization(
                test_name=test_name,
                df=dataset,
                model_results=model_results,
                scenario_info=scenario_info,
                output_dir="test_debug_output",
            )
            print(f"  Debug visualization saved for {test_name}")
        except Exception as e:
            print(f"  Warning: Could not save visualization for {test_name}: {e}")

    assert estimated_efficiency is not None
    assert expected_range[0] <= estimated_efficiency <= expected_range[1]

    efficiency_error = abs(estimated_efficiency - true_efficiency)
    assert efficiency_error < 0.15, f"Efficiency error {efficiency_error:.3f} is too high for {scenario}"


@pytest.mark.parametrize(
    "scenario, true_efficiency, expected_range",
    [
        ("good_filter", 0.85, (0.75, 0.95)),
        ("degraded_filter", 0.60, (0.50, 0.70)),
        ("poor_filter", 0.40, (0.30, 0.50)),
        ("hepa_filter", 0.97, (0.90, 1.0)),
    ],
)
def test_kalman_tracker_with_data_pipeline(scenario, true_efficiency, expected_range):
    """Test KalmanFilterTracker through the full data processing pipeline."""

    # Create config and generator for custom scenario
    config = create_test_config()
    generator = create_test_data_generator(42, config)

    # Create custom building params with the desired filter efficiency
    building_params = generator.default_building.copy()
    building_params['filter_efficiency'] = true_efficiency

    # Generate data with custom parameters, not pre-defined scenarios
    # This ensures the Kalman filter gets data consistent with its config
    dataset, true_params = generator.generate_complete_dataset(
        scenario="custom", days=14, building_params=building_params
    )

    # Use FilterEfficiencyAnalyzer with the SAME config used for data generation
    mock_client = MockSheetsClient(dataset)

    analyzer = FilterEfficiencyAnalyzer(config, dry_run=True)
    analyzer.sheets_client = mock_client  # type: ignore

    # Override the _process_data method to skip night-time filtering
    def _process_data_no_night_filter(df):
        """Process data without night-time filtering for testing."""
        # Convert AQI to PM2.5 (with corruption protection)
        df_pm25 = analyzer.data_processor.convert_aqi_columns(df)

        # Skip night-time filtering - use all data
        all_data = df_pm25.copy()

        # Calculate I/O ratio
        all_data = analyzer.data_processor.calculate_io_ratio(all_data)

        # Skip outlier detection for raw algorithm test
        clean_data = all_data.copy()

        # Prepare model data
        model_data = analyzer.data_processor.prepare_model_data(clean_data)

        return {'raw_data': df, 'night_data': all_data, 'clean_data': clean_data, 'model_data': model_data}

    # Monkey patch the method
    analyzer._process_data = _process_data_no_night_filter

    results = analyzer.run_analysis(days_back=14)

    # Create automatic visualization for debugging (skip in CI)
    if not os.environ.get('CI'):
        test_name = f"pipeline_{scenario}_eff_{true_efficiency:.0%}"
        scenario_info = {
            'name': scenario,
            'filter_efficiency': true_efficiency,
            'description': f'Pipeline Test: {scenario} (True: {true_efficiency:.0%})',
        }

        # Extract estimated efficiency for visualization
        estimated_efficiency = None
        if results['success']:
            estimated_efficiency = results['analysis_results']['filter_efficiency']

        model_results = {
            'kalman': {
                'model': analyzer.tracker,
                'success': results['success'],
                'estimated_efficiency': estimated_efficiency,
            }
        }

        try:
            save_test_visualization(
                test_name=test_name,
                df=dataset,
                model_results=model_results,
                scenario_info=scenario_info,
                output_dir="test_debug_output",
            )
            print(f"  Debug visualization saved for {test_name}")
        except Exception as e:
            print(f"  Warning: Could not save visualization for {test_name}: {e}")

    assert results['success']
    analysis = results['analysis_results']
    estimated_efficiency = analysis['filter_efficiency']

    assert estimated_efficiency is not None
    assert expected_range[0] <= estimated_efficiency <= expected_range[1]

    efficiency_error = abs(estimated_efficiency - true_efficiency)
    assert efficiency_error < 0.15, f"Efficiency error {efficiency_error:.3f} is too high for {scenario}"


@pytest.mark.parametrize(
    "scenario, true_efficiency, expected_range",
    [
        ("good_filter", 0.85, (0.75, 0.95)),
        ("degraded_filter", 0.60, (0.50, 0.70)),
        ("poor_filter", 0.40, (0.30, 0.50)),
        ("hepa_filter", 0.97, (0.90, 1.0)),
    ],
)
def test_kalman_tracker_no_outlier_removal(scenario, true_efficiency, expected_range):
    """Test KalmanFilterTracker through pipeline but skip outlier removal."""

    # Create config and generator for custom scenario
    config = create_test_config()
    generator = create_test_data_generator(42, config)

    # Create custom building params with the desired filter efficiency
    building_params = generator.default_building.copy()
    building_params['filter_efficiency'] = true_efficiency

    # Generate data with custom parameters, not pre-defined scenarios
    # This ensures the Kalman filter gets data consistent with its config
    dataset, true_params = generator.generate_complete_dataset(
        scenario="custom", days=14, building_params=building_params
    )

    # Use FilterEfficiencyAnalyzer with the SAME config used for data generation
    mock_client = MockSheetsClient(dataset)

    analyzer = FilterEfficiencyAnalyzer(config, dry_run=True)
    analyzer.sheets_client = mock_client  # type: ignore

    # Override the _process_data method to skip outlier removal
    def _process_data_no_outliers(df):
        """Process data without outlier removal for testing."""
        # Convert AQI to PM2.5 (with corruption protection)
        df_pm25 = analyzer.data_processor.convert_aqi_columns(df)

        # Skip night-time filtering - use all data
        all_data = df_pm25.copy()

        # Calculate I/O ratio
        all_data = analyzer.data_processor.calculate_io_ratio(all_data)

        # Skip outlier detection and removal - Kalman filter handles this intrinsically
        clean_data = all_data.copy()

        # Prepare model data
        model_data = analyzer.data_processor.prepare_model_data(clean_data)

        return {'raw_data': df, 'night_data': all_data, 'clean_data': clean_data, 'model_data': model_data}

    # Monkey patch the method
    analyzer._process_data = _process_data_no_outliers

    results = analyzer.run_analysis(days_back=14)

    # Create automatic visualization for debugging (skip in CI)
    if not os.environ.get('CI'):
        test_name = f"no_outliers_{scenario}_eff_{true_efficiency:.0%}"
        scenario_info = {
            'name': scenario,
            'filter_efficiency': true_efficiency,
            'description': f'No Outlier Removal Test: {scenario} (True: {true_efficiency:.0%})',
        }

        # Extract estimated efficiency for visualization
        estimated_efficiency = None
        if results['success']:
            estimated_efficiency = results['analysis_results']['filter_efficiency']

        model_results = {
            'kalman': {
                'model': analyzer.tracker,
                'success': results['success'],
                'estimated_efficiency': estimated_efficiency,
            }
        }

        try:
            save_test_visualization(
                test_name=test_name,
                df=dataset,
                model_results=model_results,
                scenario_info=scenario_info,
                output_dir="test_debug_output",
            )
            print(f"  Debug visualization saved for {test_name}")
        except Exception as e:
            print(f"  Warning: Could not save visualization for {test_name}: {e}")

    assert results['success']
    analysis = results['analysis_results']
    estimated_efficiency = analysis['filter_efficiency']

    assert estimated_efficiency is not None
    assert expected_range[0] <= estimated_efficiency <= expected_range[1]

    efficiency_error = abs(estimated_efficiency - true_efficiency)
    assert efficiency_error < 0.15, f"Efficiency error {efficiency_error:.3f} is too high for {scenario}"
