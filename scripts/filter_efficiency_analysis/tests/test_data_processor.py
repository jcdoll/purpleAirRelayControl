"""
Unit tests for data processing components.
"""

import pytest
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.data_processor import DataProcessor
from tests.test_utils import generate_test_dataset, create_test_config, pm25_to_aqi


class TestAQIConversion:
    """Test AQI to PM2.5 conversion functions."""
    
    def test_aqi_to_pm25_conversion(self):
        """Test AQI to PM2.5 conversion with known values."""
        processor = DataProcessor(create_test_config())
        
        # Test known breakpoints
        test_cases = [
            (0, 0.0),      # Minimum
            (50, 12.0),    # Good/Moderate boundary  
            (100, 35.4),   # Moderate/USG boundary
            (150, 55.4),   # USG/Unhealthy boundary
            (200, 150.4),  # Unhealthy/Very Unhealthy boundary
        ]
        
        for aqi, expected_pm25 in test_cases:
            result = processor.aqi_to_pm25(aqi)
            assert abs(result - expected_pm25) < 0.1, f"AQI {aqi} -> PM2.5 {result}, expected {expected_pm25}"
    
    def test_pm25_to_aqi_conversion(self):
        """Test PM2.5 to AQI conversion with known values."""
        # Test known breakpoints  
        test_cases = [
            (0.0, 0),
            (12.0, 50),
            (35.4, 100),
            (55.4, 150),
            (150.4, 200),
        ]
        
        for pm25, expected_aqi in test_cases:
            result = pm25_to_aqi(pm25)
            assert abs(result - expected_aqi) <= 1, f"PM2.5 {pm25} -> AQI {result}, expected {expected_aqi}"
    
    def test_convert_aqi_columns(self):
        """Test AQI column conversion in DataFrame."""
        processor = DataProcessor(create_test_config())
        
        # Create test data
        test_data = pd.DataFrame({
            'timestamp': pd.date_range('2024-01-01', periods=24, freq='H'),
            'indoor_aqi': [25, 50, 75, 100] * 6,
            'outdoor_aqi': [30, 60, 90, 120] * 6
        })
        
        result = processor.convert_aqi_columns(test_data, 'indoor_aqi', 'outdoor_aqi')
        
        # Check that PM2.5 columns were added
        assert 'indoor_pm25' in result.columns
        assert 'outdoor_pm25' in result.columns
        
        # Check conversions are reasonable
        assert all(result['indoor_pm25'] > 0)
        assert all(result['outdoor_pm25'] > 0)
        assert all(result['indoor_pm25'] < 200)  # Reasonable upper bound


class TestTimeFiltering:
    """Test time-based data filtering functions."""
    
    def test_filter_night_time_data(self):
        """Test night-time data filtering."""
        processor = DataProcessor(create_test_config())
        
        # Create 48-hour test data
        test_data = pd.DataFrame({
            'timestamp': pd.date_range('2024-01-01', periods=48, freq='H'),
            'indoor_pm25': np.random.uniform(5, 20, 48),
            'outdoor_pm25': np.random.uniform(10, 30, 48)
        })
        
        night_data = processor.filter_night_time_data(test_data, 'timestamp')
        
        # Check that only night-time hours are included (22:00-08:00)
        hours = pd.to_datetime(night_data['timestamp']).dt.hour
        valid_hours = set(list(range(22, 24)) + list(range(0, 8)))
        assert all(hour in valid_hours for hour in hours)
        
        # Should have approximately 20 hours out of 48 (10 hours per night * 2 nights)
        assert 18 <= len(night_data) <= 22
    
    def test_filter_night_time_empty_result(self):
        """Test night-time filtering with data that has no night-time hours."""
        processor = DataProcessor(create_test_config())
        
        # Create data with only daytime hours
        test_data = pd.DataFrame({
            'timestamp': pd.date_range('2024-01-01 10:00', periods=6, freq='H'),  # 10:00-15:00
            'indoor_pm25': np.random.uniform(5, 20, 6),
            'outdoor_pm25': np.random.uniform(10, 30, 6)
        })
        
        night_data = processor.filter_night_time_data(test_data, 'timestamp')
        
        # Should return empty DataFrame
        assert len(night_data) == 0


class TestOutlierDetection:
    """Test outlier detection and removal."""
    
    def test_detect_outliers_normal_data(self):
        """Test outlier detection with normal data."""
        processor = DataProcessor(create_test_config())
        
        # Create normal data with no outliers
        np.random.seed(42)
        normal_data = np.random.normal(15, 3, 100)
        
        outliers = processor.detect_outliers(normal_data)
        
        # Should detect very few outliers in normal data
        assert np.sum(outliers) < 10  # Less than 10% outliers
    
    def test_detect_outliers_with_outliers(self):
        """Test outlier detection with intentional outliers."""
        processor = DataProcessor(create_test_config())
        
        # Create data with clear outliers
        normal_data = np.random.normal(15, 3, 95)
        outlier_data = np.array([100, 120, 150, 200, 250])  # Clear outliers
        test_data = np.concatenate([normal_data, outlier_data])
        
        outliers = processor.detect_outliers(test_data)
        
        # Should detect the 5 outliers we added
        assert np.sum(outliers) >= 4  # At least 4 of the 5 outliers detected
    
    def test_detect_outliers_io_ratio(self):
        """Test outlier detection on indoor/outdoor ratios."""
        processor = DataProcessor(create_test_config())
        
        # Create test data with some bad ratios
        test_data = pd.DataFrame({
            'indoor_pm25': [10, 12, 15, 18, 100, 8],  # One outlier (100)
            'outdoor_pm25': [20, 25, 30, 35, 30, 15]
        })
        
        result = processor.prepare_model_data(test_data, 'indoor_pm25', 'outdoor_pm25')
        
        # Should remove the outlier point
        assert len(result) == 5  # Original 6 minus 1 outlier


class TestDataPreparation:
    """Test data preparation for model fitting."""
    
    def test_prepare_model_data_basic(self):
        """Test basic data preparation functionality."""
        processor = DataProcessor(create_test_config())
        
        # Create clean test data
        test_data = pd.DataFrame({
            'indoor_pm25': [8, 10, 12, 15, 18],
            'outdoor_pm25': [15, 20, 25, 30, 35]
        })
        
        result = processor.prepare_model_data(test_data, 'indoor_pm25', 'outdoor_pm25')
        
        # Check basic structure
        assert 'indoor_values' in result
        assert 'outdoor_values' in result
        assert 'io_ratio' in result
        
        # Check data types
        assert isinstance(result['indoor_values'], np.ndarray)
        assert isinstance(result['outdoor_values'], np.ndarray)
        assert isinstance(result['io_ratio'], np.ndarray)
        
        # Check that indoor/outdoor ratio makes sense
        expected_ratios = test_data['indoor_pm25'] / test_data['outdoor_pm25']
        np.testing.assert_array_almost_equal(result['io_ratio'], expected_ratios)
    
    def test_prepare_model_data_with_missing_values(self):
        """Test data preparation with missing/invalid values."""
        processor = DataProcessor(create_test_config())
        
        # Create data with missing and invalid values
        test_data = pd.DataFrame({
            'indoor_pm25': [8, np.nan, 12, 0, 18],
            'outdoor_pm25': [15, 20, np.nan, 30, 0]
        })
        
        result = processor.prepare_model_data(test_data, 'indoor_pm25', 'outdoor_pm25')
        
        # Should remove rows with missing or zero values
        assert len(result['indoor_values']) == 1  # Only one valid pair
    
    def test_prepare_model_data_insufficient_data(self):
        """Test data preparation with insufficient data points."""
        processor = DataProcessor(create_test_config())
        
        # Create data with too few points
        test_data = pd.DataFrame({
            'indoor_pm25': [8, 10],
            'outdoor_pm25': [15, 20]
        })
        
        # Should raise an error or return empty result
        result = processor.prepare_model_data(test_data, 'indoor_pm25', 'outdoor_pm25')
        
        # With min_data_points = 10 in config, should return empty or minimal data
        assert len(result['indoor_values']) < 10


class TestDataProcessorIntegration:
    """Integration tests for the complete data processing pipeline."""
    
    def test_full_pipeline_with_synthetic_data(self):
        """Test complete data processing pipeline with synthetic data."""
        # Generate synthetic test data
        dataset, true_params = generate_test_dataset(
            scenario="good_filter",
            days=7,
            random_seed=42
        )
        
        processor = DataProcessor(create_test_config())
        
        # Convert AQI to PM2.5
        processed_data = processor.convert_aqi_columns(
            dataset, 'indoor_aqi', 'outdoor_aqi'
        )
        
        # Filter night-time data
        night_data = processor.filter_night_time_data(processed_data, 'timestamp')
        
        # Prepare for modeling
        model_data = processor.prepare_model_data(
            night_data, 'indoor_pm25', 'outdoor_pm25'
        )
        
        # Check that we have reasonable data for modeling
        assert len(model_data['indoor_values']) >= 10
        assert all(model_data['io_ratio'] > 0)
        assert all(model_data['io_ratio'] < 1.5)  # Indoor should generally be lower than outdoor
        
        # Check that conversions are consistent
        # The I/O ratio should reflect the true filter efficiency
        mean_ratio = np.mean(model_data['io_ratio'])
        expected_ratio = true_params['filter_efficiency']  # Approximate expected ratio
        
        # The ratio should be significantly less than 1.0 for a good filter
        assert mean_ratio < 0.8, f"Mean I/O ratio {mean_ratio} too high for good filter"
    
    def test_building_parameter_calculation(self):
        """Test calculation of building parameters from config."""
        config = create_test_config()
        processor = DataProcessor(config)
        
        # Check that building parameters were calculated correctly
        expected_volume = 3000 * 9 * 0.0283168  # sq ft * ft * conversion
        expected_filtration = 1500 * 1.69901     # CFM * conversion
        
        assert abs(processor.volume - expected_volume) < 1.0
        assert abs(processor.filtration_rate - expected_filtration) < 10.0
        assert processor.deposition_rate > 0
    
    def test_different_scenarios(self):
        """Test data processing with different filter scenarios."""
        scenarios = ["good_filter", "degraded_filter", "poor_filter"]
        
        for scenario in scenarios:
            dataset, true_params = generate_test_dataset(
                scenario=scenario,
                days=5,
                random_seed=42
            )
            
            processor = DataProcessor(create_test_config())
            
            # Process the data
            processed_data = processor.convert_aqi_columns(
                dataset, 'indoor_aqi', 'outdoor_aqi'
            )
            night_data = processor.filter_night_time_data(processed_data, 'timestamp')
            model_data = processor.prepare_model_data(
                night_data, 'indoor_pm25', 'outdoor_pm25'
            )
            
            # All scenarios should produce valid data
            assert len(model_data['indoor_values']) > 5
            
            # Different scenarios should produce different I/O ratios
            mean_ratio = np.mean(model_data['io_ratio'])
            
            if scenario == "good_filter":
                assert mean_ratio < 0.7  # Good filter should have low ratio
            elif scenario == "poor_filter":
                assert mean_ratio > 0.8  # Poor filter should have high ratio


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 