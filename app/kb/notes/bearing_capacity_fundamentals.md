# Bearing Capacity Fundamentals

**Source:** Geotechnical Engineering Principles and Terzaghi's Foundation Theory

## Introduction

Bearing capacity is the maximum load per unit area that a foundation can support without causing shear failure in the supporting soil. Understanding bearing capacity is fundamental to safe and economical foundation design in geotechnical engineering.

## Terzaghi's Bearing Capacity Theory

Karl Terzaghi developed the classical bearing capacity theory in 1943, which remains the foundation for modern bearing capacity analysis. His theory applies to shallow foundations where the depth-to-width ratio is less than or equal to 1.

### General Bearing Capacity Equation

For a strip footing on cohesive-frictional soil:
**q_ult = c × Nc + γ × Df × Nq + 0.5 × γ × B × Nγ**

Where:
- c = soil cohesion
- γ = unit weight of soil
- Df = depth of foundation
- B = width of foundation
- Nc, Nq, Nγ = bearing capacity factors (functions of friction angle φ)

### Cohesionless Soils

For purely cohesionless soils (c = 0), the equation simplifies to:
**q_ult = γ × Df × Nq + 0.5 × γ × B × Nγ**

This is the formula implemented in our calculation tools.

## Bearing Capacity Factors

The bearing capacity factors are dimensionless parameters that depend solely on the internal friction angle (φ):

### Nq Factor
- Represents the contribution of surcharge (overburden pressure)
- Nq = e^(π×tan φ) × tan²(45° + φ/2)
- Increases exponentially with friction angle

### Nγ Factor (N-gamma)
- Represents the contribution of soil weight below foundation level
- More complex expression involving friction angle
- Also increases significantly with φ

### Nc Factor
- Represents cohesion contribution (not used for cohesionless soils)
- Nc = (Nq - 1) × cot φ

## Failure Mechanisms

Terzaghi identified three types of shear failure:

### General Shear Failure
- Occurs in dense soils or heavily overconsolidated clays
- Well-defined failure surface
- Sudden failure with heaving adjacent to foundation

### Local Shear Failure
- Occurs in medium-dense soils
- Partial development of failure zones
- Gradual failure with limited heaving

### Punching Shear Failure
- Occurs in loose soils
- Vertical shear around foundation perimeter
- Compression and densification below foundation

## Factors Affecting Bearing Capacity

### Soil Properties
- Internal friction angle (φ)
- Cohesion (c)
- Unit weight (γ)
- Soil density and compressibility

### Foundation Geometry
- Width (B) and length (L)
- Depth of embedment (Df)
- Shape (strip, square, circular)

### Loading Conditions
- Vertical loads
- Inclined loads
- Eccentric loads
- Combined loading effects

## Safety Factors

Allowable bearing capacity is determined by applying safety factors:
**q_allow = q_ult / FS**

Typical safety factors:
- Dead loads only: FS = 2.5 to 3.0
- Dead + live loads: FS = 2.0 to 2.5
- Including wind/seismic: FS = 1.5 to 2.0

## Modern Developments

While Terzaghi's theory remains fundamental, modern approaches include:
- Meyerhof's shape and depth factors
- Hansen's and Vesic's modifications
- Numerical methods (finite element analysis)
- Probabilistic design approaches

Understanding these fundamentals is essential for proper application of bearing capacity calculations in foundation design.
