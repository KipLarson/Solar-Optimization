"""Modular Battery Energy Storage System (BESS) model"""
from typing import Tuple


class BatteryModel:
    """
    Modular battery model interface.
    
    Currently implements idealized battery:
    - 100% round-trip efficiency
    - No limitations on charge/discharge rate
    - No SOC limits (0 to capacity)
    - No degradation
    
    Can be extended with:
    - Round-trip efficiency
    - Charge/discharge rate limits (C-rate)
    - SOC limits (min/max)
    - Degradation over time
    - Self-discharge
    """
    
    def __init__(self):
        """Initialize idealized battery model"""
        pass
    
    def get_round_trip_efficiency(self, year: int = 1) -> float:
        """
        Get round-trip efficiency (energy out / energy in).
        
        Args:
            year: Year in service (for degradation models)
            
        Returns:
            Round-trip efficiency (0-1). Currently 1.0 (100%) for idealized model.
        """
        return 1.0
    
    def get_charge_efficiency(self, year: int = 1) -> float:
        """
        Get charging efficiency.
        
        Args:
            year: Year in service
            
        Returns:
            Charging efficiency (0-1). Currently 1.0 (100%) for idealized model.
        """
        return 1.0
    
    def get_discharge_efficiency(self, year: int = 1) -> float:
        """
        Get discharging efficiency.
        
        Args:
            year: Year in service
            
        Returns:
            Discharging efficiency (0-1). Currently 1.0 (100%) for idealized model.
        """
        return 1.0
    
    def get_max_charge_rate(self, capacity_mwh: float, year: int = 1) -> float:
        """
        Get maximum charge rate in MW.
        
        Args:
            capacity_mwh: Battery capacity in MWh
            year: Year in service
            
        Returns:
            Maximum charge rate in MW. Currently unlimited (return capacity) for idealized model.
        """
        # Idealized: can charge at full capacity in 1 hour (1C rate)
        return capacity_mwh
    
    def get_max_discharge_rate(self, capacity_mwh: float, year: int = 1) -> float:
        """
        Get maximum discharge rate in MW.
        
        Args:
            capacity_mwh: Battery capacity in MWh
            year: Year in service
            
        Returns:
            Maximum discharge rate in MW. Currently unlimited (return capacity) for idealized model.
        """
        # Idealized: can discharge at full capacity in 1 hour (1C rate)
        return capacity_mwh
    
    def get_soc_limits(self, capacity_mwh: float, year: int = 1) -> Tuple[float, float]:
        """
        Get state of charge limits (min, max) in MWh.
        
        Args:
            capacity_mwh: Battery capacity in MWh
            year: Year in service
            
        Returns:
            Tuple of (min_soc_mwh, max_soc_mwh). Currently (0, capacity) for idealized model.
        """
        return (0.0, capacity_mwh)
    
    def apply_degradation(self, capacity_mwh: float, year: int) -> float:
        """
        Apply capacity degradation over time.
        
        Args:
            capacity_mwh: Original capacity in MWh
            year: Year in service
            
        Returns:
            Degraded capacity in MWh. Currently no degradation (returns original) for idealized model.
        """
        return capacity_mwh
    
    def apply_self_discharge(self, soc_mwh: float, hours: float) -> float:
        """
        Apply self-discharge over time.
        
        Args:
            soc_mwh: Current state of charge in MWh
            hours: Number of hours
            
        Returns:
            State of charge after self-discharge. Currently no self-discharge for idealized model.
        """
        return soc_mwh
    
    def calculate_energy_stored(self, energy_in_mwh: float, year: int = 1) -> float:
        """
        Calculate energy stored after charging (accounting for efficiency).
        
        Args:
            energy_in_mwh: Energy input in MWh
            year: Year in service
            
        Returns:
            Energy stored in MWh. Currently returns input (100% efficiency) for idealized model.
        """
        return energy_in_mwh * self.get_charge_efficiency(year)
    
    def calculate_energy_released(self, energy_stored_mwh: float, year: int = 1) -> float:
        """
        Calculate energy released from storage (accounting for efficiency).
        
        Args:
            energy_stored_mwh: Energy stored in MWh
            year: Year in service
            
        Returns:
            Energy released in MWh. Currently returns stored (100% efficiency) for idealized model.
        """
        return energy_stored_mwh * self.get_discharge_efficiency(year)
