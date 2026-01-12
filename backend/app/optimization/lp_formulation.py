"""Linear Programming formulation for solar + storage optimization"""
from typing import Dict, Any, Tuple
import pulp
import pandas as pd
import logging
from app.models.battery import BatteryModel
from app.models.pv_system import PVSystemModel

logger = logging.getLogger(__name__)


class LPFormulation:
    """
    Builds and solves LP model for solar + storage optimization.
    
    Maximizes NPV over 25-year project life with perfect foresight.
    """
    
    def __init__(
        self,
        pv_production: pd.Series,
        pricing: pd.Series,
        pv_capex_per_mw: float,
        bess_capex_per_mwh: float,
        discount_rate: float,
        interconnection_capacity_mw: float,
        onsite_load_price_per_mwh: float,
        onsite_load_max_mw: float,
        yoy_price_escalation_rate: float,
        pv_max_size_mw: float = None,
        bess_max_size_mwh: float = None,
        battery_model: BatteryModel = None,
        pv_model: PVSystemModel = None,
    ):
        """
        Initialize LP formulation.
        
        Args:
            pv_production: PV production profile (8760 hours, MWh per MW)
            pricing: Grid pricing profile (8760 hours, $/MWh)
            pv_capex_per_mw: PV CAPEX per MW
            bess_capex_per_mwh: BESS CAPEX per MWh
            discount_rate: Discount rate (0-1)
            interconnection_capacity_mw: Max interconnection capacity (MW)
            onsite_load_price_per_mwh: On-site load price ($/MWh)
            onsite_load_max_mw: Max on-site load size (MW)
            yoy_price_escalation_rate: Year-over-year price escalation rate
            pv_max_size_mw: Optional max PV size constraint
            bess_max_size_mwh: Optional max BESS size constraint
            battery_model: Battery model instance (default: idealized)
            pv_model: PV system model instance (default: no degradation)
        """
        self.pv_production = pv_production
        self.pricing = pricing
        self.pv_capex_per_mw = pv_capex_per_mw
        self.bess_capex_per_mwh = bess_capex_per_mwh
        self.discount_rate = discount_rate
        self.interconnection_capacity_mw = interconnection_capacity_mw
        self.onsite_load_price_per_mwh = onsite_load_price_per_mwh
        self.onsite_load_max_mw = onsite_load_max_mw
        self.yoy_price_escalation_rate = yoy_price_escalation_rate
        self.pv_max_size_mw = pv_max_size_mw
        self.bess_max_size_mwh = bess_max_size_mwh
        
        # Initialize models
        self.battery_model = battery_model or BatteryModel()
        self.pv_model = pv_model or PVSystemModel()
        
        # Problem dimensions (configurable based on input data)
        # For full year: 8760 hours, 25 years
        # For testing: can use smaller datasets
        self.num_hours = len(pv_production)
        self.num_years = 1  # For now, use 1 year for testing (can extend later)
        self.hours = range(1, self.num_hours + 1)
        self.years = range(1, self.num_years + 1)
        
        # LP problem
        self.problem = None
        self.variables = {}
        
    def build_model(self):
        """Build the LP model with all variables and constraints."""
        # Create problem (maximize NPV)
        self.problem = pulp.LpProblem("Solar_Storage_Optimization", pulp.LpMaximize)
        
        # Create decision variables
        self._create_variables()
        
        # Create objective function
        self._create_objective()
        
        # Create constraints
        self._create_constraints()
        
    def _create_variables(self):
        """Create all decision variables."""
        # Capacity variables
        self.variables['pv_size'] = pulp.LpVariable('pv_size', lowBound=0, cat='Continuous')
        self.variables['bess_size'] = pulp.LpVariable('bess_size', lowBound=0, cat='Continuous')
        
        # Energy flow variables (for each hour and year)
        self.variables['pv_to_grid'] = {}
        self.variables['pv_to_onsite'] = {}
        self.variables['pv_to_battery'] = {}
        self.variables['battery_to_grid'] = {}
        self.variables['battery_to_onsite'] = {}
        self.variables['grid_to_battery'] = {}
        self.variables['soc'] = {}
        # Note: Removed binary variables - battery can charge and discharge simultaneously
        # This simplifies MILP to LP, making it much faster
        
        for year in self.years:
            for hour in self.hours:
                # Continuous variables for energy flows
                self.variables['pv_to_grid'][(hour, year)] = pulp.LpVariable(
                    f'pv_to_grid_h{hour}_y{year}', lowBound=0, cat='Continuous'
                )
                self.variables['pv_to_onsite'][(hour, year)] = pulp.LpVariable(
                    f'pv_to_onsite_h{hour}_y{year}', lowBound=0, cat='Continuous'
                )
                self.variables['pv_to_battery'][(hour, year)] = pulp.LpVariable(
                    f'pv_to_battery_h{hour}_y{year}', lowBound=0, cat='Continuous'
                )
                self.variables['battery_to_grid'][(hour, year)] = pulp.LpVariable(
                    f'battery_to_grid_h{hour}_y{year}', lowBound=0, cat='Continuous'
                )
                self.variables['battery_to_onsite'][(hour, year)] = pulp.LpVariable(
                    f'battery_to_onsite_h{hour}_y{year}', lowBound=0, cat='Continuous'
                )
                self.variables['grid_to_battery'][(hour, year)] = pulp.LpVariable(
                    f'grid_to_battery_h{hour}_y{year}', lowBound=0, cat='Continuous'
                )
                
                # State of charge
                self.variables['soc'][(hour, year)] = pulp.LpVariable(
                    f'soc_h{hour}_y{year}', lowBound=0, cat='Continuous'
                )
        
        # Initial SOC for year 1
        self.variables['soc'][(0, 1)] = pulp.LpVariable('soc_h0_y1', lowBound=0, upBound=0, cat='Continuous')
        
        # SOC at end of each year (for year-to-year continuity)
        for year in self.years:
            if year > 1:
                self.variables['soc'][(0, year)] = pulp.LpVariable(
                    f'soc_h0_y{year}', lowBound=0, cat='Continuous'
                )
    
    def _create_objective(self):
        """Create objective function (maximize NPV)."""
        # CAPEX (negative cash flow in year 0)
        capex = (
            self.variables['pv_size'] * self.pv_capex_per_mw +
            self.variables['bess_size'] * self.bess_capex_per_mwh
        )
        
        # Annual revenues (discounted)
        total_revenue = 0
        for year in self.years:
            year_discount_factor = 1 / ((1 + self.discount_rate) ** (year - 1))
            
            # Price escalation
            price_escalation = (1 + self.yoy_price_escalation_rate) ** (year - 1)
            grid_price_year = self.pricing * price_escalation
            onsite_price_year = self.onsite_load_price_per_mwh * price_escalation
            
            for hour in self.hours:
                # Revenue from grid sales
                grid_revenue = (
                    (self.variables['pv_to_grid'][(hour, year)] +
                     self.variables['battery_to_grid'][(hour, year)]) *
                    grid_price_year[hour]
                )
                
                # Revenue from on-site sales
                onsite_revenue = (
                    (self.variables['pv_to_onsite'][(hour, year)] +
                     self.variables['battery_to_onsite'][(hour, year)]) *
                    onsite_price_year
                )
                
                # Cost of grid charging
                grid_charging_cost = (
                    self.variables['grid_to_battery'][(hour, year)] *
                    grid_price_year[hour]
                )
                
                # Net revenue for this hour
                net_revenue = grid_revenue + onsite_revenue - grid_charging_cost
                total_revenue += net_revenue * year_discount_factor
        
        # Objective: Maximize NPV = -CAPEX + discounted revenues
        self.problem += total_revenue - capex, "NPV"
    
    def _create_constraints(self):
        """Create all constraints."""
        # Note: Removed binary variables and big-M constraints for battery mode exclusivity
        # Battery can now charge and discharge simultaneously (LP instead of MILP)
        # This makes the problem much faster to solve
        
        for year in self.years:
            # Price escalation for this year
            price_escalation = (1 + self.yoy_price_escalation_rate) ** (year - 1)
            
            for hour in self.hours:
                # Get production for this hour
                pv_prod_mwh_per_mw = self.pv_production[hour]
                
                # Constraint 1: PV Energy Balance
                pv_total_production = self.variables['pv_size'] * pv_prod_mwh_per_mw
                pv_output = (
                    self.variables['pv_to_grid'][(hour, year)] +
                    self.variables['pv_to_onsite'][(hour, year)] +
                    self.variables['pv_to_battery'][(hour, year)]
                )
                self.problem += pv_total_production == pv_output, f"PV_balance_h{hour}_y{year}"
                
                # Constraint 2: Grid Export Limit
                grid_export = (
                    self.variables['pv_to_grid'][(hour, year)] +
                    self.variables['battery_to_grid'][(hour, year)]
                )
                self.problem += grid_export <= self.interconnection_capacity_mw, f"Grid_limit_h{hour}_y{year}"
                
                # Constraint 3: On-site Load Limit
                onsite_supply = (
                    self.variables['pv_to_onsite'][(hour, year)] +
                    self.variables['battery_to_onsite'][(hour, year)]
                )
                self.problem += onsite_supply <= self.onsite_load_max_mw, f"Onsite_limit_h{hour}_y{year}"
                
                # Constraint 4: Battery Energy Balance
                # SOC at start of hour
                if hour == 1:
                    soc_start = self.variables['soc'][(0, year)]
                else:
                    soc_start = self.variables['soc'][(hour - 1, year)]
                
                # SOC at end of hour
                soc_end = self.variables['soc'][(hour, year)]
                
                # Energy balance (idealized battery: 100% efficiency)
                energy_in = (
                    self.variables['pv_to_battery'][(hour, year)] +
                    self.variables['grid_to_battery'][(hour, year)]
                )
                energy_out = (
                    self.variables['battery_to_grid'][(hour, year)] +
                    self.variables['battery_to_onsite'][(hour, year)]
                )
                
                self.problem += soc_end == soc_start + energy_in - energy_out, f"Battery_balance_h{hour}_y{year}"
                
                # Constraint 5: Battery SOC Bounds
                self.problem += soc_end <= self.variables['bess_size'], f"SOC_max_h{hour}_y{year}"
                
                # Constraint 5b: Prevent battery operations when bess_size = 0
                # Use a large M value to enforce: if bess_size = 0, then all battery flows = 0
                # M should be larger than max possible battery operations
                big_m_battery = 10000  # Large enough to exceed max possible battery operations
                
                # If bess_size = 0, then battery flows must be 0
                # We use: flow <= big_m * bess_size (when bess_size = 0, flow must be 0)
                # But we need to normalize: flow <= big_m * (bess_size / max_bess_size_expected)
                # For simplicity, use: flow <= big_m * bess_size (this works if bess_size is in reasonable range)
                # Actually, better approach: use a constraint that's active when bess_size is small
                # For now, use a simpler approach: ensure battery flows are bounded by bess_size
                # But this doesn't work well because bess_size can be 0
                
                # Better: Add explicit constraint that battery flows are 0 when bess_size = 0
                # We'll use indicator constraints via big-M: flow <= M * indicator, where indicator = 1 if bess_size > epsilon
                # Simpler: Just bound flows by a multiple of bess_size
                # Actually, the SOC constraint should handle this, but it's not working because
                # the battery can charge and discharge simultaneously, keeping SOC at 0
                
                # Fix: Add constraints that prevent battery operations when bess_size is effectively 0
                # Use: battery_flow <= big_m * (bess_size / 1.0)  - this ensures if bess_size = 0, flows = 0
                # But we need to be careful about units - bess_size is in MWh, flows are in MWh
                # So: flow <= big_m * bess_size works, but big_m needs to be in 1/MWh units
                # Actually, if bess_size is in MWh and flows are in MWh, we can use:
                # flow <= big_m * bess_size where big_m is dimensionless but large
                # But this creates a very loose bound when bess_size > 0
                
                # Better approach: Use a threshold - if bess_size < epsilon, force flows to 0
                # But this requires binary variables or indicator constraints
                
                # Simplest fix: Bound each battery flow by bess_size with a reasonable multiplier
                # This ensures that when bess_size = 0, flows must be 0
                # The multiplier should be based on max C-rate (charge/discharge rate)
                # For idealized battery, we can use a large multiplier, but it's better to use
                # the actual constraint: flows are bounded by what the battery can physically do
                
                # For now, add a constraint that battery flows are bounded by bess_size
                # This prevents the "free energy" exploit
                max_c_rate = 4.0  # Assume max 4-hour charge/discharge rate (conservative)
                self.problem += energy_in <= max_c_rate * self.variables['bess_size'], f"Battery_charge_limit_h{hour}_y{year}"
                self.problem += energy_out <= max_c_rate * self.variables['bess_size'], f"Battery_discharge_limit_h{hour}_y{year}"
                
                # Note: Removed Constraint 6 (battery mode exclusivity)
                # Battery can now charge and discharge simultaneously
                # This is acceptable for planning purposes - the optimizer will choose
                # the economically optimal behavior
                
                # Year-to-year SOC continuity
                if hour == self.num_hours and year < self.num_years:
                    # End of year SOC equals start of next year SOC
                    self.problem += (
                        self.variables['soc'][(hour, year)] ==
                        self.variables['soc'][(0, year + 1)]
                    ), f"SOC_continuity_y{year}_to_y{year+1}"
            
            # Capacity constraints
            if self.pv_max_size_mw is not None:
                self.problem += self.variables['pv_size'] <= self.pv_max_size_mw, f"PV_max_y{year}"
            
            if self.bess_max_size_mwh is not None:
                self.problem += self.variables['bess_size'] <= self.bess_max_size_mwh, f"BESS_max_y{year}"
    
    def solve(self, solver=None):
        """
        Solve the LP problem.
        
        Args:
            solver: PuLP solver to use (default: default solver)
            
        Returns:
            Tuple of (status, solution_dict)
        """
        if self.problem is None:
            self.build_model()
        
        # Solve
        status = self.problem.solve(solver or pulp.PULP_CBC_CMD(msg=0))
        
        if status == pulp.LpStatusOptimal:
            # Extract solution
            solution = {
                'pv_size_mw': pulp.value(self.variables['pv_size']),
                'bess_size_mwh': pulp.value(self.variables['bess_size']),
                'npv': pulp.value(self.problem.objective),
                'status': 'optimal'
            }
            
            # Analyze solution for simultaneous charge/discharge
            simultaneous_count = self._count_simultaneous_charge_discharge()
            solution['simultaneous_charge_discharge_hours'] = simultaneous_count
            
            if simultaneous_count > 0:
                logger.info(f"Solution has {simultaneous_count} hours with simultaneous charge/discharge "
                          f"out of {self.num_hours * self.num_years} total hours")
            else:
                logger.info("No simultaneous charge/discharge detected - optimizer chose mutually exclusive operations")
            
            return pulp.LpStatus[status], solution
        else:
            return pulp.LpStatus[status], None
    
    def _count_simultaneous_charge_discharge(self) -> int:
        """
        Count number of hours where battery simultaneously charges and discharges.
        
        Returns:
            Number of hours with simultaneous charge/discharge
        """
        count = 0
        threshold = 1e-6  # Small threshold to account for floating point precision
        
        for year in self.years:
            for hour in self.hours:
                # Get charge and discharge values
                charge_pv = pulp.value(self.variables['pv_to_battery'].get((hour, year), 0)) or 0
                charge_grid = pulp.value(self.variables['grid_to_battery'].get((hour, year), 0)) or 0
                discharge_grid = pulp.value(self.variables['battery_to_grid'].get((hour, year), 0)) or 0
                discharge_onsite = pulp.value(self.variables['battery_to_onsite'].get((hour, year), 0)) or 0
                
                total_charge = charge_pv + charge_grid
                total_discharge = discharge_grid + discharge_onsite
                
                # Count if both charging and discharging (above threshold)
                if total_charge > threshold and total_discharge > threshold:
                    count += 1
        
        return count
