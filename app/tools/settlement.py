"""Settlement calculation tool."""

import asyncio
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field, validator
from app.core.config import get_settings
from app.core.logging import get_logger
from app.core.metrics import get_metrics_collector

settings = get_settings()
logger = get_logger()


class SettlementInput(BaseModel):
    """Input parameters for settlement calculation."""
    load: float = Field(..., gt=0, description="Applied load (kN or similar units)")
    young_modulus: float = Field(..., gt=0, description="Young's modulus (kPa or similar units)")
    
    @validator('load')
    def validate_load(cls, v):
        """Validate load is positive and reasonable."""
        if v <= 0:
            raise ValueError("Load must be positive")
        if v > 1e6:  # Reasonable upper limit (1,000,000 kN)
            raise ValueError("Load value seems unreasonably large (>1,000,000 kN)")
        if v < 0.1:  # Very small loads might indicate unit issues
            raise ValueError("Load value seems unreasonably small (<0.1 kN)")
        return v
    
    @validator('young_modulus')
    def validate_young_modulus(cls, v):
        """Validate Young's modulus is positive and reasonable."""
        if v <= 0:
            raise ValueError("Young's modulus must be positive")
        if v > 1e9:  # Reasonable upper limit for soil/rock (1,000,000,000 kPa)
            raise ValueError("Young's modulus value seems unreasonably large (>1,000,000,000 kPa)")
        if v < 100:  # Very low modulus might indicate unit issues
            raise ValueError("Young's modulus value seems unreasonably small (<100 kPa)")
        return v


class SettlementResult(BaseModel):
    """Result of settlement calculation."""
    settlement: float = Field(..., description="Calculated settlement")
    units: str = Field(default="mm", description="Units of settlement")
    inputs: Dict[str, float] = Field(..., description="Input parameters used")
    formula: str = Field(default="settlement = load / Young's modulus", description="Formula used")
    steps: list = Field(default_factory=list, description="Calculation steps")


class SettlementCalculator:
    """Settlement calculator tool."""
    
    def __init__(self, trace_id: Optional[str] = None):
        self.trace_id = trace_id
        self.timeout = getattr(settings, 'settlement_timeout_seconds', 30)  # Default 30 seconds
    
    def calculate(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate settlement using simplified formula: settlement = load / Young's modulus.
        
        Args:
            params: Dictionary containing 'load' and 'E' (Young's modulus)
            
        Returns:
            Dictionary with calculation results
        """
        # Extract parameters
        load = params.get('load')
        young_modulus = params.get('E')  # E is the parameter name used in compute.py
        
        if load is None or young_modulus is None:
            raise ValueError(f"Missing required parameters: load={load}, E={young_modulus}")
        
        try:
            load = float(load)
            young_modulus = float(young_modulus)
        except (ValueError, TypeError) as e:
            raise ValueError(f"Invalid parameter types: load={load}, E={young_modulus}") from e
        
        return self._calculate_sync(load, young_modulus)
    
    async def calculate_async(self, load: float, young_modulus: float) -> SettlementResult:
        """
        Calculate settlement using simplified formula: settlement = load / Young's modulus.
        
        Note: This is a simplified calculation. In practice, settlement calculations
        would involve more complex factors like foundation geometry, soil layers,
        stress distribution, etc.
        """
        logger.info(
            "Starting settlement calculation",
            trace_id=self.trace_id,
            load=load,
            young_modulus=young_modulus
        )
        
        start_time = asyncio.get_event_loop().time()
        metrics_collector = get_metrics_collector()
        
        try:
            # Validate inputs
            inputs = SettlementInput(load=load, young_modulus=young_modulus)
            
            # Perform calculation with timeout
            settlement = await asyncio.wait_for(
                self._perform_calculation(inputs.load, inputs.young_modulus),
                timeout=self.timeout
            )
            
            # Prepare result
            result = SettlementResult(
                settlement=settlement,
                units="mm",  # Assuming load in kN and E in kPa gives settlement in mm
                inputs={
                    "load": inputs.load,
                    "young_modulus": inputs.young_modulus
                },
                formula="settlement = load / Young's modulus",
                steps=[
                    f"Given: Load = {inputs.load} kN",
                    f"Given: Young's modulus = {inputs.young_modulus} kPa",
                    f"Formula: settlement = load / E",
                    f"Calculation: settlement = {inputs.load} / {inputs.young_modulus}",
                    f"Result: settlement = {settlement:.3f} mm"
                ]
            )
            
            # Calculate duration and update metrics
            duration_ms = (asyncio.get_event_loop().time() - start_time) * 1000
            metrics_collector.increment_tool_calls("settlement", success=True)
            
            logger.timing("Settlement calculation completed", duration_ms,
                         trace_id=self.trace_id, settlement=settlement)
            
            return result
            
        except asyncio.TimeoutError:
            duration_ms = (asyncio.get_event_loop().time() - start_time) * 1000
            metrics_collector.increment_tool_calls("settlement", success=False)
            metrics_collector.increment_error("timeout")
            
            error_msg = f"Settlement calculation timed out after {self.timeout}s"
            logger.error(error_msg, trace_id=self.trace_id, duration_ms=duration_ms)
            raise ValueError(error_msg)
        except Exception as e:
            logger.error(
                "Settlement calculation failed",
                trace_id=self.trace_id,
                error=str(e)
            )
            raise
    
    async def _perform_calculation(self, load: float, young_modulus: float) -> float:
        """Perform the actual settlement calculation."""
        # Simple calculation: settlement = load / Young's modulus
        # In practice, this would be much more complex
        settlement = load / young_modulus
        
        # Simulate some processing time
        await asyncio.sleep(0.01)
        
        return settlement
    
    def _calculate_sync(self, load: float, young_modulus: float) -> Dict[str, Any]:
        """
        Synchronous settlement calculation for use in compute module.
        
        Args:
            load: Applied load (kN)
            young_modulus: Young's modulus (kPa)
            
        Returns:
            Dictionary with calculation results
        """
        logger.info(
            "Starting settlement calculation",
            trace_id=self.trace_id,
            load=load,
            young_modulus=young_modulus
        )
        
        try:
            # Validate inputs
            inputs = SettlementInput(load=load, young_modulus=young_modulus)
            
            # Perform calculation
            settlement = self._perform_calculation_sync(inputs.load, inputs.young_modulus)
            
            # Calculate foundation width for display
            foundation_width = max(1.0, (inputs.load / 100) ** 0.5)
            
            # Prepare result
            result = {
                "settlement": settlement,
                "units": "mm",
                "inputs": {
                    "load": inputs.load,
                    "young_modulus": inputs.young_modulus,
                    "foundation_width": foundation_width
                },
                "formula": "settlement = (load * width) / (E * width) * 1000",
                "steps": [
                    f"Given: Load = {inputs.load} kN",
                    f"Given: Young's modulus = {inputs.young_modulus} kPa",
                    f"Estimated foundation width = {foundation_width:.3f} m",
                    f"Formula: settlement = (load * width) / (E * width) * 1000",
                    f"Calculation: settlement = ({inputs.load} * {foundation_width:.3f}) / ({inputs.young_modulus} * {foundation_width:.3f}) * 1000",
                    f"Result: settlement = {settlement:.3f} mm"
                ]
            }
            
            logger.info(
                "Settlement calculation completed",
                trace_id=self.trace_id,
                settlement=settlement
            )
            
            return result
            
        except Exception as e:
            logger.error(
                "Settlement calculation failed",
                trace_id=self.trace_id,
                error=str(e)
            )
            raise
    
    def _perform_calculation_sync(self, load: float, young_modulus: float) -> float:
        """
        Perform the actual settlement calculation synchronously.
        
        This uses a simplified elastic settlement formula:
        settlement = (load * foundation_width) / (Young's_modulus * foundation_length)
        
        For simplicity, we assume a square foundation with width = sqrt(load/100)
        This is a very simplified approach - real calculations would consider:
        - Foundation geometry and depth
        - Soil layer properties
        - Stress distribution
        - Consolidation effects
        """
        # Simplified foundation width estimation (very rough approximation)
        # In practice, this would be a design parameter
        foundation_width = max(1.0, (load / 100) ** 0.5)  # Minimum 1m width
        
        # Simplified elastic settlement calculation
        # settlement = (load * width) / (E * length) where length = width for square foundation
        settlement = (load * foundation_width) / (young_modulus * foundation_width)
        
        # Convert to mm (assuming load in kN, E in kPa, gives settlement in m)
        settlement_mm = settlement * 1000
        
        return settlement_mm


async def compute_settlement(
    load: float, 
    young_modulus: float, 
    trace_id: Optional[str] = None
) -> SettlementResult:
    """
    Convenience function to compute settlement.
    
    Args:
        load: Applied load (kN)
        young_modulus: Young's modulus (kPa)
        trace_id: Optional trace ID for logging
    
    Returns:
        SettlementResult with calculation details
    """
    calculator = SettlementCalculator(trace_id=trace_id)
    return await calculator.calculate_async(load, young_modulus)
