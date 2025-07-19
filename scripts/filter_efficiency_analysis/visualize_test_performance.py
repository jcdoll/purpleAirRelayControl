#!/usr/bin/env python3
"""
Visualize test performance for filter efficiency analysis.

This module provides comprehensive visualization of filter efficiency estimation
performance across different scenarios and test conditions.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

import matplotlib.pyplot as plt
import numpy as np
from analyze_filter_performance import FilterEfficiencyAnalyzer

from tests.test_utils import create_test_config
from utils.test_data_generator import generate_standard_test_dataset
from utils.visualization import FilterVisualization


class TestPerformanceVisualizer:
    """Visualize filter efficiency analysis performance on synthetic data."""

    def __init__(self, output_dir: str = "test_visualizations"):
        """Initialize visualizer with output directory."""
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

        # Configure matplotlib for high-quality plots
        plt.style.use('default')
        plt.rcParams.update(
            {'figure.figsize': (12, 8), 'figure.dpi': 100, 'font.size': 10, 'axes.grid': True, 'grid.alpha': 0.3}
        )

        self.results = {}
        self.viz = FilterVisualization(output_dir)

    def run_comprehensive_analysis(self, days: int = 14, random_seed: int = 42) -> Dict[str, Any]:
        """Run analysis on all scenarios and collect results."""
        scenarios = ["good_filter", "degraded_filter", "poor_filter", "hepa_filter", "high_pollution"]

        print("Running comprehensive analysis across scenarios...")

        for scenario in scenarios:
            print(f"\nAnalyzing scenario: {scenario}")

            try:
                # Generate synthetic data
                dataset, true_params = generate_standard_test_dataset(
                    scenario=scenario, days=days, random_seed=random_seed
                )

                # Run analysis
                config = create_test_config()

                # Create mock analyzer (dry run mode)
                analyzer = FilterEfficiencyAnalyzer(config, dry_run=True)

                # Override data loading with our synthetic data
                def make_data_loader(data):
                    return lambda days_back: data

                analyzer._load_data = make_data_loader(dataset)

                # Run analysis
                analysis_results = analyzer.run_analysis(days_back=days)

                # Store results
                self.results[scenario] = {
                    'dataset': dataset,
                    'true_params': true_params,
                    'analysis_results': analysis_results,
                    'success': analysis_results.get('success', False),
                }

                if analysis_results.get('success'):
                    perf = analysis_results['analysis_results']['filter_performance']
                    print(
                        f"  ✓ Success: Estimated efficiency = {perf['efficiency_percentage']:.1f}% "
                        f"(true = {true_params['filter_efficiency']*100:.1f}%)"
                    )
                else:
                    print(f"  ✗ Failed: {analysis_results.get('error', 'Unknown error')}")

            except Exception as e:
                print(f"  ✗ Exception: {str(e)}")
                self.results[scenario] = {'error': str(e), 'success': False}

        return self.results

    def create_time_series_plots(self):
        """Create time series plots for each scenario."""
        fig, axes = plt.subplots(len(self.results), 1, figsize=(15, 3 * len(self.results)))
        if len(self.results) == 1:
            axes = [axes]

        for idx, (scenario, data) in enumerate(self.results.items()):
            if not data.get('success'):
                axes[idx].text(
                    0.5,
                    0.5,
                    f"{scenario}: Analysis Failed",
                    ha='center',
                    va='center',
                    transform=axes[idx].transAxes,
                    fontsize=12,
                    color='red',
                )
                axes[idx].set_title(f"{scenario.replace('_', ' ').title()}")
                continue

            dataset = data['dataset']
            true_params = data['true_params']

            # Plot time series
            axes[idx].plot(
                dataset['timestamp'],
                dataset['outdoor_pm25'],
                label='Outdoor PM2.5',
                color='red',
                alpha=0.7,
                linewidth=1,
            )
            axes[idx].plot(
                dataset['timestamp'], dataset['indoor_pm25'], label='Indoor PM2.5', color='blue', alpha=0.8, linewidth=1
            )

            # Format x-axis using common function
            self.viz.format_datetime_axis(axes[idx], dataset)

            # Add efficiency info
            true_eff = true_params['filter_efficiency'] * 100
            if data['analysis_results']['success']:
                est_eff = data['analysis_results']['analysis_results']['filter_performance']['efficiency_percentage']
                title = f"{scenario.replace('_', ' ').title()} - True: {true_eff:.1f}%, Estimated: {est_eff:.1f}%"
            else:
                title = f"{scenario.replace('_', ' ').title()} - True: {true_eff:.1f}%, Estimation Failed"

            axes[idx].set_title(title)
            axes[idx].set_ylabel('PM2.5 (μg/m³)')
            axes[idx].legend()
            axes[idx].grid(True, alpha=0.3)

        plt.xlabel('Date')
        plt.tight_layout()
        plt.savefig(self.output_dir / 'time_series_comparison.png', dpi=150, bbox_inches='tight')
        plt.close()

        print(f"Saved time series plot: {self.output_dir / 'time_series_comparison.png'}")

    def create_scatter_plots(self):
        """Create indoor vs outdoor scatter plots."""
        fig, axes = plt.subplots(2, 3, figsize=(18, 12))
        axes = axes.flatten()

        for idx, (scenario, data) in enumerate(self.results.items()):
            if idx >= len(axes):
                break

            if not data.get('success'):
                axes[idx].text(
                    0.5,
                    0.5,
                    "Analysis Failed",
                    ha='center',
                    va='center',
                    transform=axes[idx].transAxes,
                    fontsize=12,
                    color='red',
                )
                axes[idx].set_title(f"{scenario.replace('_', ' ').title()}")
                continue

            dataset = data['dataset']
            true_params = data['true_params']

            # Create scatter plot
            axes[idx].scatter(dataset['outdoor_pm25'], dataset['indoor_pm25'], alpha=0.6, s=20, color='blue')

            # Add 1:1 line
            max_val = max(dataset['outdoor_pm25'].max(), dataset['indoor_pm25'].max())
            axes[idx].plot([0, max_val], [0, max_val], 'r--', alpha=0.5, label='1:1 line')

            # Add theoretical line based on true parameters
            outdoor_range = np.linspace(0, max_val, 100)
            true_eff = true_params['filter_efficiency']
            true_infilt = true_params['infiltration_rate_m3h']
            true_filt = true_params['filtration_rate_m3h']
            true_dep = true_params['deposition_rate_m3h']

            # Steady state model
            denominator = true_infilt + true_eff * true_filt + true_dep
            theoretical_indoor = (true_infilt * outdoor_range) / denominator
            axes[idx].plot(outdoor_range, theoretical_indoor, 'g-', label=f'True model (η={true_eff:.2f})', linewidth=2)

            # Add estimated line if analysis succeeded
            if data['analysis_results']['success']:
                analysis = data['analysis_results']['analysis_results']
                est_eff = analysis['filter_performance']['current_efficiency']
                est_infilt = analysis['filter_performance']['infiltration_rate_m3h']

                est_denominator = est_infilt + est_eff * true_filt + true_dep
                estimated_indoor = (est_infilt * outdoor_range) / est_denominator
                axes[idx].plot(
                    outdoor_range, estimated_indoor, 'm--', label=f'Estimated (η={est_eff:.2f})', linewidth=2
                )

            axes[idx].set_xlabel('Outdoor PM2.5 (μg/m³)')
            axes[idx].set_ylabel('Indoor PM2.5 (μg/m³)')
            axes[idx].set_title(f"{scenario.replace('_', ' ').title()}")
            axes[idx].legend()
            axes[idx].grid(True, alpha=0.3)

        # Remove empty subplots
        for idx in range(len(self.results), len(axes)):
            fig.delaxes(axes[idx])

        plt.tight_layout()
        plt.savefig(self.output_dir / 'scatter_plots.png', dpi=150, bbox_inches='tight')
        plt.close()

        print(f"Saved scatter plots: {self.output_dir / 'scatter_plots.png'}")

    def create_parameter_comparison(self):
        """Create parameter comparison plots."""
        # Collect parameter data
        scenarios = []
        true_efficiencies = []
        estimated_efficiencies = []
        true_infiltrations = []
        estimated_infiltrations = []
        r_squared_values = []

        for scenario, data in self.results.items():
            if not data.get('success'):
                continue

            scenarios.append(scenario.replace('_', ' ').title())
            true_params = data['true_params']
            analysis = data['analysis_results']['analysis_results']

            true_efficiencies.append(true_params['filter_efficiency'] * 100)
            estimated_efficiencies.append(analysis['filter_performance']['efficiency_percentage'])

            true_infiltrations.append(true_params['infiltration_ach'])
            estimated_infiltrations.append(analysis['filter_performance']['infiltration_rate_ach'])

            r_squared_values.append(analysis['model_quality']['r_squared'])

        # Create comparison plots
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))

        # Filter efficiency comparison
        x = np.arange(len(scenarios))
        width = 0.35

        axes[0, 0].bar(x - width / 2, true_efficiencies, width, label='True', alpha=0.8, color='green')
        axes[0, 0].bar(x + width / 2, estimated_efficiencies, width, label='Estimated', alpha=0.8, color='blue')
        axes[0, 0].set_xlabel('Scenario')
        axes[0, 0].set_ylabel('Filter Efficiency (%)')
        axes[0, 0].set_title('Filter Efficiency: True vs Estimated')
        axes[0, 0].set_xticks(x)
        axes[0, 0].set_xticklabels(scenarios, rotation=45, ha='right')
        axes[0, 0].legend()
        axes[0, 0].grid(True, alpha=0.3)

        # Infiltration rate comparison
        axes[0, 1].bar(x - width / 2, true_infiltrations, width, label='True', alpha=0.8, color='green')
        axes[0, 1].bar(x + width / 2, estimated_infiltrations, width, label='Estimated', alpha=0.8, color='blue')
        axes[0, 1].set_xlabel('Scenario')
        axes[0, 1].set_ylabel('Infiltration Rate (ACH)')
        axes[0, 1].set_title('Infiltration Rate: True vs Estimated')
        axes[0, 1].set_xticks(x)
        axes[0, 1].set_xticklabels(scenarios, rotation=45, ha='right')
        axes[0, 1].legend()
        axes[0, 1].grid(True, alpha=0.3)

        # Efficiency accuracy scatter
        axes[1, 0].scatter(true_efficiencies, estimated_efficiencies, s=100, alpha=0.7, color='purple')
        max_eff = max(max(true_efficiencies), max(estimated_efficiencies))
        axes[1, 0].plot([0, max_eff], [0, max_eff], 'r--', alpha=0.7, label='Perfect estimation')
        axes[1, 0].set_xlabel('True Efficiency (%)')
        axes[1, 0].set_ylabel('Estimated Efficiency (%)')
        axes[1, 0].set_title('Filter Efficiency Estimation Accuracy')
        axes[1, 0].legend()
        axes[1, 0].grid(True, alpha=0.3)

        # Add scenario labels to points
        for i, scenario in enumerate(scenarios):
            axes[1, 0].annotate(
                scenario,
                (true_efficiencies[i], estimated_efficiencies[i]),
                xytext=(5, 5),
                textcoords='offset points',
                fontsize=8,
            )

        # Model quality (R²)
        colors = ['red' if r2 < 0.5 else 'orange' if r2 < 0.7 else 'green' for r2 in r_squared_values]
        bars = axes[1, 1].bar(scenarios, r_squared_values, color=colors, alpha=0.7)
        axes[1, 1].axhline(y=0.5, color='red', linestyle='--', alpha=0.7, label='Minimum acceptable (0.5)')
        axes[1, 1].axhline(y=0.7, color='orange', linestyle='--', alpha=0.7, label='Good (0.7)')
        axes[1, 1].set_xlabel('Scenario')
        axes[1, 1].set_ylabel('R² Value')
        axes[1, 1].set_title('Model Fit Quality (R²)')
        axes[1, 1].set_xticklabels(scenarios, rotation=45, ha='right')
        axes[1, 1].legend()
        axes[1, 1].grid(True, alpha=0.3)

        # Add R² values on bars
        for bar, r2 in zip(bars, r_squared_values):
            height = bar.get_height()
            axes[1, 1].text(
                bar.get_x() + bar.get_width() / 2.0, height + 0.01, f'{r2:.3f}', ha='center', va='bottom', fontsize=9
            )

        plt.tight_layout()
        plt.savefig(self.output_dir / 'parameter_comparison.png', dpi=150, bbox_inches='tight')
        plt.close()

        print(f"Saved parameter comparison: {self.output_dir / 'parameter_comparison.png'}")

    def create_error_analysis(self):
        """Create detailed error analysis."""
        # Calculate errors
        efficiency_errors = []
        infiltration_errors = []
        scenario_names = []

        for scenario, data in self.results.items():
            if not data.get('success'):
                continue

            true_params = data['true_params']
            analysis = data['analysis_results']['analysis_results']

            true_eff = true_params['filter_efficiency']
            est_eff = analysis['filter_performance']['current_efficiency']
            eff_error = abs(est_eff - true_eff) / true_eff * 100  # Percentage error

            true_infilt = true_params['infiltration_ach']
            est_infilt = analysis['filter_performance']['infiltration_rate_ach']
            infilt_error = abs(est_infilt - true_infilt) / true_infilt * 100  # Percentage error

            efficiency_errors.append(eff_error)
            infiltration_errors.append(infilt_error)
            scenario_names.append(scenario.replace('_', ' ').title())

        # Create error analysis plot
        fig, axes = plt.subplots(1, 2, figsize=(15, 6))

        # Error bar plot
        x = np.arange(len(scenario_names))
        axes[0].bar(x, efficiency_errors, alpha=0.7, color='red', label='Filter Efficiency Error')
        axes[0].axhline(y=10, color='orange', linestyle='--', alpha=0.7, label='10% Error Threshold')
        axes[0].axhline(y=25, color='red', linestyle='--', alpha=0.7, label='25% Error Threshold (Current)')
        axes[0].set_xlabel('Scenario')
        axes[0].set_ylabel('Absolute Percentage Error (%)')
        axes[0].set_title('Filter Efficiency Estimation Errors')
        axes[0].set_xticks(x)
        axes[0].set_xticklabels(scenario_names, rotation=45, ha='right')
        axes[0].legend()
        axes[0].grid(True, alpha=0.3)

        # Add error values on bars
        for i, error in enumerate(efficiency_errors):
            axes[0].text(i, error + 0.5, f'{error:.1f}%', ha='center', va='bottom', fontsize=9)

        # Infiltration error
        axes[1].bar(x, infiltration_errors, alpha=0.7, color='blue', label='Infiltration Rate Error')
        axes[1].axhline(y=20, color='orange', linestyle='--', alpha=0.7, label='20% Error Threshold')
        axes[1].axhline(y=50, color='red', linestyle='--', alpha=0.7, label='50% Error Threshold (Current)')
        axes[1].set_xlabel('Scenario')
        axes[1].set_ylabel('Absolute Percentage Error (%)')
        axes[1].set_title('Infiltration Rate Estimation Errors')
        axes[1].set_xticks(x)
        axes[1].set_xticklabels(scenario_names, rotation=45, ha='right')
        axes[1].legend()
        axes[1].grid(True, alpha=0.3)

        # Add error values on bars
        for i, error in enumerate(infiltration_errors):
            axes[1].text(i, error + 1, f'{error:.1f}%', ha='center', va='bottom', fontsize=9)

        plt.tight_layout()
        plt.savefig(self.output_dir / 'error_analysis.png', dpi=150, bbox_inches='tight')
        plt.close()

        print(f"Saved error analysis: {self.output_dir / 'error_analysis.png'}")

        return {
            'scenarios': scenario_names,
            'efficiency_errors': efficiency_errors,
            'infiltration_errors': infiltration_errors,
        }

    def save_summary_report(self, error_data: Dict):
        """Save a summary report of the analysis."""
        successful_scenarios = len([data for data in self.results.values() if data.get('success')])
        total_scenarios = len(self.results)

        report = {
            "summary": {
                "total_scenarios": total_scenarios,
                "successful_scenarios": successful_scenarios,
                "success_rate": successful_scenarios / total_scenarios * 100,
                "timestamp": datetime.now().isoformat(),
            },
            "error_statistics": {
                "efficiency_errors": {
                    "mean": float(np.mean(error_data['efficiency_errors'])),
                    "std": float(np.std(error_data['efficiency_errors'])),
                    "max": float(np.max(error_data['efficiency_errors'])),
                    "min": float(np.min(error_data['efficiency_errors'])),
                },
                "infiltration_errors": {
                    "mean": float(np.mean(error_data['infiltration_errors'])),
                    "std": float(np.std(error_data['infiltration_errors'])),
                    "max": float(np.max(error_data['infiltration_errors'])),
                    "min": float(np.min(error_data['infiltration_errors'])),
                },
            },
            "detailed_results": {},
        }

        # Add detailed results for each scenario
        for scenario, data in self.results.items():
            if data.get('success'):
                analysis = data['analysis_results']['analysis_results']
                true_params = data['true_params']

                report["detailed_results"][scenario] = {
                    "true_efficiency": true_params['filter_efficiency'],
                    "estimated_efficiency": analysis['filter_performance']['current_efficiency'],
                    "true_infiltration_ach": true_params['infiltration_ach'],
                    "estimated_infiltration_ach": analysis['filter_performance']['infiltration_rate_ach'],
                    "r_squared": analysis['model_quality']['r_squared'],
                    "rmse": analysis['model_quality']['rmse'],
                    "mae": analysis['model_quality']['mae'],
                }
            else:
                report["detailed_results"][scenario] = {"status": "failed", "error": data.get('error', 'Unknown error')}

        # Save report
        report_file = self.output_dir / 'performance_report.json'
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)

        print(f"Saved performance report: {report_file}")

        # Print summary to console
        print("\n" + "=" * 60)
        print("FILTER EFFICIENCY ANALYSIS - TEST PERFORMANCE SUMMARY")
        print("=" * 60)
        print(f"Success Rate: {report['summary']['success_rate']:.1f}% ({successful_scenarios}/{total_scenarios})")
        print("\nFilter Efficiency Estimation Errors:")
        print(f"  Mean: {report['error_statistics']['efficiency_errors']['mean']:.1f}%")
        print(f"  Max:  {report['error_statistics']['efficiency_errors']['max']:.1f}%")
        print("\nInfiltration Rate Estimation Errors:")
        print(f"  Mean: {report['error_statistics']['infiltration_errors']['mean']:.1f}%")
        print(f"  Max:  {report['error_statistics']['infiltration_errors']['max']:.1f}%")
        print("=" * 60)


def main():
    """Main function to run the comprehensive analysis."""
    print("Filter Efficiency Analysis - Test Performance Visualization")
    print("=" * 60)

    # Create visualizer
    visualizer = TestPerformanceVisualizer()

    # Run comprehensive analysis
    visualizer.run_comprehensive_analysis(days=14, random_seed=42)

    # Create all visualizations
    print("\nCreating visualizations...")
    visualizer.create_time_series_plots()
    visualizer.create_scatter_plots()
    visualizer.create_parameter_comparison()
    error_data = visualizer.create_error_analysis()
    visualizer.save_summary_report(error_data)

    print(f"\nAll visualizations saved to: {visualizer.output_dir}")
    print("Files created:")
    for file in sorted(visualizer.output_dir.glob("*")):
        print(f"  - {file.name}")


if __name__ == "__main__":
    main()
