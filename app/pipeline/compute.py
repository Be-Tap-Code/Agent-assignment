"""
Compute module for orchestrating calculations.
"""

from typing import Dict, Any, Optional
from app.tools.terzaghi import TerzaghiCalculator
from app.tools.settlement import SettlementCalculator
from app.core.logging import get_logger

logger = get_logger()


class ComputeModule:
    """Orchestrates calculations based on decision parameters."""
    
    def __init__(self):
        self.terzaghi_calc = TerzaghiCalculator()
        self.settlement_calc = SettlementCalculator()
        self.logger = logger
    
    def perform_calculation(self, action: str, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Perform calculations based on action and parameters.
        
        Args:
            action: Action type ("compute" or "both")
            params: Calculation parameters
            
        Returns:
            Calculation results or None if no calculation needed
        """
        if action not in ["compute", "both"]:
            self.logger.simple("⏭️ Skipping calculation", action=action)
            return None
        
        self.logger.simple("🧮 Performing calculation", 
                          action=action,
                          params=params)
        
        # Determine calculation type based on available parameters
        calc_type = self._determine_calculation_type(params)
        
        if calc_type == "terzaghi":
            return self._calculate_terzaghi(params)
        elif calc_type == "settlement":
            return self._calculate_settlement(params)
        else:
            self.logger.warning("⚠️ No suitable calculation found", params=params)
            return None
    
    def _determine_calculation_type(self, params: Dict[str, Any]) -> Optional[str]:
        """Determine which calculation to perform based on parameters."""
        # Check for Terzaghi parameters
        terzaghi_params = ["B", "Df", "gamma", "phi"]
        if any(params.get(p) is not None for p in terzaghi_params):
            return "terzaghi"
        
        # Check for Settlement parameters
        settlement_params = ["load", "E"]
        if any(params.get(p) is not None for p in settlement_params):
            return "settlement"
        
        return None
    
    def _calculate_terzaghi(self, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Perform Terzaghi bearing capacity calculation."""
        try:
            # Extract parameters
            B = params.get("B")
            Df = params.get("Df")
            gamma = params.get("gamma")
            phi = params.get("phi")
            
            if not all([B, Df, gamma, phi]):
                self.logger.warning("⚠️ Missing Terzaghi parameters", 
                                   B=B, Df=Df, gamma=gamma, phi=phi)
                return None
            
            # Perform calculation
            result = self.terzaghi_calc.calculate({
                "B": B,
                "Df": Df,
                "gamma": gamma,
                "phi": phi
            })
            
            self.logger.simple("✅ Terzaghi calculation completed", 
                              result=result.get("result", 0))
            
            return {
                "type": "terzaghi",
                "result": result,
                "parameters": params
            }
            
        except Exception as e:
            self.logger.error("❌ Terzaghi calculation failed", error=str(e))
            return None
    
    def _calculate_settlement(self, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Perform settlement calculation."""
        try:
            # Extract parameters
            load = params.get("load")
            E = params.get("E")
            
            if load is None or E is None:
                self.logger.warning("⚠️ Missing settlement parameters", 
                                   load=load, E=E)
                return None
            
            # Validate parameter types
            try:
                load = float(load)
                E = float(E)
            except (ValueError, TypeError) as e:
                self.logger.error("❌ Invalid settlement parameter types", 
                                 load=load, E=E, error=str(e))
                return None
            
            # Perform calculation
            result = self.settlement_calc.calculate({
                "load": load,
                "E": E
            })
            
            self.logger.simple("✅ Settlement calculation completed", 
                              settlement=result.get("settlement", 0))
            
            return {
                "type": "settlement",
                "result": result,
                "parameters": params
            }
            
        except Exception as e:
            self.logger.error("❌ Settlement calculation failed", 
                             error=str(e), 
                             load=load, 
                             E=E,
                             error_type=type(e).__name__)
            return None