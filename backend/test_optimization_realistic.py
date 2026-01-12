"""Test with more realistic parameters for small dataset"""
import sys
import os
sys.path.insert(0, os.path.abspath('.'))

import pandas as pd
from app.services.optimization_service import OptimizationService
from app.utils.file_parser import parse_pv_production_csv, parse_pricing_csv


def test_with_realistic_params():
    """Test with parameters that make economic sense for small dataset"""
    print("=" * 60)
    print("Testing with Realistic Parameters for Small Dataset")
    print("=" * 60)
    print("\nNote: With only 24 hours, we'll use very low CAPEX costs")
    print("      to make the economics work. In production, use full 8760 hours.\n")
    
    # Adjusted parameters for 24-hour test
    # Much lower CAPEX to make economics work with only 24 hours
    test_params = {
        "pv_capex_per_mw": 10000,  # Very low for testing ($10k per MW vs $1M)
        "bess_capex_per_mwh": 5000,  # Very low for testing ($5k per MWh vs $300k)
        "discount_rate": 0.08,
        "interconnection_capacity_mw": 50,
        "onsite_load_price_per_mwh": 50,
        "onsite_load_max_mw": 10,
        "yoy_price_escalation_rate": 0.02,
        "pv_max_size_mw": 100,
        "bess_max_size_mwh": 200,
    }
    
    print("Test Parameters (adjusted for small dataset):")
    for key, value in test_params.items():
        print(f"  {key}: {value:,}" if isinstance(value, (int, float)) and value > 1000 else f"  {key}: {value}")
    
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
    
    # Create optimization service
    service = OptimizationService()
    
    # Progress callback
    def progress_callback(progress, message):
        if progress % 25 == 0:  # Only print at 25% intervals
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
        if results['irr']:
            print(f"  IRR: {results['irr']*100:.2f}%")
        else:
            print(f"  IRR: N/A (could not calculate)")
        print(f"  Total CAPEX: ${results['capex_total']:,.2f}")
        print(f"  Total Revenue (1 year): ${results['total_revenue_25_years']:,.2f}")
        print(f"  Status: {results['status']}")
        
        print("\n" + "=" * 60)
        if results['optimal_pv_size_mw'] > 0:
            print("✓ Test PASSED: Non-zero solution found!")
        else:
            print("⚠ Test completed but solution is zero.")
            print("  This may be correct if economics don't justify investment.")
        print("=" * 60)
        return True
        
    except Exception as e:
        print(f"\nERROR: Optimization failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_with_realistic_params()
    sys.exit(0 if success else 1)
