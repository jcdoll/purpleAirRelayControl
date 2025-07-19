#!/usr/bin/env python3
"""
Test cases for ERV-aware mass balance calculations.

Tests that the new ERV-specific functions in mass_balance.py work correctly
and produce consistent results with the existing functions when ERV is disabled.
"""

import pytest
import numpy as np
from utils.mass_balance import (
    calculate_steady_state_indoor_pm25,
    calculate_steady_state_indoor_pm25_with_erv,
    calculate_indoor_outdoor_ratio,
    calculate_indoor_outdoor_ratio_with_erv,
    solve_filter_efficiency_from_ratio,
    solve_filter_efficiency_from_ratio_with_erv,
    calculate_infiltration_components
)
from tests.test_utils import create_test_config


def test_erv_functions_match_original_when_erv_disabled():
    """Test that ERV functions match original functions when ERV is disabled."""
    
    # Test parameters
    outdoor_pm25 = 25.0
    natural_infiltration = 0.4
    erv_infiltration = 0.0  # ERV disabled
    filtration_rate = 3.3
    deposition_rate = 0.15
    filter_efficiency = 0.95
    
    # Test steady-state indoor PM2.5 calculation
    original_indoor = calculate_steady_state_indoor_pm25(
        outdoor_pm25=outdoor_pm25,
        infiltration_rate=natural_infiltration,  # Total infiltration when ERV disabled
        filtration_rate=filtration_rate,
        deposition_rate=deposition_rate,
        filter_efficiency=filter_efficiency
    )
    
    erv_indoor = calculate_steady_state_indoor_pm25_with_erv(
        outdoor_pm25=outdoor_pm25,
        natural_infiltration_rate=natural_infiltration,
        erv_infiltration_rate=erv_infiltration,
        filtration_rate=filtration_rate,
        deposition_rate=deposition_rate,
        filter_efficiency=filter_efficiency
    )
    
    assert abs(original_indoor - erv_indoor) < 0.001, f"Indoor PM2.5 should match: {original_indoor:.3f} vs {erv_indoor:.3f}"
    
    # Test I/O ratio calculation
    original_ratio = calculate_indoor_outdoor_ratio(
        infiltration_rate=natural_infiltration,
        filtration_rate=filtration_rate,
        deposition_rate=deposition_rate,
        filter_efficiency=filter_efficiency
    )
    
    erv_ratio = calculate_indoor_outdoor_ratio_with_erv(
        natural_infiltration_rate=natural_infiltration,
        erv_infiltration_rate=erv_infiltration,
        filtration_rate=filtration_rate,
        deposition_rate=deposition_rate,
        filter_efficiency=filter_efficiency
    )
    
    assert abs(original_ratio - erv_ratio) < 0.001, f"I/O ratio should match: {original_ratio:.3f} vs {erv_ratio:.3f}"
    
    # Test filter efficiency solving
    test_ratio = 0.08
    original_efficiency = solve_filter_efficiency_from_ratio(
        io_ratio=test_ratio,
        infiltration_rate=natural_infiltration,
        filtration_rate=filtration_rate,
        deposition_rate=deposition_rate
    )
    
    erv_efficiency = solve_filter_efficiency_from_ratio_with_erv(
        io_ratio=test_ratio,
        natural_infiltration_rate=natural_infiltration,
        erv_infiltration_rate=erv_infiltration,
        filtration_rate=filtration_rate,
        deposition_rate=deposition_rate
    )
    
    assert abs(original_efficiency - erv_efficiency) < 0.001, f"Filter efficiency should match: {original_efficiency:.3f} vs {erv_efficiency:.3f}"


def test_erv_increases_indoor_pm25():
    """Test that ERV increases indoor PM2.5 concentrations (more outdoor air)."""
    
    # Test parameters
    outdoor_pm25 = 30.0
    natural_infiltration = 0.4
    erv_infiltration = 0.3  # Significant ERV flow
    filtration_rate = 3.3
    deposition_rate = 0.15
    filter_efficiency = 0.95
    
    # Without ERV
    indoor_no_erv = calculate_steady_state_indoor_pm25_with_erv(
        outdoor_pm25=outdoor_pm25,
        natural_infiltration_rate=natural_infiltration,
        erv_infiltration_rate=0.0,
        filtration_rate=filtration_rate,
        deposition_rate=deposition_rate,
        filter_efficiency=filter_efficiency
    )
    
    # With ERV
    indoor_with_erv = calculate_steady_state_indoor_pm25_with_erv(
        outdoor_pm25=outdoor_pm25,
        natural_infiltration_rate=natural_infiltration,
        erv_infiltration_rate=erv_infiltration,
        filtration_rate=filtration_rate,
        deposition_rate=deposition_rate,
        filter_efficiency=filter_efficiency
    )
    
    assert indoor_with_erv > indoor_no_erv, f"ERV should increase indoor PM2.5: {indoor_with_erv:.3f} > {indoor_no_erv:.3f}"
    
    # ERV should increase indoor concentration significantly  
    percent_increase = ((indoor_with_erv / indoor_no_erv) - 1) * 100
    assert percent_increase > 10, f"ERV should significantly increase indoor PM2.5 by >{percent_increase:.1f}%"


def test_erv_increases_io_ratio():
    """Test that ERV increases indoor/outdoor ratio (less filtration effectiveness)."""
    
    # Test parameters
    natural_infiltration = 0.4
    erv_infiltration = 0.3
    filtration_rate = 3.3
    deposition_rate = 0.15
    filter_efficiency = 0.95
    
    # Without ERV
    ratio_no_erv = calculate_indoor_outdoor_ratio_with_erv(
        natural_infiltration_rate=natural_infiltration,
        erv_infiltration_rate=0.0,
        filtration_rate=filtration_rate,
        deposition_rate=deposition_rate,
        filter_efficiency=filter_efficiency
    )
    
    # With ERV
    ratio_with_erv = calculate_indoor_outdoor_ratio_with_erv(
        natural_infiltration_rate=natural_infiltration,
        erv_infiltration_rate=erv_infiltration,
        filtration_rate=filtration_rate,
        deposition_rate=deposition_rate,
        filter_efficiency=filter_efficiency
    )
    
    assert ratio_with_erv > ratio_no_erv, f"ERV should increase I/O ratio: {ratio_with_erv:.3f} > {ratio_no_erv:.3f}"


def test_erv_affects_filter_efficiency_estimation():
    """Test that ERV affects filter efficiency estimation from I/O ratios."""
    
    # Parameters
    natural_infiltration = 0.4
    erv_infiltration = 0.3
    filtration_rate = 3.3
    deposition_rate = 0.15
    true_filter_efficiency = 0.95
    
    # Generate "measured" I/O ratio with ERV present
    measured_ratio = calculate_indoor_outdoor_ratio_with_erv(
        natural_infiltration_rate=natural_infiltration,
        erv_infiltration_rate=erv_infiltration,
        filtration_rate=filtration_rate,
        deposition_rate=deposition_rate,
        filter_efficiency=true_filter_efficiency
    )
    
    # Estimate filter efficiency ignoring ERV (old method)
    estimated_efficiency_no_erv = solve_filter_efficiency_from_ratio(
        io_ratio=measured_ratio,
        infiltration_rate=natural_infiltration,  # Only natural infiltration
        filtration_rate=filtration_rate,
        deposition_rate=deposition_rate
    )
    
    # Estimate filter efficiency accounting for ERV (new method)
    estimated_efficiency_with_erv = solve_filter_efficiency_from_ratio_with_erv(
        io_ratio=measured_ratio,
        natural_infiltration_rate=natural_infiltration,
        erv_infiltration_rate=erv_infiltration,
        filtration_rate=filtration_rate,
        deposition_rate=deposition_rate
    )
    
    # ERV-aware method should be more accurate
    error_no_erv = abs(estimated_efficiency_no_erv - true_filter_efficiency)
    error_with_erv = abs(estimated_efficiency_with_erv - true_filter_efficiency)
    
    assert error_with_erv < error_no_erv, f"ERV-aware method should be more accurate: {error_with_erv:.3f} < {error_no_erv:.3f}"
    assert estimated_efficiency_no_erv < true_filter_efficiency, "Ignoring ERV should underestimate filter efficiency"
    assert abs(estimated_efficiency_with_erv - true_filter_efficiency) < 0.05, "ERV-aware method should be within 5% of true efficiency"


def test_calculate_infiltration_components():
    """Test the infiltration components calculation function."""
    
    config = create_test_config()
    config['hvac']['erv_enabled'] = True
    config['hvac']['erv_flow_rate_cfm'] = 170.0
    config['hvac']['erv_runtime_fraction'] = 0.9
    
    components = calculate_infiltration_components(config)
    
    # Check required keys
    assert 'natural_ach' in components
    assert 'erv_ach' in components  
    assert 'total_ach' in components
    
    # Check relationships
    assert components['total_ach'] == components['natural_ach'] + components['erv_ach']
    assert components['erv_ach'] > 0, "ERV should contribute positive airflow"
    assert components['natural_ach'] > 0, "Natural infiltration should be positive"
    
    # Test with ERV disabled
    config['hvac']['erv_enabled'] = False
    components_no_erv = calculate_infiltration_components(config)
    
    assert components_no_erv['erv_ach'] == 0.0, "ERV should contribute 0 when disabled"
    assert components_no_erv['total_ach'] == components_no_erv['natural_ach'], "Total should equal natural when ERV disabled"


def test_erv_mass_balance_consistency():
    """Test consistency between ERV mass balance calculations."""
    
    # Test parameters
    outdoor_pm25 = 20.0
    natural_infiltration = 0.35
    erv_infiltration = 0.25
    filtration_rate = 3.0
    deposition_rate = 0.12
    filter_efficiency = 0.92
    
    # Calculate indoor PM2.5
    indoor_pm25 = calculate_steady_state_indoor_pm25_with_erv(
        outdoor_pm25=outdoor_pm25,
        natural_infiltration_rate=natural_infiltration,
        erv_infiltration_rate=erv_infiltration,
        filtration_rate=filtration_rate,
        deposition_rate=deposition_rate,
        filter_efficiency=filter_efficiency
    )
    
    # Calculate I/O ratio
    io_ratio = calculate_indoor_outdoor_ratio_with_erv(
        natural_infiltration_rate=natural_infiltration,
        erv_infiltration_rate=erv_infiltration,
        filtration_rate=filtration_rate,
        deposition_rate=deposition_rate,
        filter_efficiency=filter_efficiency
    )
    
    # I/O ratio should match indoor/outdoor
    calculated_ratio = indoor_pm25 / outdoor_pm25
    assert abs(io_ratio - calculated_ratio) < 0.001, f"I/O ratios should match: {io_ratio:.3f} vs {calculated_ratio:.3f}"
    
    # Solve back for filter efficiency
    solved_efficiency = solve_filter_efficiency_from_ratio_with_erv(
        io_ratio=io_ratio,
        natural_infiltration_rate=natural_infiltration,
        erv_infiltration_rate=erv_infiltration,
        filtration_rate=filtration_rate,
        deposition_rate=deposition_rate
    )
    
    assert abs(solved_efficiency - filter_efficiency) < 0.001, f"Solved efficiency should match: {solved_efficiency:.3f} vs {filter_efficiency:.3f}"


if __name__ == "__main__":
    test_erv_functions_match_original_when_erv_disabled()
    test_erv_increases_indoor_pm25()
    test_erv_increases_io_ratio()
    test_erv_affects_filter_efficiency_estimation()
    test_calculate_infiltration_components()
    test_erv_mass_balance_consistency()
    print("All ERV mass balance tests passed!") 