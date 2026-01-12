# Solar + Storage Optimization - Frontend

React frontend for the Solar + Storage Optimization web application.

## Setup

1. **Install dependencies:**
   ```bash
   npm install
   ```

2. **Configure API URL:**
   - The default API URL is `http://localhost:8000`
   - You can override this by setting `VITE_API_BASE_URL` in `.env` file

3. **Start development server:**
   ```bash
   npm run dev
   ```

   The frontend will be available at `http://localhost:5173` (or the port shown in terminal)

## Build for Production

```bash
npm run build
```

The built files will be in the `dist` directory.

## Features

- **Upload Form**: Upload CSV files (PV production and pricing) and enter optimization parameters
- **Progress Tracking**: Real-time progress updates with progress bar
- **Results Display**: View optimal configuration, financial metrics, and monthly revenue charts
- **Responsive Design**: Works on desktop and mobile devices

## Components

- `UploadForm`: Form for uploading CSV files and entering parameters
- `ProgressIndicator`: Real-time progress display with polling
- `ResultsDisplay`: Display optimization results with charts
- `MonthlyRevenueChart`: Chart visualization of monthly revenues over 25 years

## API Integration

The frontend communicates with the FastAPI backend via:
- `POST /api/optimize` - Submit optimization request
- `GET /api/status/{task_id}` - Poll for progress
- `GET /api/results/{task_id}` - Get final results
