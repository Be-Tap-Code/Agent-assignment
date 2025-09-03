"""Terzaghi bearing capacity calculation tool."""

import asyncio
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field, validator
from app.core.config import get_settings
from app.core.logging import get_logger
from app.core.metrics import get_metrics_collector
from app.tools.tables import terzaghi_tables

settings = get_settings()
logger = get_logger()


class TerzaghiInput(BaseModel):
    """Input parameters for Terzaghi bearing capacity calculation."""
    B: float = Field(..., gt=0, description="Foundation width (m)")
    gamma: float = Field(..., gt=0, description="Unit weight of soil (kN/m³)")
    Df: float = Field(..., ge=0, description="Depth of foundation (m)")
    phi: float = Field(..., ge=0, le=50, description="Internal friction angle (degrees)")
    
    @validator('B')
    def validate_width(cls, v):
        """Validate foundation width."""
        if v <= 0:
            raise ValueError("Foundation width must be positive")
        if v > 100:  # Reasonable upper limit
            raise ValueError("Foundation width seems unreasonably large")
        return v
    
    @validator('gamma')
    def validate_unit_weight(cls, v):
        """Validate unit weight."""
        if v <= 0:
            raise ValueError("Unit weight must be positive")
        if v > 30:  # Reasonable upper limit for soil
            raise ValueError("Unit weight seems unreasonably large for soil")
        return v
    
    @validator('Df')
    def validate_depth(cls, v):
        """Validate foundation depth."""
        if v < 0:
            raise ValueError("Foundation depth cannot be negative")
        if v > 50:  # Reasonable upper limit
            raise ValueError("Foundation depth seems unreasonably large")
        return v
    
    @validator('phi')
    def validate_friction_angle(cls, v):
        """Validate friction angle."""
        min_phi, max_phi = terzaghi_tables.get_table_range()
        if v < min_phi or v > max_phi:
            raise ValueError(f"Friction angle must be between {min_phi} and {max_phi} degrees, got {v}")
        return v


class TerzaghiResult(BaseModel):
    """Result of Terzaghi bearing capacity calculation."""
    q_ult: float = Field(..., description="Ultimate bearing capacity (kPa)")
    inputs: Dict[str, float] = Field(..., description="Input parameters used")
    factors: Dict[str, float] = Field(..., description="Bearing capacity factors")
    formula: str = Field(
        default="q_ult = γ*Df*Nq + 0.5*γ*B*Nr",
        description="Formula used"
    )
    steps: list = Field(default_factory=list, description="Calculation steps")
    notes: list = Field(default_factory=list, description="Engineering notes")


class TerzaghiCalculator:
    """Terzaghi bearing capacity calculator for cohesionless soils."""
    
    def __init__(self, trace_id: Optional[str] = None):
        self.trace_id = trace_id
        self.timeout = settings.terzaghi_timeout_seconds
    
    def calculate(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate Terzaghi bearing capacity using simplified formula.
        
        Args:
            params: Dictionary containing 'B', 'Df', 'gamma', 'phi'
            
        Returns:
            Dictionary with calculation results
        """
        # Extract parameters
        B = params.get('B')
        Df = params.get('Df')
        gamma = params.get('gamma')
        phi = params.get('phi')
        
        if B is None or Df is None or gamma is None or phi is None:
            raise ValueError(f"Missing required parameters: B={B}, Df={Df}, gamma={gamma}, phi={phi}")
        
        try:
            B = float(B)
            Df = float(Df)
            gamma = float(gamma)
            phi = float(phi)
        except (ValueError, TypeError) as e:
            raise ValueError(f"Invalid parameter types: B={B}, Df={Df}, gamma={gamma}, phi={phi}") from e
        
        return self._calculate_sync(B, gamma, Df, phi)
    
    async def calculate_async(self, B: float, gamma: float, Df: float, phi: float) -> TerzaghiResult:
        """
        Calculate ultimate bearing capacity using Terzaghi's formula for cohesionless soils.
        
        Formula: q_ult = γ*Df*Nq + 0.5*γ*B*Nr
        
        Where:
        - γ: Unit weight of soil
        - Df: Depth of foundation
        - B: Width of foundation
        - Nq, Nr: Bearing capacity factors (function of φ)
        """
        logger.info(
            "Starting Terzaghi bearing capacity calculation",
            trace_id=self.trace_id,
            B=B, gamma=gamma, Df=Df, phi=phi
        )
        
        start_time = asyncio.get_event_loop().time()
        metrics_collector = get_metrics_collector()
        
        try:
            # Validate inputs
            inputs = TerzaghiInput(B=B, gamma=gamma, Df=Df, phi=phi)
            
            # Perform calculation with timeout
            result = await asyncio.wait_for(
                self._perform_calculation(inputs),
                timeout=self.timeout
            )
            
            # Calculate duration and update metrics
            duration_ms = (asyncio.get_event_loop().time() - start_time) * 1000
            metrics_collector.increment_tool_calls("terzaghi", success=True)
            
            logger.timing("Terzaghi calculation completed", duration_ms,
                         trace_id=self.trace_id, q_ult=result.q_ult)
            
            return result
            
        except asyncio.TimeoutError:
            duration_ms = (asyncio.get_event_loop().time() - start_time) * 1000
            metrics_collector.increment_tool_calls("terzaghi", success=False)
            metrics_collector.increment_error("timeout")
            
            error_msg = f"Terzaghi calculation timed out after {self.timeout}s"
            logger.error(error_msg, trace_id=self.trace_id, duration_ms=duration_ms)
            raise ValueError(error_msg)
        except Exception as e:
            logger.error(
                "Terzaghi calculation failed",
                trace_id=self.trace_id,
                error=str(e)
            )
            raise
    
    async def _perform_calculation(self, inputs: TerzaghiInput) -> TerzaghiResult:
        """Perform the actual Terzaghi bearing capacity calculation."""
        
        # Get bearing capacity factors from lookup table
        Nc, Nq, Nr = terzaghi_tables.get_factors(inputs.phi)

        # Calculate ultimate bearing capacity
        # q_ult = γ*Df*Nq + 0.5*γ*B*Nr
        term1 = inputs.gamma * inputs.Df * Nq
        term2 = 0.5 * inputs.gamma * inputs.B * Nr
        q_ult = term1 + term2
        
        # Simulate some processing time
        await asyncio.sleep(0.01)
        
        # Prepare calculation steps
        steps = [
            f"Given: B = {inputs.B} m (foundation width)",
            f"Given: γ = {inputs.gamma} kN/m³ (unit weight)",
            f"Given: Df = {inputs.Df} m (foundation depth)",
            f"Given: φ = {inputs.phi}° (friction angle)",
            f"Lookup: Nq = {Nq:.2f}, Nr = {Nr:.2f} (from tables)",
            f"Formula: q_ult = γ*Df*Nq + 0.5*γ*B*Nr",
            f"Term 1: γ*Df*Nq = {inputs.gamma} × {inputs.Df} × {Nq:.2f} = {term1:.2f} kPa",
            f"Term 2: 0.5*γ*B*Nr = 0.5 × {inputs.gamma} × {inputs.B} × {Nr:.2f} = {term2:.2f} kPa",
            f"Result: q_ult = {term1:.2f} + {term2:.2f} = {q_ult:.2f} kPa"
        ]
        
        # Engineering notes
        notes = [
            "This calculation uses Terzaghi's bearing capacity formula for cohesionless soils",
            "The formula assumes a strip footing and general shear failure",
            f"Bearing capacity factors taken from lookup table for φ = {inputs.phi}° (with interpolation if needed)",
            "Note: Using Nr notation for the unit weight term",
            "For design purposes, apply appropriate safety factors to the ultimate capacity"
        ]
        
        return TerzaghiResult(
            q_ult=q_ult,
            inputs={
                "B": inputs.B,
                "gamma": inputs.gamma,
                "Df": inputs.Df,
                "phi": inputs.phi
            },
            factors={
                "Nc": Nc,
                "Nq": Nq,
                "Nr": Nr
            },
            steps=steps,
            notes=notes
        )
    
    def _calculate_sync(self, B: float, gamma: float, Df: float, phi: float) -> Dict[str, Any]:
        """
        Synchronous Terzaghi bearing capacity calculation for use in compute module.
        
        Args:
            B: Foundation width (m)
            gamma: Unit weight of soil (kN/m³)
            Df: Foundation depth (m)
            phi: Internal friction angle (degrees)
            
        Returns:
            Dictionary with calculation results
        """
        logger.info(
            "Starting Terzaghi bearing capacity calculation",
            trace_id=self.trace_id,
            B=B, gamma=gamma, Df=Df, phi=phi
        )
        
        try:
            # Validate inputs
            inputs = TerzaghiInput(B=B, gamma=gamma, Df=Df, phi=phi)
            
            # Get bearing capacity factors from lookup table
            Nc, Nq, Nr = terzaghi_tables.get_factors(inputs.phi)

            # Calculate ultimate bearing capacity
            # q_ult = γ*Df*Nq + 0.5*γ*B*Nr
            term1 = inputs.gamma * inputs.Df * Nq
            term2 = 0.5 * inputs.gamma * inputs.B * Nr
            q_ult = term1 + term2
            
            # Prepare calculation steps
            steps = [
                f"Given: B = {inputs.B} m (foundation width)",
                f"Given: γ = {inputs.gamma} kN/m³ (unit weight)",
                f"Given: Df = {inputs.Df} m (foundation depth)",
                f"Given: φ = {inputs.phi}° (friction angle)",
                f"Lookup: Nq = {Nq:.2f}, Nr = {Nr:.2f} (from tables)",
                f"Formula: q_ult = γ*Df*Nq + 0.5*γ*B*Nr",
                f"Term 1: γ*Df*Nq = {inputs.gamma} × {inputs.Df} × {Nq:.2f} = {term1:.2f} kPa",
                f"Term 2: 0.5*γ*B*Nr = 0.5 × {inputs.gamma} × {inputs.B} × {Nr:.2f} = {term2:.2f} kPa",
                f"Result: q_ult = {term1:.2f} + {term2:.2f} = {q_ult:.2f} kPa"
            ]
            
            # Engineering notes
            notes = [
                "This calculation uses Terzaghi's bearing capacity formula for cohesionless soils",
                "The formula assumes a strip footing and general shear failure",
                f"Bearing capacity factors taken from lookup table for φ = {inputs.phi}° (with interpolation if needed)",
                "Note: Using Nr notation for the unit weight term",
                "For design purposes, apply appropriate safety factors to the ultimate capacity"
            ]
            
            # Prepare result
            result = {
                "result": q_ult,
                "inputs": {
                    "B": inputs.B,
                    "gamma": inputs.gamma,
                    "Df": inputs.Df,
                    "phi": inputs.phi
                },
                "factors": {
                    "Nc": Nc,
                    "Nq": Nq,
                    "Nr": Nr
                },
                "formula": "q_ult = γ*Df*Nq + 0.5*γ*B*Nr",
                "steps": steps,
                "notes": notes
            }
            
            logger.info(
                "Terzaghi calculation completed",
                trace_id=self.trace_id,
                q_ult=q_ult
            )
            
            return result
            
        except Exception as e:
            logger.error(
                "Terzaghi calculation failed",
                trace_id=self.trace_id,
                error=str(e)
            )
            raise


async def compute_bearing_capacity(
    B: float, 
    gamma: float, 
    Df: float, 
    phi: float,
    trace_id: Optional[str] = None
) -> TerzaghiResult:
    """
    Convenience function to compute Terzaghi bearing capacity.
    
    Args:
        B: Foundation width (m)
        gamma: Unit weight of soil (kN/m³)
        Df: Foundation depth (m)
        phi: Internal friction angle (degrees)
        trace_id: Optional trace ID for logging
    
    Returns:
        TerzaghiResult with calculation details
    """
    calculator = TerzaghiCalculator(trace_id=trace_id)
    return await calculator.calculate_async(B, gamma, Df, phi)
