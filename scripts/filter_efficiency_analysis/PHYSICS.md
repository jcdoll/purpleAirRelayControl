# HVAC Filter Efficiency Estimation: Physical Theory and Mathematical Foundation

## Overview

This document presents the theoretical foundation for estimating HVAC filter efficiency from indoor and outdoor PM2.5 concentration measurements. The approach is based on fundamental mass balance principles and exploits stable night-time conditions for parameter estimation.

## Theoretical Foundation

### Mass Balance Model

The fundamental equation governing indoor PM2.5 concentration in a well-mixed building:

```
V * dC_in/dt = Q_inf * C_out + Q_gen - Q_filt * η * C_in - Q_dep * C_in
```

**Where:**
- `C_in`, `C_out`: Indoor/outdoor PM2.5 concentrations (μg/m³)
- `V`: Building volume (m³)
- `Q_inf`: Infiltration rate (m³/h) - air leakage from outside
- `Q_filt`: HVAC filtration flow rate (m³/h)
- `η`: Filter efficiency (0-1) - **primary parameter to estimate**
- `Q_gen`: Indoor particle generation rate (μg/h)
- `Q_dep`: Particle deposition/settling rate (m³/h)

### Physical Interpretation

**Particle Sources (Inputs):**
- `Q_inf * C_out`: Outdoor particles entering through building leakage
- `Q_gen`: Indoor particle generation (cooking, activity, dust resuspension)

**Particle Sinks (Removal):**
- `Q_filt * η * C_in`: HVAC filtration removal
- `Q_dep * C_in`: Natural settling and surface deposition
- `V * dC_in/dt`: Rate of concentration change (storage term)

### Steady-State Approximation

For periods with stable conditions (night-time), the rate of change approaches zero:

```
dC_in/dt ≈ 0
```

This simplifies the mass balance to:

```
0 = Q_inf * C_out + Q_gen - Q_filt * η * C_in - Q_dep * C_in
```

Rearranging for indoor concentration:

```
C_in = (Q_inf * C_out + Q_gen) / (Q_inf + Q_filt * η + Q_dep)
```

### Night-Time Conditions

During sealed night-time periods (typically 10 PM - 8 AM):

**Simplified Assumptions:**
- `Q_gen ≈ 0` (minimal indoor particle generation)
- `Q_inf` is relatively constant (doors/windows closed)
- HVAC operation is consistent

**Simplified Model:**
```
C_in = (Q_inf * C_out) / (Q_inf + Q_filt * η + Q_dep)
```

### Solving for Filter Efficiency

Rearranging the steady-state equation to solve for filter efficiency:

```
η = (Q_inf * (C_out - C_in) - Q_dep * C_in) / (Q_filt * C_in)
```

**Physical Meaning:**
- When `C_out > C_in`: Filter is removing particles (positive efficiency)
- When `C_out ≈ C_in`: Minimal filtration occurring (low efficiency)
- When `C_out < C_in`: Indoor generation dominates (model invalid)

## Mathematical Framework

### State-Space Representation

For dynamic analysis over time, we model filter degradation as an exponential decay process:

```
η[t+1] = η[t] * exp(-degradation_rate * dt) + w_η[t]
```

Where:
- `degradation_rate`: Filter degradation constant (1/time)
- `w_η[t]`: Process noise (random variations)

**Infiltration Rate Evolution:**
```
λ_inf[t+1] = λ_inf[t] + w_λ[t]
```

**Observation Model:**
```
C_in[t] = (λ_inf[t] * C_out[t]) / (λ_inf[t] + η[t] * Q_filt + Q_dep) + v[t]
```

Where `v[t]` represents measurement noise.

### Bayesian Parameter Estimation

**Prior Distributions:**

*Filter Efficiency:*
```
η ~ Beta(α=8, β=2)  # Prior belief: most filters are reasonably effective
```

*Infiltration Rate (in Air Changes per Hour):*
```
ACH ~ Gamma(shape=2, scale=0.3)  # Prior: 0.6 ACH mean, 0.3 ACH mode
```

**Likelihood Function:**

For night-time data points, assuming Gaussian measurement noise:

```
L(η, λ_inf | data) = ∏ N(C_in_predicted[i], σ²)
```

Where:
```
C_in_predicted[i] = (λ_inf * C_out[i]) / (λ_inf + η * Q_filt + Q_dep)
```

**Posterior Distribution:**
```
P(η, λ_inf | data) ∝ L(η, λ_inf | data) * P(η) * P(λ_inf)
```

## Physical Constraints and Assumptions

### Model Validity Conditions

**Building Air Mixing:**
- Well-mixed air assumption requires adequate HVAC circulation
- Typically valid for residential/commercial buildings with forced air systems

**Steady-State Validity:**
- Night-time periods provide quasi-steady conditions
- Time scales: outdoor concentration changes (hours) >> building mixing time (minutes)

**Filter Representation:**
- Single efficiency value represents average performance across particle sizes
- Assumes uniform flow through filter medium

### Physical Parameter Ranges

**Filter Efficiency (η):**
- HEPA filters: 0.97-0.999 (97-99.9%)
- High-efficiency pleated: 0.80-0.95 (80-95%)
- Standard pleated: 0.40-0.80 (40-80%)
- Fiberglass: 0.10-0.40 (10-40%)

**Air Changes per Hour (ACH):**
- Very tight buildings: <0.5 ACH
- Well-sealed modern: 0.5-1.0 ACH
- Typical residential: 1.0-2.0 ACH
- Leaky buildings: >2.0 ACH

**Deposition Rate:**
- Typical indoor deposition: 0.1-0.5 h⁻¹
- Depends on particle size, air movement, surface area

## Model Limitations and Uncertainties

### Fundamental Assumptions

**Single Well-Mixed Zone:**
- Reality: Buildings have multiple zones with different mixing
- Impact: Average efficiency across building, not local values

**Constant Filter Efficiency:**
- Reality: Efficiency varies with particle size, flow rate, loading
- Impact: Represents average performance across operating conditions

**Steady-State During Night:**
- Reality: Some transient effects always present
- Impact: Good approximation for analysis periods >2 hours

### Uncertainty Sources

**Measurement Uncertainty:**
- Sensor accuracy: ±15-20% typical for PM2.5 sensors
- Calibration drift over time
- Environmental factors (humidity, temperature)

**Model Uncertainty:**
- Unmodeled physics (particle coagulation, chemical reactions)
- Simplified building representation
- Weather-dependent infiltration variations

**Parameter Uncertainty:**
- Building volume estimation errors
- HVAC flow rate variations
- Deposition rate assumptions

## Regime Classification

### Night-Time Regime (Primary Analysis)

**Characteristics:**
- Sealed building envelope (minimal door/window openings)
- Reduced occupant activity
- Stable indoor particle generation
- Consistent HVAC operation

**Optimal for:**
- Filter efficiency estimation
- Baseline infiltration rate determination
- Model parameter calibration

### Day-Time Regime (Future Extension)

**Characteristics:**
- Variable infiltration (door openings, window operations)
- Occupant activity effects
- Variable indoor generation (cooking, cleaning)
- Potential HVAC cycling

**Analysis Approach:**
- Apply night-calibrated parameters
- Detect and account for activity events
- Model variable infiltration rates

## Validation Metrics

### Model Fit Quality

**Coefficient of Determination (R²):**
```
R² = 1 - SS_res / SS_tot
```
- Values >0.8 indicate excellent fit
- Values 0.6-0.8 indicate good fit
- Values <0.6 suggest model limitations or data quality issues

**Root Mean Square Error (RMSE):**
```
RMSE = √(Σ(C_predicted - C_observed)² / N)
```
- Lower values indicate better predictions
- Units: μg/m³ (same as concentration)

### Physical Consistency Checks

**Mass Balance Closure:**
- Predicted vs. observed indoor concentrations
- Energy balance for particle transport

**Parameter Reasonableness:**
- Filter efficiency within expected ranges
- Infiltration rates consistent with building type
- Temporal trends consistent with filter aging

## Extension to Multiple Pollutants

### Particle Size Dependence

The framework can be extended to size-resolved analysis:

```
C_in[d] = (Q_inf * C_out[d]) / (Q_inf + η[d] * Q_filt + Q_dep[d])
```

Where `d` represents particle diameter, and efficiency `η[d]` varies with size.

### Multi-Pollutant Analysis

For gases and vapors that are not filtered:

```
C_in_gas = (Q_inf * C_out_gas) / Q_inf
```

This provides an independent check on infiltration rate estimation.

## Summary

This theoretical framework provides a physically-based approach to estimating HVAC filter efficiency from readily available indoor/outdoor concentration measurements. The night-time calibration strategy exploits stable conditions to enable robust parameter estimation, while the Bayesian framework provides uncertainty quantification. The model's foundation in fundamental mass balance principles ensures physical consistency and interpretability of results. 