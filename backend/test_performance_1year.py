"""Performance test for 1-year optimization"""
import sys
import os
import time
from pathlib import Path

sys.path.insert(0, os.path.abspath('.'))

from app.services.optimization_service import OptimizationService
from app.utils.file_parser import parse_pv_production_csv, parse_pricing_csv

TEST_DATA_DIR = Path(__file__).parent / "test_data"


def test_1year_performance():
    """Test optimization performance for 1 year (8760 hours)"""
    print("="*60)
    print("1-Year Optimization Performance Test")
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
            return
    
    print("\nLoading test data (8760 hours)...")
    with open(pv_file, "rb") as f:
        pv_content = f.read()
    with open(pricing_file, "rb") as f:
        pricing_content = f.read()
    
    pv_series = parse_pv_production_csv(pv_content)
    price_series = parse_pricing_csv(pricing_content)
    
    print(f"  PV production: {len(pv_series)} hours")
    print(f"  Pricing: {len(price_series)} hours")
    
    # Test parameters (realistic for production)
    test_params = {
        "pv_capex_per_mw": 1000000,  # $1M per MW
        "bess_capex_per_mwh": 300000,  # $300k per MWh
        "discount_rate": 0.08,
        "interconnection_capacity_mw": 100,
        "onsite_load_price_per_mwh": 50,
        "onsite_load_max_mw": 20,
        "yoy_price_escalation_rate": 0.02,
        "pv_max_size_mw": None,
        "bess_max_size_mwh": None,
    }
    
    print("\nTest Parameters:")
    for key, value in test_params.items():
        if isinstance(value, (int, float)) and value > 1000:
            print(f"  {key}: ${value:,}")
        else:
            print(f"  {key}: {value}")
    
    # Create optimization service
    print("\nCreating optimization service...")
    service = OptimizationService()
    
    # Track progress
    progress_updates = []
    def progress_callback(progress, message):
        progress_updates.append((progress, message, time.time()))
        if progress % 25 == 0:  # Print at 25% intervals
            print(f"  {progress}% - {message}")
    
    # Run optimization and measure time
    print("\n" + "="*60)
    print("Running Optimization...")
    print("="*60)
    
    start_time = time.time()
    
    try:
        results = service.optimize(
            pv_production=pv_series,
            pricing=price_series,
            progress_callback=progress_callback,
            **test_params
        )
        
        total_time = time.time() - start_time
        
        # Calculate time by phase (roughly)
        phase_times = {}
        if progress_updates:
            initial_time = start_time
            for progress, message, timestamp in progress_updates:
                if progress == 10:
                    phase_times['building'] = timestamp - initial_time
                elif progress == 30:
                    phase_times['solving'] = timestamp - phase_times.get('building', timestamp)
                elif progress == 70:
                    phase_times['processing'] = timestamp - phase_times.get('solving', timestamp)
        
        # Display results
        print("\n" + "="*60)
        print("Performance Results")
        print("="*60)
        print(f"\nTotal Execution Time: {total_time:.2f} seconds ({total_time/60:.2f} minutes)")
        
        if phase_times:
            print("\nApproximate Time by Phase:")
            if 'building' in phase_times:
                print(f"  Model Building: ~{phase_times['building']:.2f} seconds")
            if 'solving' in phase_times:
                print(f"  Optimization Solving: ~{phase_times['solving']:.2f} seconds")
            if 'processing' in phase_times:
                print(f"  Results Processing: ~{phase_times['processing']:.2f} seconds")
        
        print("\n" + "="*60)
        print("Optimization Results")
        print("="*60)
        print(f"  Optimal PV Size: {results.get('optimal_pv_size_mw', 0):.2f} MW")
        print(f"  Optimal BESS Size: {results.get('optimal_bess_size_mwh', 0):.2f} MWh")
        print(f"  NPV: ${results.get('npv', 0):,.2f}")
        if results.get('irr'):
            print(f"  IRR: {results.get('irr', 0)*100:.2f}%")
        else:
            print(f"  IRR: N/A")
        print(f"  Total CAPEX: ${results.get('capex_total', 0):,.2f}")
        
        print("\n" + "="*60)
        print("Performance Summary")
        print("="*60)
        print(f"\n1-Year Optimization (8760 hours):")
        print(f"  Execution Time: {total_time:.2f} seconds ({total_time/60:.2f} minutes)")
        print(f"  Status: {'✓ Success' if results.get('status') == 'completed' else '✗ Failed'}")
        
        print("\n" + "="*60)
        return True
        
    except Exception as e:
        total_time = time.time() - start_time
        print(f"\n✗ Optimization failed after {total_time:.2f} seconds")
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_1year_performance()
    sys.exit(0 if success else 1)
