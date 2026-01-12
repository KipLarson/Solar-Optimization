"""Optimization service - orchestrates the optimization process"""
from typing import Dict, Any, List
import pandas as pd
from app.optimization.lp_formulation import LPFormulation
from app.models.financial import FinancialModel
from app.models.battery import BatteryModel
from app.models.pv_system import PVSystemModel


class OptimizationService:
    """
    Service to orchestrate the optimization process.
    
    Coordinates:
    - LP formulation
    - Solver execution
    - Results processing
    - Financial calculations (IRR, cash flows)
    """
    
    def __init__(self):
        """Initialize optimization service"""
        self.financial_model = FinancialModel()
        self.battery_model = BatteryModel()
        self.pv_model = PVSystemModel()
    
    def optimize(
        self,
        pv_production: pd.Series,
        pricing: pd.Series,
        pv_capex_per_mw: float,
        bess_capex_per_mwh: float,
        discount_rate: float,
        interconnection_capacity_mw: float,
        onsite_load_price_per_mwh: float,
        onsite_load_max_mw: float,
        yoy_price_escalation_rate: float,
        pv_max_size_mw: float = None,
        bess_max_size_mwh: float = None,
        progress_callback=None,
    ) -> Dict[str, Any]:
        """
        Run optimization and return results.
        
        Args:
            pv_production: PV production profile (8760 hours)
            pricing: Grid pricing profile (8760 hours)
            pv_capex_per_mw: PV CAPEX per MW
            bess_capex_per_mwh: BESS CAPEX per MWh
            discount_rate: Discount rate
            interconnection_capacity_mw: Max interconnection capacity
            onsite_load_price_per_mwh: On-site load price
            onsite_load_max_mw: Max on-site load size
            yoy_price_escalation_rate: Year-over-year price escalation
            pv_max_size_mw: Optional max PV size
            bess_max_size_mwh: Optional max BESS size
            progress_callback: Optional callback function(progress, message)
            
        Returns:
            Dictionary with optimization results
        """
        if progress_callback:
            progress_callback(10, "Building optimization model...")
        
        # Build LP formulation
        lp_formulation = LPFormulation(
            pv_production=pv_production,
            pricing=pricing,
            pv_capex_per_mw=pv_capex_per_mw,
            bess_capex_per_mwh=bess_capex_per_mwh,
            discount_rate=discount_rate,
            interconnection_capacity_mw=interconnection_capacity_mw,
            onsite_load_price_per_mwh=onsite_load_price_per_mwh,
            onsite_load_max_mw=onsite_load_max_mw,
            yoy_price_escalation_rate=yoy_price_escalation_rate,
            pv_max_size_mw=pv_max_size_mw,
            bess_max_size_mwh=bess_max_size_mwh,
            battery_model=self.battery_model,
            pv_model=self.pv_model,
        )
        
        if progress_callback:
            progress_callback(30, "Solving optimization problem...")
        
        # Solve
        status, solution = lp_formulation.solve()
        
        if status != 'Optimal' or solution is None:
            raise ValueError(f"Optimization failed with status: {status}")
        
        if progress_callback:
            progress_callback(70, "Calculating financial metrics...")
        
        # Extract cash flows and calculate IRR
        results = self._process_results(
            solution,
            lp_formulation,
            pv_capex_per_mw,
            bess_capex_per_mwh,
            discount_rate,
            yoy_price_escalation_rate,
            onsite_load_price_per_mwh,
        )
        
        if progress_callback:
            progress_callback(100, "Optimization complete!")
        
        return results
    
    def _process_results(
        self,
        solution: Dict[str, Any],
        lp_formulation: LPFormulation,
        pv_capex_per_mw: float,
        bess_capex_per_mwh: float,
        discount_rate: float,
        yoy_price_escalation_rate: float,
        onsite_load_price_per_mwh: float,
    ) -> Dict[str, Any]:
        """
        Process optimization results and calculate financial metrics.
        
        This is a simplified version that extracts basic results.
        Full implementation would extract hourly flows and calculate monthly revenues.
        """
        pv_size = solution['pv_size_mw']
        bess_size = solution['bess_size_mwh']
        npv = solution['npv']
        
        # Calculate CAPEX
        capex_total = pv_size * pv_capex_per_mw + bess_size * bess_capex_per_mwh
        
        # Calculate cash flows (simplified - would need to extract from solution)
        # For now, calculate annual revenue approximation
        cash_flows = [-capex_total]  # Year 0: negative CAPEX
        
        # TODO: Extract actual annual revenues from solution
        # For now, use a placeholder that maintains NPV
        # This will be replaced with actual revenue extraction
        annual_revenue = (npv + capex_total) / lp_formulation.num_years  # Approximation
        for _ in range(lp_formulation.num_years):
            cash_flows.append(annual_revenue)
        
        # Calculate IRR
        irr = self.financial_model.calculate_irr(cash_flows)
        
        # TODO: Calculate monthly revenues from solution
        # For now, create placeholder monthly revenues
        monthly_revenues = []
        for year in range(1, lp_formulation.num_years + 1):
            for month in range(1, 13):
                monthly_revenues.append({
                    'year': year,
                    'month': month,
                    'revenue': annual_revenue / 12  # Approximation
                })
        
        # Calculate total revenue over 25 years
        total_revenue = sum(cash_flows[1:])  # Sum of all positive cash flows
        
        return {
            'optimal_pv_size_mw': pv_size,
            'optimal_bess_size_mwh': bess_size,
            'npv': npv,
            'irr': irr if irr else 0.0,
            'capex_total': capex_total,
            'monthly_revenues': monthly_revenues,
            'total_revenue_25_years': total_revenue,
            'status': 'completed'
        }
