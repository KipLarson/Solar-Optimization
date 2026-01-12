"""Optimization service - orchestrates the optimization process"""
from typing import Dict, Any, List
import pandas as pd
import logging
from app.optimization.lp_formulation import LPFormulation
from app.models.financial import FinancialModel
from app.models.battery import BatteryModel
from app.models.pv_system import PVSystemModel
from app.utils.representative_days import select_representative_days, scale_results_to_full_year

logger = logging.getLogger(__name__)


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
        use_representative_days: bool = True,
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
        # Select representative days if using full-year data
        scale_factor = 1.0
        optimization_pv = pv_production
        optimization_pricing = pricing
        
        if use_representative_days and len(pv_production) == 8760:
            if progress_callback:
                progress_callback(5, "Selecting representative days...")
            
            # Default to 52 days (one per week) for better accuracy
            num_representative_days = 52
            logger.info(f"Using representative days: {num_representative_days} days = {num_representative_days * 24} hours")
            optimization_pv, optimization_pricing, scale_factor = select_representative_days(
                pv_production, pricing, num_days=num_representative_days
            )
            logger.info(f"Selected {len(optimization_pv)} hours from representative days")
            logger.info(f"Scale factor for full year: {scale_factor:.2f}")
        elif len(pv_production) != 8760:
            # For non-full-year data (e.g., 24-hour test), don't use representative days
            logger.info(f"Using {len(pv_production)} hours directly (not full year)")
        
        if progress_callback:
            progress_callback(10, "Building optimization model...")
        
        # Build LP formulation with representative days (or original data)
        lp_formulation = LPFormulation(
            pv_production=optimization_pv,
            pricing=optimization_pricing,
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
        
        # Log simultaneous charge/discharge count if available
        if 'simultaneous_charge_discharge_hours' in solution:
            simultaneous_count = solution['simultaneous_charge_discharge_hours']
            total_hours = lp_formulation.num_hours * lp_formulation.num_years
            logger.info(f"Optimization complete: {simultaneous_count}/{total_hours} hours with simultaneous charge/discharge")
            
            if simultaneous_count > 0:
                percentage = (simultaneous_count / total_hours) * 100
                logger.warning(f"Warning: {percentage:.2f}% of hours show simultaneous charge/discharge "
                             f"(model allows this for performance reasons)")
        
        if progress_callback:
            progress_callback(70, "Calculating 25-year financial metrics...")
        
        # Extract annual revenue from 1-year optimization
        # First, get the unscaled annual revenue from the solution
        npv_1yr_unscaled = solution['npv']
        pv_size = solution['pv_size_mw']
        bess_size = solution['bess_size_mwh']
        capex_total = pv_size * pv_capex_per_mw + bess_size * bess_capex_per_mwh
        
        # Annual revenue from 1-year optimization (unscaled)
        # NPV = -CAPEX + discounted_revenue, so revenue = NPV + CAPEX
        annual_revenue_year1_unscaled = npv_1yr_unscaled + capex_total
        
        # Scale to full year if using representative days
        if scale_factor > 1.0:
            annual_revenue_year1 = annual_revenue_year1_unscaled * scale_factor
            logger.info(f"Scaled annual revenue by factor {scale_factor:.2f} to represent full year")
        else:
            annual_revenue_year1 = annual_revenue_year1_unscaled
        
        # Calculate 25-year cash flows and financial metrics
        results = self._process_results_25yr(
            solution,
            lp_formulation,
            pv_capex_per_mw,
            bess_capex_per_mwh,
            discount_rate,
            yoy_price_escalation_rate,
            annual_revenue_year1,
        )
        
        # Add metadata
        if scale_factor > 1.0:
            results['scale_factor'] = scale_factor
            results['representative_days_used'] = True
        
        if progress_callback:
            progress_callback(100, "Optimization complete!")
        
        return results
    
    def _process_results_25yr(
        self,
        solution: Dict[str, Any],
        lp_formulation: LPFormulation,
        pv_capex_per_mw: float,
        bess_capex_per_mwh: float,
        discount_rate: float,
        yoy_price_escalation_rate: float,
        annual_revenue_year1: float,
    ) -> Dict[str, Any]:
        """
        Process optimization results and calculate 25-year financial metrics.
        
        The optimization runs for 1 year (with representative days), then we:
        1. Use the scaled annual revenue from year 1
        2. Calculate 25-year cash flows with price escalation
        3. Calculate NPV and IRR over 25 years
        """
        pv_size = solution['pv_size_mw']
        bess_size = solution['bess_size_mwh']
        
        # Calculate CAPEX (one-time cost in year 0)
        capex_total = pv_size * pv_capex_per_mw + bess_size * bess_capex_per_mwh
        
        # Calculate 25-year cash flows with price escalation
        cash_flows_25yr = [-capex_total]  # Year 0: negative CAPEX
        
        # Years 1-25: annual revenue with price escalation
        total_revenue_25_years = 0.0
        for year in range(1, 26):
            # Apply price escalation: revenue increases by (1 + escalation_rate)^(year-1)
            price_escalation_factor = (1 + yoy_price_escalation_rate) ** (year - 1)
            annual_revenue = annual_revenue_year1 * price_escalation_factor
            cash_flows_25yr.append(annual_revenue)
            total_revenue_25_years += annual_revenue
        
        # Calculate NPV over 25 years
        npv_25yr = self.financial_model.calculate_npv(cash_flows_25yr, discount_rate)
        
        # Calculate IRR over 25 years
        irr_25yr = self.financial_model.calculate_irr(cash_flows_25yr)
        
        # Calculate monthly revenues for all 25 years
        monthly_revenues = []
        for year in range(1, 26):
            price_escalation_factor = (1 + yoy_price_escalation_rate) ** (year - 1)
            annual_revenue = annual_revenue_year1 * price_escalation_factor
            monthly_revenue = annual_revenue / 12
            for month in range(1, 13):
                monthly_revenues.append({
                    'year': year,
                    'month': month,
                    'revenue': monthly_revenue
                })
        
        result_dict = {
            'optimal_pv_size_mw': pv_size,
            'optimal_bess_size_mwh': bess_size,
            'npv': npv_25yr,  # 25-year NPV
            'irr': irr_25yr if irr_25yr else 0.0,  # 25-year IRR
            'capex_total': capex_total,
            'monthly_revenues': monthly_revenues,
            'total_revenue_25_years': total_revenue_25_years,
            'annual_revenue_year1': annual_revenue_year1,  # For reference
            'status': 'completed'
        }
        
        # Add simultaneous charge/discharge count if available in solution
        if 'simultaneous_charge_discharge_hours' in solution:
            result_dict['simultaneous_charge_discharge_hours'] = solution['simultaneous_charge_discharge_hours']
        
        return result_dict
