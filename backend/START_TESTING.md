# Quick Start Guide for End-to-End Testing

## Current Status
- ✓ Redis is running
- ✓ FastAPI server is running (you have it running from earlier)
- ⚠ Celery worker needs to be started

## Steps to Run End-to-End Test

### Step 1: Install requests (if needed)
```bash
cd backend
pip install requests
# Or install all requirements:
pip install -r requirements.txt
```

### Step 2: Start Celery Worker

Open a **new terminal window** (keep FastAPI server running in the current one) and run:

```bash
cd "/Users/kiplarson/Cursor Project/Solar Optimization Model/backend"
celery -A app.core.celery_app worker --loglevel=info
```

You should see output like:
```
celery@hostname v5.3.4

[tasks]
  . app.core.tasks.optimize_solar_storage

[INFO/MainProcess] connected to redis://localhost:6379/0
[INFO/MainProcess] celery@hostname ready.
```

**Keep this terminal window open** - the Celery worker needs to keep running.

### Step 3: Run the Test

In a **third terminal window** (or you can use the same one where FastAPI is running if you run it in background), run:

```bash
cd "/Users/kiplarson/Cursor Project/Solar Optimization Model/backend"
python test_e2e.py
```

## What You Should See

The test will:
1. ✓ Check that FastAPI server is running
2. Upload test CSV files
3. Get a task ID
4. Poll the task status (you'll see progress updates)
5. Retrieve and display results

## Expected Output

```
============================================================
End-to-End Integration Test
============================================================
✓ FastAPI server is running

============================================================
Step 1: Upload CSV files and start optimization
============================================================
  ✓ Request successful!
  Task ID: <some-uuid>

============================================================
Step 2: Poll task status
============================================================
  [2.1s] 10% - processing: Building optimization model...
  [5.3s] 30% - processing: Solving optimization problem...
  [8.7s] 70% - processing: Calculating financial metrics...
  [11.2s] 100% - processing: Optimization complete!
  ✓ Task completed!

============================================================
Step 3: Get optimization results
============================================================
  ✓ Results retrieved successfully!
  [Results displayed here...]

✓ End-to-end test PASSED!
```

## Troubleshooting

### "Celery worker not processing tasks"
- Make sure Redis is running (we already checked - it is!)
- Make sure Celery worker started successfully (check for errors in worker logs)
- Verify task name matches: `app.core.tasks.optimize_solar_storage`

### "Task stays in PENDING"
- Check Celery worker logs for errors
- Verify worker is connected to Redis

### "Import errors"
- Make sure you're in the `backend` directory
- Make sure virtual environment is activated: `source ../venv/bin/activate`
- Install dependencies: `pip install -r requirements.txt`
