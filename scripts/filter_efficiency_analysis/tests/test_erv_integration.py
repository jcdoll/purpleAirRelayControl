#!/usr/bin/env python3
"""
Test cases for ERV (Energy Recovery Ventilator) integration.

Tests that ERV airflow is properly added to natural infiltration
and affects the mass balance calculations correctly.
"""

import pytest
from utils.config_helpers import calculate_infiltration_rate, _calculate_erv_infiltration
from tests.test_utils import create_test_config


def test_erv_disabled():
    """Test that ERV doesn't contribute when disabled."""
    
    config = create_test_config()
    config['hvac']['erv_enabled'] = False
    config['hvac']['erv_flow_rate_cfm'] = 200.0
    
    erv_ach = _calculate_erv_infiltration(config)
    assert erv_ach == 0.0, "ERV should contribute 0 ACH when disabled"


def test_erv_enabled_calculation():
    """Test ERV ACH calculation when enabled."""
    
    config = create_test_config()
    config['hvac']['erv_enabled'] = True
    config['hvac']['erv_flow_rate_cfm'] = 170.0
    config['hvac']['erv_runtime_fraction'] = 0.9
    
    # Calculate expected ERV ACH
    # 170 CFM * 0.9 runtime * 60 min/hr / (3000 sq ft * 9 ft) = expected ACH
    expected_erv_ach = (170 * 0.9 * 60) / (3000 * 9)
    
    erv_ach = _calculate_erv_infiltration(config)
    assert abs(erv_ach - expected_erv_ach) < 0.001, f"ERV ACH should be {expected_erv_ach:.3f}, got {erv_ach:.3f}"


def test_erv_adds_to_natural_infiltration():
    """Test that ERV is added to natural infiltration rate."""
    
    config = create_test_config()
    
    # Test without ERV
    config['hvac']['erv_enabled'] = False
    natural_only = calculate_infiltration_rate(config)
    
    # Test with ERV
    config['hvac']['erv_enabled'] = True
    config['hvac']['erv_flow_rate_cfm'] = 170.0
    config['hvac']['erv_runtime_fraction'] = 0.9
    total_with_erv = calculate_infiltration_rate(config)
    
    # ERV should increase total infiltration
    assert total_with_erv > natural_only, f"ERV should increase infiltration: {total_with_erv:.3f} > {natural_only:.3f}"
    
    # Calculate expected ERV contribution
    expected_erv = (170 * 0.9 * 60) / (3000 * 9)
    expected_total = natural_only + expected_erv
    
    assert abs(total_with_erv - expected_total) < 0.001, f"Total should be {expected_total:.3f}, got {total_with_erv:.3f}"


def test_erv_runtime_fraction_effect():
    """Test that runtime fraction affects ERV contribution."""
    
    config = create_test_config()
    config['hvac']['erv_enabled'] = True
    config['hvac']['erv_flow_rate_cfm'] = 170.0
    
    # Test different runtime fractions
    config['hvac']['erv_runtime_fraction'] = 1.0
    erv_100_percent = _calculate_erv_infiltration(config)
    
    config['hvac']['erv_runtime_fraction'] = 0.5
    erv_50_percent = _calculate_erv_infiltration(config)
    
    config['hvac']['erv_runtime_fraction'] = 0.0
    erv_0_percent = _calculate_erv_infiltration(config)
    
    # Verify proportional relationships
    assert erv_0_percent == 0.0, "0% runtime should give 0 ACH"
    assert abs(erv_50_percent - erv_100_percent * 0.5) < 0.001, "50% runtime should be half of 100%"
    assert erv_100_percent > erv_50_percent > erv_0_percent, "ACH should increase with runtime fraction"


def test_erv_different_flow_rates():
    """Test that different ERV flow rates give proportional results."""
    
    config = create_test_config()
    config['hvac']['erv_enabled'] = True
    config['hvac']['erv_runtime_fraction'] = 1.0
    
    # Test different flow rates
    config['hvac']['erv_flow_rate_cfm'] = 100.0
    erv_100_cfm = _calculate_erv_infiltration(config)
    
    config['hvac']['erv_flow_rate_cfm'] = 200.0
    erv_200_cfm = _calculate_erv_infiltration(config)
    
    # 200 CFM should give double the ACH of 100 CFM
    assert abs(erv_200_cfm - erv_100_cfm * 2.0) < 0.001, f"200 CFM should be 2x 100 CFM: {erv_200_cfm:.3f} vs {erv_100_cfm * 2:.3f}"


def test_erv_zero_flow_rate():
    """Test ERV with zero flow rate."""
    
    config = create_test_config()
    config['hvac']['erv_enabled'] = True
    config['hvac']['erv_flow_rate_cfm'] = 0.0
    config['hvac']['erv_runtime_fraction'] = 1.0
    
    erv_ach = _calculate_erv_infiltration(config)
    assert erv_ach == 0.0, "Zero flow rate should give 0 ACH"


def test_erv_realistic_example():
    """Test realistic ERV example matching user's Lifebreath 170 ERVD."""
    
    config = create_test_config()
    config['building']['area_sq_ft'] = 3000
    config['building']['ceiling_height_ft'] = 9
    config['hvac']['erv_enabled'] = True
    config['hvac']['erv_flow_rate_cfm'] = 170  # Lifebreath 170 ERVD
    config['hvac']['erv_runtime_fraction'] = 0.9  # 90% runtime
    
    erv_ach = _calculate_erv_infiltration(config)
    total_ach = calculate_infiltration_rate(config)
    
    # Expected values for this configuration
    expected_erv_ach = (170 * 0.9 * 60) / (3000 * 9)  # ≈ 0.34 ACH
    
    assert abs(erv_ach - expected_erv_ach) < 0.01, f"ERV ACH should be ~{expected_erv_ach:.3f}, got {erv_ach:.3f}"
    assert erv_ach > 0.3, f"ERV should contribute significant airflow: {erv_ach:.3f} ACH"
    assert total_ach > 0.7, f"Total infiltration should be substantial with ERV: {total_ach:.3f} ACH"
    
    print(f"Lifebreath 170 ERVD Analysis:")
    print(f"  ERV contribution: {erv_ach:.3f} ACH")
    print(f"  Total infiltration: {total_ach:.3f} ACH")


if __name__ == "__main__":
    test_erv_disabled()
    test_erv_enabled_calculation()
    test_erv_adds_to_natural_infiltration()
    test_erv_runtime_fraction_effect()
    test_erv_different_flow_rates()
    test_erv_zero_flow_rate()
    test_erv_realistic_example()
    print("All ERV integration tests passed!") 