"""Test script for optimization"""
import sys
import os
sys.path.insert(0, os.path.abspath('.'))

import pandas as pd
from app.services.optimization_service import OptimizationService
from app.utils.file_parser import parse_pv_production_csv, parse_pricing_csv


def test_optimization_small():
    """Test optimization with small dataset (24 hours)"""
    print("=" * 60)
    print("Testing Solar + Storage Optimization (Small Dataset)")
    print("=" * 60)
    
    # Test parameters
    test_params = {
        "pv_capex_per_mw": 1000000,  # $1M per MW
        "bess_capex_per_mwh": 300000,  # $300k per MWh
        "discount_rate": 0.08,  # 8%
        "interconnection_capacity_mw": 50,  # 50 MW
        "onsite_load_price_per_mwh": 50,  # $50/MWh
        "onsite_load_max_mw": 10,  # 10 MW
        "yoy_price_escalation_rate": 0.02,  # 2% per year
        "pv_max_size_mw": 100,  # 100 MW max
        "bess_max_size_mwh": 200,  # 200 MWh max
    }
    
    print("\nTest Parameters:")
    for key, value in test_params.items():
        print(f"  {key}: {value}")
    
    # Load test data
    print("\nLoading test data...")
    try:
        with open("test_data/pv_production_test_24h.csv", "rb") as f:
            pv_content = f.read()
        with open("test_data/pricing_test_24h.csv", "rb") as f:
            pricing_content = f.read()
        
        pv_series = parse_pv_production_csv(pv_content)
        price_series = parse_pricing_csv(pricing_content)
        
        print(f"  PV production profile: {len(pv_series)} hours")
        print(f"  Pricing profile: {len(price_series)} hours")
        print(f"  PV production range: {pv_series.min():.3f} - {pv_series.max():.3f} MWh/MW")
        print(f"  Pricing range: ${price_series.min():.2f} - ${price_series.max():.2f}/MWh")
        
    except FileNotFoundError as e:
        print(f"ERROR: Test data files not found. Please run generate_test_data.py first.")
        print(f"  Error: {e}")
        return False
    except Exception as e:
        print(f"ERROR: Failed to load test data: {e}")
        return False
    
    # Create optimization service
    print("\nCreating optimization service...")
    service = OptimizationService()
    
    # Progress callback
    def progress_callback(progress, message):
        print(f"  Progress: {progress}% - {message}")
    
    # Run optimization
    print("\nRunning optimization...")
    try:
        results = service.optimize(
            pv_production=pv_series,
            pricing=price_series,
            progress_callback=progress_callback,
            **test_params
        )
        
        print("\n" + "=" * 60)
        print("Optimization Results:")
        print("=" * 60)
        print(f"  Optimal PV Size: {results['optimal_pv_size_mw']:.2f} MW")
        print(f"  Optimal BESS Size: {results['optimal_bess_size_mwh']:.2f} MWh")
        print(f"  NPV: ${results['npv']:,.2f}")
        print(f"  IRR: {results['irr']*100:.2f}%" if results['irr'] else "  IRR: N/A")
        print(f"  Total CAPEX: ${results['capex_total']:,.2f}")
        print(f"  Total Revenue (25 years): ${results['total_revenue_25_years']:,.2f}")
        print(f"  Status: {results['status']}")
        
        print("\n" + "=" * 60)
        print("Test completed successfully!")
        print("=" * 60)
        return True
        
    except Exception as e:
        print(f"\nERROR: Optimization failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_optimization_small()
    sys.exit(0 if success else 1)
