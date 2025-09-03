# Soil Parameters and Correlations

**Source:** Geotechnical Engineering Reference Manual and Field Testing Guidelines

## Introduction

Accurate determination of soil parameters is essential for reliable geotechnical analysis. This note summarizes key soil parameters and their correlations with field and laboratory test results, particularly focusing on parameters used in settlement and bearing capacity calculations.

## Key Soil Parameters

### Strength Parameters

**Internal Friction Angle (φ)**
- Fundamental shear strength parameter for granular soils
- Typical ranges: Dense sand (35-45°), Medium sand (30-35°), Loose sand (25-30°)
- Critical for bearing capacity calculations

**Cohesion (c)**
- Shear strength intercept for cohesive soils
- Undrained cohesion (cu) for short-term analysis
- Effective cohesion (c') for long-term analysis

### Deformation Parameters

**Young's Modulus (E)**
- Elastic stiffness parameter
- Used in immediate settlement calculations
- Varies significantly with stress level and soil type

**Poisson's Ratio (ν)**
- Ratio of lateral to axial strain
- Typical values: Sand (0.2-0.4), Clay (0.3-0.5)
- Affects stress distribution and settlement

## SPT Correlations

### Friction Angle from SPT
**Peck, Hanson & Thornburn (1974):**
- φ = 27.1 + 0.3 × N60 - 0.00054 × N60²
- Valid for normally consolidated sands

**Hatanaka & Uchida (1996):**
- φ = √(20 × N60) + 20 (for clean sands)
- More reliable for modern practice

### Young's Modulus from SPT
**Bowles (1997):**
- E = 500 × (N60 + 15) kPa (for sands)
- E = 300 × (N60 + 6) kPa (for silts and sandy clays)

**Kulhawy & Mayne (1990):**
- E = 8.5 × N60^0.84 MPa (for granular soils)

## CPT Correlations

### Friction Angle from CPT
**Robertson & Campanella (1983):**
- φ = arctan(0.1 + 0.38 × log(qc/σ'v0))
- Where qc is cone resistance and σ'v0 is effective overburden stress

**Kulhawy & Mayne (1990):**
- φ = 17.6 + 11.0 × log(qc/σ'v0)

### Young's Modulus from CPT
**Lunne et al. (1997):**
- E = α × qc
- Where α = 2-4 for sands, 3-8 for silts, 1-2 for clays

**Mayne (2007):**
- E = 8.5 × qc^0.13 × (qc/100)^0.5 MPa

## Unit Weight Correlations

### From SPT
**Meyerhof (1956):**
- γ = 11.0 + 0.33 × N60 kN/m³ (for sands above water table)
- γsat = 16.0 + 0.15 × N60 kN/m³ (for saturated sands)

### From CPT
**Robertson & Cabal (2015):**
- γ = 0.27 × log(Rf) + 0.36 × log(qc/Pa) + 1.236 g/cm³
- Where Rf is friction ratio and Pa is atmospheric pressure

## Consolidation Parameters

### Compression Index (Cc)
**Terzaghi & Peck (1967):**
- Cc = 0.009 × (LL - 10) (for remolded clays)
- Where LL is liquid limit

**Skempton (1944):**
- Cc = 0.007 × (LL - 7) (for undisturbed clays)

### Coefficient of Consolidation (cv)
**Typical ranges:**
- Soft clays: 1-5 m²/year
- Medium clays: 5-20 m²/year
- Stiff clays: 20-100 m²/year

## Quality and Reliability

### SPT Limitations
- Energy efficiency variations (60-90%)
- Sampling disturbance effects
- Equipment and procedural differences
- Limited applicability in gravels

### CPT Advantages
- Continuous profiling
- Standardized procedures
- High repeatability
- Real-time data acquisition
- Better statistical reliability

### Laboratory Testing
- Provides fundamental parameters
- Quality control for correlations
- Site-specific calibration
- Advanced testing capabilities

## Application Guidelines

### Parameter Selection
- Use multiple correlation methods
- Compare with local experience
- Consider soil variability
- Apply engineering judgment

### Uncertainty Management
- Acknowledge correlation limitations
- Use conservative estimates
- Perform sensitivity analysis
- Validate with field performance

### Best Practices
- Combine field and laboratory data
- Use site-specific correlations when available
- Document assumptions and limitations
- Update parameters based on performance

These correlations provide valuable tools for preliminary design and parameter estimation, but should be used with appropriate engineering judgment and validation.
