# End-to-End Integration Testing Guide

## Prerequisites

Before running end-to-end tests, you need to have three services running:

### 1. Redis Server
Redis is used as the message broker for Celery.

**Check if running:**
```bash
redis-cli ping
# Should return: PONG
```

**Start Redis (if not running):**
```bash
# On macOS with Homebrew:
brew services start redis
# Or run directly:
redis-server
```

### 2. Celery Worker
The Celery worker processes optimization tasks in the background.

**Start Celery worker:**
```bash
cd backend
celery -A app.core.celery_app worker --loglevel=info
```

You should see output like:
```
celery@hostname v5.3.4

[tasks]
  . app.core.tasks.optimize_solar_storage

[2024-01-XX ...] connected to redis://localhost:6379/0
[2024-01-XX ...] celery@hostname ready.
```

### 3. FastAPI Server
The API server handles HTTP requests.

**Start FastAPI server:**
```bash
cd backend
uvicorn app.main:app --reload
```

You should see:
```
INFO:     Uvicorn running on http://127.0.0.1:8000
```

## Running End-to-End Test

Once all three services are running, run the test script:

```bash
cd backend
python test_e2e.py
```

The test will:
1. Check if the server is running
2. Upload CSV files and start optimization
3. Poll task status until completion
4. Retrieve and display results

## Expected Output

```
============================================================
End-to-End Integration Test
============================================================

Prerequisites:
  1. Redis server running
  2. Celery worker running: celery -A app.core.celery_app worker --loglevel=info
  3. FastAPI server running: uvicorn app.main:app --reload

✓ FastAPI server is running

============================================================
Step 1: Upload CSV files and start optimization
============================================================
  Using PV file: test_data/pv_production_test_24h.csv
  Using pricing file: test_data/pricing_test_24h.csv

  Sending POST request to /api/optimize...
  ✓ Request successful!
  Task ID: <uuid>

============================================================
Step 2: Poll task status
============================================================
  Task ID: <uuid>
  Polling every 2 seconds (max 120s)...
  [0.1s] 5% - processing: Initializing optimization...
  [2.2s] 10% - processing: Building optimization model...
  [5.5s] 30% - processing: Solving optimization problem...
  [8.1s] 70% - processing: Calculating financial metrics...
  [10.3s] 100% - processing: Optimization complete!

  ✓ Task completed!

============================================================
Step 3: Get optimization results
============================================================
  ✓ Results retrieved successfully!

  Optimization Results:
    Optimal PV Size: X.XX MW
    Optimal BESS Size: X.XX MWh
    NPV: $X,XXX.XX
    IRR: X.XX%
    Total CAPEX: $X,XXX.XX
    Total Revenue: $X,XXX.XX
    Monthly revenues: X entries

============================================================
✓ End-to-end test PASSED!
============================================================
```

## Troubleshooting

### Redis Connection Error
- Make sure Redis is running: `redis-cli ping`
- Check Redis URL in `app/core/config.py`

### Celery Worker Not Processing Tasks
- Check Celery worker logs for errors
- Ensure Redis is accessible
- Verify task is registered: Look for `app.core.tasks.optimize_solar_storage` in worker startup

### FastAPI Server Not Responding
- Check if server is running on port 8000
- Check for errors in server logs
- Verify dependencies are installed: `pip install -r requirements.txt`

### Task Stays in PENDING State
- Ensure Celery worker is running
- Check worker logs for errors
- Verify task function name matches

### Task Fails with Error
- Check Celery worker logs for detailed error messages
- Check optimization service logs
- Verify test data files exist and are valid
