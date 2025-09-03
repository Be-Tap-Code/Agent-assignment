# CPT Analysis in Settle3

**Source:** Rocscience Settle3 Documentation and CPT Analysis Guidelines

## Overview

Cone Penetration Test (CPT) analysis in Settle3 provides a powerful method for determining soil parameters and settlement predictions directly from in-situ test data. The CPT is one of the most reliable and widely used geotechnical investigation methods for characterizing soil behavior.

## CPT Data Integration

Settle3 allows direct import of CPT data including:
- Cone resistance (qc)
- Sleeve friction (fs)
- Friction ratio (Rf = fs/qc × 100%)
- Pore pressure measurements (u2)

The software automatically processes this data to derive soil parameters such as unit weight, friction angle, and compressibility characteristics using established correlations.

## Soil Classification

CPT data enables automatic soil classification using the Robertson (1990) soil behavior type (SBT) chart. This classification system uses normalized cone resistance (Qt) and friction ratio (Fr) to identify:
- Clean sands to silty sands
- Silt mixtures
- Clay mixtures
- Organic soils

## Settlement Analysis Methods

Settle3 implements several CPT-based settlement calculation methods:

1. **Direct Method**: Uses CPT resistance values directly in settlement calculations
2. **Schmertmann Method**: Applies strain influence factors based on CPT data
3. **Mayne & Poulos Method**: Correlates settlement with cone resistance and stress history

## Parameter Correlations

Key correlations used in Settle3 for CPT analysis include:
- Young's modulus: E = α × qc (where α varies with soil type)
- Friction angle: φ = arctan(0.1 + 0.38 × log(qc/σ'v0))
- Overconsolidation ratio: OCR = k × (qc/σ'v0)^n

## Quality Control

CPT analysis in Settle3 includes quality control features:
- Data filtering and smoothing options
- Identification of anomalous readings
- Statistical analysis of parameter variations
- Comparison with laboratory test results

## Advantages

CPT-based analysis offers several advantages:
- Continuous soil profiling
- Reduced uncertainty compared to discrete sampling
- Real-time data acquisition
- Cost-effective site characterization
- Reliable settlement predictions

The integration of CPT data in Settle3 provides engineers with a robust framework for settlement analysis that combines the reliability of in-situ testing with advanced computational methods.
