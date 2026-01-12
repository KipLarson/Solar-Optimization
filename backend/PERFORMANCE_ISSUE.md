# Performance Issue Analysis

## Problem Identified

The optimization is taking over an hour (and still running) because:

### The Problem Size

For **1 year (8760 hours)**, the optimization problem has:

- **8760 binary variables** (one per hour for battery charging/discharging mode)
- **~70,000 continuous variables** (energy flows, SOC for each hour)
- **~175,000 constraints** (energy balance, capacity limits, battery mode constraints)

### Why This Is Slow

1. **Mixed Integer Linear Programming (MILP)**: Binary variables make this a MILP problem, not just LP
2. **Large Problem Size**: 8760 binary variables is a very large MILP problem
3. **CBC Solver**: The free CBC solver (bundled with PuLP) struggles with large MILP problems
4. **Combinatorial Complexity**: Binary variables create exponential search space

### Estimated Time

- **1 year (8760 hours)**: Hours to days (likely not feasible)
- **25 years (219,000 hours)**: Would be completely infeasible with current approach

## Solutions

### Option 1: Simplify the Model (Recommended for Now)

Remove the binary variables for battery mode. Instead, allow simultaneous charging and discharging (which can be constrained to be mutually exclusive in practice). This converts MILP to LP, which is much faster.

**Trade-off**: The model becomes less strict (but for planning purposes, this may be acceptable).

### Option 2: Use Commercial Solvers

- **Gurobi** (academic license available) - Much faster for MILP
- **CPLEX** (academic license available) - Also faster
- These can handle much larger problems

### Option 3: Reduce Problem Size

- Use **representative days** (e.g., 12-30 typical days per year) instead of all 8760 hours
- Use **time aggregation** (e.g., 4-hour blocks instead of hourly)
- Optimize **1 year** and scale/extrapolate results

### Option 4: Relax Constraints

- Remove the "charge OR discharge" constraint (allow both simultaneously, with upper bounds)
- Use continuous approximation of battery mode

## Recommendation

For now, **document that full 8760-hour optimization is not feasible** with the current MILP formulation and CBC solver. The 24-hour test works fine, but full-year requires one of the solutions above.

**For production use**, implement Option 3 (representative days) or Option 1 (simplified model).
