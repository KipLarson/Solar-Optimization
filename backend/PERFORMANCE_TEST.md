# Performance Test Instructions

## Running the 1-Year Performance Test

The performance test measures how long it takes to optimize a 1-year (8760 hours) configuration.

### Prerequisites

1. **Activate virtual environment:**
   ```bash
   cd backend
   source ../venv/bin/activate
   ```

2. **Ensure full-year test data exists:**
   ```bash
   python test_data/generate_full_year_data.py
   ```

### Running the Test

```bash
python test_performance_1year.py
```

### What to Expect

The test will:
1. Load 8760 hours of PV production and pricing data
2. Build the LP optimization model
3. Solve the optimization problem
4. Process and return results
5. Report timing for each phase

**Expected Runtime:** This may take several minutes (possibly 5-30 minutes) depending on your system, as the optimization problem for 8760 hours is quite large.

### Understanding the Results

The test reports:
- **Total Execution Time**: Complete time from start to finish
- **Time by Phase**: Approximate time for building model, solving, and processing results
- **Optimization Results**: The actual results (PV size, BESS size, NPV, etc.)

### Note on 25-Year Performance

**Important:** The current implementation is set to use 1 year internally. For a true 25-year optimization (25 × 8760 = 219,000 time steps), the problem would be extremely large and likely not feasible with the current solver setup.

**Recommendations for 25-year optimization:**
- Use representative days (e.g., 12 typical days per year) instead of all hours
- Optimize 1 year and scale/extrapolate results
- Use commercial solvers (Gurobi, CPLEX) which handle large problems better
- Consider time aggregation methods
