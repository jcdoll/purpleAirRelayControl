#!/usr/bin/env python3
"""
Test cases for zero confidence multiplier functionality.

Tests that the Kalman filter handles confidence_multiplier = 0 gracefully
without crashing or producing invalid results.
"""

import pytest
from datetime import datetime, timedelta
from models.kalman_filter_tracker import KalmanFilterTracker
from tests.test_utils import create_test_config


def test_zero_confidence_no_crash():
    """Test that zero confidence multiplier doesn't cause crashes."""
    
    # Create config with zero day confidence
    config = create_test_config()
    config['kalman_filter']['day_confidence_multiplier'] = 0.0
    config['kalman_filter']['night_confidence_multiplier'] = 2.0
    
    tracker = KalmanFilterTracker(config)
    
    # Test that we can add measurements without crashing
    day_timestamp = datetime(2024, 1, 1, 12, 0)  # Noon
    night_timestamp = datetime(2024, 1, 1, 23, 0)  # 11 PM
    
    # Add daytime measurements (zero confidence)
    for i in range(5):
        tracker.add_measurement(
            day_timestamp + timedelta(minutes=i*10), 
            indoor_pm25=20.0 + i, 
            outdoor_pm25=50.0 + i*2
        )
    
    # Add nighttime measurements (normal confidence)
    for i in range(5):
        tracker.add_measurement(
            night_timestamp + timedelta(minutes=i*10),
            indoor_pm25=15.0 + i,
            outdoor_pm25=45.0 + i*2
        )
    
    # Should not crash and should return valid efficiency
    efficiency = tracker.get_current_efficiency()
    assert efficiency is not None, "Efficiency should not be None"
    assert 0.0 <= efficiency <= 1.0, f"Efficiency should be between 0 and 1, got {efficiency}"
    
    print(f"Zero confidence test passed - final efficiency: {efficiency:.3f}")


def test_both_zero_confidence():
    """Test edge case where both confidence multipliers are zero."""
    
    config = create_test_config()
    config['kalman_filter']['day_confidence_multiplier'] = 0.0
    config['kalman_filter']['night_confidence_multiplier'] = 0.0
    
    tracker = KalmanFilterTracker(config)
    
    # Add measurements at various times
    timestamps = [
        datetime(2024, 1, 1, 8, 0),   # Morning
        datetime(2024, 1, 1, 12, 0),  # Noon  
        datetime(2024, 1, 1, 18, 0),  # Evening
        datetime(2024, 1, 1, 23, 0),  # Night
    ]
    
    for i, ts in enumerate(timestamps):
        tracker.add_measurement(ts, indoor_pm25=20.0 + i*2, outdoor_pm25=50.0 + i*3)
    
    # Should work without errors
    efficiency = tracker.get_current_efficiency()
    stats = tracker.get_summary_stats()
    
    assert efficiency is not None
    assert 0.0 <= efficiency <= 1.0
    assert stats is not None
    
    print(f"Both zero confidence test passed - efficiency: {efficiency:.3f}")


def test_confidence_multiplier_configuration():
    """Test that confidence multipliers are correctly read from config."""
    
    config = create_test_config()
    config['kalman_filter']['day_confidence_multiplier'] = 0.1
    config['kalman_filter']['night_confidence_multiplier'] = 3.0
    
    tracker = KalmanFilterTracker(config)
    
    # Test that the confidence multipliers are read correctly
    day_timestamp = datetime(2024, 1, 1, 12, 0)
    night_timestamp = datetime(2024, 1, 1, 23, 0)
    
    day_conf = tracker._get_time_confidence_multiplier(day_timestamp)
    night_conf = tracker._get_time_confidence_multiplier(night_timestamp)
    
    assert day_conf == 0.1, f"Day confidence should be 0.1, got {day_conf}"
    assert night_conf == 3.0, f"Night confidence should be 3.0, got {night_conf}"
    
    print(f"Configuration test passed - day: {day_conf}, night: {night_conf}")


if __name__ == "__main__":
    test_zero_confidence_no_crash()
    test_both_zero_confidence()
    test_confidence_multiplier_configuration()
    print("All zero confidence tests passed!") 