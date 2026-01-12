"""Performance test for optimization - measure execution time for different time horizons"""
import sys
import os
import time
import pandas as pd
from pathlib import Path

sys.path.insert(0, os.path.abspath('.'))

from app.services.optimization_service import OptimizationService
from app.utils.file_parser import parse_pv_production_csv, parse_pricing_csv
from app.optimization.lp_formulation import LPFormulation

TEST_DATA_DIR = Path(__file__).parent / "test_data"


def load_test_data(hours=8760):
    """Load test data (full year or 24-hour sample)"""
    if hours == 8760:
        pv_file = TEST_DATA_DIR / "pv_production_8760h.csv"
        pricing_file = TEST_DATA_DIR / "pricing_8760h.csv"
    else:
        pv_file = TEST_DATA_DIR / "pv_production_test_24h.csv"
        pricing_file = TEST_DATA_DIR / "pricing_test_24h.csv"
    
    if not pv_file.exists() or not pricing_file.exists():
        raise FileNotFoundError(f"Test data files not found. Please generate them first.")
    
    with open(pv_file, "rb") as f:
        pv_content = f.read()
    with open(pricing_file, "rb") as f:
        pricing_content = f.read()
    
    pv_series = parse_pv_production_csv(pv_content)
    price_series = parse_pricing_csv(pricing_content)
    
    return pv_series, price_series


def test_optimization_performance(num_years=1, hours_per_year=8760, verbose=True):
    """
    Test optimization performance for given number of years.
    
    Note: The current LP formulation uses num_years=1 internally,
    but we can measure time for building and solving the model.
    """
    if verbose:
        print(f"\n{'='*60}")
        print(f"Performance Test: {num_years} year(s), {hours_per_year} hours/year")
        print(f"{'='*60}")
    
    # Load test data
    if verbose:
        print("Loading test data...")
    pv_series, price_series = load_test_data(hours_per_year)
    
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
    
    # Measure model building time
    if verbose:
        print("Building LP model...")
    start_build = time.time()
    
    try:
        lp = LPFormulation(
            pv_production=pv_series,
            pricing=price_series,
            **test_params
        )
        lp.build_model()
        build_time = time.time() - start_build
        
        if verbose:
            print(f"  Model built in {build_time:.2f} seconds")
            print(f"  Variables: {len(lp.variables)}")
            print(f"  Constraints: {len(lp.problem.constraints)}")
        
        # Measure solving time
        if verbose:
            print("Solving optimization problem...")
        start_solve = time.time()
        
        status, solution = lp.solve()
        solve_time = time.time() - start_solve
        
        total_time = build_time + solve_time
        
        if verbose:
            print(f"  Solved in {solve_time:.2f} seconds")
            print(f"  Status: {status}")
            if solution:
                print(f"  PV Size: {solution.get('pv_size_mw', 0):.2f} MW")
                print(f"  BESS Size: {solution.get('bess_size_mwh', 0):.2f} MWh")
        
        return {
            'num_years': num_years,
            'hours_per_year': hours_per_year,
            'total_hours': num_years * hours_per_year,
            'build_time': build_time,
            'solve_time': solve_time,
            'total_time': total_time,
            'status': status,
            'variables': len(lp.variables),
            'constraints': len(lp.problem.constraints),
        }
        
    except Exception as e:
        if verbose:
            print(f"  ERROR: {e}")
        return {
            'num_years': num_years,
            'hours_per_year': hours_per_year,
            'total_hours': num_years * hours_per_year,
            'build_time': None,
            'solve_time': None,
            'total_time': None,
            'status': 'error',
            'error': str(e),
        }


def estimate_25_year_runtime(results_1_year):
    """
    Estimate runtime for 25 years based on 1-year results.
    
    Note: This is a rough estimate. Actual scaling may not be linear
    due to solver behavior with larger problems.
    """
    if results_1_year['total_time'] is None:
        return None
    
    # Simple linear extrapolation (may underestimate for very large problems)
    estimated_25yr_time = results_1_year['total_time'] * 25
    
    # Rough estimate of problem size scaling
    # Variables scale roughly with hours * years
    # But solver time may scale worse than linearly
    # Use a conservative estimate: time scales with (hours * years)^1.5
    estimated_25yr_time_conservative = results_1_year['total_time'] * (25 ** 1.5)
    
    return {
        'linear_estimate_seconds': estimated_25yr_time,
        'linear_estimate_minutes': estimated_25yr_time / 60,
        'linear_estimate_hours': estimated_25yr_time / 3600,
        'conservative_estimate_seconds': estimated_25yr_time_conservative,
        'conservative_estimate_minutes': estimated_25yr_time_conservative / 60,
        'conservative_estimate_hours': estimated_25yr_time_conservative / 3600,
    }


def main():
    """Run performance tests"""
    print("="*60)
    print("Optimization Performance Test")
    print("="*60)
    print("\nTesting optimization execution time for different scenarios...")
    print("\nNote: Current implementation uses 1 year internally.")
    print("      This test measures 1-year performance and estimates 25-year runtime.")
    
    results = []
    
    # Test 1: 24-hour dataset (quick test)
    print("\n" + "="*60)
    print("Quick Test: 24 hours")
    print("="*60)
    try:
        result_24h = test_optimization_performance(num_years=1, hours_per_year=24)
        results.append(result_24h)
    except Exception as e:
        print(f"Error in 24h test: {e}")
    
    # Test 2: Full year (8760 hours) - this is the key test
    print("\n" + "="*60)
    print("Full Year Test: 8760 hours")
    print("="*60)
    
    # Check if full-year data exists
    pv_file = TEST_DATA_DIR / "pv_production_8760h.csv"
    if not pv_file.exists():
        print("\nFull-year data not found. Generating...")
        import subprocess
        try:
            subprocess.run(
                [sys.executable, "test_data/generate_full_year_data.py"],
                check=True,
                cwd=Path(__file__).parent
            )
            print("Full-year data generated successfully.")
        except Exception as e:
            print(f"Error generating data: {e}")
            print("Skipping full-year test.")
            return
    
    try:
        result_1yr = test_optimization_performance(num_years=1, hours_per_year=8760)
        results.append(result_1yr)
    except Exception as e:
        print(f"Error in 1-year test: {e}")
        return
    
    # Generate performance report
    print("\n" + "="*60)
    print("Performance Summary")
    print("="*60)
    
    for result in results:
        print(f"\n{result['num_years']} year(s), {result['hours_per_year']} hours/year:")
        if result['total_time']:
            print(f"  Build time: {result['build_time']:.2f} seconds")
            print(f"  Solve time: {result['solve_time']:.2f} seconds")
            print(f"  Total time: {result['total_time']:.2f} seconds ({result['total_time']/60:.2f} minutes)")
            print(f"  Variables: {result.get('variables', 'N/A')}")
            print(f"  Constraints: {result.get('constraints', 'N/A')}")
        else:
            print(f"  Status: {result.get('status', 'unknown')}")
            if 'error' in result:
                print(f"  Error: {result['error']}")
    
    # Estimate 25-year runtime
    if result_1yr and result_1yr.get('total_time'):
        print("\n" + "="*60)
        print("25-Year Runtime Estimate")
        print("="*60)
        
        estimate = estimate_25_year_runtime(result_1yr)
        if estimate:
            print(f"\nBased on 1-year performance ({result_1yr['total_time']:.2f} seconds):")
            print(f"\nLinear Extrapolation (may underestimate):")
            print(f"  Estimated time: {estimate['linear_estimate_seconds']:.0f} seconds")
            print(f"                 {estimate['linear_estimate_minutes']:.1f} minutes")
            print(f"                 {estimate['linear_estimate_hours']:.2f} hours")
            
            print(f"\nConservative Estimate (accounts for non-linear scaling):")
            print(f"  Estimated time: {estimate['conservative_estimate_seconds']:.0f} seconds")
            print(f"                 {estimate['conservative_estimate_minutes']:.1f} minutes")
            print(f"                 {estimate['conservative_estimate_hours']:.2f} hours")
            
            print(f"\n⚠ WARNING:")
            print(f"  25 years × 8760 hours = 219,000 time steps")
            print(f"  This is an EXTREMELY large optimization problem.")
            print(f"  The current implementation may not be feasible for 25 years.")
            print(f"  Consider:")
            print(f"    - Using representative days instead of all hours")
            print(f"    - Aggregating time periods")
            print(f"    - Using commercial solvers (Gurobi, CPLEX)")
            print(f"    - Optimizing 1 year and scaling results")
    
    print("\n" + "="*60)


if __name__ == "__main__":
    main()
