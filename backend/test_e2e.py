"""End-to-end integration test for the optimization API"""
import sys
import os
import time
import requests
from pathlib import Path

# Test configuration
BASE_URL = "http://localhost:8000"
TEST_DATA_DIR = Path(__file__).parent / "test_data"


def check_server_running():
    """Check if FastAPI server is running"""
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=2)
        if response.status_code == 200:
            print("✓ FastAPI server is running")
            return True
    except requests.exceptions.ConnectionError:
        print("✗ FastAPI server is not running")
        print("  Please start it with: uvicorn app.main:app --reload")
        return False
    except Exception as e:
        print(f"✗ Error checking server: {e}")
        return False
    return False


def upload_optimization_request():
    """Upload CSV files and start optimization"""
    print("\n" + "=" * 60)
    print("Step 1: Upload CSV files and start optimization")
    print("=" * 60)
    
    # Check test data files exist
    pv_file = TEST_DATA_DIR / "pv_production_test_24h.csv"
    pricing_file = TEST_DATA_DIR / "pricing_test_24h.csv"
    
    if not pv_file.exists() or not pricing_file.exists():
        print(f"✗ Test data files not found in {TEST_DATA_DIR}")
        print("  Please run: python test_data/generate_test_data.py")
        return None
    
    print(f"  Using PV file: {pv_file}")
    print(f"  Using pricing file: {pricing_file}")
    
    # Prepare form data
    files = {
        'pv_production_file': ('pv_production_test_24h.csv', open(pv_file, 'rb'), 'text/csv'),
        'pricing_file': ('pricing_test_24h.csv', open(pricing_file, 'rb'), 'text/csv'),
    }
    
    data = {
        'pv_capex_per_mw': '10000',  # Low CAPEX for testing
        'bess_capex_per_mwh': '5000',
        'discount_rate': '0.08',
        'interconnection_capacity_mw': '50',
        'onsite_load_price_per_mwh': '50',
        'onsite_load_max_mw': '10',
        'yoy_price_escalation_rate': '0.02',
        'pv_max_size_mw': '100',
        'bess_max_size_mwh': '200',
    }
    
    try:
        print("\n  Sending POST request to /api/optimize...")
        response = requests.post(f"{BASE_URL}/api/optimize", files=files, data=data, timeout=30)
        
        files['pv_production_file'][1].close()
        files['pricing_file'][1].close()
        
        if response.status_code == 200:
            result = response.json()
            task_id = result.get('task_id')
            print(f"  ✓ Request successful!")
            print(f"  Task ID: {task_id}")
            return task_id
        else:
            print(f"  ✗ Request failed with status {response.status_code}")
            print(f"  Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"  ✗ Error uploading request: {e}")
        return None


def poll_task_status(task_id, max_wait=120, poll_interval=2):
    """Poll task status until completion"""
    print("\n" + "=" * 60)
    print("Step 2: Poll task status")
    print("=" * 60)
    print(f"  Task ID: {task_id}")
    print(f"  Polling every {poll_interval} seconds (max {max_wait}s)...")
    
    start_time = time.time()
    last_progress = -1
    
    while time.time() - start_time < max_wait:
        try:
            response = requests.get(f"{BASE_URL}/api/status/{task_id}", timeout=5)
            
            if response.status_code == 200:
                status_data = response.json()
                status = status_data.get('status')
                progress = status_data.get('progress', 0)
                message = status_data.get('message', '')
                
                # Print progress updates
                if progress != last_progress:
                    print(f"  [{time.time() - start_time:.1f}s] {progress}% - {status}: {message}")
                    last_progress = progress
                
                if status == 'completed':
                    print(f"\n  ✓ Task completed!")
                    return status_data
                elif status == 'failed':
                    print(f"\n  ✗ Task failed: {message}")
                    return status_data
                elif status == 'pending':
                    print(f"  Waiting for task to start...")
                elif status == 'processing':
                    pass  # Continue polling
                    
            else:
                print(f"  ✗ Status request failed: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"  ✗ Error polling status: {e}")
            return None
        
        time.sleep(poll_interval)
    
    print(f"\n  ✗ Timeout: Task did not complete within {max_wait} seconds")
    return None


def get_results(task_id):
    """Get optimization results"""
    print("\n" + "=" * 60)
    print("Step 3: Get optimization results")
    print("=" * 60)
    
    try:
        response = requests.get(f"{BASE_URL}/api/results/{task_id}", timeout=5)
        
        if response.status_code == 200:
            results = response.json()
            print("  ✓ Results retrieved successfully!")
            print("\n  Optimization Results:")
            print(f"    Optimal PV Size: {results.get('optimal_pv_size_mw', 0):.2f} MW")
            print(f"    Optimal BESS Size: {results.get('optimal_bess_size_mwh', 0):.2f} MWh")
            print(f"    NPV: ${results.get('npv', 0):,.2f}")
            if results.get('irr'):
                print(f"    IRR: {results.get('irr', 0)*100:.2f}%")
            else:
                print(f"    IRR: N/A")
            print(f"    Total CAPEX: ${results.get('capex_total', 0):,.2f}")
            print(f"    Total Revenue: ${results.get('total_revenue_25_years', 0):,.2f}")
            print(f"    Monthly revenues: {len(results.get('monthly_revenues', []))} entries")
            return results
        else:
            print(f"  ✗ Results request failed: {response.status_code}")
            print(f"  Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"  ✗ Error getting results: {e}")
        return None


def main():
    """Run end-to-end test"""
    print("=" * 60)
    print("End-to-End Integration Test")
    print("=" * 60)
    print("\nPrerequisites:")
    print("  1. Redis server running")
    print("  2. Celery worker running: celery -A app.core.celery_app worker --loglevel=info")
    print("  3. FastAPI server running: uvicorn app.main:app --reload")
    print()
    
    # Check server is running
    if not check_server_running():
        return False
    
    # Step 1: Upload and start optimization
    task_id = upload_optimization_request()
    if not task_id:
        return False
    
    # Step 2: Poll status
    status_data = poll_task_status(task_id)
    if not status_data:
        return False
    
    if status_data.get('status') != 'completed':
        print("\n  Task did not complete successfully")
        return False
    
    # Step 3: Get results
    results = get_results(task_id)
    
    print("\n" + "=" * 60)
    if results:
        print("✓ End-to-end test PASSED!")
        print("=" * 60)
        return True
    else:
        print("✗ End-to-end test FAILED")
        print("=" * 60)
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
