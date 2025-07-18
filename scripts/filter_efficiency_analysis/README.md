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

### Interpreting Results

**Filter Efficiency:**
- **90%+**: Excellent (HEPA-level performance)
- **80-90%**: Very Good (high-quality pleated filter)
- **60-80%**: Good (standard pleated filter)
- **40-60%**: Fair (basic filter, may need replacement)
- **<40%**: Poor (replace immediately)

**Air Changes per Hour (ACH):**
- **<0.5**: Very tight building
- **0.5-1.0**: Well-sealed building (typical new construction)
- **1.0-2.0**: Average building tightness
- **>2.0**: Leaky building (older construction)

**Model Confidence (R²):**
- **>0.8**: Excellent fit, high confidence
- **0.6-0.8**: Good fit, reasonable confidence  
- **0.4-0.6**: Moderate fit, check data quality
- **<0.4**: Poor fit, results may be unreliable

## Troubleshooting

### Common Issues

**"Insufficient night-time data"**
- Check that your data includes timestamps
- Verify night-time hours in config match your schedule
- Ensure you have data spanning multiple days

**"Missing required columns"**
- Check column names in your Google Sheets
- Update column mapping in config if needed
- Ensure both indoor and outdoor AQI columns exist

**"Analysis confidence is low"**
- Check for sensor calibration issues
- Look for periods with unusual activity (parties, construction)
- Verify HVAC system was running during analysis period

**"Google Sheets connection failed"**
- Verify service account email has access to spreadsheet
- Check that spreadsheet ID is correct
- Ensure Google Sheets API is enabled

### Data Quality Tips

1. **Sensor Placement**: 
   - Indoor sensor away from HVAC vents
   - Outdoor sensor in representative location
   - Avoid kitchens, bathrooms, or dusty areas

2. **Data Collection**:
   - Collect at least 7 days of continuous data
   - Include both weekdays and weekends
   - Avoid periods with unusual activities

3. **HVAC Operation**:
   - Ensure system runs regularly during analysis period
   - Note any filter changes or maintenance
   - Consider seasonal variations in operation

## Building Parameter Guide

### Measuring Your Building Volume

**Simple Method:**
```
Volume = Floor Area × Ceiling Height × 0.8
```
(The 0.8 factor accounts for interior walls, furniture, etc.)

**Detailed Method:**
1. Measure each conditioned room
2. Multiply length × width × height
3. Sum all rooms
4. Include hallways, closets
5. Exclude garage, unfinished basement

### Determining HVAC Flow Rate

**From Equipment Labels:**
- Air handler unit nameplate
- Blower motor specifications
- System design documents

**Professional Measurement:**
- HVAC contractor with flow meter
- Duct blaster testing
- Commissioning reports

**Estimation by Tonnage:**
```
CFM ≈ Cooling Tons × 400
```
(Standard rule of thumb: 400 CFM per ton)

## Advanced Configuration

### Custom Alert Thresholds

Adjust thresholds based on your filter type:

```yaml
# For basic fiberglass filters
alerts:
  efficiency_thresholds:
    excellent: 0.60
    good: 0.40
    declining: 0.30
    poor: 0.20

# For HEPA filters  
alerts:
  efficiency_thresholds:
    excellent: 0.95
    good: 0.90
    declining: 0.85
    poor: 0.80
```

### Multiple Buildings

Create separate config files:

```bash
# House config
python analyze_filter_performance.py --config house_config.yaml

# Office config  
python analyze_filter_performance.py --config office_config.yaml
```

## Technical Details

### Dependencies

- **numpy, pandas, scipy**: Data analysis and scientific computing
- **PyYAML**: Configuration file parsing
- **google-api-python-client**: Google Sheets integration
- **matplotlib** (optional): Plotting and visualization

### Algorithm Overview

1. **Data Preprocessing**: Convert AQI to PM2.5, filter night-time data, remove outliers
2. **Model Fitting**: Maximum likelihood estimation of filter efficiency and infiltration rate
3. **Validation**: Calculate R², RMSE, and other quality metrics
4. **Trending**: Track efficiency changes over time
5. **Recommendations**: Generate actionable insights

### Model Assumptions

- Building air is well-mixed
- Filter efficiency is constant during analysis period
- Night-time conditions are representative
- Indoor particle generation is minimal at night
- HVAC system operation is consistent

## Contributing

This system is designed to be extensible. Areas for improvement:

- **Additional Models**: Implement other analysis methods (Extended Kalman Filter, machine learning)
- **Visualization**: Add charts and plots for better insights
- **Integration**: Connect with smart home systems or IoT platforms
- **Validation**: Compare with professional HVAC testing

## Support

For issues and questions:

1. Check the troubleshooting guide above
2. Review GitHub Issues for similar problems  
3. Run with `--log-level DEBUG` for detailed diagnostics
4. Verify your building parameters and data quality

## License

This project is part of the Purple Air Relay Control system and follows the same licensing terms. 