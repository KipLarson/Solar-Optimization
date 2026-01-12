"""Test optimization with 52 representative days"""
import sys
import os
import time
import logging
from pathlib import Path

sys.path.insert(0, os.path.abspath('.'))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s - %(name)s - %(message)s'
)

from app.services.optimization_service import OptimizationService
from app.utils.file_parser import parse_pv_production_csv, parse_pricing_csv

TEST_DATA_DIR = Path(__file__).parent / "test_data"


def test_52_days():
    """Test optimization with 52 representative days"""
    print("="*60)
    print("Testing Optimization with 52 Representative Days")
    print("="*60)
    
    # Load full-year test data
    pv_file = TEST_DATA_DIR / "pv_production_8760h.csv"
    pricing_file = TEST_DATA_DIR / "pricing_8760h.csv"
    
    if not pv_file.exists() or not pricing_file.exists():
        print(f"\nFull-year test data not found.")
        print(f"Generating test data...")
        import subprocess
        try:
            subprocess.run(
                [sys.executable, "test_data/generate_full_year_data.py"],
                check=True,
                cwd=Path(__file__).parent
            )
        except Exception as e:
            print(f"Error generating data: {e}")
            return False
    
    print("\nLoading full-year test data (8760 hours)...")
    with open(pv_file, "rb") as f:
        pv_content = f.read()
    with open(pricing_file, "rb") as f:
        pricing_content = f.read()
    
    pv_series = parse_pv_production_csv(pv_content)
    price_series = parse_pricing_csv(pricing_content)
    
    print(f"  PV production: {len(pv_series)} hours")
    print(f"  Pricing: {len(price_series)} hours")
    
    # Test parameters
    test_params = {
        "pv_capex_per_mw": 1000000,
        "bess_capex_per_mwh": 300000,
        "discount_rate": 0.08,
        "interconnection_capacity_mw": 100,
        "onsite_load_price_per_mwh": 50,
        "onsite_load_max_mw": 20,
        "yoy_price_escalation_rate": 0.02,
        "pv_max_size_mw": None,
        "bess_max_size_mwh": None,
        "use_representative_days": True,  # Use representative days
    }
    
    print("\nTest Parameters:")
    for key, value in test_params.items():
        if isinstance(value, (int, float)) and value > 1000:
            print(f"  {key}: ${value:,}")
        else:
            print(f"  {key}: {value}")
    
    print("\n" + "="*60)
    print("Running Optimization with 52 Representative Days...")
    print("="*60)
    print("(52 days × 24 hours = 1,248 hours instead of 8760)")
    
    service = OptimizationService()
    
    start_time = time.time()
    
    try:
        results = service.optimize(
            pv_production=pv_series,
            pricing=price_series,
            **test_params
        )
        
        total_time = time.time() - start_time
        
        print("\n" + "="*60)
        print("Performance Results")
        print("="*60)
        print(f"\nTotal Execution Time: {total_time:.2f} seconds ({total_time/60:.2f} minutes)")
        
        print("\n" + "="*60)
        print("Optimization Results (Scaled to Full Year)")
        print("="*60)
        print(f"  Optimal PV Size: {results.get('optimal_pv_size_mw', 0):.2f} MW")
        print(f"  Optimal BESS Size: {results.get('optimal_bess_size_mwh', 0):.2f} MWh")
        print(f"  NPV: ${results.get('npv', 0):,.2f}")
        if results.get('irr'):
            print(f"  IRR: {results.get('irr', 0)*100:.2f}%")
        else:
            print(f"  IRR: N/A")
        print(f"  Total CAPEX: ${results.get('capex_total', 0):,.2f}")
        print(f"  Total Revenue (25 years): ${results.get('total_revenue_25_years', 0):,.2f}")
        
        if results.get('representative_days_used'):
            print(f"\n  Scale Factor: {results.get('scale_factor', 1):.2f}x")
            print(f"  Representative Days: 52 days (1,248 hours)")
        
        if 'simultaneous_charge_discharge_hours' in results:
            count = results['simultaneous_charge_discharge_hours']
            total_hours_optimized = 52 * 24  # 1,248 hours
            percentage = (count / total_hours_optimized) * 100
            print(f"\n  Simultaneous Charge/Discharge:")
            print(f"    {count}/{total_hours_optimized} hours ({percentage:.2f}%)")
        else:
            print(f"\n  Simultaneous Charge/Discharge: Not available in results")
        
        print("\n" + "="*60)
        print("✓ Test completed successfully!")
        print("="*60)
        return True
        
    except Exception as e:
        print(f"\n✗ Optimization failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_52_days()
    sys.exit(0 if success else 1)
