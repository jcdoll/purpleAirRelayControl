"""
Unit tests for night-time calibration model.
"""

import pytest
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.night_calibration import NightTimeCalibration
from utils.data_processor import DataProcessor
from tests.test_utils import generate_test_dataset, create_test_config


class TestNightTimeCalibrationBasics:
    """Test basic functionality of the NightTimeCalibration model."""
    
    def test_model_initialization(self):
        """Test model initialization with different configurations."""
        config = create_test_config()
        processor = DataProcessor(config)
        building_params = processor._calculate_building_params()
        
        model = NightTimeCalibration(config, building_params)
        
        # Check that model attributes are set correctly
        assert model.volume > 0
        assert model.filtration_rate > 0
        assert model.deposition_rate > 0
        assert hasattr(model, 'config')
    
    def test_steady_state_model(self):
        """Test the steady-state mass balance calculation."""
        config = create_test_config()
        processor = DataProcessor(config)
        building_params = processor._calculate_building_params()
        
        model = NightTimeCalibration(config, building_params)
        
        # Test with known parameters
        outdoor_pm25 = 20.0
        filter_efficiency = 0.8
        infiltration_rate = 400.0  # m³/h
        
        indoor_pm25 = model.steady_state_model(
            outdoor_pm25, infiltration_rate, filter_efficiency
        )
        
        # Indoor should be lower than outdoor with good filter
        assert indoor_pm25 < outdoor_pm25
        assert indoor_pm25 > 0
        
        # Test with perfect filter (efficiency = 1.0)
        indoor_perfect = model.steady_state_model(
            outdoor_pm25, infiltration_rate, 1.0
        )
        assert indoor_perfect < indoor_pm25  # Should be even lower
        
        # Test with no filtration (efficiency = 0.0)
        indoor_no_filter = model.steady_state_model(
            outdoor_pm25, infiltration_rate, 0.0
        )
        assert indoor_no_filter > indoor_pm25  # Should be higher
    
    def test_log_prior_function(self):
        """Test the log prior probability function."""
        config = create_test_config()
        processor = DataProcessor(config)
        building_params = processor._calculate_building_params()
        
        model = NightTimeCalibration(config, building_params)
        
        # Test with reasonable parameters
        efficiency = 0.8
        infiltration_rate = 400.0  # m³/h
        
        log_prior = model.log_prior(efficiency, infiltration_rate)
        assert np.isfinite(log_prior)
        
        # Test boundary conditions
        # Efficiency = 0 should have low prior probability
        log_prior_zero = model.log_prior(0.0, infiltration_rate)
        assert log_prior_zero < log_prior
        
        # Efficiency > 1 should be impossible
        log_prior_invalid = model.log_prior(1.5, infiltration_rate)
        assert log_prior_invalid == -np.inf
        
        # Negative infiltration should be impossible
        log_prior_negative = model.log_prior(efficiency, -100.0)
        assert log_prior_negative == -np.inf
    
    def test_log_likelihood_function(self):
        """Test the log likelihood calculation."""
        config = create_test_config()
        processor = DataProcessor(config)
        building_params = processor._calculate_building_params()
        
        model = NightTimeCalibration(config, building_params)
        
        # Create simple test data
        indoor_values = np.array([8, 10, 12, 15])
        outdoor_values = np.array([15, 20, 25, 30])
        
        efficiency = 0.8
        infiltration_rate = 400.0
        
        log_likelihood = model.log_likelihood(
            efficiency, infiltration_rate, indoor_values, outdoor_values
        )
        
        assert np.isfinite(log_likelihood)
        assert log_likelihood <= 0  # Log probability should be ≤ 0


class TestParameterEstimation:
    """Test parameter estimation functionality."""
    
    def test_fit_with_synthetic_data(self):
        """Test model fitting with synthetic data where we know the true parameters."""
        # Generate test data with known parameters
        dataset, true_params = generate_test_dataset(
            scenario="good_filter",
            days=10,
            random_seed=42
        )
        
        # Process the data
        config = create_test_config()
        processor = DataProcessor(config)
        
        processed_data = processor.convert_aqi_columns(
            dataset, 'indoor_aqi', 'outdoor_aqi'
        )
        night_data = processor.filter_night_time_data(processed_data, 'timestamp')
        model_data = processor.prepare_model_data(
            night_data, 'indoor_pm25', 'outdoor_pm25'
        )
        
        # Fit the model
        building_params = processor._calculate_building_params()
        model = NightTimeCalibration(config, building_params)
        
        fit_results = model.fit_maximum_likelihood(
            model_data['indoor_values'],
            model_data['outdoor_values']
        )
        
        # Check that fit was successful
        assert fit_results['success']
        assert 'filter_efficiency' in fit_results
        assert 'infiltration_rate_m3h' in fit_results
        assert 'infiltration_rate_ach' in fit_results
        
        # Check that estimated parameters are reasonable
        estimated_efficiency = fit_results['filter_efficiency']
        estimated_infiltration = fit_results['infiltration_rate_ach']
        
        assert 0.0 <= estimated_efficiency <= 1.0
        assert estimated_infiltration > 0
        
        # Check that estimates are close to true values (within reasonable tolerance)
        true_efficiency = true_params['filter_efficiency']
        true_infiltration = true_params['infiltration_ach']
        
        efficiency_error = abs(estimated_efficiency - true_efficiency)
        infiltration_error = abs(estimated_infiltration - true_infiltration)
        
        # Allow for some estimation error due to noise
        assert efficiency_error < 0.15, f"Efficiency error {efficiency_error:.3f} too large"
        assert infiltration_error < 0.3, f"Infiltration error {infiltration_error:.3f} too large"
    
    def test_fit_different_scenarios(self):
        """Test model fitting with different filter scenarios."""
        scenarios = ["good_filter", "degraded_filter", "poor_filter"]
        
        for scenario in scenarios:
            dataset, true_params = generate_test_dataset(
                scenario=scenario,
                days=7,
                random_seed=42
            )
            
            # Process data
            config = create_test_config()
            processor = DataProcessor(config)
            
            processed_data = processor.convert_aqi_columns(
                dataset, 'indoor_aqi', 'outdoor_aqi'
            )
            night_data = processor.filter_night_time_data(processed_data, 'timestamp')
            model_data = processor.prepare_model_data(
                night_data, 'indoor_pm25', 'outdoor_pm25'
            )
            
            # Fit model
            building_params = processor._calculate_building_params()
            model = NightTimeCalibration(config, building_params)
            
            fit_results = model.fit_maximum_likelihood(
                model_data['indoor_values'],
                model_data['outdoor_values']
            )
            
            # All scenarios should produce successful fits
            assert fit_results['success'], f"Fit failed for scenario {scenario}"
            
            estimated_efficiency = fit_results['filter_efficiency']
            true_efficiency = true_params['filter_efficiency']
            
            # Check that different scenarios produce different efficiency estimates
            # and that they're in the right ballpark
            if scenario == "good_filter":
                assert estimated_efficiency > 0.6, f"Good filter efficiency too low: {estimated_efficiency}"
            elif scenario == "poor_filter":
                assert estimated_efficiency < 0.5, f"Poor filter efficiency too high: {estimated_efficiency}"
    
    def test_fit_insufficient_data(self):
        """Test model behavior with insufficient data."""
        config = create_test_config()
        processor = DataProcessor(config)
        building_params = processor._calculate_building_params()
        
        model = NightTimeCalibration(config, building_params)
        
        # Try to fit with very little data
        indoor_values = np.array([10, 12])
        outdoor_values = np.array([20, 25])
        
        fit_results = model.fit_maximum_likelihood(indoor_values, outdoor_values)
        
        # Should handle insufficient data gracefully
        assert 'success' in fit_results
        if not fit_results['success']:
            assert 'error' in fit_results


class TestModelPredictions:
    """Test model prediction functionality."""
    
    def test_predict_basic(self):
        """Test basic prediction functionality."""
        # Generate and fit model first
        dataset, true_params = generate_test_dataset(
            scenario="good_filter",
            days=7,
            random_seed=42
        )
        
        config = create_test_config()
        processor = DataProcessor(config)
        
        processed_data = processor.convert_aqi_columns(
            dataset, 'indoor_aqi', 'outdoor_aqi'
        )
        night_data = processor.filter_night_time_data(processed_data, 'timestamp')
        model_data = processor.prepare_model_data(
            night_data, 'indoor_pm25', 'outdoor_pm25'
        )
        
        building_params = processor._calculate_building_params()
        model = NightTimeCalibration(config, building_params)
        
        fit_results = model.fit_maximum_likelihood(
            model_data['indoor_values'],
            model_data['outdoor_values']
        )
        
        # Make predictions
        test_outdoor = np.array([15, 20, 25, 30])
        predictions = model.predict(
            test_outdoor,
            fit_results['filter_efficiency'],
            fit_results['infiltration_rate_m3h']
        )
        
        # Check prediction properties
        assert len(predictions) == len(test_outdoor)
        assert all(predictions > 0)
        assert all(predictions < test_outdoor)  # Indoor should be lower than outdoor
    
    def test_predict_edge_cases(self):
        """Test predictions with edge case outdoor concentrations."""
        config = create_test_config()
        processor = DataProcessor(config)
        building_params = processor._calculate_building_params()
        
        model = NightTimeCalibration(config, building_params)
        
        # Test with various outdoor concentrations
        test_cases = [
            np.array([1.0]),     # Very low
            np.array([100.0]),   # High
            np.array([0.1]),     # Near zero
        ]
        
        efficiency = 0.8
        infiltration_rate = 400.0
        
        for outdoor_values in test_cases:
            predictions = model.predict(outdoor_values, efficiency, infiltration_rate)
            
            assert len(predictions) == len(outdoor_values)
            assert all(predictions > 0)
            assert all(np.isfinite(predictions))


class TestModelDiagnostics:
    """Test model diagnostic and validation functionality."""
    
    def test_get_diagnostics(self):
        """Test diagnostic calculation."""
        # Generate and fit model
        dataset, true_params = generate_test_dataset(
            scenario="good_filter",
            days=10,
            random_seed=42
        )
        
        config = create_test_config()
        processor = DataProcessor(config)
        
        processed_data = processor.convert_aqi_columns(
            dataset, 'indoor_aqi', 'outdoor_aqi'
        )
        night_data = processor.filter_night_time_data(processed_data, 'timestamp')
        model_data = processor.prepare_model_data(
            night_data, 'indoor_pm25', 'outdoor_pm25'
        )
        
        building_params = processor._calculate_building_params()
        model = NightTimeCalibration(config, building_params)
        
        fit_results = model.fit_maximum_likelihood(
            model_data['indoor_values'],
            model_data['outdoor_values']
        )
        
        # Calculate diagnostics
        diagnostics = model.get_diagnostics(
            model_data['indoor_values'],
            model_data['outdoor_values'],
            fit_results['filter_efficiency'],
            fit_results['infiltration_rate_m3h']
        )
        
        # Check that all expected metrics are present
        expected_metrics = ['r_squared', 'rmse', 'mae', 'mean_bias', 'data_points']
        for metric in expected_metrics:
            assert metric in diagnostics
            assert np.isfinite(diagnostics[metric])
        
        # Check that R² is reasonable (should be good for synthetic data)
        assert 0.5 <= diagnostics['r_squared'] <= 1.0
        
        # Check that errors are positive
        assert diagnostics['rmse'] >= 0
        assert diagnostics['mae'] >= 0
    
    def test_generate_recommendations(self):
        """Test recommendation generation."""
        config = create_test_config()
        processor = DataProcessor(config)
        building_params = processor._calculate_building_params()
        
        model = NightTimeCalibration(config, building_params)
        
        # Test with different efficiency levels
        test_cases = [
            (0.9, 0.6, 0.95),   # Excellent filter
            (0.7, 0.8, 0.90),   # Good filter
            (0.5, 1.0, 0.85),   # Declining filter
            (0.3, 1.2, 0.75),   # Poor filter
        ]
        
        for efficiency, infiltration_ach, r_squared in test_cases:
            recommendations = model.generate_recommendations(
                efficiency, infiltration_ach, r_squared
            )
            
            assert 'status' in recommendations
            assert 'message' in recommendations
            assert 'actions' in recommendations
            
            # Check that status is one of expected values
            valid_statuses = ['excellent', 'good', 'declining', 'poor']
            assert recommendations['status'] in valid_statuses


class TestModelIntegration:
    """Integration tests for the complete model pipeline."""
    
    def test_full_analysis_pipeline(self):
        """Test the complete analysis pipeline from data to recommendations."""
        # Generate test data
        dataset, true_params = generate_test_dataset(
            scenario="degraded_filter",
            days=14,
            random_seed=42
        )
        
        # Complete pipeline
        config = create_test_config()
        processor = DataProcessor(config)
        
        # Data processing
        processed_data = processor.convert_aqi_columns(
            dataset, 'indoor_aqi', 'outdoor_aqi'
        )
        night_data = processor.filter_night_time_data(processed_data, 'timestamp')
        model_data = processor.prepare_model_data(
            night_data, 'indoor_pm25', 'outdoor_pm25'
        )
        
        # Model fitting
        building_params = processor._calculate_building_params()
        model = NightTimeCalibration(config, building_params)
        
        fit_results = model.fit_maximum_likelihood(
            model_data['indoor_values'],
            model_data['outdoor_values']
        )
        
        # Diagnostics
        diagnostics = model.get_diagnostics(
            model_data['indoor_values'],
            model_data['outdoor_values'],
            fit_results['filter_efficiency'],
            fit_results['infiltration_rate_m3h']
        )
        
        # Recommendations
        recommendations = model.generate_recommendations(
            fit_results['filter_efficiency'],
            fit_results['infiltration_rate_ach'],
            diagnostics['r_squared']
        )
        
        # Verify complete pipeline worked
        assert fit_results['success']
        assert diagnostics['r_squared'] > 0.3  # Reasonable fit
        assert recommendations['status'] in ['excellent', 'good', 'declining', 'poor']
        
        # Check that the analysis detected a degraded filter appropriately
        if fit_results['filter_efficiency'] < 0.7:
            assert recommendations['status'] in ['declining', 'poor']
    
    def test_robustness_to_noise(self):
        """Test model robustness to different noise levels."""
        # Test with different random seeds (different noise realizations)
        seeds = [42, 123, 456, 789]
        efficiency_estimates = []
        
        for seed in seeds:
            dataset, true_params = generate_test_dataset(
                scenario="good_filter",
                days=10,
                random_seed=seed
            )
            
            config = create_test_config()
            processor = DataProcessor(config)
            
            processed_data = processor.convert_aqi_columns(
                dataset, 'indoor_aqi', 'outdoor_aqi'
            )
            night_data = processor.filter_night_time_data(processed_data, 'timestamp')
            model_data = processor.prepare_model_data(
                night_data, 'indoor_pm25', 'outdoor_pm25'
            )
            
            building_params = processor._calculate_building_params()
            model = NightTimeCalibration(config, building_params)
            
            fit_results = model.fit_maximum_likelihood(
                model_data['indoor_values'],
                model_data['outdoor_values']
            )
            
            if fit_results['success']:
                efficiency_estimates.append(fit_results['filter_efficiency'])
        
        # Check that estimates are consistent across noise realizations
        if len(efficiency_estimates) > 1:
            efficiency_std = np.std(efficiency_estimates)
            assert efficiency_std < 0.1, f"Efficiency estimates too variable: std={efficiency_std}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 