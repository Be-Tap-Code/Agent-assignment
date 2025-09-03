"""
Terzaghi bearing capacity factors tables.
"""

from typing import Dict, Tuple, Optional
import numpy as np


class TerzaghiTables:
    """Terzaghi bearing capacity factors lookup table."""
    
    def __init__(self):
        # Terzaghi bearing capacity factors table
        # Format: phi (degrees) -> (Nc, Nq, Nr)
        self.factors_table = {
            0: (5.7, 1.0, 0.0),
            5: (7.3, 1.6, 0.5),
            10: (9.6, 2.7, 1.2),
            15: (12.9, 4.4, 2.5),
            20: (17.7, 7.4, 5.0),
            25: (25.1, 12.7, 9.7),
            30: (37.2, 22.5, 19.7),
            35: (57.8, 41.4, 42.4),
            40: (95.7, 81.3, 100.4),
        }
    
    def get_factors(self, phi: float) -> Tuple[float, float, float]:
        """
        Get Terzaghi bearing capacity factors for given friction angle.
        
        Args:
            phi: Friction angle in degrees
            
        Returns:
            Tuple of (Nc, Nq, Nr)
        """
        phi = float(phi)
        
        # Check if exact value exists
        if phi in self.factors_table:
            return self.factors_table[phi]
        
        # Find bounding values for interpolation
        phi_values = sorted(self.factors_table.keys())
        
        if phi < phi_values[0]:
            # Extrapolate below minimum
            return self.factors_table[phi_values[0]]
        
        if phi > phi_values[-1]:
            # Extrapolate above maximum
            return self.factors_table[phi_values[-1]]
        
        # Find the two closest values
        for i in range(len(phi_values) - 1):
            if phi_values[i] <= phi <= phi_values[i + 1]:
                phi1, phi2 = phi_values[i], phi_values[i + 1]
                factors1 = self.factors_table[phi1]
                factors2 = self.factors_table[phi2]
                
                # Linear interpolation
                ratio = (phi - phi1) / (phi2 - phi1)
                Nc = factors1[0] + ratio * (factors2[0] - factors1[0])
                Nq = factors1[1] + ratio * (factors2[1] - factors1[1])
                Nr = factors1[2] + ratio * (factors2[2] - factors1[2])
                
                return (Nc, Nq, Nr)
        
        # Fallback
        return self.factors_table[phi_values[0]]
    
    def get_table_range(self) -> Tuple[float, float]:
        """Get the range of phi values in the table."""
        phi_values = list(self.factors_table.keys())
        return (min(phi_values), max(phi_values))
    
    def is_valid_phi(self, phi: float) -> bool:
        """Check if phi value is within table range."""
        min_phi, max_phi = self.get_table_range()
        return min_phi <= phi <= max_phi


# Global instance
terzaghi_tables = TerzaghiTables()
