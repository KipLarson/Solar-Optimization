"""Modular Photovoltaic (PV) System model"""
from typing import Optional


class PVSystemModel:
    """
    Modular PV system model interface.
    
    Currently assumes no degradation.
    Can be extended with:
    - Annual degradation rate
    - Temperature effects
    - Soiling losses
    """
    
    def __init__(self, degradation_rate: float = 0.0):
        """
        Initialize PV system model.
        
        Args:
            degradation_rate: Annual degradation rate (0-1). Default 0.0 (no degradation).
        """
        self.degradation_rate = degradation_rate
    
    def get_production(self, capacity_mw: float, production_profile_mwh_per_mw: float, year: int = 1) -> float:
        """
        Get PV production for given capacity and hour.
        
        Args:
            capacity_mw: Installed PV capacity in MW
            production_profile_mwh_per_mw: Production per MW for the hour (from CSV)
            year: Year in service (for degradation)
            
        Returns:
            Production in MWh
        """
        # Apply degradation
        effective_capacity = self.apply_degradation(capacity_mw, year)
        production = effective_capacity * production_profile_mwh_per_mw
        
        return production
    
    def apply_degradation(self, capacity_mw: float, year: int) -> float:
        """
        Apply capacity degradation over time.
        
        Args:
            capacity_mw: Original capacity in MW
            year: Year in service (1-based)
            
        Returns:
            Degraded capacity in MW. Currently no degradation (returns original) for idealized model.
        """
        if self.degradation_rate == 0.0:
            return capacity_mw
        
        # Apply annual degradation: capacity * (1 - degradation_rate)^(years - 1)
        effective_capacity = capacity_mw * ((1 - self.degradation_rate) ** (year - 1))
        return effective_capacity
    
    def get_annual_degradation_factor(self, year: int) -> float:
        """
        Get annual degradation factor (multiplier for production).
        
        Args:
            year: Year in service (1-based)
            
        Returns:
            Degradation factor (0-1). Currently 1.0 (no degradation) for idealized model.
        """
        if self.degradation_rate == 0.0:
            return 1.0
        
        return (1 - self.degradation_rate) ** (year - 1)
