"""API request and response schemas"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional
from decimal import Decimal


class OptimizationRequest(BaseModel):
    """Request schema for optimization endpoint"""
    
    pv_capex_per_mw: float = Field(..., gt=0, description="PV CAPEX cost per MW")
    bess_capex_per_mwh: float = Field(..., gt=0, description="BESS CAPEX cost per MWh")
    discount_rate: float = Field(..., ge=0, le=1, description="Discount rate (0-1)")
    interconnection_capacity_mw: float = Field(..., gt=0, description="Max interconnection capacity in MW")
    onsite_load_price_per_mwh: float = Field(..., gt=0, description="On-site load price per MWh")
    onsite_load_max_mw: float = Field(..., gt=0, description="Max on-site load size in MW")
    yoy_price_escalation_rate: float = Field(..., ge=0, description="Year-over-year price escalation rate")
    pv_max_size_mw: Optional[float] = Field(None, gt=0, description="Max PV size constraint (optional)")
    bess_max_size_mwh: Optional[float] = Field(None, gt=0, description="Max BESS size constraint (optional)")
    
    @field_validator('discount_rate')
    @classmethod
    def validate_discount_rate(cls, v):
        """Validate discount rate is in reasonable range"""
        if not 0 <= v <= 1:
            raise ValueError('Discount rate must be between 0 and 1')
        return v


class MonthlyRevenue(BaseModel):
    """Monthly revenue entry"""
    year: int
    month: int
    revenue: float


class OptimizationResults(BaseModel):
    """Response schema for optimization results"""
    
    optimal_pv_size_mw: float = Field(..., description="Optimal PV size in MW")
    optimal_bess_size_mwh: float = Field(..., description="Optimal BESS size in MWh")
    npv: float = Field(..., description="Net Present Value")
    irr: float = Field(..., description="Internal Rate of Return")
    capex_total: float = Field(..., description="Total CAPEX investment")
    monthly_revenues: list[MonthlyRevenue] = Field(..., description="Monthly revenue breakdown")
    total_revenue_25_years: float = Field(..., description="Total revenue over 25 years")


class TaskStatus(BaseModel):
    """Task status response"""
    task_id: str
    status: str = Field(..., description="Status: pending, processing, completed, failed")
    progress: int = Field(..., ge=0, le=100, description="Progress percentage (0-100)")
    message: Optional[str] = Field(None, description="Status message")
    results: Optional[OptimizationResults] = Field(None, description="Results if completed")
