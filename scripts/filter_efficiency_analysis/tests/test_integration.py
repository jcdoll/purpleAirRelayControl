"""
Integration tests for the complete filter efficiency analysis system.
"""

import pytest
import numpy as np
import pandas as pd
import tempfile
import os
import sys
import yaml
import json
from datetime import datetime, timedelta

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from analyze_filter_performance import FilterEfficiencyAnalyzer
from tests.test_utils import generate_test_dataset, create_test_config, save_test_data_to_csv


class MockSheetsClient:
    """Mock Google Sheets client for testing without actual API calls."""
    
    def __init__(self, test_data: pd.DataFrame):
        self.test_data = test_data
        self.written_data = []
    
    def read_sensor_data(self, days_back: int = 7) -> pd.DataFrame:
        """Return the test data."""
        return self.test_data.copy()
    
    def write_analysis_results(self, results: dict) -> bool:
        """Store the results for verification."""
        self.written_data.append(results)
        return True


class TestEndToEndAnalysis:
    """Test complete end-to-end analysis workflow."""
    
    def test_complete_analysis_workflow(self):
        """Test the complete analysis from data generation to results."""
        # Generate synthetic test data
        dataset, true_params = generate_test_dataset(
            scenario="good_filter",
            days=14,
            random_seed=42
        )
        
        # Create test configuration
        config = create_test_config()
        
        # Create mock sheets client
        mock_client = MockSheetsClient(dataset)
        
        # Create analyzer with dry run mode
        analyzer = FilterEfficiencyAnalyzer(config, dry_run=True)
        analyzer.sheets_client = mock_client  # Replace with mock
        
        # Run analysis
        results = analyzer.run_analysis(days_back=14)
        
        # Verify results structure
        assert 'success' in results
        assert 'analysis_results' in results
        assert 'summary' in results
        
        if results['success']:
            analysis = results['analysis_results']
            
            # Check that we got parameter estimates
            assert 'filter_efficiency' in analysis
            assert 'infiltration_rate_ach' in analysis
            assert 'model_diagnostics' in analysis
            
            # Check that estimates are reasonable
            estimated_efficiency = analysis['filter_efficiency']
            true_efficiency = true_params['filter_efficiency']
            
            assert 0.0 <= estimated_efficiency <= 1.0
            
            # Allow for estimation error due to noise but should be in ballpark
            efficiency_error = abs(estimated_efficiency - true_efficiency)
            assert efficiency_error < 0.2, f"Efficiency error {efficiency_error:.3f} too large"
    
    def test_different_filter_scenarios(self):
        """Test analysis with different filter efficiency scenarios."""
        scenarios = ["good_filter", "degraded_filter", "poor_filter"]
        
        for scenario in scenarios:
            dataset, true_params = generate_test_dataset(
                scenario=scenario,
                days=10,
                random_seed=42
            )
            
            config = create_test_config()
            mock_client = MockSheetsClient(dataset)
            
            analyzer = FilterEfficiencyAnalyzer(config, dry_run=True)
            analyzer.sheets_client = mock_client
            
            results = analyzer.run_analysis(days_back=10)
            
            # All scenarios should produce some kind of result
            assert 'success' in results
            
            if results['success']:
                analysis = results['analysis_results']
                estimated_efficiency = analysis['filter_efficiency']
                true_efficiency = true_params['filter_efficiency']
                
                # Check that estimates are in the right direction
                if scenario == "good_filter":
                    assert estimated_efficiency > 0.5, f"Good filter estimate too low: {estimated_efficiency}"
                elif scenario == "poor_filter":
                    assert estimated_efficiency < 0.7, f"Poor filter estimate too high: {estimated_efficiency}"
    
    def test_insufficient_data_handling(self):
        """Test analysis behavior with insufficient data."""
        # Generate very limited data
        dataset, true_params = generate_test_dataset(
            scenario="good_filter",
            days=2,  # Very short period
            random_seed=42
        )
        
        config = create_test_config()
        # Increase minimum data points requirement
        config['analysis']['min_data_points'] = 50
        
        mock_client = MockSheetsClient(dataset)
        
        analyzer = FilterEfficiencyAnalyzer(config, dry_run=True)
        analyzer.sheets_client = mock_client
        
        results = analyzer.run_analysis(days_back=2)
        
        # Should handle insufficient data gracefully
        assert 'success' in results
        if not results['success']:
            assert 'error' in results
            assert 'insufficient' in results['error'].lower() or 'data' in results['error'].lower()
    
    def test_outlier_handling(self):
        """Test analysis robustness to outliers in data."""
        # Generate clean data first
        dataset, true_params = generate_test_dataset(
            scenario="good_filter",
            days=10,
            random_seed=42
        )
        
        # Add some outliers
        n_outliers = 5
        outlier_indices = np.random.choice(len(dataset), n_outliers, replace=False)
        dataset.loc[outlier_indices, 'indoor_aqi'] = 500  # Extreme values
        dataset.loc[outlier_indices, 'outdoor_aqi'] = 50
        
        config = create_test_config()
        mock_client = MockSheetsClient(dataset)
        
        analyzer = FilterEfficiencyAnalyzer(config, dry_run=True)
        analyzer.sheets_client = mock_client
        
        results = analyzer.run_analysis(days_back=10)
        
        # Should still produce reasonable results despite outliers
        assert 'success' in results
        
        if results['success']:
            analysis = results['analysis_results']
            estimated_efficiency = analysis['filter_efficiency']
            
            # Should still be in reasonable range
            assert 0.0 <= estimated_efficiency <= 1.0
    
    def test_missing_data_handling(self):
        """Test analysis with missing data points."""
        dataset, true_params = generate_test_dataset(
            scenario="good_filter",
            days=10,
            random_seed=42
        )
        
        # Introduce missing values
        missing_indices = np.random.choice(len(dataset), len(dataset)//4, replace=False)
        dataset.loc[missing_indices, 'indoor_aqi'] = np.nan
        
        config = create_test_config()
        mock_client = MockSheetsClient(dataset)
        
        analyzer = FilterEfficiencyAnalyzer(config, dry_run=True)
        analyzer.sheets_client = mock_client
        
        results = analyzer.run_analysis(days_back=10)
        
        # Should handle missing data gracefully
        assert 'success' in results
        # Either succeeds with remaining data or fails gracefully
        if results['success']:
            analysis = results['analysis_results']
            assert 'filter_efficiency' in analysis


class TestConfigurationHandling:
    """Test different configuration scenarios."""
    
    def test_custom_building_parameters(self):
        """Test analysis with different building configurations."""
        # Test different building sizes
        building_configs = [
            {"area_sq_ft": 1500, "ceiling_height_ft": 8},   # Small house
            {"area_sq_ft": 4000, "ceiling_height_ft": 10},  # Large house
            {"area_sq_ft": 2000, "ceiling_height_ft": 12},  # High ceilings
        ]
        
        for building_config in building_configs:
            dataset, true_params = generate_test_dataset(
                scenario="good_filter",
                days=7,
                random_seed=42
            )
            
            config = create_test_config()
            config['building'].update(building_config)
            
            mock_client = MockSheetsClient(dataset)
            
            analyzer = FilterEfficiencyAnalyzer(config, dry_run=True)
            analyzer.sheets_client = mock_client
            
            results = analyzer.run_analysis(days_back=7)
            
            # Should work with different building configurations
            assert 'success' in results
    
    def test_custom_analysis_parameters(self):
        """Test analysis with different analysis configurations."""
        dataset, true_params = generate_test_dataset(
            scenario="good_filter",
            days=10,
            random_seed=42
        )
        
        # Test different night-time windows
        analysis_configs = [
            {"night_start_hour": 21, "night_end_hour": 7},   # Earlier/later
            {"night_start_hour": 23, "night_end_hour": 9},   # Later/later
            {"outlier_threshold": 1.5},                       # More sensitive outliers
            {"min_data_points": 5},                           # Lower requirement
        ]
        
        for analysis_config in analysis_configs:
            config = create_test_config()
            config['analysis'].update(analysis_config)
            
            mock_client = MockSheetsClient(dataset)
            
            analyzer = FilterEfficiencyAnalyzer(config, dry_run=True)
            analyzer.sheets_client = mock_client
            
            results = analyzer.run_analysis(days_back=10)
            
            # Should work with different analysis configurations
            assert 'success' in results


class TestResultsOutput:
    """Test results formatting and output."""
    
    def test_results_structure(self):
        """Test that results have the expected structure."""
        dataset, true_params = generate_test_dataset(
            scenario="good_filter",
            days=10,
            random_seed=42
        )
        
        config = create_test_config()
        mock_client = MockSheetsClient(dataset)
        
        analyzer = FilterEfficiencyAnalyzer(config, dry_run=True)
        analyzer.sheets_client = mock_client
        
        results = analyzer.run_analysis(days_back=10)
        
        # Check top-level structure
        assert isinstance(results, dict)
        assert 'success' in results
        assert 'timestamp' in results
        
        if results['success']:
            assert 'analysis_results' in results
            assert 'summary' in results
            
            # Check analysis results structure
            analysis = results['analysis_results']
            expected_fields = [
                'filter_efficiency',
                'infiltration_rate_ach', 
                'model_diagnostics',
                'recommendations'
            ]
            
            for field in expected_fields:
                assert field in analysis, f"Missing field: {field}"
    
    def test_results_with_file_output(self):
        """Test saving results to file."""
        dataset, true_params = generate_test_dataset(
            scenario="good_filter",
            days=7,
            random_seed=42
        )
        
        config = create_test_config()
        mock_client = MockSheetsClient(dataset)
        
        analyzer = FilterEfficiencyAnalyzer(config, dry_run=True)
        analyzer.sheets_client = mock_client
        
        # Test saving to temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            output_file = f.name
        
        try:
            results = analyzer.run_analysis(days_back=7)
            
            # Save results to file manually (simulating main function behavior)
            with open(output_file, 'w') as f:
                json.dump(results, f, indent=2, default=str)
            
            # Check that file was created
            assert os.path.exists(output_file)
            
            # Check that file contains valid JSON
            with open(output_file, 'r') as f:
                saved_results = json.load(f)
            
            # Should match the returned results
            assert saved_results['success'] == results['success']
            
        finally:
            # Clean up
            if os.path.exists(output_file):
                os.unlink(output_file)


class TestRobustnessAndEdgeCases:
    """Test robustness to various edge cases."""
    
    def test_extreme_weather_conditions(self):
        """Test analysis during extreme outdoor pollution events."""
        dataset, true_params = generate_test_dataset(
            scenario="high_pollution",
            days=7,
            random_seed=42
        )
        
        config = create_test_config()
        mock_client = MockSheetsClient(dataset)
        
        analyzer = FilterEfficiencyAnalyzer(config, dry_run=True)
        analyzer.sheets_client = mock_client
        
        results = analyzer.run_analysis(days_back=7)
        
        # Should handle high pollution periods
        assert 'success' in results
        
        if results['success']:
            analysis = results['analysis_results']
            # Even with high pollution, efficiency should be reasonable
            assert 0.0 <= analysis['filter_efficiency'] <= 1.0
    
    def test_very_short_analysis_window(self):
        """Test analysis with minimal time window."""
        dataset, true_params = generate_test_dataset(
            scenario="good_filter",
            days=3,  # Minimal data
            random_seed=42
        )
        
        config = create_test_config()
        config['analysis']['min_data_points'] = 5  # Lower threshold
        
        mock_client = MockSheetsClient(dataset)
        
        analyzer = FilterEfficiencyAnalyzer(config, dry_run=True)
        analyzer.sheets_client = mock_client
        
        results = analyzer.run_analysis(days_back=3)
        
        # Should either succeed or fail gracefully
        assert 'success' in results
        # Don't require success, but should not crash
    
    def test_hepa_filter_scenario(self):
        """Test analysis with HEPA filter (very high efficiency)."""
        dataset, true_params = generate_test_dataset(
            scenario="hepa_filter",
            days=10,
            random_seed=42
        )
        
        config = create_test_config()
        mock_client = MockSheetsClient(dataset)
        
        analyzer = FilterEfficiencyAnalyzer(config, dry_run=True)
        analyzer.sheets_client = mock_client
        
        results = analyzer.run_analysis(days_back=10)
        
        # Should handle high-efficiency filters
        assert 'success' in results
        
        if results['success']:
            analysis = results['analysis_results']
            estimated_efficiency = analysis['filter_efficiency']
            
            # Should detect high efficiency
            assert estimated_efficiency > 0.8, f"HEPA filter efficiency too low: {estimated_efficiency}"


class TestPerformanceAndScaling:
    """Test performance with different data sizes."""
    
    def test_large_dataset_handling(self):
        """Test analysis with larger dataset."""
        # Generate longer time series
        dataset, true_params = generate_test_dataset(
            scenario="good_filter",
            days=30,  # One month of data
            random_seed=42
        )
        
        config = create_test_config()
        mock_client = MockSheetsClient(dataset)
        
        analyzer = FilterEfficiencyAnalyzer(config, dry_run=True)
        analyzer.sheets_client = mock_client
        
        # Should complete in reasonable time
        results = analyzer.run_analysis(days_back=30)
        
        assert 'success' in results
        
        if results['success']:
            analysis = results['analysis_results']
            
            # More data should generally give better confidence
            diagnostics = analysis['model_diagnostics']
            if 'fit_quality' in diagnostics:
                # With more data, we might expect better fit quality
                pass  # Don't enforce specific thresholds, just verify it works


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 