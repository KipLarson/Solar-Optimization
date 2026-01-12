# Solar + Storage Optimization Model

A web application that identifies the financially optimal configuration for a solar PV + battery energy storage system (BESS) power plant.

## Overview

This application optimizes the configuration of a solar PV + battery energy storage system to maximize NPV over a 25-year service life, then calculates and returns the IRR of the optimal configuration.

## Project Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI application
│   ├── api/                    # API routes and schemas
│   ├── core/                   # Configuration and tasks
│   ├── models/                 # Modular models (Battery, PV, Financial)
│   ├── optimization/           # Optimization engine
│   ├── utils/                  # Utility functions
│   └── services/               # Business logic
├── requirements.txt            # Python dependencies
└── uploads/                    # Uploaded CSV files (created at runtime)
```

## Setup

### Prerequisites

- Python 3.9+
- Redis (for Celery task queue)
- pip (Python package manager)

### Installation

1. **Create and activate virtual environment** (if not already done):
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On macOS/Linux
   ```

2. **Install dependencies**:
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

3. **Start Redis** (if not already running):
   ```bash
   redis-server
   # Or if installed via Homebrew: brew services start redis
   ```

4. **Run the FastAPI server**:
   ```bash
   cd backend
   uvicorn app.main:app --reload
   ```

   The API will be available at `http://localhost:8000`

5. **View API documentation**:
   - Swagger UI: `http://localhost:8000/docs`
   - ReDoc: `http://localhost:8000/redoc`

## Development Status

This project is currently in Phase 1 (Core Backend Setup). See `PLAN.md` for detailed implementation plan.

## License

[To be determined]
