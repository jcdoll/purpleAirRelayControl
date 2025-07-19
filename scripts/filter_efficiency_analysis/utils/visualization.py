"""
Common visualization utilities for filter efficiency analysis.

This module provides standardized plotting functions to eliminate code duplication
across test files and ensure consistent visualization across the entire test suite.
"""

import matplotlib
matplotlib.use("Agg")  # Use non-interactive backend for headless operation

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.figure import Figure
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple, Union
import warnings

# Suppress pandas FutureWarnings
warnings.filterwarnings('ignore', category=FutureWarning)

from utils.mass_balance import calculate_indoor_outdoor_ratio

# Configure matplotlib for consistent, high-quality plots
plt.style.use('default')
plt.rcParams.update({
    'figure.dpi': 150,
    'font.size': 10,
    'axes.grid': True,
    'grid.alpha': 0.3,
    'figure.facecolor': 'white'
})


class FilterVisualization:
    """Standardized visualization for filter efficiency analysis."""
    
    def __init__(self, output_dir: Union[str, Path] = "test_visualizations"):
        """Initialize visualization with output directory."""
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
    def save_plot(self, filename: str, dpi: int = 150) -> Path:
        """Save current plot with standard settings."""
        save_path = self.output_dir / filename
        plt.savefig(save_path, dpi=dpi, bbox_inches='tight', facecolor='white')
        plt.close()
        return save_path
    
    def format_datetime_axis(self, ax, df: pd.DataFrame, interval_hours: int = 2):
        """Apply standard datetime formatting to x-axis."""
        total_hours = (df['timestamp'].max() - df['timestamp'].min()).total_seconds() / 3600
        
        if total_hours <= 48:  # Less than 2 days - show hours
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
            ax.xaxis.set_major_locator(mdates.HourLocator(interval=interval_hours))
        elif total_hours <= 168:  # Less than 1 week - show days
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
            ax.xaxis.set_major_locator(mdates.DayLocator(interval=1))
        else:  # More than 1 week - show dates with intervals
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
            ax.xaxis.set_major_locator(mdates.DayLocator(interval=max(1, int(total_hours / (24*5)))))
        
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)
    
    def _calculate_expected_io_ratio(self, filter_efficiency: float, scenario_info: Dict[str, Any]) -> float:
        """Calculate expected I/O ratio using actual building parameters."""
        # Default building parameters (from test_data_generator defaults)
        infiltration_ach = 0.5  # Default
        hvac_m3h = 2549.0  # 1500 CFM converted
        volume_m3 = 765.0  # 3000 sq ft * 9 ft
        deposition_ach = 0.02  # 2% per hour for PM2.5
        
        # Override with scenario-specific values if available
        if 'infiltration_ach' in scenario_info:
            infiltration_ach = scenario_info['infiltration_ach']
        elif 'infiltration_m3h' in scenario_info:
            infiltration_ach = scenario_info['infiltration_m3h'] / volume_m3
            
        if 'hvac_m3h' in scenario_info:
            hvac_m3h = scenario_info['hvac_m3h']
        
        if 'building_volume_m3' in scenario_info:
            volume_m3 = scenario_info['building_volume_m3']
            
        # Calculate filtration ACH
        filtration_ach = hvac_m3h / volume_m3
        
        # Use mass balance function for correct calculation
        expected_ratio = calculate_indoor_outdoor_ratio(
            infiltration_rate=infiltration_ach,
            filtration_rate=filtration_ach,
            deposition_rate=deposition_ach,
            filter_efficiency=filter_efficiency
        )
        
        return expected_ratio
    
    def plot_time_series(self, 
                        df: pd.DataFrame, 
                        title: str = "PM2.5 Time Series",
                        show_predicted: bool = False,
                        predicted_indoor: Optional[List[float]] = None) -> Any:
        """Create standardized time series plot."""
        fig, ax = plt.subplots(figsize=(12, 6))
        
        # Plot actual data
        ax.plot(df['timestamp'], df['outdoor_pm25'], 'r-', linewidth=2, 
                label='Outdoor PM2.5', alpha=0.8)
        ax.plot(df['timestamp'], df['indoor_pm25'], 'b-', linewidth=1.5, 
                label='Indoor PM2.5', alpha=0.9)
        
        # Plot predicted if available
        if show_predicted and predicted_indoor is not None:
            ax.plot(df['timestamp'], predicted_indoor, 'k--', linewidth=1.2, 
                   label='Predicted Indoor', alpha=0.8)
        
        ax.set_title(title)
        ax.set_ylabel('PM2.5 (μg/m³)')
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        self.format_datetime_axis(ax, df)
        return fig
    
    def plot_io_ratio(self,
                     df: pd.DataFrame,
                     title: str = "Indoor/Outdoor Ratio",
                     expected_ratio: Optional[float] = None,
                     step_boundaries: Optional[List[datetime]] = None) -> Any:
        """Create standardized I/O ratio plot."""
        fig, ax = plt.subplots(figsize=(12, 6))
        
        # Calculate ratio
        ratio = df['indoor_pm25'] / df['outdoor_pm25']
        ax.plot(df['timestamp'], ratio, 'purple', linewidth=1.5, alpha=0.8, label='I/O Ratio')
        
        # Add expected ratio line
        if expected_ratio is not None:
            ax.axhline(y=expected_ratio, color='gray', linestyle='--', alpha=0.7,
                      label=f'Expected Steady State ({expected_ratio:.3f})')
        
        # Add step boundaries for step tests
        if step_boundaries:
            for boundary in step_boundaries:
                boundary_num = mdates.date2num(boundary)
                if isinstance(boundary_num, np.ndarray):
                    boundary_num = float(boundary_num.item())
                ax.axvline(x=boundary_num, color='gray', linestyle='--', alpha=0.5)
        
        ax.set_title(title)
        ax.set_ylabel('Indoor/Outdoor Ratio')
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        self.format_datetime_axis(ax, df)
        return fig
    
    def plot_efficiency_over_time(self,
                                 model_history: pd.DataFrame,
                                 true_efficiency: float,
                                 title: str = "Filter Efficiency Over Time") -> Any:
        """Create standardized efficiency tracking plot."""
        fig, ax = plt.subplots(figsize=(12, 6))
        
        # Plot efficiency
        ax.plot(model_history['timestamp'], model_history['efficiency'] * 100, 
               'b-', linewidth=2, label='Estimated Efficiency')
        
        # True efficiency reference line
        ax.axhline(y=true_efficiency * 100, color='red', linestyle='--', alpha=0.7,
                  label=f'True Efficiency ({true_efficiency:.0%})')
        
        # Confidence band if available
        if 'efficiency_lower' in model_history.columns and 'efficiency_upper' in model_history.columns:
            ax.fill_between(model_history['timestamp'], 
                           model_history['efficiency_lower'] * 100,
                           model_history['efficiency_upper'] * 100,
                           alpha=0.2, color='blue', label='Confidence Interval')
        
        ax.set_title(title)
        ax.set_ylabel('Filter Efficiency (%)')
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        self.format_datetime_axis(ax, model_history)
        return fig
    
    def plot_scatter_comparison(self,
                               df: pd.DataFrame,
                               true_params: Dict[str, float],
                               title: str = "Indoor vs Outdoor PM2.5") -> Any:
        """Create standardized scatter plot with theoretical lines."""
        fig, ax = plt.subplots(figsize=(10, 8))
        
        # Scatter plot
        ax.scatter(df['outdoor_pm25'], df['indoor_pm25'], alpha=0.6, s=20, color='blue')
        
        # 1:1 line
        max_val = max(df['outdoor_pm25'].max(), df['indoor_pm25'].max())
        ax.plot([0, max_val], [0, max_val], 'r--', alpha=0.5, label='1:1 line')
        
        # Theoretical line based on true parameters
        if all(key in true_params for key in ['filter_efficiency', 'infiltration_rate_m3h', 
                                             'filtration_rate_m3h', 'deposition_rate_m3h']):
            outdoor_range = np.linspace(0, max_val, 100)
            from utils.mass_balance import calculate_steady_state_indoor_pm25
            theoretical_indoor = calculate_steady_state_indoor_pm25(
                outdoor_pm25=outdoor_range,
                infiltration_rate=true_params['infiltration_rate_m3h'],
                filtration_rate=true_params['filtration_rate_m3h'],
                deposition_rate=true_params['deposition_rate_m3h'],
                filter_efficiency=true_params['filter_efficiency'],
                indoor_generation=0.0
            )
            ax.plot(outdoor_range, np.array(theoretical_indoor), 'g-', 
                   label=f'True Model (η={true_params["filter_efficiency"]:.2f})', linewidth=2)
        
        ax.set_xlabel('Outdoor PM2.5 (μg/m³)')
        ax.set_ylabel('Indoor PM2.5 (μg/m³)')
        ax.set_title(title)
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        return fig
    
    def plot_step_test_analysis(self,
                               df: pd.DataFrame,
                               model_results: Dict[str, Any],
                               scenario_info: Dict[str, Any]) -> Any:
        """Create comprehensive step test analysis plot."""
        num_models = len(model_results)
        fig, axes = plt.subplots(4, num_models, figsize=(6*num_models, 20))
        
        # Ensure axes is 2D
        if num_models == 1:
            axes = axes.reshape(4, 1)
        
        # Add step boundaries
        hours_per_step = scenario_info.get('hours_per_step', 6)
        step_boundaries = []
        for step_hour in [hours_per_step, 2*hours_per_step]:
            step_time = df['timestamp'].iloc[0] + timedelta(hours=step_hour)
            step_boundaries.append(step_time)
        
        for col, (model_name, result) in enumerate(model_results.items()):
            model = result['model']
            
            # Row 0: Combined outdoor & indoor
            ax = axes[0, col]
            ax.plot(df['timestamp'], df['outdoor_pm25'], 'r-', linewidth=2, label='Outdoor')
            ax.plot(df['timestamp'], df['indoor_pm25'], 'b-', linewidth=1.5, label='Indoor')
            
            # Add predicted if available
            if hasattr(model, 'predict_indoor_pm25'):
                predicted = []
                for _, row in df.iterrows():
                    pred = model.predict_indoor_pm25(row['outdoor_pm25'])
                    predicted.append(pred if pred is not None else np.nan)
                ax.plot(df['timestamp'], np.array(predicted), 'k--', linewidth=1.2, 
                       label='Predicted Indoor')
            
            # Step boundaries
            for boundary in step_boundaries:
                boundary_num = mdates.date2num(boundary)
                if isinstance(boundary_num, np.ndarray):
                    boundary_num = float(boundary_num.item())
                ax.axvline(x=boundary_num, color='gray', linestyle='--', alpha=0.5)
            
            ax.set_title(f'{model_name.upper()} - PM2.5 Step Response')
            ax.set_ylabel('PM2.5 (μg/m³)')
            ax.legend()
            ax.grid(True, alpha=0.3)
            self.format_datetime_axis(ax, df)
            
            # Row 1: I/O Ratio
            ax = axes[1, col]
            ratio = df['indoor_pm25'] / df['outdoor_pm25']
            ax.plot(df['timestamp'], ratio, 'purple', linewidth=1.5, alpha=0.8, label='I/O Ratio')
            
            # Expected ratio
            true_eff = scenario_info['filter_efficiency']
            expected_ratio = self._calculate_expected_io_ratio(true_eff, scenario_info)
            ax.axhline(y=expected_ratio, color='gray', linestyle='--', alpha=0.7,
                      label=f'Expected ({expected_ratio:.3f})')
            
            ax.set_title(f'{model_name.upper()} - I/O Ratio')
            ax.set_ylabel('Indoor/Outdoor Ratio')
            ax.legend()
            ax.grid(True, alpha=0.3)
            self.format_datetime_axis(ax, df)
            
            # Row 2: Filter efficiency
            ax = axes[2, col]
            if hasattr(model, 'state_history') and model.state_history:
                hist_df = pd.DataFrame(model.state_history)
                hist_df['timestamp'] = pd.to_datetime(hist_df['timestamp'])
                ax.plot(hist_df['timestamp'], hist_df['efficiency']*100, 
                       'b-', linewidth=2, label='Estimated Efficiency')
                ax.axhline(y=true_eff * 100, color='red', linestyle='--', alpha=0.7,
                          label=f'True Efficiency ({true_eff:.0%})')
                ax.set_ylabel('Filter Efficiency (%)')
                ax.legend()
                self.format_datetime_axis(ax, hist_df)
            else:
                ax.text(0.5, 0.5, 'No efficiency tracking\navailable', 
                       transform=ax.transAxes, ha='center', va='center')
                ax.axis('off')
            
            ax.set_title(f'{model_name.upper()} - Efficiency Tracking')
            ax.grid(True, alpha=0.3)
            
            # Row 3: Model diagnostics
            ax = axes[3, col]
            if hasattr(model, 'state_history') and model.state_history:
                hist_df = pd.DataFrame(model.state_history)
                hist_df['timestamp'] = pd.to_datetime(hist_df['timestamp'])
                ax.plot(hist_df['timestamp'], hist_df['efficiency']*100, 
                       'b-', linewidth=1.5, label='η (%)')
                if 'leak_ach' in hist_df.columns:
                    ax.plot(hist_df['timestamp'], hist_df['leak_ach'], 
                           'g-', linewidth=1.5, label='Infiltration ACH')
                ax.set_ylabel('Model Parameters')
                ax.legend()
                self.format_datetime_axis(ax, hist_df)
            else:
                ax.axis('off')
            
            ax.set_title(f'{model_name.upper()} - Diagnostics')
            ax.grid(True, alpha=0.3)
        
        plt.suptitle(f'Step Test Analysis: {scenario_info.get("description", "Unknown")}', 
                     fontsize=16, y=0.98)
        plt.tight_layout(rect=(0,0,1,0.97))
        
        return fig
    
    def plot_parameter_comparison(self,
                                 results: Dict[str, Dict],
                                 title: str = "Parameter Comparison") -> Any:
        """Create parameter comparison bar charts."""
        scenarios = []
        true_effs = []
        est_effs = []
        errors = []
        
        for scenario, data in results.items():
            if not data.get('success', False):
                continue
            
            scenarios.append(scenario.replace('_', ' ').title())
            true_eff = data['true_params']['filter_efficiency'] * 100
            est_eff = data.get('estimated_efficiency', 0) * 100
            
            true_effs.append(true_eff)
            est_effs.append(est_eff)
            errors.append(abs(est_eff - true_eff))
        
        fig, axes = plt.subplots(1, 2, figsize=(15, 6))
        
        # Efficiency comparison
        x = np.arange(len(scenarios))
        width = 0.35
        
        axes[0].bar(x - width/2, true_effs, width, label='True', alpha=0.8, color='green')
        axes[0].bar(x + width/2, est_effs, width, label='Estimated', alpha=0.8, color='blue')
        axes[0].set_xlabel('Scenario')
        axes[0].set_ylabel('Filter Efficiency (%)')
        axes[0].set_title('Filter Efficiency: True vs Estimated')
        axes[0].set_xticks(x)
        axes[0].set_xticklabels(scenarios, rotation=45, ha='right')
        axes[0].legend()
        axes[0].grid(True, alpha=0.3)
        
        # Error analysis
        colors = ['red' if err > 10 else 'orange' if err > 5 else 'green' for err in errors]
        bars = axes[1].bar(scenarios, errors, color=colors, alpha=0.7)
        axes[1].axhline(y=5, color='orange', linestyle='--', alpha=0.7, label='5% Error')
        axes[1].axhline(y=10, color='red', linestyle='--', alpha=0.7, label='10% Error')
        axes[1].set_xlabel('Scenario')
        axes[1].set_ylabel('Absolute Error (%)')
        axes[1].set_title('Estimation Errors')
        axes[1].set_xticklabels(scenarios, rotation=45, ha='right')
        axes[1].legend()
        axes[1].grid(True, alpha=0.3)
        
        # Add error values on bars
        for bar, error in zip(bars, errors):
            height = bar.get_height()
            axes[1].text(bar.get_x() + bar.get_width()/2., height + 0.1,
                        f'{error:.1f}%', ha='center', va='bottom', fontsize=9)
        
        plt.tight_layout()
        return fig
    
    def create_test_summary_plot(self,
                                test_name: str,
                                scenarios: List[str],
                                results: Dict[str, Dict],
                                save_filename: Optional[str] = None) -> Path:
        """Create a comprehensive test summary visualization."""
        num_scenarios = len(scenarios)
        
        # Create main comparison plot
        fig = self.plot_parameter_comparison(results, f"{test_name} - Summary")
        
        if save_filename:
            save_path = self.save_plot(save_filename)
            print(f"Test summary saved: {save_path}")
            return save_path
        else:
            return self.save_plot(f"{test_name.lower().replace(' ', '_')}_summary.png")

    def plot_comprehensive_analysis(self,
                                   df: pd.DataFrame,
                                   model_results: Dict[str, Any],
                                   scenario_info: Dict[str, Any],
                                   title: str = "Filter Analysis") -> Any:
        """Create comprehensive analysis plot with 3 subplots."""
        fig, axes = plt.subplots(3, 1, figsize=(15, 12))
        
        # Subplot 1: Time series data
        axes[0].plot(df['timestamp'], df['outdoor_pm25'], 'r-', linewidth=2, 
                    label='Outdoor PM2.5', alpha=0.8)
        axes[0].plot(df['timestamp'], df['indoor_pm25'], 'b-', linewidth=1.5, 
                    label='Indoor PM2.5', alpha=0.9)
        
        # Add predicted if available
        for model_name, result in model_results.items():
            if result.get('success') and 'model' in result:
                model = result['model']
                if hasattr(model, 'state_history') and model.state_history:
                    hist_df = pd.DataFrame(model.state_history)
                    hist_df['timestamp'] = pd.to_datetime(hist_df['timestamp'])
                    if 'predicted_indoor' in hist_df.columns:
                        axes[0].plot(hist_df['timestamp'], hist_df['predicted_indoor'], 
                                   'k--', linewidth=1.2, alpha=0.8, 
                                   label=f'{model_name.upper()} Predicted')
        
        axes[0].set_title(f'{title} - Time Series')
        axes[0].set_ylabel('PM2.5 (μg/m³)')
        axes[0].legend()
        axes[0].grid(True, alpha=0.3)
        self.format_datetime_axis(axes[0], df)
        
        # Subplot 2: I/O Ratio
        ratio = df['indoor_pm25'] / df['outdoor_pm25']
        axes[1].plot(df['timestamp'], ratio, 'purple', linewidth=1.5, alpha=0.8, label='I/O Ratio')
        
        # Expected ratio line
        if 'filter_efficiency' in scenario_info:
            eff = scenario_info['filter_efficiency']
            expected_ratio = self._calculate_expected_io_ratio(eff, scenario_info)
            axes[1].axhline(y=expected_ratio, color='gray', linestyle='--', alpha=0.7,
                          label=f'Expected Steady State ({expected_ratio:.3f})')
        
        axes[1].set_title(f'{title} - Indoor/Outdoor Ratio')
        axes[1].set_ylabel('Indoor/Outdoor Ratio')
        axes[1].legend()
        axes[1].grid(True, alpha=0.3)
        self.format_datetime_axis(axes[1], df)
        
        # Subplot 3: Kalman filter results
        has_filter_data = False
        for model_name, result in model_results.items():
            if result.get('success') and 'model' in result:
                model = result['model']
                if hasattr(model, 'state_history') and model.state_history:
                    hist_df = pd.DataFrame(model.state_history)
                    hist_df['timestamp'] = pd.to_datetime(hist_df['timestamp'])
                    
                    # Plot efficiency evolution
                    axes[2].plot(hist_df['timestamp'], hist_df['efficiency'] * 100, 
                               'b-', linewidth=2, label=f'{model_name.upper()} Efficiency')
                    
                    # Add final estimate as text
                    final_eff = hist_df['efficiency'].iloc[-1] * 100
                    axes[2].text(0.02, 0.98, f'Final Estimate: {final_eff:.1f}%', 
                               transform=axes[2].transAxes, fontsize=12, 
                               bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.8),
                               verticalalignment='top')
                    
                    has_filter_data = True
        
        # True efficiency reference line
        if 'filter_efficiency' in scenario_info:
            true_eff = scenario_info['filter_efficiency'] * 100
            axes[2].axhline(y=true_eff, color='red', linestyle='--', alpha=0.7,
                          label=f'True Efficiency ({true_eff:.0f}%)')
        
        if has_filter_data:
            axes[2].set_title(f'{title} - Filter Efficiency Evolution')
            axes[2].set_ylabel('Filter Efficiency (%)')
            axes[2].set_xlabel('Time')
            axes[2].legend()
            axes[2].grid(True, alpha=0.3)
            # Get timestamp range from filter data
            for model_name, result in model_results.items():
                if result.get('success') and 'model' in result:
                    model = result['model']
                    if hasattr(model, 'state_history') and model.state_history:
                        hist_df = pd.DataFrame(model.state_history)
                        hist_df['timestamp'] = pd.to_datetime(hist_df['timestamp'])
                        self.format_datetime_axis(axes[2], hist_df)
                        break
        else:
            axes[2].text(0.5, 0.5, 'No Kalman filter tracking\navailable', 
                       transform=axes[2].transAxes, ha='center', va='center',
                       fontsize=14, color='gray')
            axes[2].set_title(f'{title} - Filter Efficiency (No Data)')
            axes[2].axis('off')
        
        plt.suptitle(f'{scenario_info.get("description", title)}', fontsize=16, y=0.98)
        plt.tight_layout(rect=(0, 0, 1, 0.96))
        
        return fig


# Convenience functions for direct use
def create_visualizer(output_dir: Union[str, Path] = "test_visualizations") -> FilterVisualization:
    """Create a FilterVisualization instance."""
    return FilterVisualization(output_dir)


def save_test_visualization(test_name: str,
                           df: pd.DataFrame,
                           model_results: Dict[str, Any],
                           scenario_info: Dict[str, Any],
                           true_params: Optional[Dict[str, float]] = None,
                           output_dir: Union[str, Path] = "test_visualizations") -> List[Path]:
    """
    Save a comprehensive test visualization with 3 subplots in a single figure.
    
    Returns list of saved file paths.
    """
    viz = FilterVisualization(output_dir)
    saved_files = []
    
    # Create comprehensive single figure with 3 subplots
    fig = viz.plot_comprehensive_analysis(df, model_results, scenario_info, test_name)
    saved_files.append(viz.save_plot(f"{test_name}_comprehensive.png"))
    
    return saved_files 