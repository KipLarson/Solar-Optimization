"""Utility functions for selecting representative days"""
import pandas as pd
import numpy as np
from typing import Tuple


def select_representative_days(pv_production: pd.Series, pricing: pd.Series, num_days: int = 12) -> Tuple[pd.Series, pd.Series, float]:
    """
    Select representative days evenly spaced throughout the year and scale factor.
    
    Args:
        pv_production: Full-year PV production profile (8760 hours)
        pricing: Full-year pricing profile (8760 hours)
        num_days: Number of representative days to select (default: 12, one per month)
        
    Returns:
        Tuple of (representative_pv, representative_pricing, scale_factor)
        where scale_factor is used to scale results to full year
    """
    if len(pv_production) != 8760:
        raise ValueError(f"Expected 8760 hours, got {len(pv_production)}")
    if len(pricing) != 8760:
        raise ValueError(f"Expected 8760 hours, got {len(pricing)}")
    
    if num_days < 1 or num_days > 365:
        raise ValueError(f"num_days must be between 1 and 365, got {num_days}")
    
    # Select days evenly spaced throughout the year
    # For 52 days: select approximately every 7th day (365/52 ≈ 7.02)
    # For 12 days: select approximately every 30th day (one per month)
    days_per_year = 365
    day_interval = days_per_year / num_days
    
    representative_hours = []
    representative_pv_values = []
    representative_pricing_values = []
    
    for day_idx in range(num_days):
        # Calculate which day of the year to select (0-indexed, then convert to 1-indexed)
        day_of_year = int(day_idx * day_interval + day_interval / 2)  # Midpoint of interval
        day_of_year = min(day_of_year, 364)  # Ensure we don't exceed day 364 (0-indexed)
        
        # Convert day to hour range (day 0 = hours 1-24, day 1 = hours 25-48, etc.)
        start_hour = day_of_year * 24 + 1
        end_hour = start_hour + 24
        
        # Extract 24 hours for this representative day
        for hour in range(start_hour, end_hour):
            if hour <= len(pv_production):
                representative_hours.append(len(representative_hours) + 1)  # Re-index sequentially
                representative_pv_values.append(pv_production[hour])
                representative_pricing_values.append(pricing[hour])
    
    # Create new series with representative days
    representative_pv = pd.Series(
        representative_pv_values,
        index=range(1, len(representative_pv_values) + 1),
        name='Production_MWh_per_MW'
    )
    
    representative_pricing = pd.Series(
        representative_pricing_values,
        index=range(1, len(representative_pricing_values) + 1),
        name='Price_per_MWh'
    )
    
    # Scale factor: full year (365 days) / representative days
    scale_factor = 365.0 / num_days
    
    return representative_pv, representative_pricing, scale_factor


def scale_results_to_full_year(results: dict, scale_factor: float, capex_total: float) -> dict:
    """
    Scale optimization results from representative days to full year.
    
    Args:
        results: Results dictionary from optimization
        scale_factor: Scaling factor (typically 365/12 = 30.42)
        capex_total: Total CAPEX (should NOT be scaled)
        
    Returns:
        Scaled results dictionary
    """
    scaled_results = results.copy()
    
    # NPV scaling: NPV = -CAPEX + scaled_revenues
    # The optimization was done on representative days, so revenues need scaling
    # But CAPEX is a one-time cost, so it doesn't scale
    if 'npv' in scaled_results:
        # Extract revenue component: NPV = revenue - CAPEX
        # So revenue = NPV + CAPEX
        # Scale revenue, then recalculate NPV
        original_npv = scaled_results['npv']
        revenue_component = original_npv + capex_total
        scaled_revenue = revenue_component * scale_factor
        scaled_results['npv'] = scaled_revenue - capex_total
    
    if 'total_revenue_25_years' in scaled_results:
        scaled_results['total_revenue_25_years'] = scaled_results['total_revenue_25_years'] * scale_factor
    
    # Scale monthly revenues
    if 'monthly_revenues' in scaled_results:
        for revenue_entry in scaled_results['monthly_revenues']:
            revenue_entry['revenue'] = revenue_entry['revenue'] * scale_factor
    
    # Note: PV size and BESS size don't scale (they're capacity decisions)
    # Note: IRR calculation should use scaled cash flows
    
    return scaled_results
