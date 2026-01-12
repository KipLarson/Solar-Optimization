"""Test logging output for simultaneous charge/discharge"""
import sys
import os
import logging

sys.path.insert(0, os.path.abspath('.'))

# Configure logging to see the output
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s - %(name)s - %(message)s'
)

from app.services.optimization_service import OptimizationService
from app.utils.file_parser import parse_pv_production_csv, parse_pricing_csv
from pathlib import Path

TEST_DATA_DIR = Path(__file__).parent / "test_data"

def test_logging():
    """Test optimization with logging enabled"""
    print("="*60)
    print("Testing Logging Output for Simultaneous Charge/Discharge")
    print("="*60)
    
    # Load 24-hour test data
    with open(TEST_DATA_DIR / "pv_production_test_24h.csv", "rb") as f:
        pv_content = f.read()
    with open(TEST_DATA_DIR / "pricing_test_24h.csv", "rb") as f:
        pricing_content = f.read()
    
    pv_series = parse_pv_production_csv(pv_content)
    price_series = parse_pricing_csv(pricing_content)
    
    test_params = {
        "pv_capex_per_mw": 10000,  # Low for testing
        "bess_capex_per_mwh": 5000,
        "discount_rate": 0.08,
        "interconnection_capacity_mw": 50,
        "onsite_load_price_per_mwh": 50,
        "onsite_load_max_mw": 10,
        "yoy_price_escalation_rate": 0.02,
        "pv_max_size_mw": 100,
        "bess_max_size_mwh": 200,
    }
    
    print("\nRunning optimization with logging enabled...\n")
    
    service = OptimizationService()
    
    try:
        results = service.optimize(
            pv_production=pv_series,
            pricing=price_series,
            **test_params
        )
        
        print("\n" + "="*60)
        print("Results:")
        print("="*60)
        print(f"  Optimal PV Size: {results.get('optimal_pv_size_mw', 0):.2f} MW")
        print(f"  Optimal BESS Size: {results.get('optimal_bess_size_mwh', 0):.2f} MWh")
        
        if 'simultaneous_charge_discharge_hours' in results:
            count = results['simultaneous_charge_discharge_hours']
            total_hours = len(pv_series)
            print(f"\n  Simultaneous Charge/Discharge:")
            print(f"    {count}/{total_hours} hours ({count/total_hours*100:.1f}%)")
        else:
            print(f"\n  Simultaneous Charge/Discharge: Not available in results")
        
        print("\n" + "="*60)
        return True
        
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_logging()
    sys.exit(0 if success else 1)
