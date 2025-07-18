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

import os
import sys
import argparse
import logging
import yaml
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Optional

# Add utils to path
script_dir = Path(__file__).parent
sys.path.append(str(script_dir / 'utils'))
sys.path.append(str(script_dir / 'models'))

from data_processor import DataProcessor
from night_calibration import NightTimeCalibration
from sheets_client import SheetsClient


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
        datefmt='%Y-%m-%d %H:%M:%S'
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
        raise ValueError(
            "Please update google_sheets.spreadsheet_id in config.yaml with your actual spreadsheet ID"
        )
    
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
        self.night_model = NightTimeCalibration(config, self.data_processor.building_params)
        
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
            
            # Step 3: Run night-time analysis
            self.logger.info("Running night-time calibration analysis...")
            analysis_results = self._analyze_filter_efficiency(processed_data)
            
            # Step 4: Generate recommendations
            self.logger.info("Generating recommendations...")
            recommendations = self.night_model.generate_recommendations()
            analysis_results['recommendations'] = recommendations
            
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
            
            self.logger.info("Analysis completed successfully")
            return {
                'analysis_results': analysis_results,
                'summary': summary,
                'success': True
            }
            
        except Exception as e:
            self.logger.error(f"Analysis failed: {e}")
            return {
                'error': str(e),
                'success': False
            }
    
    def _load_data(self, days_back: int) -> Any:
        """Load data from Google Sheets."""
        if self.dry_run:
            # For dry run, create mock data
            return self._create_mock_data(days_back)
        else:
            return self.sheets_client.read_sensor_data(days_back)
    
    def _create_mock_data(self, days_back: int) -> Any:
        """Create mock data for dry run testing."""
        import pandas as pd
        import numpy as np
        
        # Generate timestamps
        end_time = datetime.now()
        start_time = end_time - timedelta(days=days_back)
        timestamps = pd.date_range(start=start_time, end=end_time, freq='H')
        
        # Generate realistic AQI data
        n_points = len(timestamps)
        np.random.seed(42)  # For reproducible results
        
        # Outdoor varies more, indoor is filtered
        outdoor_aqi = 25 + 15 * np.sin(np.linspace(0, 2*np.pi*days_back, n_points)) + np.random.normal(0, 8, n_points)
        indoor_aqi = outdoor_aqi * 0.3 + np.random.normal(0, 3, n_points)
        
        # Ensure positive values
        outdoor_aqi = np.maximum(outdoor_aqi, 5)
        indoor_aqi = np.maximum(indoor_aqi, 2)
        
        df = pd.DataFrame({
            'timestamp': timestamps,
            'indoor_aqi': indoor_aqi,
            'outdoor_aqi': outdoor_aqi
        })
        
        self.logger.info(f"Created mock data with {len(df)} points for testing")
        return df
    
    def _process_data(self, df: Any) -> Dict[str, Any]:
        """Process and clean the raw data."""
        # Convert AQI to PM2.5
        df_pm25 = self.data_processor.convert_aqi_columns(df)
        
        # Filter for night-time data
        night_data = self.data_processor.filter_night_time_data(df_pm25)
        
        min_points = self.config['analysis']['min_data_points']
        if len(night_data) < min_points:
            raise ValueError(
                f"Insufficient night-time data: {len(night_data)} points "
                f"(minimum required: {min_points})"
            )
        
        # Calculate I/O ratio
        night_data = self.data_processor.calculate_io_ratio(night_data)
        
        # Detect outliers
        night_data = self.data_processor.detect_outliers(
            night_data, 
            ['indoor_pm25', 'outdoor_pm25']
        )
        
        # Remove outliers
        clean_mask = ~(night_data['indoor_pm25_outlier'] | night_data['outdoor_pm25_outlier'])
        clean_data = night_data[clean_mask].copy()
        
        if len(clean_data) < 5:
            raise ValueError(
                f"Insufficient clean data after outlier removal: {len(clean_data)} points"
            )
        
        # Prepare model data
        model_data = self.data_processor.prepare_model_data(clean_data)
        
        return {
            'raw_data': df,
            'night_data': night_data,
            'clean_data': clean_data,
            'model_data': model_data
        }
    
    def _analyze_filter_efficiency(self, processed_data: Dict[str, Any]) -> Dict[str, Any]:
        """Run the filter efficiency analysis."""
        model_data = processed_data['model_data']
        
        # Fit the night-time calibration model
        fit_results = self.night_model.fit_maximum_likelihood(
            model_data['indoor_pm25'],
            model_data['outdoor_pm25']
        )
        
        # Update parameter history
        self.night_model.update_parameter_history()
        
        # Get diagnostics
        diagnostics = self.night_model.get_diagnostics()
        
        # Calculate performance metrics
        performance = {
            'current_efficiency': fit_results['efficiency'],
            'efficiency_percentage': fit_results['efficiency'] * 100,
            'infiltration_rate_ach': fit_results['infiltration_rate_ach'],
            'infiltration_rate_m3h': fit_results['infiltration_rate_m3h'],
            'degradation_rate_per_day': self.night_model.get_filter_degradation_rate()
        }
        
        # Data period info
        clean_data = processed_data['clean_data']
        data_period = {
            'start': clean_data['timestamp'].min(),
            'end': clean_data['timestamp'].max(),
            'n_points_total': len(processed_data['night_data']),
            'n_points_clean': len(clean_data)
        }
        
        return {
            'analysis_timestamp': datetime.now(),
            'filter_performance': performance,
            'model_quality': {
                'r_squared': fit_results['r_squared'],
                'rmse': fit_results['rmse'],
                'mae': fit_results['mae']
            },
            'data_period': data_period,
            'diagnostics': diagnostics,
            'fit_results': fit_results
        }
    
    def _write_results(self, results: Dict[str, Any]) -> bool:
        """Write analysis results to Google Sheets."""
        try:
            return self.sheets_client.write_analysis_results(results)
        except Exception as e:
            self.logger.error(f"Failed to write results to Google Sheets: {e}")
            return False
    
    def _create_summary(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Create a human-readable summary of results."""
        performance = results['filter_performance']
        quality = results['model_quality']
        recommendations = results.get('recommendations', {})
        
        # Status determination
        efficiency_pct = performance['efficiency_percentage']
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
        
        summary = {
            'filter_efficiency': {
                'value': round(efficiency_pct, 1),
                'unit': '%',
                'status': status_text,
                'color': status_color
            },
            'air_changes_per_hour': {
                'value': round(performance['infiltration_rate_ach'], 2),
                'unit': 'ACH',
                'description': 'Building air leakage rate'
            },
            'model_confidence': {
                'value': round(quality['r_squared'] * 100, 1),
                'unit': '%',
                'description': 'Analysis reliability'
            },
            'last_updated': results['analysis_timestamp'].isoformat(),
            'alerts': recommendations.get('alerts', []),
            'next_actions': recommendations.get('actions', [])[:3],  # Top 3 actions
            'data_quality': {
                'points_used': results['data_period']['n_points_clean'],
                'time_span_days': (
                    results['data_period']['end'] - 
                    results['data_period']['start']
                ).days
            }
        }
        
        # Add degradation info if available
        if performance['degradation_rate_per_day'] is not None:
            summary['degradation_rate'] = {
                'value': round(performance['degradation_rate_per_day'] * 100, 3),
                'unit': '%/day',
                'description': 'Efficiency loss per day'
            }
        
        return summary


def main():
    """Main entry point for the script."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description='Analyze HVAC filter efficiency from indoor/outdoor PM2.5 data'
    )
    parser.add_argument(
        '--config', '-c',
        default='config.yaml',
        help='Configuration file path (default: config.yaml)'
    )
    parser.add_argument(
        '--days', '-d',
        type=int,
        default=7,
        help='Number of days of historical data to analyze (default: 7)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Run analysis without writing results to Google Sheets'
    )
    parser.add_argument(
        '--log-level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        default='INFO',
        help='Logging level (default: INFO)'
    )
    parser.add_argument(
        '--output', '-o',
        help='Output file for results (JSON format)'
    )
    
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
            print("\n" + "="*60)
            print("FILTER EFFICIENCY ANALYSIS RESULTS")
            print("="*60)
            print(f"Filter Efficiency: {summary['filter_efficiency']['value']}% ({summary['filter_efficiency']['status']})")
            print(f"Air Changes per Hour: {summary['air_changes_per_hour']['value']} ACH")
            print(f"Model Confidence: {summary['model_confidence']['value']}%")
            print(f"Analysis Date: {datetime.fromisoformat(summary['last_updated']).strftime('%Y-%m-%d %H:%M:%S')}")
            
            if summary['alerts']:
                print(f"\n🚨 ALERTS:")
                for alert in summary['alerts']:
                    print(f"  • {alert}")
            
            if summary['next_actions']:
                print(f"\n📋 RECOMMENDED ACTIONS:")
                for i, action in enumerate(summary['next_actions'], 1):
                    print(f"  {i}. {action}")
            
            print(f"\nData Quality: {summary['data_quality']['points_used']} points over {summary['data_quality']['time_span_days']} days")
            print("="*60)
            
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