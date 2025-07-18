"""
Night-time calibration model for filter efficiency estimation.

This module implements a Bayesian approach to estimate filter efficiency
and infiltration parameters during stable night-time conditions.
"""

import numpy as np
import pandas as pd
from typing import Dict, Any, Optional, Tuple, List
from scipy import optimize
from scipy.stats import norm, gamma, beta
import logging
from datetime import datetime, timedelta
import warnings

logger = logging.getLogger(__name__)


class NightTimeCalibration:
    """
    Bayesian night-time calibration model for filter efficiency estimation.
    
    This model uses night-time data (10pm-8am) when the building is sealed
    to estimate filter efficiency and infiltration parameters under stable
    conditions.
    """
    
    def __init__(self, config: Dict[str, Any], building_params: Dict[str, float]):
        """
        Initialize the night-time calibration model.
        
        Args:
            config: Configuration dictionary from config.yaml
            building_params: Calculated building parameters from DataProcessor
        """
        self.config = config
        self.building_params = building_params
        self.logger = logging.getLogger(__name__)
        
        # Extract building parameters
        self.volume = building_params['volume']
        self.filtration_rate = building_params['filtration_rate']
        self.deposition_rate = building_params['deposition_rate']
        
        # Model state
        self.is_fitted = False
        self.fit_results = {}
        self.parameter_history = []
        
        self.logger.info(f"Initialized model with building volume {self.volume:.1f} m³, "
                        f"filtration rate {self.filtration_rate:.1f} m³/h")
        
    def steady_state_model(
        self, 
        outdoor_pm25: float, 
        infiltration_rate: float, 
        efficiency: float
    ) -> float:
        """
        Calculate steady-state indoor PM2.5 concentration.
        
        Based on mass balance equation in steady state:
        C_in = (λ_inf * C_out) / (λ_inf + η * λ_filt + λ_dep)
        
        Args:
            outdoor_pm25: Outdoor PM2.5 concentration (μg/m³)
            infiltration_rate: Air infiltration rate (m³/h)
            efficiency: Filter efficiency (0-1)
            
        Returns:
            Predicted indoor PM2.5 concentration (μg/m³)
        """
        denominator = (infiltration_rate + 
                      efficiency * self.filtration_rate + 
                      self.deposition_rate)
        
        if denominator <= 0:
            return outdoor_pm25  # No filtering effect
        
        return (infiltration_rate * outdoor_pm25) / denominator
    
    def log_likelihood(
        self, 
        params: np.ndarray, 
        indoor_pm25: np.ndarray, 
        outdoor_pm25: np.ndarray
    ) -> float:
        """
        Calculate log-likelihood for given parameters.
        
        Args:
            params: [infiltration_rate, efficiency, noise_std]
            indoor_pm25: Observed indoor PM2.5 concentrations
            outdoor_pm25: Corresponding outdoor PM2.5 concentrations
            
        Returns:
            Log-likelihood value
        """
        infiltration_rate, efficiency, noise_std = params
        
        # Parameter bounds checking
        if (infiltration_rate <= 0 or efficiency < 0 or efficiency > 1 or 
            noise_std <= 0):
            return -np.inf
        
        # Calculate predicted values
        predicted = np.array([
            self.steady_state_model(out_pm25, infiltration_rate, efficiency)
            for out_pm25 in outdoor_pm25
        ])
        
        # Calculate residuals
        residuals = indoor_pm25 - predicted
        
        # Log-likelihood assuming Gaussian noise
        log_likelihood = np.sum(norm.logpdf(residuals, scale=noise_std))
        
        return log_likelihood
    
    def log_prior(self, params: np.ndarray) -> float:
        """
        Calculate log-prior for parameters.
        
        Args:
            params: [infiltration_rate, efficiency, noise_std]
            
        Returns:
            Log-prior value
        """
        infiltration_rate, efficiency, noise_std = params
        
        # Prior distributions (can be adjusted based on building knowledge)
        # Infiltration rate: Gamma distribution (typical range 0.1-2.0 ACH)
        # Efficiency: Beta distribution (favoring higher efficiency for new filters)
        # Noise std: Gamma distribution (small positive values)
        
        log_prior = 0.0
        
        # Convert infiltration rate from m³/h to ACH for priors
        ach = infiltration_rate / self.volume
        
        # Infiltration rate prior: Gamma(shape=2, scale=0.3) -> mean=0.6 ACH, mode=0.3 ACH
        if ach > 0:
            log_prior += gamma.logpdf(ach, a=2.0, scale=0.3)
        else:
            return -np.inf
        
        # Efficiency prior: Beta(alpha=8, beta=2) -> favors high efficiency
        if 0 <= efficiency <= 1:
            log_prior += beta.logpdf(efficiency, a=8.0, b=2.0)
        else:
            return -np.inf
        
        # Noise std prior: Gamma(shape=2, scale=2) -> allows reasonable noise levels
        if noise_std > 0:
            log_prior += gamma.logpdf(noise_std, a=2.0, scale=2.0)
        else:
            return -np.inf
        
        return log_prior
    
    def log_posterior(
        self, 
        params: np.ndarray, 
        indoor_pm25: np.ndarray, 
        outdoor_pm25: np.ndarray
    ) -> float:
        """
        Calculate log-posterior (likelihood + prior).
        
        Args:
            params: [infiltration_rate, efficiency, noise_std]
            indoor_pm25: Observed indoor PM2.5 concentrations
            outdoor_pm25: Corresponding outdoor PM2.5 concentrations
            
        Returns:
            Log-posterior value
        """
        return (self.log_likelihood(params, indoor_pm25, outdoor_pm25) + 
                self.log_prior(params))
    
    def fit_maximum_likelihood(
        self, 
        indoor_pm25: np.ndarray, 
        outdoor_pm25: np.ndarray
    ) -> Dict[str, Any]:
        """
        Fit model using maximum likelihood estimation.
        
        Args:
            indoor_pm25: Night-time indoor PM2.5 concentrations
            outdoor_pm25: Corresponding outdoor PM2.5 concentrations
            
        Returns:
            Dictionary with fitted parameters and diagnostics
        """
        if len(indoor_pm25) != len(outdoor_pm25):
            raise ValueError("Indoor and outdoor arrays must have same length")
        
        min_points = self.config['analysis']['min_data_points']
        if len(indoor_pm25) < min_points:
            raise ValueError(f"Need at least {min_points} data points for fitting")
        
        # Initial parameter guess (convert from ACH to m³/h)
        initial_guess = np.array([
            0.5 * self.volume,  # infiltration_rate (0.5 ACH converted to m³/h)
            0.8,               # efficiency
            2.0                # noise_std
        ])
        
        # Parameter bounds
        bounds = [
            (0.01 * self.volume, 5.0 * self.volume),   # infiltration_rate (0.01-5 ACH)
            (0.0, 1.0),                                # efficiency
            (0.01, 20.0)                               # noise_std
        ]
        
        # Negative log-posterior for minimization
        def neg_log_posterior(params):
            return -self.log_posterior(params, indoor_pm25, outdoor_pm25)
        
        # Optimization
        try:
            result = optimize.minimize(
                neg_log_posterior,
                initial_guess,
                bounds=bounds,
                method='L-BFGS-B'
            )
            
            if not result.success:
                self.logger.warning(f"Optimization did not converge: {result.message}")
            
            fitted_params = result.x
            infiltration_rate, efficiency, noise_std = fitted_params
            
            # Calculate model predictions
            predicted = np.array([
                self.steady_state_model(out_pm25, infiltration_rate, efficiency)
                for out_pm25 in outdoor_pm25
            ])
            
            # Calculate diagnostics
            residuals = indoor_pm25 - predicted
            rmse = np.sqrt(np.mean(residuals**2))
            mae = np.mean(np.abs(residuals))
            
            # R-squared
            ss_res = np.sum(residuals**2)
            ss_tot = np.sum((indoor_pm25 - np.mean(indoor_pm25))**2)
            r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0.0
            
            # Convert infiltration rate to ACH for reporting
            infiltration_ach = infiltration_rate / self.volume
            
            fit_results = {
                'infiltration_rate_m3h': infiltration_rate,
                'infiltration_rate_ach': infiltration_ach,
                'efficiency': efficiency,
                'noise_std': noise_std,
                'log_likelihood': -result.fun,
                'rmse': rmse,
                'mae': mae,
                'r_squared': r_squared,
                'n_points': len(indoor_pm25),
                'predicted': predicted,
                'residuals': residuals,
                'optimization_success': result.success,
                'fit_timestamp': datetime.now()
            }
            
            self.fit_results = fit_results
            self.is_fitted = True
            
            self.logger.info(
                f"Model fitted successfully: "
                f"efficiency={efficiency:.3f}, "
                f"infiltration_rate={infiltration_ach:.3f} ACH, "
                f"R²={r_squared:.3f}"
            )
            
            return fit_results
            
        except Exception as e:
            self.logger.error(f"Fitting failed: {str(e)}")
            raise
    
    def predict(
        self, 
        outdoor_pm25: np.ndarray,
        use_uncertainty: bool = False
    ) -> Dict[str, np.ndarray]:
        """
        Predict indoor PM2.5 concentrations given outdoor values.
        
        Args:
            outdoor_pm25: Outdoor PM2.5 concentrations
            use_uncertainty: Whether to include parameter uncertainty
            
        Returns:
            Dictionary with predictions and uncertainty bounds
        """
        if not self.is_fitted:
            raise ValueError("Model must be fitted before making predictions")
        
        # Point predictions using fitted parameters
        infiltration_rate = self.fit_results['infiltration_rate_m3h']
        efficiency = self.fit_results['efficiency']
        
        predictions = np.array([
            self.steady_state_model(out_pm25, infiltration_rate, efficiency)
            for out_pm25 in outdoor_pm25
        ])
        
        return {
            'mean': predictions,
            'std': np.full_like(predictions, self.fit_results.get('noise_std', 1.0))
        }
    
    def get_filter_degradation_rate(self, time_window_days: int = 30) -> Optional[float]:
        """
        Estimate filter degradation rate from parameter history.
        
        Args:
            time_window_days: Time window for calculating degradation rate
            
        Returns:
            Degradation rate (efficiency loss per day) or None if insufficient data
        """
        if len(self.parameter_history) < 2:
            return None
        
        # Filter recent history
        cutoff_date = datetime.now() - timedelta(days=time_window_days)
        recent_history = [
            entry for entry in self.parameter_history
            if entry['timestamp'] >= cutoff_date
        ]
        
        if len(recent_history) < 2:
            return None
        
        # Extract efficiency values and timestamps
        efficiencies = [entry['efficiency'] for entry in recent_history]
        timestamps = [entry['timestamp'] for entry in recent_history]
        
        # Convert to days since first measurement
        days = np.array([
            (ts - timestamps[0]).total_seconds() / (24 * 3600)
            for ts in timestamps
        ])
        
        # Linear fit to estimate degradation rate
        if len(days) >= 2 and np.std(days) > 0:
            coeffs = np.polyfit(days, efficiencies, 1)
            degradation_rate = -coeffs[0]  # Negative slope = degradation
            return max(0.0, degradation_rate)  # Non-negative
        
        return None
    
    def update_parameter_history(self):
        """
        Add current fit results to parameter history.
        """
        if self.is_fitted:
            history_entry = {
                'timestamp': self.fit_results.get('fit_timestamp', datetime.now()),
                'infiltration_rate_ach': self.fit_results['infiltration_rate_ach'],
                'efficiency': self.fit_results['efficiency'],
                'r_squared': self.fit_results['r_squared'],
                'n_points': self.fit_results['n_points']
            }
            self.parameter_history.append(history_entry)
            
            # Keep only recent history (last 6 months)
            cutoff_date = datetime.now() - timedelta(days=180)
            self.parameter_history = [
                entry for entry in self.parameter_history
                if entry['timestamp'] >= cutoff_date
            ]
    
    def get_diagnostics(self) -> Dict[str, Any]:
        """
        Get comprehensive model diagnostics.
        
        Returns:
            Dictionary with model performance metrics and diagnostics
        """
        if not self.is_fitted:
            return {'status': 'not_fitted'}
        
        min_confidence = self.config['alerts']['min_confidence']
        
        diagnostics = {
            'status': 'fitted',
            'fit_quality': {
                'r_squared': self.fit_results['r_squared'],
                'rmse': self.fit_results['rmse'],
                'mae': self.fit_results['mae'],
                'n_points': self.fit_results['n_points'],
                'meets_confidence_threshold': self.fit_results['r_squared'] >= min_confidence
            },
            'parameters': {
                'infiltration_rate_ach': self.fit_results['infiltration_rate_ach'],
                'infiltration_rate_m3h': self.fit_results['infiltration_rate_m3h'],
                'efficiency': self.fit_results['efficiency'],
                'efficiency_percentage': self.fit_results['efficiency'] * 100,
                'noise_std': self.fit_results['noise_std']
            },
            'building_params': {
                'volume': self.volume,
                'filtration_rate': self.filtration_rate,
                'deposition_rate': self.deposition_rate
            },
            'fit_timestamp': self.fit_results.get('fit_timestamp'),
            'optimization_success': self.fit_results.get('optimization_success', True)
        }
        
        # Add degradation information if available
        degradation_rate = self.get_filter_degradation_rate()
        if degradation_rate is not None:
            thresholds = self.config['alerts']['efficiency_thresholds']
            current_efficiency = self.fit_results['efficiency']
            
            # Estimate days until efficiency drops below "declining" threshold
            declining_threshold = thresholds['declining']
            if current_efficiency > declining_threshold and degradation_rate > 0:
                days_to_replacement = (current_efficiency - declining_threshold) / degradation_rate
            else:
                days_to_replacement = None
            
            diagnostics['degradation'] = {
                'rate_per_day': degradation_rate,
                'estimated_replacement_days': days_to_replacement
            }
        
        return diagnostics
    
    def generate_recommendations(self) -> Dict[str, Any]:
        """
        Generate actionable recommendations based on current model state.
        
        Returns:
            Dictionary with alerts and recommendations
        """
        if not self.is_fitted:
            return {
                'status': 'no_analysis',
                'alerts': ['No filter efficiency analysis available yet.'],
                'actions': ['Run filter efficiency analysis to get recommendations.']
            }
        
        efficiency = self.fit_results['efficiency']
        r_squared = self.fit_results['r_squared']
        thresholds = self.config['alerts']['efficiency_thresholds']
        min_confidence = self.config['alerts']['min_confidence']
        
        recommendations = {
            'alerts': [],
            'actions': [],
            'filter_status': 'unknown'
        }
        
        # Model quality checks
        if r_squared < min_confidence:
            recommendations['alerts'].append(
                f"Analysis confidence is low (R² = {r_squared:.2f}). "
                "Results may be unreliable. Check for data quality issues."
            )
        
        # Efficiency-based recommendations
        if efficiency >= thresholds['excellent']:
            recommendations['filter_status'] = 'excellent'
            recommendations['actions'].append("Filter performing excellently. Continue regular monitoring.")
        elif efficiency >= thresholds['good']:
            recommendations['filter_status'] = 'good'
            recommendations['actions'].append("Filter performance is good. Monitor for degradation trends.")
        elif efficiency >= thresholds['declining']:
            recommendations['filter_status'] = 'declining'
            recommendations['alerts'].append(
                f"Filter efficiency declining to {efficiency:.1%}. Consider replacement soon."
            )
            recommendations['actions'].append("Schedule filter replacement within 2-4 weeks.")
        else:
            recommendations['filter_status'] = 'poor'
            recommendations['alerts'].append(
                f"Filter efficiency very low at {efficiency:.1%}. Replace immediately."
            )
            recommendations['actions'].append("Replace filter as soon as possible.")
        
        # Degradation trend analysis
        degradation_rate = self.get_filter_degradation_rate()
        if degradation_rate is not None and degradation_rate > 0:
            days_to_replacement = (efficiency - thresholds['declining']) / degradation_rate
            
            if days_to_replacement > 0 and days_to_replacement < 30:
                recommendations['alerts'].append(
                    f"Filter estimated to reach replacement threshold in {days_to_replacement:.0f} days."
                )
                recommendations['actions'].append("Order replacement filter now.")
            elif days_to_replacement > 30:
                recommendations['actions'].append(
                    f"Filter replacement recommended in approximately {days_to_replacement:.0f} days."
                )
        
        return recommendations 