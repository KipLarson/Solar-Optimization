"""Financial calculations (NPV, IRR, cash flows)"""
from typing import List, Optional
import numpy as np
try:
    from numpy_financial import irr
except ImportError:
    # Fallback if numpy-financial is not available
    try:
        from numpy import irr
    except ImportError:
        irr = None


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
    
    def __init__(self):
        """Initialize financial model"""
        pass
    
    def calculate_npv(self, cash_flows: List[float], discount_rate: float) -> float:
        """
        Calculate Net Present Value (NPV) of cash flows.
        
        Args:
            cash_flows: List of cash flows, where cash_flows[0] is year 0 (CAPEX),
                       cash_flows[1] is year 1, etc.
            discount_rate: Discount rate (0-1)
            
        Returns:
            NPV in dollars
        """
        npv = 0.0
        for year, cash_flow in enumerate(cash_flows):
            npv += cash_flow / ((1 + discount_rate) ** year)
        return npv
    
    def calculate_irr(self, cash_flows: List[float], guess: float = 0.1) -> Optional[float]:
        """
        Calculate Internal Rate of Return (IRR) from cash flows.
        
        Args:
            cash_flows: List of cash flows, where cash_flows[0] is year 0 (CAPEX),
                       cash_flows[1] is year 1, etc.
            guess: Initial guess for IRR (default 0.1 = 10%)
            
        Returns:
            IRR as decimal (e.g., 0.125 for 12.5%), or None if cannot be calculated
        """
        # Convert to numpy array
        cf_array = np.array(cash_flows)
        
        # Check if we have at least one negative and one positive cash flow
        if np.all(cf_array >= 0) or np.all(cf_array <= 0):
            return None
        
        # Use numpy-financial's IRR function if available
        if irr is not None:
            try:
                return float(irr(cf_array))
            except (ValueError, RuntimeError):
                # Try Newton-Raphson method as fallback
                return self._calculate_irr_newton_raphson(cash_flows, guess)
        else:
            # Fallback to Newton-Raphson
            return self._calculate_irr_newton_raphson(cash_flows, guess)
    
    def _calculate_irr_newton_raphson(self, cash_flows: List[float], guess: float = 0.1, max_iter: int = 100, tol: float = 1e-6) -> Optional[float]:
        """
        Calculate IRR using Newton-Raphson method.
        
        Args:
            cash_flows: List of cash flows
            guess: Initial guess for IRR
            max_iter: Maximum iterations
            tol: Tolerance for convergence
            
        Returns:
            IRR as decimal, or None if cannot converge
        """
        r = guess
        cf_array = np.array(cash_flows)
        
        for _ in range(max_iter):
            # Calculate NPV and derivative
            npv = np.sum(cf_array / ((1 + r) ** np.arange(len(cf_array))))
            
            if abs(npv) < tol:
                return float(r)
            
            # Derivative of NPV with respect to r
            dnpv = -np.sum(cf_array * np.arange(len(cf_array)) / ((1 + r) ** (np.arange(len(cf_array)) + 1)))
            
            if abs(dnpv) < tol:
                break
            
            # Newton-Raphson update
            r_new = r - npv / dnpv
            
            # Prevent negative rates
            if r_new < -0.99:
                r_new = -0.99
            
            if abs(r_new - r) < tol:
                return float(r_new)
            
            r = r_new
        
        return None
    
    def apply_o_and_m_costs(self, revenue: float, year: int, **kwargs) -> float:
        """
        Apply O&M costs to revenue.
        
        Currently not implemented (returns revenue unchanged).
        Can be extended to subtract O&M costs.
        
        Args:
            revenue: Revenue for the period
            year: Year in service
            **kwargs: Additional parameters (e.g., pv_size_mw, bess_size_mwh)
            
        Returns:
            Revenue after O&M costs (currently returns revenue unchanged)
        """
        # TODO: Implement O&M cost calculation
        # Example: return revenue - o_and_m_cost_per_year
        return revenue
    
    def apply_itc(self, capex: float, itc_rate: float = 0.0) -> float:
        """
        Apply Investment Tax Credit (ITC).
        
        Currently not implemented (returns 0).
        Can be extended to return ITC amount.
        
        Args:
            capex: Total CAPEX investment
            itc_rate: ITC rate (0-1), e.g., 0.30 for 30%
            
        Returns:
            ITC amount (currently 0)
        """
        # TODO: Implement ITC calculation
        # Example: return capex * itc_rate
        return 0.0
    
    def calculate_cash_flow_with_itc(self, capex: float, annual_revenues: List[float], itc_rate: float = 0.0) -> List[float]:
        """
        Calculate cash flows including ITC.
        
        Args:
            capex: Total CAPEX investment
            annual_revenues: List of annual revenues
            itc_rate: ITC rate (0-1)
            
        Returns:
            List of cash flows including ITC benefit in year 0
        """
        itc_amount = self.apply_itc(capex, itc_rate)
        cash_flows = [-capex + itc_amount]  # Year 0: negative CAPEX + ITC
        cash_flows.extend(annual_revenues)
        return cash_flows
