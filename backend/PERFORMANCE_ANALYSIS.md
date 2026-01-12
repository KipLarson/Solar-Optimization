# Performance Analysis - Why 1-Year Optimization is Still Slow

## Problem Size Analysis

For **1 year (8760 hours)**, the current LP formulation creates:

### Variables
- **2 capacity variables**: `pv_size`, `bess_size`
- **7 flow variables per hour**: 
  - `pv_to_grid`, `pv_to_onsite`, `pv_to_battery`
  - `battery_to_grid`, `battery_to_onsite`
  - `grid_to_battery`
  - `soc` (state of charge)
- **Total**: 2 + (7 × 8760) = **61,322 variables**

### Constraints
- **Energy balance constraints**: ~8760 (one per hour)
- **Capacity limit constraints**: ~8760 (grid export, on-site load, SOC bounds)
- **Year-to-year continuity**: 1
- **Total**: ~**17,500+ constraints**

## Why This Is Still Slow

Even without binary variables, this is a **very large LP problem**:
- **61,000+ variables**
- **17,500+ constraints**
- **Dense constraint matrix** (many variables appear in each constraint)

The CBC solver (free solver) can handle this, but it takes a long time because:
1. **Problem size**: 61K variables is at the upper limit for free solvers
2. **Constraint density**: Many variables are coupled (SOC depends on previous hour)
3. **Solver efficiency**: CBC is good but not optimized for very large problems

## Solutions

### Option 1: Use Representative Days (Recommended)
Instead of 8760 hours, use **12-30 representative days** (288-720 hours):
- **12 days**: 288 hours → ~1,000 variables → **Much faster** (minutes)
- **30 days**: 720 hours → ~5,000 variables → **Still manageable**

### Option 2: Time Aggregation
Aggregate hours into larger blocks:
- **4-hour blocks**: 8760 → 2190 time steps
- **Daily blocks**: 8760 → 365 time steps
- Trade-off: Less granularity, but much faster

### Option 3: Commercial Solver
Use Gurobi or CPLEX (academic licenses available):
- **Gurobi**: Can handle 61K variables much faster
- **CPLEX**: Also very fast for large problems
- **Cost**: Free for academic use

### Option 4: Multi-Year Approximation
- Optimize **1 representative year** in detail
- Scale/extrapolate results for remaining 24 years
- Much faster than optimizing all 25 years

## Recommendation

**For production use**, implement **representative days**:
- Select 12-30 typical days that represent the year
- Optimize those days
- Scale results to full year
- **Expected runtime**: 5-30 minutes instead of 90+ minutes

This maintains accuracy while making the problem tractable.
