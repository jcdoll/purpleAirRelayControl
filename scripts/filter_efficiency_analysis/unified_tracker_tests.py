#!/usr/bin/env python3
"""
Unified test framework for filter efficiency tracking models.

This module provides a common testing framework that can evaluate and compare
different filter tracking approaches using the canonical test data generator.
"""

import os
import warnings
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

from models.base_filter_tracker import BaseFilterTracker
from models.kalman_filter_tracker import KalmanFilterTracker
from utils.test_data_generator import create_test_data_generator
from utils.visualization import FilterVisualization, save_test_visualization

# Suppress pandas FutureWarnings
warnings.filterwarnings('ignore', category=FutureWarning)


class ModelFactory:
    """Factory for creating filter tracking models."""

    MODELS = {'kalman': KalmanFilterTracker}

    @classmethod
    def create_model(cls, model_type: str, config: Dict[str, Any]) -> BaseFilterTracker:
        """Create a model instance of the specified type."""
        if model_type not in cls.MODELS:
            raise ValueError(f"Unknown model type: {model_type}. Available: {list(cls.MODELS.keys())}")

        return cls.MODELS[model_type](config)

    @classmethod
    def get_available_models(cls) -> List[str]:
        """Get list of available model types."""
        return list(cls.MODELS.keys())


class UnifiedTester:
    """Unified testing framework for filter tracking models."""

    def __init__(self, output_dir: str = "unified_test_results"):
        """Initialize the tester."""
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

        # Standard configuration for all tests
        self.config = {
            'building': {'area_sq_ft': 3000, 'ceiling_height_ft': 9, 'construction_type': 'average', 'age_years': 15},
            'hvac': {'flow_rate_cfm': 1500},
        }

        self.results = {}

    def run_scenario(
        self,
        scenario_name: str,
        measurements: List[Dict],
        scenario_info: Dict,
        models_to_test: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Run a test scenario with multiple models."""
        if models_to_test is None:
            models_to_test = ModelFactory.get_available_models()

        print(f"\n{'='*60}")
        print(f"Testing Scenario: {scenario_name.upper()}")
        print(f"Description: {scenario_info['description']}")
        print(f"Models: {', '.join(models_to_test)}")
        print(f"{'='*60}")

        scenario_results = {'scenario_info': scenario_info, 'measurements': measurements, 'model_results': {}}

        # Test each model
        for model_name in models_to_test:
            print(f"\nTesting {model_name.upper()} model...")

            try:
                # Create and run model
                model = ModelFactory.create_model(model_name, self.config)

                # Process all measurements
                for measurement in measurements:
                    model.add_measurement(
                        timestamp=measurement['timestamp'],
                        indoor_pm25=measurement['indoor_pm25'],
                        outdoor_pm25=measurement['outdoor_pm25'],
                    )

                # Get results
                stats = model.get_summary_stats()

                # Calculate performance metrics
                performance = self._calculate_performance_metrics(model, measurements, scenario_info)

                scenario_results['model_results'][model_name] = {
                    'model': model,
                    'stats': stats,
                    'performance': performance,
                    'success': True,
                }

                print(f"  ✓ {model_name}: {performance['summary']}")

            except Exception as e:
                print(f"  ✗ {model_name}: Failed - {str(e)}")
                scenario_results['model_results'][model_name] = {'error': str(e), 'success': False}

        # Store results
        self.results[scenario_name] = scenario_results
        return scenario_results

    def _calculate_performance_metrics(
        self, model: BaseFilterTracker, measurements: List[Dict], scenario_info: Dict
    ) -> Dict[str, Any]:
        """Calculate performance metrics for a model."""
        stats = model.get_summary_stats()

        # Get current efficiency estimate
        if hasattr(model, 'efficiency'):
            estimated_efficiency = getattr(model, 'efficiency', 0.0)
        else:
            current_eff_pct = stats.get('current_efficiency_percent')
            estimated_efficiency = current_eff_pct / 100.0 if current_eff_pct is not None else 0.0

        # True efficiency (constant for most scenarios)
        if 'true_efficiency' in scenario_info:
            true_efficiency = scenario_info['true_efficiency']
        else:
            # For degradation scenarios, use mean efficiency
            true_efficiencies = [m['true_efficiency'] for m in measurements]
            true_efficiency = np.mean(true_efficiencies)

        # Calculate error
        error = abs(estimated_efficiency - true_efficiency)
        error_percent = (error / true_efficiency * 100) if true_efficiency > 0 else 100

        # Calculate confidence/uncertainty
        uncertainty = stats.get('efficiency_uncertainty', 100.0)
        confidence = max(0.0, min(1.0, 1.0 - (uncertainty / 100.0)))

        performance = {
            'estimated_efficiency': estimated_efficiency,
            'true_efficiency': true_efficiency,
            'error': error,
            'error_percent': error_percent,
            'confidence': confidence,
            'uncertainty': uncertainty,
            'summary': f"Est: {estimated_efficiency:.1%}, True: {true_efficiency:.1%}, Error: {error_percent:.1f}%",
        }

        return performance

    def create_comparison_plots(self, scenario_name: str) -> List[str]:
        """Create comparison plots for a scenario."""
        if scenario_name not in self.results:
            print(f"No results found for scenario: {scenario_name}")
            return []

        scenario_data = self.results[scenario_name]

        # Convert measurements to DataFrame
        df = pd.DataFrame(scenario_data['measurements'])
        df['timestamp'] = pd.to_datetime(df['timestamp'])

        # Use canonical visualization
        FilterVisualization(str(self.output_dir))

        # Create plots for each successful model
        saved_files = []
        successful_models = {
            name: result for name, result in scenario_data['model_results'].items() if result.get('success', False)
        }

        if successful_models and not os.environ.get('CI'):
            try:
                output_file = save_test_visualization(
                    test_name=scenario_name,
                    df=df,
                    model_results=successful_models,
                    scenario_info=scenario_data['scenario_info'],
                    output_dir=str(self.output_dir),
                )
                saved_files.append(output_file)
                print(f"  Saved visualization: {output_file}")
            except Exception as e:
                print(f"  Failed to create visualization: {e}")

        return saved_files

    def print_summary_report(self):
        """Print a comprehensive summary report."""
        print(f"\n{'='*80}")
        print("UNIFIED TRACKER COMPARISON - SUMMARY REPORT")
        print(f"{'='*80}")

        if not self.results:
            print("No test results available.")
            return

        for scenario_name, scenario_data in self.results.items():
            print(f"\nScenario: {scenario_name.upper()}")
            print(f"Description: {scenario_data['scenario_info']['description']}")
            print("-" * 60)

            model_results = scenario_data['model_results']

            for model_name, result in model_results.items():
                if result.get('success', False):
                    perf = result['performance']
                    print(f"  {model_name:>10}: {perf['summary']}")
                else:
                    error_msg = result.get('error', 'Unknown error')
                    print(f"  {model_name:>10}: FAILED - {error_msg}")


def main():
    """Run unified tests using canonical generator."""
    print("Unified Filter Efficiency Tracker - Model Comparison")
    print("=" * 80)

    # Initialize tester
    tester = UnifiedTester()

    # Initialize canonical generator
    generator = create_test_data_generator(42)

    # Test scenarios using canonical generator with different patterns
    scenarios = [
        # Step changes scenario
        (
            'step_changes',
            generator.generate_complete_dataset(
                scenario='step_test', days=7  # 7 days = ~3 steps of 2 days each with some extra
            ),
        ),
        # Filter degradation (simulate with gradually changing efficiency)
        (
            'filter_degradation',
            generator.generate_complete_dataset(scenario='degraded_filter', days=30),  # Use existing degraded scenario
        ),
        # Noisy measurements scenario
        ('noisy_data', generator.generate_complete_dataset(scenario='good_filter', days=14)),
    ]

    # Run all scenarios
    for scenario_name, (dataset, true_params) in scenarios:
        # Convert dataset to measurements format expected by models
        measurements = []
        for _, row in dataset.iterrows():
            measurements.append(
                {
                    'timestamp': row['timestamp'],
                    'indoor_pm25': row['indoor_pm25'],
                    'outdoor_pm25': row['outdoor_pm25'],
                    'true_efficiency': true_params['filter_efficiency'],
                }
            )

        # Create scenario info
        scenario_info = {
            'name': scenario_name,
            'description': true_params['description'],
            'true_efficiency': true_params['filter_efficiency'],
        }

        # Test Kalman model
        tester.run_scenario(scenario_name, measurements, scenario_info, ['kalman'])

        # Create comparison plots
        tester.create_comparison_plots(scenario_name)

    # Print summary report
    tester.print_summary_report()


if __name__ == "__main__":
    main()
