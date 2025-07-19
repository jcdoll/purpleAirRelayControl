#!/usr/bin/env python3
"""
Kalman filter-based filter efficiency tracker with ACH estimation.

This implementation uses a Kalman filter to track both filter efficiency and
total ACH as time-varying states, learning building parameters from temporal dynamics.
"""

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import matplotlib

matplotlib.use("Agg")  # Use non-interactive backend to prevent window popups
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from utils.mass_balance import (
    calculate_steady_state_indoor_pm25,
    solve_filter_efficiency_from_ratio,
)
from utils.visualization import FilterVisualization

from .base_filter_tracker import BaseFilterTracker


class KalmanFilterTracker(BaseFilterTracker):
    """
    Kalman filter tracking both efficiency and total ACH.

    State: [efficiency, total_ach]
    Observation: indoor PM2.5 concentration

    This approach models both filter efficiency and total air changes per hour
    as slowly-varying states, learning from temporal dynamics.
    """

    def __init__(self, config: Dict[str, Any]):
        """Initialize the Kalman filter tracker."""
        super().__init__(config)

        # Single-dimensional state: [filter_efficiency η]
        # η starts at 0.8 (80% efficient filter) - will be updated with first measurement
        self.state = 0.8  # Single scalar value
        self.covariance = 0.1  # Single scalar variance

        # Process and measurement noise parameters
        self.process_noise = 1e-6  # η changes slowly over time
        self.measurement_noise = 25.0  # realistic sensor variance (5 µg std)

        # Fixed building parameters
        self.hvac_filtration_ach = self._calculate_filtration_rate()
        # Infiltration rate in ACH (h^-1)
        self.infiltration_ach = self._estimate_infiltration_rate()
        # Deposition rate in ACH (h^-1) - PM2.5 settle very slowly
        self.deposition_ach = self._calculate_deposition_rate()

        # History for analysis
        self.state_history = []
        self.measurement_history = []

        # Daily aggregation
        self.daily_data = []
        self.last_update_day = None

        # For temporal dynamics
        self.prev_timestamp = None
        self.prev_indoor = None

    @property
    def efficiency(self) -> float:
        """Current filter efficiency estimate."""
        return max(0.0, float(self.state))  # Allow efficiency > 100% to indicate model issues

    @property
    def leak_ach(self) -> float:
        """Current infiltration air-change rate λ_in (fixed)."""
        return self.infiltration_ach

    @property
    def total_removal_ach(self) -> float:
        """Current total removal ACH (depends on efficiency)."""
        return self.infiltration_ach + self.hvac_filtration_ach * self.efficiency + self.deposition_ach

    def add_measurement(self, timestamp: datetime, indoor_pm25: float, outdoor_pm25: float) -> None:
        """Add a new measurement and update the Kalman filter."""
        if outdoor_pm25 <= 0 or indoor_pm25 < 0:
            return

        # Store raw measurement
        measurement = {
            'timestamp': timestamp,
            'indoor_pm25': indoor_pm25,
            'outdoor_pm25': outdoor_pm25,
            'ratio': indoor_pm25 / outdoor_pm25,
        }
        self.measurements.append(measurement)

        # Calculate time step
        if self.prev_timestamp is not None:
            dt_hours = (timestamp - self.prev_timestamp).total_seconds() / 3600
            dt_hours = max(0.01, min(24.0, dt_hours))  # Reasonable bounds
        else:
            dt_hours = 1.0
            # First measurement - initialize efficiency from I/O ratio
            ratio = indoor_pm25 / outdoor_pm25
            initial_efficiency = solve_filter_efficiency_from_ratio(
                io_ratio=ratio,
                infiltration_rate=self.infiltration_ach,
                filtration_rate=self.hvac_filtration_ach,
                deposition_rate=self.deposition_ach,
            )
            self.state = max(0.0, initial_efficiency)  # Allow efficiency > 100% to indicate model issues

        # Always run prediction step (time propagation)
        predicted_indoor = self._predict_step(dt_hours, outdoor_pm25)

        # Only update if signal is strong enough for reliable learning
        if self._sufficient_signal(indoor_pm25, outdoor_pm25):
            # Good signal - update with appropriate confidence
            confidence_multiplier = self._get_time_confidence_multiplier(timestamp)
            self._update_step(indoor_pm25, outdoor_pm25, predicted_indoor, dt_hours, confidence_multiplier)

        # If signal is weak, skip update and carry forward previous estimate

        # Store history
        self.state_history.append(
            {
                'timestamp': timestamp,
                'efficiency': self.efficiency,
                'leak_ach': self.leak_ach,
                'total_removal_ach': self.total_removal_ach,
                'predicted_indoor': predicted_indoor,
                'actual_indoor': indoor_pm25,
                'outdoor': outdoor_pm25,
            }
        )

        self.measurement_history.append(measurement)

        # Update daily data
        self._update_daily_data(timestamp)

        self.prev_timestamp = timestamp
        self.prev_indoor = indoor_pm25
        self.initialized = True

    def _predict_step(self, dt_hours: float, outdoor_pm25: float) -> float:
        """Kalman filter prediction step."""
        # State prediction: parameters are slowly varying
        # self.state remains the same (no systematic drift model)

        # Covariance prediction: add process noise
        self.covariance += self.process_noise * dt_hours

        # Predict indoor PM2.5 using current state estimates
        if self.prev_indoor is not None:
            # Use temporal dynamics model
            predicted_indoor = self._temporal_model(self.prev_indoor, outdoor_pm25, dt_hours)
        else:
            # Use steady-state model for first measurement
            predicted_indoor = self._steady_state_model(outdoor_pm25)

        return predicted_indoor

    def _update_step(
        self,
        observed_indoor: float,
        outdoor_pm25: float,
        predicted_indoor: float,
        dt_hours: float,
        confidence_factor: float = 1.0,
    ) -> None:
        """Kalman filter update step for single parameter (efficiency)."""
        # Calculate innovation
        innovation = observed_indoor - predicted_indoor

        # Calculate Jacobian (sensitivity) w.r.t. efficiency
        H = self._calculate_jacobian(outdoor_pm25, dt_hours)

        # Innovation covariance with confidence-adjusted measurement noise
        # Handle zero confidence (no learning) by using very high noise
        if confidence_factor <= 0:
            effective_measurement_noise = self.measurement_noise * 1e6  # Very high noise = no learning
        else:
            effective_measurement_noise = self.measurement_noise / confidence_factor  # Lower = higher confidence
        S = H * self.covariance * H + effective_measurement_noise

        # Kalman gain (scalar)
        if S > 0:
            K = self.covariance * H / S

            # State update
            self.state += K * innovation

            # Covariance update
            self.covariance = (1 - K * H) * self.covariance

        # Enforce physical constraints
        self.state = max(0.0, self.state)  # Allow efficiency > 100% to indicate model issues

        # Ensure covariance stays positive
        self.covariance = max(1e-8, self.covariance)

    def _sufficient_signal(self, indoor_pm25: float, outdoor_pm25: float) -> bool:
        """Check if signal is strong enough for reliable learning."""
        kalman_config = self.config.get('kalman_filter', {})
        min_indoor = kalman_config.get('min_indoor_pm25_for_learning', 10.0)
        min_outdoor = kalman_config.get('min_outdoor_pm25_for_learning', 30.0)
        max_ratio = kalman_config.get('max_ratio_for_learning', 1.0)

        # Check minimum signal thresholds
        if indoor_pm25 < min_indoor or outdoor_pm25 < min_outdoor:
            return False

        # Check for indoor particle generation (indoor > outdoor indicates source)
        ratio = indoor_pm25 / outdoor_pm25
        if ratio >= max_ratio:
            return False

        return True

    def _get_time_confidence_multiplier(self, timestamp: datetime) -> float:
        """Get confidence multiplier based on time of day."""
        kalman_config = self.config.get('kalman_filter', {})
        hour = timestamp.hour

        if 22 <= hour or hour <= 8:  # Night time (10 PM to 8 AM)
            return kalman_config.get('night_confidence_multiplier', 2.0)
        else:
            return kalman_config.get('day_confidence_multiplier', 0.5)

    def _temporal_model(self, prev_indoor: float, outdoor_pm25: float, dt_hours: float) -> float:
        """Predict indoor concentration after dt given current state."""
        steady_state = self._steady_state_model(outdoor_pm25)

        λ_tot = self.total_removal_ach
        decay_factor = np.exp(-λ_tot * dt_hours)
        predicted = steady_state + (prev_indoor - steady_state) * decay_factor

        return predicted

    def _steady_state_model(self, outdoor_pm25: float) -> float:
        """Steady-state indoor concentration from current state."""
        return calculate_steady_state_indoor_pm25(
            outdoor_pm25=outdoor_pm25,
            infiltration_rate=self.leak_ach,
            filtration_rate=self.hvac_filtration_ach,
            deposition_rate=self.deposition_ach,
            filter_efficiency=self.efficiency,
            indoor_generation=0.0,
        )

    def _calculate_jacobian(self, outdoor_pm25: float, dt_hours: float) -> float:
        """Calculate Jacobian (sensitivity) for observation model w.r.t. efficiency."""
        # For temporal model: predicted = steady_state + (prev_indoor - steady_state) * exp(-λ_tot * dt)
        # Need derivatives of both steady_state and λ_tot w.r.t. efficiency
        λ_in = self.leak_ach
        λ_f = self.hvac_filtration_ach
        λ_dep = self.deposition_ach
        η = self.efficiency

        # Derivative of steady-state w.r.t. efficiency
        denominator = λ_in + λ_f * η + λ_dep
        d_ss_d_eta = -λ_in * λ_f * outdoor_pm25 / (denominator * denominator)

        # For temporal model, need both terms of the derivative
        exp_term = np.exp(-self.total_removal_ach * dt_hours)
        steady_state = self._steady_state_model(outdoor_pm25)

        # First term: d(steady_state)/dη * (1 - exp(-λ_tot * dt))
        term1 = d_ss_d_eta * (1 - exp_term)

        # Second term: (prev_indoor - steady_state) * exp(-λ_tot * dt) * (-dt) * d(λ_tot)/dη
        # d(λ_tot)/dη = λ_f (since λ_tot = λ_in + λ_f * η + λ_dep)
        if self.prev_indoor is not None:
            term2 = (self.prev_indoor - steady_state) * exp_term * (-dt_hours) * λ_f
        else:
            term2 = 0.0  # First measurement, no previous indoor value

        return term1 + term2

    def _update_daily_data(self, timestamp: datetime) -> None:
        """Update daily aggregated data."""
        current_day = timestamp.date()

        if self.last_update_day != current_day:
            if self.last_update_day is not None and self.state_history:
                self._finalize_daily_data(self.last_update_day)
            self.last_update_day = current_day

    def _finalize_daily_data(self, date) -> None:
        """Finalize daily data for a completed day."""
        day_history = [h for h in self.state_history if h['timestamp'].date() == date]

        if len(day_history) >= 3:
            daily_record = {
                'date': date,
                'timestamp': pd.Timestamp(str(date)),
                'efficiency': float(np.mean([h['efficiency'] for h in day_history])),
                'leak_ach': float(np.mean([h['leak_ach'] for h in day_history])),
                'total_removal_ach': float(np.mean([h['total_removal_ach'] for h in day_history])),
                'efficiency_std': float(np.std([h['efficiency'] for h in day_history])),
                'predicted_indoor': float(np.mean([h['predicted_indoor'] for h in day_history])),
                'actual_indoor': float(np.mean([h['actual_indoor'] for h in day_history])),
                'outdoor_pm25': float(np.mean([h['outdoor'] for h in day_history])),
                'ratio': float(np.mean([h['actual_indoor'] / h['outdoor'] for h in day_history])),
                'prediction_error': float(
                    np.mean([abs(h['actual_indoor'] - h['predicted_indoor']) for h in day_history])
                ),
                'measurement_count': len(day_history),
            }

            self.daily_data.append(daily_record)

    def get_current_efficiency(self) -> Optional[float]:
        """Get the current estimated filter efficiency."""
        return self.efficiency if self.initialized else None

    def get_efficiency_trend(self, days_back: Optional[int] = None) -> Optional[float]:
        """Get the efficiency trend over a specified period."""
        if len(self.daily_data) < 3:
            return None

        data = self.daily_data
        if days_back is not None:
            data = data[-days_back:] if len(data) > days_back else data

        if len(data) < 3:
            return None

        days = [(d['timestamp'] - data[0]['timestamp']).days for d in data]
        efficiencies = [d['efficiency'] for d in data]

        if len(set(days)) < 2:
            return 0.0

        coeffs = np.polyfit(days, efficiencies, 1)
        return float(coeffs[0] * 30)  # Per month

    def get_summary_stats(self) -> Dict[str, Any]:
        """Get summary statistics about filter and building performance."""
        stats = {
            'model_type': 'KalmanFilterTracker',
            'total_measurements': len(self.measurements),
            'total_days': len(self.daily_data),
            'has_building_params': self._has_building_params(),
            'current_efficiency_percent': self.efficiency * 100 if self.initialized else None,
            'efficiency_uncertainty': np.sqrt(self.covariance) * 100 if self.initialized else None,
            'efficiency_trend_per_month': self.get_efficiency_trend(),
            'estimated_leak_ach': self.leak_ach if self.initialized else None,
            'estimated_total_removal_ach': self.total_removal_ach if self.initialized else None,
            'known_filtration_ach': self.hvac_filtration_ach,
            'ach_uncertainty': np.sqrt(self.covariance) if self.initialized else None,
        }

        if self.daily_data:
            baseline_data = self.daily_data[:7] if len(self.daily_data) >= 7 else self.daily_data
            baseline_eff = float(np.mean([d['efficiency'] for d in baseline_data]))

            stats['baseline_efficiency_percent'] = baseline_eff * 100
            stats['efficiency_change_percent'] = (self.efficiency - baseline_eff) * 100

            # Prediction accuracy
            recent_data = self.daily_data[-7:] if len(self.daily_data) >= 7 else self.daily_data
            stats['mean_prediction_error'] = float(np.mean([d['prediction_error'] for d in recent_data]))
            stats['prediction_rmse'] = float(np.sqrt(np.mean([d['prediction_error'] ** 2 for d in recent_data])))
        else:
            stats.update(
                {
                    'baseline_efficiency_percent': None,
                    'efficiency_change_percent': None,
                    'mean_prediction_error': None,
                    'prediction_rmse': None,
                }
            )

        return stats

    def get_daily_data(self) -> pd.DataFrame:
        """Get daily aggregated data for plotting."""
        if self.last_update_day is not None and self.state_history:
            last_measurement = self.state_history[-1]['timestamp']
            if (datetime.now() - last_measurement).days >= 1:
                self._finalize_daily_data(self.last_update_day)

        if not self.daily_data:
            return pd.DataFrame()

        return pd.DataFrame(self.daily_data)

    def get_efficiency_confidence_interval(self, confidence: float = 0.95) -> Tuple[float, float]:
        """Get confidence interval for current efficiency estimate."""
        if not self.initialized:
            return 0.0, 1.0

        # Calculate confidence interval based on efficiency variance
        z_score = 1.96 if confidence == 0.95 else 2.576  # 95% or 99%
        std_dev = np.sqrt(self.covariance)

        lower = max(0.0, self.efficiency - z_score * std_dev)
        upper = min(1.0, self.efficiency + z_score * std_dev)

        return lower, upper

    def plot_efficiency_trend(self, days_back: Optional[int] = None, save_path: Optional[str] = None) -> None:
        """Plot the efficiency trend using standardized visualization."""
        daily_df = self.get_daily_data()

        if daily_df.empty:
            print("No data available for plotting")
            return

        if days_back is not None:
            daily_df = daily_df.tail(days_back)

        # Prepare data for standardized plotting
        plot_df = daily_df.rename(columns={'actual_indoor': 'indoor_pm25', 'outdoor_pm25': 'outdoor_pm25'})

        # Create model results structure
        model_results = {
            'kalman': {
                'success': True,
                'model': self,
                'stats': self.get_summary_stats() if hasattr(self, 'get_summary_stats') else {},
            }
        }

        # Use standardized plotting
        viz = FilterVisualization()
        title = f"Kalman Filter Efficiency Trend ({len(daily_df)} days)"

        if save_path:
            save_filename = Path(save_path).name
            viz.output_dir = Path(save_path).parent
            viz.plot_standard_analysis(
                df=plot_df, title=title, model_results=model_results, save_filename=save_filename
            )
        else:
            viz.plot_standard_analysis(df=plot_df, title=title, model_results=model_results)
            plt.show()
