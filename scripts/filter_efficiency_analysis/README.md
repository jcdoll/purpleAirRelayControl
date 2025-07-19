# HVAC Filter Efficiency Analysis

This system analyzes HVAC filter efficiency and air infiltration rates from indoor/outdoor PM2.5 concentration data using a night-time calibration approach with Bayesian parameter estimation.

## Overview

The analysis uses the fact that during night-time hours (10pm-8am), your building is typically sealed (doors/windows closed, minimal activity), creating stable conditions ideal for estimating filter performance. By comparing indoor and outdoor PM2.5 concentrations during these periods, we can determine:

- **Filter Efficiency**: How well your HVAC filter removes particles (0-100%)
- **Air Infiltration Rate**: How much outdoor air leaks into your building (Air Changes per Hour)
- **Filter Degradation**: How efficiency changes over time
- **Replacement Recommendations**: When to replace your filter based on performance

## Quick Start

### 1. Configure Your Building Parameters

Edit `config.yaml` with your building specifications:

```yaml
building:
  area_sq_ft: 3000          # Your building's floor area
  ceiling_height_ft: 9      # Average ceiling height

hvac:
  flow_rate_cfm: 1500       # Your HVAC system's air flow rate
```

### 2. Set Up Google Sheets Access

1. **Get your Spreadsheet ID** from your Google Sheets URL:
   ```
   https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/edit
   ```

2. **Update config.yaml** with your spreadsheet ID:
   ```yaml
   google_sheets:
     spreadsheet_id: "your_actual_spreadsheet_id_here"
   ```

3. **Set up Google Sheets API credentials** (see [Google Sheets Setup](#google-sheets-setup) below)

### 3. Run Analysis Locally

```bash
# Install dependencies
pip install -r requirements.txt

# Test with dry run (no write to sheets)
python analyze_filter_performance.py --dry-run

# Run actual analysis
python analyze_filter_performance.py --days 7
```

### 4. Set Up Automated Analysis (GitHub Actions)

1. **Add Google Sheets credentials** to GitHub Secrets (see [GitHub Actions Setup](#github-actions-setup))
2. **Commit and push** your configuration changes
3. **Trigger manually** from GitHub Actions tab or wait for daily scheduled run

## How It Works

### The Science Behind It

The analysis is based on a **mass balance model** for indoor air quality:

```
Indoor PM2.5 = (Outdoor Infiltration - HVAC Filtration - Natural Deposition) / Building Volume
```

During night-time when conditions are stable:
- **Outdoor infiltration** is constant (building leakage)
- **HVAC filtration** depends on filter efficiency and flow rate
- **Natural deposition** is the rate particles settle out naturally

By fitting this model to real data, we can solve for the unknown filter efficiency.

### System Requirements and Assumptions

**HVAC Operation Requirements:**
- **Continuous fan operation during night hours** - The analysis assumes relatively constant airflow through the filter during the 10pm-8am analysis window. Systems with intermittent fan operation may produce unreliable results.
- **Consistent flow rate** - While some variation during active heating/cooling is acceptable, major flow rate changes will affect accuracy.

**Data Requirements:**
- **Consistent AQI-PM2.5 conversion** - Both sensor hardware and analysis software must use the same EPA AQI standard for accurate round-trip conversion.

### Night-Time Calibration

Why night-time? During 10pm-8am:
- Doors and windows are typically closed
- Minimal indoor particle generation (no cooking, reduced activity)
- HVAC system operation is more consistent
- Provides the most stable conditions for accurate analysis

### Model Validation

The system provides several quality metrics:
- **R² (Coefficient of Determination)**: How well the model fits your data (>0.8 is excellent)
- **RMSE/MAE**: Prediction accuracy metrics
- **Data Quality**: Number of valid data points used

## **CRITICAL: Current Model Performance Issues**

**Performance testing has revealed significant issues with the current implementation:**

- **Parameter estimation failures** - Model converges to similar values (~80% efficiency) regardless of true filter performance
- **Poor fit quality** - R² values often negative, indicating model fits worse than a simple average
- **High estimation errors** - Mean efficiency estimation error of 59%, with maximum errors exceeding 200%
- **Optimization problems** - Algorithm appears to get stuck in local minima or hit parameter bounds

**Recommendation**: This tool should be considered **experimental** and not used for critical filter replacement decisions until these issues are resolved.

**For reliable filter monitoring, consider:**
- Direct pressure drop measurements across the filter
- Periodic visual inspection and manufacturer replacement schedules
- Professional HVAC system evaluation

## Configuration Reference

### Building Parameters

```yaml
building:
  area_sq_ft: 3000          # Total conditioned floor area
  ceiling_height_ft: 9      # Average ceiling height
```

**How to measure:**
- Use building plans or measure each room
- For multi-story, include all conditioned levels
- Don't include unconditioned spaces (garage, basement)

### HVAC Parameters

```yaml
hvac:
  flow_rate_cfm: 1500       # Air handler flow rate in CFM
  deposition_rate_percent: 10  # Natural particle settling rate
```

**How to find flow rate:**
- Check HVAC system specifications
- Look on air handler unit label
- HVAC contractor can measure with instruments
- Typical range: 400 CFM/ton of cooling capacity

### Analysis Settings

```yaml
analysis:
  night_start_hour: 22      # Start of sealed period (10 PM)
  night_end_hour: 8         # End of sealed period (8 AM)
  min_data_points: 10       # Minimum data points required
  outlier_threshold: 2.0    # Outlier detection sensitivity
```

### Alert Thresholds

```yaml
alerts:
  efficiency_thresholds:
    excellent: 0.85         # > 85% efficiency
    good: 0.70             # 70-85% efficiency
    declining: 0.50        # 50-70% efficiency
    poor: 0.50             # < 50% efficiency
```

## Google Sheets Setup

### 1. Create a Service Account

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable the Google Sheets API
4. Create credentials → Service Account, no role required
5. Create a new JSON key
6. Download the JSON key file

### 2. Share Your Spreadsheet

1. Open your Google Sheets document
2. Click "Share" 
3. Add the service account email (from JSON file) with "Editor" permissions

### 3. Set Up Credentials

**For Local Development:**
```bash
# Save credentials as credentials.json in the script directory
cp path/to/your/service-account-key.json scripts/filter_efficiency_analysis/credentials.json
```

**For GitHub Actions:**
Store the entire JSON content as a GitHub Secret (see below).

### 4. Validate Local Connection

Test your Google Sheets connection before running analysis:

```bash
# Test with dry run (reads data but doesn't write results)
python analyze_filter_performance.py --dry-run --days 7

# If successful, you'll see real data from your sheets
# If credentials are missing, you'll get a clear error message
```

## GitHub Actions Setup

### 1. Add Google Sheets Credentials

1. Go to your GitHub repository
2. Settings → Secrets and variables → Actions
3. Click "New repository secret"
4. Name: `GOOGLE_SHEETS_CREDENTIALS`
5. Value: Copy the entire contents of your service account JSON file

### 2. Configure the Workflow

The workflow is automatically configured to:
- Run daily at 6 AM UTC
- Use the last 7 days of data
- Write results to your Google Sheets

### 3. Manual Trigger

You can manually trigger the analysis:
1. Go to Actions tab in your GitHub repository
2. Select "Filter Efficiency Analysis"
3. Click "Run workflow"
4. Optionally adjust days of data or enable dry-run mode

## Testing

The analysis system includes comprehensive unit and integration tests to ensure reliability. Tests use synthetic data with known parameters to validate the algorithms.

### Run All Tests

```bash
# Install test dependencies
pip install pytest pytest-cov

# Run all tests with coverage
python -m pytest tests/ --cov=utils --cov=models --cov-report=term-missing

# Quick test run (no coverage)
python -m pytest tests/ -v
```

## Usage Examples

### Basic Analysis

```bash
# Analyze last 7 days
python analyze_filter_performance.py

# Analyze last 14 days  
python analyze_filter_performance.py --days 14

# Test without writing to sheets
python analyze_filter_performance.py --dry-run
```

### Advanced Options

```bash
# Custom config file
python analyze_filter_performance.py --config my_house_config.yaml

# Save results to file
python analyze_filter_performance.py --output results.json

# Debug mode
python analyze_filter_performance.py --log-level DEBUG
```
