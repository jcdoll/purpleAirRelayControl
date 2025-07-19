#!/usr/bin/env python3
"""
Filter Efficiency Analysis Script

This script analyzes filter efficiency and air infiltration rates from
indoor/outdoor PM2.5 concentration data using night-time calibration.

Usage:
    python analyze_filter_performance.py [--config CONFIG_FILE] [--days DAYS] [--dry-run]

Examples:
    # Run with default config and 7 days of data
    python analyze_filter_performance.py

    # Run with custom config and 14 days of data
    python analyze_filter_performance.py --config my_config.yaml --days 14

    # Test run without writing results
    python analyze_filter_performance.py --dry-run
"""

import argparse
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd
import yaml

# Add module paths for imports
script_dir = Path(__file__).parent.resolve()
sys.path.append(str(script_dir / 'utils'))
sys.path.append(str(script_dir / 'models'))

from models.kalman_filter_tracker import KalmanFilterTracker  # noqa: E402
from utils.data_processor import DataProcessor  # noqa: E402
from utils.sheets_client import SheetsClient  # noqa: E402
from utils.visualization import save_test_visualization  # noqa: E402


def setup_logging(log_level: str = 'INFO') -> logging.Logger:
    """
    Set up logging configuration.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)

    Returns:
        Configured logger
    """
    # Configure logging
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
    )

    # Create logger for this script
    logger = logging.getLogger('filter_analysis')
    return logger


def load_config(config_file: str) -> Dict[str, Any]:
    """
    Load configuration from YAML file.

    Args:
        config_file: Path to configuration file

    Returns:
        Configuration dictionary
    """
    config_path = Path(config_file)

    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_file}")

    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)

    # Validate required sections
    required_sections = ['building', 'hvac', 'analysis', 'google_sheets']
    missing_sections = [section for section in required_sections if section not in config]

    if missing_sections:
        raise ValueError(f"Missing required config sections: {missing_sections}")

    return config


def validate_config(config: Dict[str, Any]) -> bool:
    """
    Validate configuration parameters.

    Args:
        config: Configuration dictionary

    Returns:
        True if valid, raises exception if invalid
    """
    # Check Google Sheets spreadsheet ID
    sheets_config = config['google_sheets']
    if sheets_config['spreadsheet_id'] == 'your_spreadsheet_id_here':
        raise ValueError("Please update google_sheets.spreadsheet_id in config.yaml with your actual spreadsheet ID")

    # Check building parameters
    building = config['building']
    if building['area_sq_ft'] <= 0 or building['ceiling_height_ft'] <= 0:
        raise ValueError("Building dimensions must be positive values")

    # Check HVAC parameters
    hvac = config['hvac']
    if hvac['flow_rate_cfm'] <= 0:
        raise ValueError("HVAC flow rate must be positive")

    return True


class FilterEfficiencyAnalyzer:
    """
    Main analyzer that orchestrates the complete filter efficiency analysis.
    """

    def __init__(self, config: Dict[str, Any], dry_run: bool = False):
        """
        Initialize the analyzer.

        Args:
            config: Configuration dictionary
            dry_run: If True, don't write results to Google Sheets
        """
        self.config = config
        self.dry_run = dry_run
        self.logger = logging.getLogger(__name__)

        # Initialize components
        self.data_processor = DataProcessor(config)
        self.tracker = KalmanFilterTracker(config)

        if not dry_run:
            self.sheets_client = SheetsClient(config)
        else:
            self.sheets_client = None
            self.logger.info("Running in dry-run mode - results will not be written to Google Sheets")

    def run_analysis(self, days_back: int = 7) -> Dict[str, Any]:
        """
        Run the complete filter efficiency analysis.

        Args:
            days_back: Number of days of historical data to analyze

        Returns:
            Analysis results dictionary
        """
        self.logger.info(f"Starting filter efficiency analysis for last {days_back} days")

        try:
            # Step 1: Load data from Google Sheets
            self.logger.info("Loading sensor data from Google Sheets...")
            df = self._load_data(days_back)

            # Step 2: Process and clean data
            self.logger.info("Processing and cleaning data...")
            processed_data = self._process_data(df)

            # Step 3: Run Kalman filter analysis
            self.logger.info("Running Kalman filter analysis...")
            analysis_results = self._analyze_filter_efficiency(processed_data)

            # No recommendation engine yet; leave empty list
            analysis_results['recommendations'] = {}

            # Step 5: Write results back to Google Sheets
            if not self.dry_run:
                self.logger.info("Writing results to Google Sheets...")
                success = self._write_results(analysis_results)
                analysis_results['results_written'] = success
            else:
                analysis_results['results_written'] = False
                self.logger.info("Dry run - skipping write to Google Sheets")

            # Step 6: Generate summary
            summary = self._create_summary(analysis_results)

            # Step 7: Generate visualization
            visualization_files = self._generate_visualization(processed_data, analysis_results)

            self.logger.info("Analysis completed successfully")
            return {
                'analysis_results': analysis_results,
                'summary': summary,
                'visualization_files': visualization_files,
                'success': True,
            }

        except Exception as e:
            self.logger.error(f"Analysis failed: {e}")
            return {'error': str(e), 'success': False}

    def _load_data(self, days_back: int) -> Any:
        """Load data from Google Sheets."""
        # Use sheets_client if available (including MockSheetsClient for testing)
        if self.sheets_client is not None:
            return self.sheets_client.read_sensor_data(days_back)
        else:
            # Fallback to mock data only if no sheets client
            from utils.test_data_generator import generate_standard_test_dataset

            dataset, _ = generate_standard_test_dataset(scenario="good_filter", days=days_back, random_seed=42)
            self.logger.info(f"Created fallback mock data with {len(dataset)} points")
            return dataset

    def _process_data(self, df: Any) -> Dict[str, Any]:
        """Process and clean the raw data."""
        # Convert AQI to PM2.5
        df_pm25 = self.data_processor.convert_aqi_columns(df)

        # Filter for night-time data
        night_data = self.data_processor.filter_night_time_data(df_pm25)

        min_points = self.config['analysis']['min_data_points']
        if len(night_data) < min_points:
            raise ValueError(
                f"Insufficient night-time data: {len(night_data)} points " f"(minimum required: {min_points})"
            )

        # Calculate I/O ratio
        night_data = self.data_processor.calculate_io_ratio(night_data)

        # Detect outliers
        night_data = self.data_processor.detect_outliers(night_data, ['indoor_pm25', 'outdoor_pm25'])

        # Remove outliers
        clean_mask = ~(night_data['indoor_pm25_outlier'] | night_data['outdoor_pm25_outlier'])
        clean_data = night_data[clean_mask].copy()

        if len(clean_data) < 5:
            raise ValueError(f"Insufficient clean data after outlier removal: {len(clean_data)} points")

        # Prepare model data
        assert isinstance(clean_data, pd.DataFrame), "clean_data must be a DataFrame"
        model_data = self.data_processor.prepare_model_data(clean_data)

        return {'raw_data': df, 'night_data': night_data, 'clean_data': clean_data, 'model_data': model_data}

    def _analyze_filter_efficiency(self, processed_data: Dict[str, Any]) -> Dict[str, Any]:
        """Run Kalman filter on processed data and compute metrics."""
        model_data = processed_data['model_data']

        # Fix: Use timestamps from model_data to ensure alignment with PM2.5 values
        for ts, indoor, outdoor in zip(model_data['timestamps'], model_data['indoor_pm25'], model_data['outdoor_pm25']):
            # Convert numpy.datetime64 to Python datetime
            if hasattr(ts, 'to_pydatetime'):
                ts = ts.to_pydatetime()
            elif hasattr(ts, 'item'):
                ts = pd.Timestamp(ts).to_pydatetime()

            # Ensure ts is a valid datetime object
            if not isinstance(ts, datetime):
                continue  # Skip invalid timestamps

            self.tracker.add_measurement(ts, float(indoor), float(outdoor))

        current_eff = self.tracker.get_current_efficiency()
        diagnostics = {
            'state_history_len': len(self.tracker.state_history),
            'measurement_count': len(self.tracker.measurements),
        }

        # Calculate infiltration rate in m³/h
        infiltration_m3h = None
        if hasattr(self.tracker, '_calculate_infiltration_rate_m3h'):
            try:
                infiltration_m3h = self.tracker._calculate_infiltration_rate_m3h()
            except Exception:
                infiltration_m3h = None

        # Calculate degradation rate from efficiency trend
        degradation_rate = None
        if hasattr(self.tracker, 'get_efficiency_trend'):
            try:
                trend_per_month = self.tracker.get_efficiency_trend()
                if trend_per_month is not None:
                    degradation_rate = -trend_per_month / 30.0  # Convert monthly trend to daily
            except Exception:
                degradation_rate = None

        performance = {
            'current_efficiency': current_eff,
            'efficiency_percentage': current_eff * 100 if current_eff is not None else None,
            'infiltration_rate_ach': self.tracker.leak_ach,
            'infiltration_rate_m3h': infiltration_m3h,
            'degradation_rate_per_day': degradation_rate,
        }

        # Data period info
        clean_data = processed_data['clean_data']
        data_period = {
            'start': clean_data['timestamp'].min(),
            'end': clean_data['timestamp'].max(),
            'n_points_total': len(processed_data['night_data']),
            'n_points_clean': len(clean_data),
        }

        # Calculate Kalman filter-appropriate model quality metrics
        model_quality = self._calculate_kalman_model_quality()

        # Build consolidated analysis results dictionary expected by downstream code/tests
        analysis_results = {
            'analysis_timestamp': datetime.now(),
            'filter_performance': performance,
            'model_quality': model_quality,
            'data_period': data_period,
            'diagnostics': diagnostics,
            'fit_results': None,  # No direct fit_results for Kalman filter
        }

        # ------------------------------------------------------------------
        #  Compatibility keys for integration tests / external consumers
        # ------------------------------------------------------------------
        # Direct access keys (scalar values)
        analysis_results['filter_efficiency'] = performance['current_efficiency']
        analysis_results['infiltration_rate_ach'] = performance['infiltration_rate_ach']
        # Aggregate diagnostics
        analysis_results['model_diagnostics'] = analysis_results['model_quality']

        return analysis_results

    def _calculate_kalman_model_quality(self) -> Dict[str, Any]:
        """Calculate appropriate model quality metrics for Kalman filter."""
        try:
            # Get summary statistics from the tracker
            stats = self.tracker.get_summary_stats()

            # Calculate prediction accuracy metrics
            prediction_rmse = stats.get('prediction_rmse')
            mean_prediction_error = stats.get('mean_prediction_error')

            # Calculate pseudo R-squared from prediction accuracy
            pseudo_r_squared = None
            if prediction_rmse is not None and prediction_rmse > 0:
                # Simple heuristic: good predictions (RMSE < 5 μg/m³) get higher R²
                # This is a rough approximation since R² isn't directly applicable to Kalman filters
                if prediction_rmse < 5.0:
                    pseudo_r_squared = 0.9 - (prediction_rmse / 50.0)  # Scale: 0.8-0.9 for good predictions
                elif prediction_rmse < 15.0:
                    pseudo_r_squared = 0.7 - (prediction_rmse / 50.0)  # Scale: 0.4-0.7 for moderate predictions
                else:
                    pseudo_r_squared = 0.3 - (prediction_rmse / 100.0)  # Scale: 0.0-0.3 for poor predictions

                pseudo_r_squared = max(0.0, min(1.0, pseudo_r_squared))

            # Use mean absolute error (MAE) from prediction error
            mae = abs(mean_prediction_error) if mean_prediction_error is not None else None

            return {
                'r_squared': pseudo_r_squared,
                'rmse': prediction_rmse,
                'mae': mae,
            }

        except Exception as e:
            self.logger.warning(f"Could not calculate Kalman model quality metrics: {e}")
            return {
                'r_squared': None,
                'rmse': None,
                'mae': None,
            }

    def _write_results(self, results: Dict[str, Any]) -> bool:
        """Write analysis results to Google Sheets."""
        try:
            if self.sheets_client is not None:
                return self.sheets_client.write_analysis_results(results)
            else:
                self.logger.info("Dry run, skipping write to sheets.")
                return True
        except Exception as e:
            self.logger.error(f"Failed to write results to Google Sheets: {e}")
            return False

    def _create_summary(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Create a human-readable summary of results."""
        performance = results['filter_performance']
        recommendations = results.get('recommendations', {})

        # Status determination
        efficiency_pct = performance['efficiency_percentage']
        if efficiency_pct is not None:
            if efficiency_pct >= 85:
                status_color = 'green'
                status_text = 'Excellent'
            elif efficiency_pct >= 70:
                status_color = 'yellow'
                status_text = 'Good'
            elif efficiency_pct >= 50:
                status_color = 'orange'
                status_text = 'Declining'
            else:
                status_color = 'red'
                status_text = 'Poor'
        else:
            status_color = 'gray'
            status_text = 'N/A'

        summary = {
            'filter_efficiency': {
                'value': (
                    round(performance['efficiency_percentage'], 1)
                    if performance['efficiency_percentage'] is not None
                    else 'N/A'
                ),
                'unit': '%',
                'status': status_text,
                'color': status_color,
            },
            'air_changes_per_hour': {
                'value': round(performance['infiltration_rate_ach'], 2),
                'unit': 'ACH',
                'description': 'Building air leakage rate',
            },
            'model_confidence': {
                'value': (
                    round(results['model_quality']['r_squared'] * 100, 1)
                    if results['model_quality']['r_squared'] is not None
                    else 'N/A'
                ),
                'unit': '%',
                'description': 'Analysis reliability',
            },
            'last_updated': results['analysis_timestamp'].isoformat(),
            'alerts': recommendations.get('alerts', []),
            'next_actions': recommendations.get('actions', [])[:3],  # Top 3 actions
            'data_quality': {
                'points_used': results['data_period']['n_points_clean'],
                'time_span_days': (results['data_period']['end'] - results['data_period']['start']).days,
            },
        }

        # Add degradation info if available
        if performance['degradation_rate_per_day'] is not None:
            summary['degradation_rate'] = {
                'value': round(performance['degradation_rate_per_day'] * 100, 3),
                'unit': '%/day',
                'description': 'Efficiency loss per day',
            }

        return summary

    def _generate_visualization(self, processed_data: Dict[str, Any], analysis_results: Dict[str, Any]) -> List[str]:
        """Generate visualization charts for the analysis results."""
        try:
            visualization_files = []

            # Prepare data for visualization
            clean_data = processed_data['clean_data'].copy()

            # Ensure clean_data has the expected columns
            if 'indoor_pm25' not in clean_data.columns or 'outdoor_pm25' not in clean_data.columns:
                self.logger.warning("Missing required columns for visualization")
                return []

            # Create model results structure expected by visualization
            model_results = {
                'kalman': {
                    'success': True,
                    'model': self.tracker,
                    'stats': self.tracker.get_summary_stats() if hasattr(self.tracker, 'get_summary_stats') else {},
                }
            }

            # Create scenario info structure
            scenario_info = {
                'description': f"Filter Efficiency Analysis - {analysis_results['analysis_timestamp'].strftime('%Y-%m-%d %H:%M')}",
                'filter_efficiency': analysis_results['filter_performance']['current_efficiency'],
                'infiltration_ach': analysis_results['filter_performance']['infiltration_rate_ach'],
                'building_volume_m3': (
                    self.tracker._calculate_building_volume_m3()
                    if hasattr(self.tracker, '_calculate_building_volume_m3')
                    else 765
                ),
                'hvac_m3h': (
                    self.tracker._calculate_filtration_rate() * self.tracker._calculate_building_volume_m3()
                    if hasattr(self.tracker, '_calculate_building_volume_m3')
                    else 2549
                ),
            }

            # Generate visualization
            timestamp_str = analysis_results['analysis_timestamp'].strftime('%Y%m%d_%H%M%S')
            test_name = f"filter_analysis_{timestamp_str}"

            # Save visualization
            saved_files = save_test_visualization(
                test_name=test_name,
                df=clean_data,
                model_results=model_results,
                scenario_info=scenario_info,
                output_dir="analysis_visualizations",
            )

            visualization_files = [str(f) for f in saved_files]
            self.logger.info(f"Generated {len(visualization_files)} visualization files: {visualization_files}")

            return visualization_files

        except Exception as e:
            self.logger.warning(f"Failed to generate visualization: {e}")
            return []


def main():
    """Main entry point for the script."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Analyze HVAC filter efficiency from indoor/outdoor PM2.5 data')
    parser.add_argument('--config', '-c', default='config.yaml', help='Configuration file path (default: config.yaml)')
    parser.add_argument(
        '--days', '-d', type=int, default=7, help='Number of days of historical data to analyze (default: 7)'
    )
    parser.add_argument('--dry-run', action='store_true', help='Run analysis without writing results to Google Sheets')
    parser.add_argument(
        '--log-level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        default='INFO',
        help='Logging level (default: INFO)',
    )
    parser.add_argument('--output', '-o', help='Output file for results (JSON format)')

    args = parser.parse_args()

    # Set up logging
    logger = setup_logging(args.log_level)

    try:
        # Load and validate configuration
        logger.info(f"Loading configuration from {args.config}")
        config = load_config(args.config)
        validate_config(config)

        # Initialize analyzer
        analyzer = FilterEfficiencyAnalyzer(config, dry_run=args.dry_run)

        # Run analysis
        results = analyzer.run_analysis(days_back=args.days)

        if results['success']:
            summary = results['summary']

            # Print summary
            print("\n" + "=" * 60)
            print("FILTER EFFICIENCY ANALYSIS RESULTS")
            print("=" * 60)
            eff_val = summary['filter_efficiency']['value']
            eff_status = summary['filter_efficiency']['status']
            print(f"Filter Efficiency: {eff_val}% ({eff_status})")
            print(f"Air Changes per Hour: {summary['air_changes_per_hour']['value']} ACH")
            print(f"Model Confidence: {summary['model_confidence']['value']}%")
            print(f"Analysis Date: {datetime.fromisoformat(summary['last_updated']).strftime('%Y-%m-%d %H:%M:%S')}")

            if summary['alerts']:
                print("\nALERTS:")
                for alert in summary['alerts']:
                    print(f"  • {alert}")

            if summary['next_actions']:
                print("\nRECOMMENDED ACTIONS:")
                for i, action in enumerate(summary['next_actions'], 1):
                    print(f"  {i}. {action}")

            points_used = summary['data_quality']['points_used']
            time_span = summary['data_quality']['time_span_days']
            print(f"\nData Quality: {points_used} points over {time_span} days")

            # Show visualization files if generated
            if 'visualization_files' in results and results['visualization_files']:
                print("\nGenerated Visualizations:")
                for viz_file in results['visualization_files']:
                    print(f"  • {viz_file}")

            print("=" * 60)

            # Save results to file if requested
            if args.output:
                with open(args.output, 'w') as f:
                    json.dump(results, f, indent=2, default=str)
                logger.info(f"Results saved to {args.output}")

            # Exit with success
            sys.exit(0)

        else:
            print(f"\n❌ Analysis failed: {results['error']}")
            sys.exit(1)

    except KeyboardInterrupt:
        logger.info("Analysis interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        if args.log_level == 'DEBUG':
            import traceback

            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
