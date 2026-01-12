# Solar + Storage Optimization Web Application - Implementation Plan

## Overview
A web application that optimizes the configuration of a solar PV + battery energy storage system (BESS) power plant to maximize NPV over a 25-year service life, then calculates and returns the IRR of the optimal configuration.

## Core Requirements

### User Inputs
1. **Hourly PV Production Profile** (CSV): Single MW of installed PV capacity (8760 hours)
2. **Hourly Nodal Pricing Data** (CSV): Grid electricity prices (8760 hours)
3. **PV CAPEX Cost** ($/MW): Per-MW capital cost for PV installation
4. **BESS CAPEX Cost** ($/MWh): Per-MWh capital cost for battery storage
5. **Discount Rate** (%): Used for NPV calculations
6. **Interconnection Maximum Capacity** (MW): Hard cap on total MW exported to grid
7. **On-site Load Price** ($/MWh): Price paid by on-site load for electricity
8. **On-site Load Max Size** (MW): Maximum load capacity
9. **Year-over-Year Price Escalation Rate** (%): Applied to both grid prices and on-site load prices
10. **PV Max Size** (MW, optional): Maximum PV capacity constraint
11. **BESS Max Size** (MWh, optional): Maximum BESS capacity constraint

### Optimization Objective
**Maximize NPV** (Net Present Value) of the 25-year project, then calculate and return the IRR (Internal Rate of Return) of the optimal configuration

### Energy Management Rules
- Plant can sell power to grid OR on-site load (whichever has higher price, if energy available)
- Battery can charge from excess PV generation OR from grid (arbitrage)
- Battery and PV can both discharge to on-site load
- Battery can only charge OR discharge in a given hour (not both)
- Optimizer has perfect foresight (sees all future prices)
- Battery: Idealized model (100% RTE, no C-rate limits, no SoC limits, no degradation) - **MODULAR FOR FUTURE ENHANCEMENT**

## Technology Stack Recommendation

### Backend
- **Python 3.9+**
  - **FastAPI**: Modern, fast web framework with async support
  - **PuLP** or **OR-Tools**: Open-source linear programming libraries (PuLP is simpler, OR-Tools is more powerful)
  - **pandas**: Data processing for CSV files
  - **numpy**: Numerical computations
  - **celery**: Background task processing with Redis/RabbitMQ broker
  - **redis**: Message broker and progress tracking

### Frontend
- **React** or **Vue.js**: Modern UI framework
- **Chart.js** or **Recharts**: For revenue visualization
- **Axios**: HTTP client for API calls
- **File upload component**: For CSV uploads

### Database (Optional - for result storage)
- **SQLite** or **PostgreSQL**: Store calculation results and user sessions

## System Architecture

### High-Level Architecture
```
┌─────────────┐         ┌──────────────┐         ┌─────────────┐
│   Frontend  │◄───────►│   FastAPI    │◄───────►│   Celery    │
│   (React)   │  REST   │   Backend    │  Queue  │  Workers    │
└─────────────┘         └──────────────┘         └─────────────┘
                               │                         │
                               │                         │
                        ┌──────▼──────┐          ┌──────▼──────┐
                        │   Redis     │          │  Optimization│
                        │  (Progress) │          │   Engine    │
                        └─────────────┘          └─────────────┘
```

### Request Flow
1. User uploads CSV files and enters parameters via frontend
2. Frontend sends POST request to FastAPI `/optimize` endpoint
3. FastAPI validates inputs and queues optimization task via Celery
4. Returns task ID to frontend
5. Frontend polls `/status/{task_id}` endpoint for progress
6. Celery worker processes optimization in background
7. Updates progress in Redis
8. On completion, results stored and returned via `/results/{task_id}`
9. Frontend displays results with charts

## Data Model

### CSV File Formats

#### PV Production Profile (`pv_production.csv`)
```csv
Hour,Production_MWh_per_MW
1,0.0
2,0.0
...
8760,0.5
```

#### Nodal Pricing Data (`pricing.csv`)
```csv
Hour,Price_per_MWh
1,45.2
2,42.1
...
8760,38.5
```

### Request Payload
```json
{
  "pv_capex_per_mw": 1000000,
  "bess_capex_per_mwh": 300000,
  "discount_rate": 0.08,
  "interconnection_capacity_mw": 100,
  "onsite_load_price_per_mwh": 50,
  "onsite_load_max_mw": 20,
  "yoy_price_escalation_rate": 0.02,
  "pv_max_size_mw": null,
  "bess_max_size_mwh": null,
  "pv_production_file": "<base64 or multipart>",
  "pricing_file": "<base64 or multipart>"
}
```

### Response Payload
```json
{
  "task_id": "uuid",
  "status": "completed",
  "results": {
    "optimal_pv_size_mw": 75.5,
    "optimal_bess_size_mwh": 150.0,
    "npv": 2500000,
    "irr": 0.125,
    "capex_total": 107500000,
    "monthly_revenues": [
      {"year": 1, "month": 1, "revenue": 125000},
      ...
    ],
    "25_year_total_revenue": 150000000
  }
}
```

## Optimization Model Formulation

### Decision Variables (for each hour t = 1...8760, for each year y = 1...25)

1. **PV size** (MW): `pv_size` (continuous, non-negative)
2. **BESS size** (MWh): `bess_size` (continuous, non-negative)
3. **PV to Grid** (MWh): `pv_to_grid[t,y]` (continuous, non-negative)
4. **PV to On-site** (MWh): `pv_to_onsite[t,y]` (continuous, non-negative)
5. **PV to Battery** (MWh): `pv_to_battery[t,y]` (continuous, non-negative)
6. **Battery to Grid** (MWh): `battery_to_grid[t,y]` (continuous, non-negative)
7. **Battery to On-site** (MWh): `battery_to_onsite[t,y]` (continuous, non-negative)
8. **Grid to Battery** (MWh): `grid_to_battery[t,y]` (continuous, non-negative)
9. **Battery State of Charge** (MWh): `soc[t,y]` (continuous, non-negative)
10. **Binary variable for battery mode**: `battery_charging[t,y]` (1 if charging, 0 if discharging)

### Objective Function
**Maximize NPV** (Net Present Value)

NPV is calculated as:
```
NPV = -CAPEX + Σ(Revenue[t,y] - Grid_Charging_Cost[t,y]) / (1 + discount_rate)^(year-1)
```

Where:
- CAPEX = pv_size * pv_capex_per_mw + bess_size * bess_capex_per_mwh
- Revenue[t,y] = revenue from grid and on-site sales (see Revenue Calculation constraint)
- Grid_Charging_Cost[t,y] = cost of charging battery from grid
- Sum is over all hours t=1...8760 and years y=1...25

**Post-optimization**: Calculate IRR from the cash flows of the optimal solution using numpy's IRR function or Newton-Raphson method

### Constraints

1. **Energy Balance - PV Output**:
   ```
   pv_size * pv_production[t] = pv_to_grid[t,y] + pv_to_onsite[t,y] + pv_to_battery[t,y]
   ```

2. **Energy Balance - Grid Export Limit**:
   ```
   pv_to_grid[t,y] + battery_to_grid[t,y] <= interconnection_capacity_mw
   ```

3. **Energy Balance - On-site Load**:
   ```
   pv_to_onsite[t,y] + battery_to_onsite[t,y] <= onsite_load_max_mw
   ```

4. **Battery Energy Balance**:
   ```
   soc[t+1,y] = soc[t,y] + pv_to_battery[t,y] + grid_to_battery[t,y] 
                - battery_to_grid[t,y] - battery_to_onsite[t,y]
   ```
   (For idealized battery with 100% RTE)

5. **Battery State of Charge Bounds** (for idealized: 0 <= soc <= bess_size):
   ```
   0 <= soc[t,y] <= bess_size
   ```

6. **Battery Mode Constraint** (charge OR discharge, not both):
   ```
   grid_to_battery[t,y] + pv_to_battery[t,y] <= M * battery_charging[t,y]
   battery_to_grid[t,y] + battery_to_onsite[t,y] <= M * (1 - battery_charging[t,y])
   ```
   Where M is a large number (big M method)

7. **Initial/Final SOC** (for yearly cycles):
   ```
   soc[0,y] = soc[8760,y-1]  (end of year y-1 = start of year y)
   soc[0,1] = 0  (start empty)
   ```

8. **Capacity Constraints**:
   ```
   pv_size <= pv_max_size_mw (if provided)
   bess_size <= bess_max_size_mwh (if provided)
   ```

9. **Revenue Calculation** (for each hour):
   ```
   revenue[t,y] = (pv_to_grid[t,y] + battery_to_grid[t,y]) * grid_price[t,y]
                  + (pv_to_onsite[t,y] + battery_to_onsite[t,y]) * onsite_price[y]
                  - grid_to_battery[t,y] * grid_price[t,y]
   ```
   (Subtract cost of grid charging)

10. **Price Escalation**:
    ```
    grid_price[t,y] = grid_price[t,1] * (1 + escalation_rate)^(y-1)
    onsite_price[y] = onsite_price[1] * (1 + escalation_rate)^(y-1)
    ```

### Optimization Algorithm

**Approach**:
1. **Solve LP to maximize NPV**:
   - Build linear programming model with NPV as objective function
   - Decision variables: PV size, BESS size, all energy flows, battery SOC
   - Constraints: Energy balance, capacity limits, battery operation rules
   - Solve using PuLP or OR-Tools solver
   
2. **Extract cash flows from optimal solution**:
   - Year 0: -CAPEX (negative cash flow)
   - Year 1-25: Annual net revenue (revenue - grid charging costs)
   
3. **Calculate IRR from cash flows**:
   - Use numpy's `irr` function (numpy_financial.irr) or
   - Implement Newton-Raphson method to find rate where NPV = 0
   - IRR is the discount rate that makes the NPV of the cash flows equal to zero

## Module Structure

### Backend Structure
```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI application
│   ├── api/
│   │   ├── __init__.py
│   │   ├── routes.py           # API endpoints
│   │   └── schemas.py          # Pydantic models
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py           # Configuration
│   │   └── tasks.py            # Celery task definitions
│   ├── models/
│   │   ├── __init__.py
│   │   ├── battery.py          # ⭐ MODULAR Battery model
│   │   ├── pv_system.py        # ⭐ MODULAR PV system model
│   │   └── financial.py        # Financial calculations (NPV, IRR)
│   ├── optimization/
│   │   ├── __init__.py
│   │   ├── optimizer.py        # Main optimization logic
│   │   ├── lp_formulation.py   # LP model construction
│   │   └── solver.py           # Solver interface
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── file_parser.py      # CSV parsing
│   │   └── progress.py         # Progress tracking
│   └── services/
│       ├── __init__.py
│       └── calculation.py      # Business logic orchestration
```

### Key Module Interfaces

#### `models/battery.py`
```python
class BatteryModel:
    """
    Modular battery model interface.
    Currently implements idealized battery.
    Can be extended with:
    - Round-trip efficiency
    - Charge/discharge rate limits (C-rate)
    - SOC limits (min/max)
    - Degradation over time
    - Self-discharge
    """
    def get_round_trip_efficiency(self, ...) -> float
    def get_max_charge_rate(self, capacity_mwh: float, ...) -> float
    def get_max_discharge_rate(self, capacity_mwh: float, ...) -> float
    def get_soc_limits(self, ...) -> tuple[float, float]
    def apply_degradation(self, capacity_mwh: float, year: int) -> float
    def apply_self_discharge(self, soc: float, hours: float) -> float
```

#### `models/pv_system.py`
```python
class PVSystemModel:
    """
    Modular PV system model interface.
    Currently assumes no degradation.
    Can be extended with:
    - Annual degradation rate
    - Temperature effects
    - Soiling losses
    """
    def get_production(self, capacity_mw: float, hour: int, year: int) -> float
    def apply_degradation(self, production_mwh: float, year: int) -> float
```

#### `models/financial.py`
```python
class FinancialModel:
    """
    Financial calculations.
    Currently ignores O&M and tax credits.
    Can be extended with:
    - Annual O&M costs
    - ITC calculations
    - Depreciation
    - Tax implications
    """
    def calculate_npv(self, cash_flows: list, discount_rate: float) -> float
    def calculate_irr(self, cash_flows: list) -> float
    def apply_o_and_m_costs(self, revenue: float, ...) -> float
    def apply_itc(self, capex: float, ...) -> float
```

## API Endpoints

### 1. POST `/api/optimize`
- Upload CSV files and parameters
- Queue optimization task
- Returns: `{task_id: "uuid"}`

### 2. GET `/api/status/{task_id}`
- Check optimization progress
- Returns: `{status: "pending|processing|completed|failed", progress: 0-100, message: "..."}`

### 3. GET `/api/results/{task_id}`
- Get optimization results
- Returns: Full results payload (see Data Model section)

### 4. GET `/api/health`
- Health check endpoint

## Frontend Components

### Main Components
1. **UploadForm**: CSV file uploads and parameter inputs
2. **ProgressIndicator**: Real-time progress display
3. **ResultsDisplay**: 
   - Optimal configuration (PV size, BESS size)
   - Financial metrics (NPV, IRR)
   - Monthly revenue chart
   - 25-year summary
4. **ChartComponent**: Monthly revenue visualization (Chart.js/Recharts)

### UI Flow
1. User lands on upload page
2. Uploads CSVs, enters parameters, submits
3. Progress bar appears with status updates
4. Results page loads automatically when complete
5. Charts and metrics displayed

## Implementation Phases

### Phase 1: Core Backend Setup
- [ ] Set up FastAPI project structure
- [ ] Configure Celery with Redis
- [ ] Implement CSV parsing utilities
- [ ] Create basic API endpoints (upload, status, results)

### Phase 2: Optimization Engine
- [ ] Implement battery model (idealized)
- [ ] Implement PV system model (no degradation)
- [ ] Implement financial model (basic NPV/IRR)
- [ ] Build LP formulation for optimization
- [ ] Integrate PuLP/OR-Tools solver
- [ ] Test with small dataset

### Phase 3: Financial Calculations
- [ ] Implement NPV calculation (for objective function)
- [ ] Apply year-over-year price escalation
- [ ] Calculate monthly revenues
- [ ] Implement IRR calculation (post-optimization from cash flows, numpy-based)

### Phase 4: Background Processing
- [ ] Implement Celery task for optimization
- [ ] Add progress tracking (Redis)
- [ ] Handle long-running calculations
- [ ] Error handling and retries

### Phase 5: Frontend
- [ ] Set up React/Vue project
- [ ] Create upload form with validation
- [ ] Implement progress polling
- [ ] Build results display
- [ ] Add monthly revenue chart
- [ ] Styling and UX polish

### Phase 6: Testing & Refinement
- [ ] Unit tests for models
- [ ] Integration tests for optimization
- [ ] End-to-end testing
- [ ] Performance optimization
- [ ] Documentation

## Important Design Decisions

### 1. NPV Optimization with IRR Calculation
- **Objective**: Maximize NPV (linear objective function, suitable for LP)
- **IRR Calculation**: Post-optimization step from resulting cash flows
- **Benefits**: 
  - Simpler optimization (linear objective)
  - Standard LP solvers can be used
  - IRR calculated once from optimal solution
- **IRR Method**: Use numpy's IRR function or Newton-Raphson to find discount rate where NPV = 0

### 2. Optimization Scale
- 25 years × 8760 hours = 219,000 time steps
- This is a LARGE optimization problem
- Consider:
  - Aggregating hours (e.g., representative days)
  - Using commercial solvers (Gurobi academic license)
  - Multi-year approximation (optimize Year 1, scale for remaining years)

### 3. Battery SOC Initialization
- Year 1 starts empty
- Year 2+ can start with SOC from end of previous year
- For optimization, may need to allow flexible start/end SOC

### 4. Perfect Foresight Implications
- With perfect foresight, optimizer sees all future prices
- This is realistic for planning but not for real-time operation
- Document this assumption clearly

## Future Enhancements (Modular Design Enables)

1. **Battery Model**:
   - Add round-trip efficiency
   - Add C-rate limits
   - Add SOC limits
   - Add degradation curves
   - Add self-discharge

2. **PV System Model**:
   - Add annual degradation (e.g., 0.5%/year)
   - Add temperature coefficients
   - Add soiling losses

3. **Financial Model**:
   - Add O&M costs (fixed or % of capex)
   - Add ITC (30% federal credit)
   - Add state/local incentives
   - Add depreciation schedules
   - Add tax implications

4. **Optimization**:
   - Add uncertainty/stochastic optimization
   - Add scenario analysis
   - Add sensitivity analysis
   - Add multi-objective optimization (NPV + risk)

5. **UI/UX**:
   - Add result export (PDF, Excel)
   - Add comparison of multiple scenarios
   - Add interactive parameter sliders
   - Add hourly dispatch visualization

## Notes and Considerations

1. **Computational Complexity**: 25-year hourly optimization is computationally intensive. Consider representative day aggregation or multi-year approximation.

2. **Solver Choice**: PuLP is simple but may struggle with large problems. OR-Tools is more powerful. Consider Gurobi (academic license) for better performance.

3. **Progress Tracking**: For long-running optimizations, provide meaningful progress updates (e.g., "Optimizing Year 5 of 25...").

4. **Error Handling**: Validate CSV formats, check for missing data, handle solver failures gracefully.

5. **Data Validation**: Ensure PV production values are reasonable, prices are positive, etc.

6. **Result Storage**: Consider storing results in database for later retrieval/review.
