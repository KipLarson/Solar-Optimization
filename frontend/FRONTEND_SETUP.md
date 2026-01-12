# Frontend Setup Instructions

## Prerequisites

You need to have Node.js and npm installed. If you don't have them:

### macOS (using Homebrew)
```bash
brew install node
```

### Or download from:
- https://nodejs.org/

## Installation

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

## Running the Full Application

1. **Start Redis** (in a separate terminal):
   ```bash
   redis-server
   ```

2. **Start FastAPI backend** (in a separate terminal):
   ```bash
   cd backend
   source ../venv/bin/activate
   uvicorn app.main:app --reload
   ```

3. **Start Celery worker** (in a separate terminal):
   ```bash
   cd backend
   source ../venv/bin/activate
   celery -A app.core.celery_app worker --loglevel=info
   ```

4. **Start frontend** (in a separate terminal):
   ```bash
   cd frontend
   npm run dev
   ```

## Features

- ✅ Upload CSV files (PV production and pricing)
- ✅ Enter optimization parameters
- ✅ Real-time progress tracking
- ✅ Results display with charts
- ✅ Responsive design

## Project Structure

```
frontend/
├── src/
│   ├── components/
│   │   ├── UploadForm.jsx          # File upload and parameter form
│   │   ├── ProgressIndicator.jsx   # Progress bar and status
│   │   ├── ResultsDisplay.jsx      # Results display
│   │   └── MonthlyRevenueChart.jsx # Revenue chart
│   ├── api/
│   │   └── client.js               # API client (Axios)
│   ├── App.jsx                     # Main app component
│   ├── App.css                     # Styles
│   └── main.jsx                    # Entry point
├── package.json
├── vite.config.js
└── index.html
```
