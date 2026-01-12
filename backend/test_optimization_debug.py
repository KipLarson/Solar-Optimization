"""Debug test script for optimization"""
import sys
import os
sys.path.insert(0, os.path.abspath('.'))

import pandas as pd
import pulp
from app.optimization.lp_formulation import LPFormulation
from app.utils.file_parser import parse_pv_production_csv, parse_pricing_csv


def test_lp_formulation_directly():
    """Test LP formulation directly with debugging"""
    print("=" * 60)
    print("Testing LP Formulation Directly (Debug Mode)")
    print("=" * 60)
    
    # Load test data
    print("\nLoading test data...")
    with open("test_data/pv_production_test_24h.csv", "rb") as f:
        pv_content = f.read()
    with open("test_data/pricing_test_24h.csv", "rb") as f:
        pricing_content = f.read()
    
    pv_series = parse_pv_production_csv(pv_content)
    price_series = parse_pricing_csv(pricing_content)
    
    print(f"  PV production: {len(pv_series)} hours")
    print(f"  Pricing: {len(price_series)} hours")
    
    # Create LP formulation
    print("\nCreating LP formulation...")
    lp = LPFormulation(
        pv_production=pv_series,
        pricing=price_series,
        pv_capex_per_mw=1000000,
        bess_capex_per_mwh=300000,
        discount_rate=0.08,
        interconnection_capacity_mw=50,
        onsite_load_price_per_mwh=50,
        onsite_load_max_mw=10,
        yoy_price_escalation_rate=0.02,
        pv_max_size_mw=100,
        bess_max_size_mwh=200,
    )
    
    print(f"  Problem dimensions: {lp.num_hours} hours, {lp.num_years} years")
    
    # Build model
    print("\nBuilding LP model...")
    try:
        lp.build_model()
        print(f"  Model built successfully")
        print(f"  Number of variables: {len(lp.variables)}")
        print(f"  Number of constraints: {len(lp.problem.constraints)}")
    except Exception as e:
        print(f"  ERROR building model: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Solve
    print("\nSolving LP problem...")
    try:
        status, solution = lp.solve(solver=pulp.PULP_CBC_CMD(msg=1))  # Enable solver messages
        print(f"  Solver status: {status}")
        print(f"  Solution: {solution}")
        
        if solution:
            print(f"\n  PV Size: {solution.get('pv_size_mw', 'N/A')} MW")
            print(f"  BESS Size: {solution.get('bess_size_mwh', 'N/A')} MWh")
            print(f"  NPV: ${solution.get('npv', 0):,.2f}")
        
        # Check if we can access variables
        if lp.variables and 'pv_size' in lp.variables:
            pv_size_var = lp.variables['pv_size']
            print(f"\n  PV Size variable value: {pulp.value(pv_size_var)}")
        
        return True
        
    except Exception as e:
        print(f"  ERROR solving: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_lp_formulation_directly()
    sys.exit(0 if success else 1)
