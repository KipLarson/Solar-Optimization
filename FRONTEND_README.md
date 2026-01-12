# Frontend - Solar + Storage Optimization

React frontend application for the Solar + Storage Optimization web application.

## Quick Start

### Prerequisites
- Node.js 18+ and npm (or yarn/pnpm)

### Installation

1. **Navigate to frontend directory:**
   ```bash
   cd frontend
   ```

2. **Install dependencies:**
   ```bash
   npm install
   ```

3. **Start development server:**
   ```bash
   npm run dev
   ```

   The frontend will be available at `http://localhost:5173`

## Features

✅ **Upload Form**
- Upload PV production CSV file (8760 hours)
- Upload pricing CSV file (8760 hours)
- Enter optimization parameters (CAPEX, discount rate, etc.)
- Form validation

✅ **Progress Tracking**
- Real-time progress updates
- Progress bar (0-100%)
- Status messages
- Automatic polling

✅ **Results Display**
- Optimal PV size (MW)
- Optimal BESS size (MWh)
- 25-year NPV
- 25-year IRR
- Total CAPEX
- Total revenue over 25 years
- Monthly revenue chart

✅ **Responsive Design**
- Works on desktop and mobile
- Modern, clean UI

## Project Structure

```
frontend/
├── src/
│   ├── components/
│   │   ├── UploadForm.jsx          # File upload and parameter form
│   │   ├── ProgressIndicator.jsx   # Progress bar and status
│   │   ├── ResultsDisplay.jsx      # Results display
│   │   └── MonthlyRevenueChart.jsx # Revenue chart (Recharts)
│   ├── api/
│   │   └── client.js               # API client (Axios)
│   ├── App.jsx                     # Main app component
│   ├── App.css                     # Styles
│   ├── main.jsx                    # Entry point
│   └── index.css                   # Base styles
├── package.json
├── vite.config.js
├── index.html
└── README.md
```

## API Integration

The frontend communicates with the FastAPI backend:

- **POST `/api/optimize`** - Submit optimization request
  - Multipart form data with CSV files and parameters
  - Returns: `{task_id: "uuid"}`

- **GET `/api/status/{task_id}`** - Poll for progress
  - Returns: `{status, progress, message, results?}`

- **GET `/api/results/{task_id}`** - Get final results
  - Returns: Full results object

## Configuration

Set the API base URL in `.env`:
```
VITE_API_BASE_URL=http://localhost:8000
```

Or it defaults to `http://localhost:8000` if not set.

## Build for Production

```bash
npm run build
```

Output will be in the `dist/` directory.

## Running the Full Stack

1. **Start Redis:**
   ```bash
   redis-server
   ```

2. **Start FastAPI backend:**
   ```bash
   cd backend
   source ../venv/bin/activate
   uvicorn app.main:app --reload
   ```

3. **Start Celery worker:**
   ```bash
   cd backend
   source ../venv/bin/activate
   celery -A app.core.celery_app worker --loglevel=info
   ```

4. **Start frontend:**
   ```bash
   cd frontend
   npm run dev
   ```

Then open `http://localhost:5173` in your browser.
