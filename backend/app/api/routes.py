"""API routes"""
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from typing import Optional
import uuid
from app.api.schemas import TaskStatus, OptimizationResults
from app.core.tasks import optimize_solar_storage_task
from app.utils.file_parser import validate_csv_files
from app.core.config import settings
import os

router = APIRouter(prefix="/api", tags=["optimization"])


# Ensure uploads directory exists
os.makedirs(settings.upload_folder, exist_ok=True)


@router.post("/optimize", response_model=dict)
async def optimize(
    pv_production_file: UploadFile = File(..., description="PV production profile CSV"),
    pricing_file: UploadFile = File(..., description="Nodal pricing CSV"),
    pv_capex_per_mw: float = Form(...),
    bess_capex_per_mwh: float = Form(...),
    discount_rate: float = Form(...),
    interconnection_capacity_mw: float = Form(...),
    onsite_load_price_per_mwh: float = Form(...),
    onsite_load_max_mw: float = Form(...),
    yoy_price_escalation_rate: float = Form(...),
    pv_max_size_mw: Optional[float] = Form(None),
    bess_max_size_mwh: Optional[float] = Form(None),
):
    """
    Upload CSV files and start optimization task.
    
    For now, accepts form data. In production, might want to use multipart/form-data
    with JSON for parameters.
    """
    task_id = str(uuid.uuid4())
    
    try:
        # Read and validate CSV files
        pv_content = await pv_production_file.read()
        pricing_content = await pricing_file.read()
        
        # Validate file sizes
        if len(pv_content) > settings.max_upload_size:
            raise HTTPException(status_code=400, detail="PV production file too large")
        if len(pricing_content) > settings.max_upload_size:
            raise HTTPException(status_code=400, detail="Pricing file too large")
        
        # Validate CSV format
        pv_series, price_series = validate_csv_files(pv_content, pricing_content)
        
        # Prepare optimization parameters
        optimization_params = {
            "pv_capex_per_mw": pv_capex_per_mw,
            "bess_capex_per_mwh": bess_capex_per_mwh,
            "discount_rate": discount_rate,
            "interconnection_capacity_mw": interconnection_capacity_mw,
            "onsite_load_price_per_mwh": onsite_load_price_per_mwh,
            "onsite_load_max_mw": onsite_load_max_mw,
            "yoy_price_escalation_rate": yoy_price_escalation_rate,
            "pv_max_size_mw": pv_max_size_mw,
            "bess_max_size_mwh": bess_max_size_mwh,
            "pv_production": pv_series.to_dict(),  # Convert to dict for serialization
            "pricing": price_series.to_dict(),
        }
        
        # Queue optimization task
        task = optimize_solar_storage_task.delay(optimization_params)
        task_id = task.id
        
        return {"task_id": task_id, "status": "queued"}
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/status/{task_id}", response_model=TaskStatus)
async def get_task_status(task_id: str):
    """Get optimization task status and progress"""
    try:
        from celery.result import AsyncResult
        from app.core.celery_app import celery_app
        
        task_result = AsyncResult(task_id, app=celery_app)
        
        # Get progress from Redis if available
        from app.utils.progress import get_task_progress
        progress_info = get_task_progress(task_id)
        
        if task_result.state == "PENDING":
            status = "pending"
            progress = 0
            message = "Task is waiting to be processed"
        elif task_result.state == "PROCESSING" or task_result.state == "STARTED":
            status = "processing"
            progress = progress_info.get("progress", 0) if progress_info else 0
            message = progress_info.get("message", "Processing...") if progress_info else "Processing..."
        elif task_result.state == "SUCCESS":
            status = "completed"
            progress = 100
            message = "Optimization completed"
            result_data = task_result.result
            # Extract results from task result
            results = None
            if isinstance(result_data, dict) and "results" in result_data:
                results_dict = result_data["results"]
                # Convert to OptimizationResults schema
                monthly_revenues = [
                    {
                        "year": mr["year"],
                        "month": mr["month"],
                        "revenue": mr["revenue"]
                    }
                    for mr in results_dict.get("monthly_revenues", [])
                ]
                results = OptimizationResults(
                    optimal_pv_size_mw=results_dict.get("optimal_pv_size_mw", 0),
                    optimal_bess_size_mwh=results_dict.get("optimal_bess_size_mwh", 0),
                    npv=results_dict.get("npv", 0),
                    irr=results_dict.get("irr", 0),
                    capex_total=results_dict.get("capex_total", 0),
                    monthly_revenues=monthly_revenues,
                    total_revenue_25_years=results_dict.get("total_revenue_25_years", 0),
                )
        elif task_result.state == "FAILURE":
            status = "failed"
            progress = 0
            message = str(task_result.info) if task_result.info else "Task failed"
        else:
            status = "processing"
            progress = 0
            message = f"Unknown state: {task_result.state}"
        
        response = TaskStatus(
            task_id=task_id,
            status=status,
            progress=progress,
            message=message,
            results=results if status == "completed" else None
        )
        
        return response
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting task status: {str(e)}")


@router.get("/results/{task_id}", response_model=OptimizationResults)
async def get_task_results(task_id: str):
    """Get optimization results (only available when task is completed)"""
    try:
        from celery.result import AsyncResult
        from app.core.celery_app import celery_app
        
        task_result = AsyncResult(task_id, app=celery_app)
        
        if task_result.state != "SUCCESS":
            raise HTTPException(
                status_code=400,
                detail=f"Task not completed. Current status: {task_result.state}"
            )
        
        result_data = task_result.result
        
        # Extract results from task result
        if not isinstance(result_data, dict) or "results" not in result_data:
            raise HTTPException(
                status_code=500,
                detail="Invalid result format from task"
            )
        
        results_dict = result_data["results"]
        
        # Convert to OptimizationResults schema
        monthly_revenues = [
            {
                "year": mr["year"],
                "month": mr["month"],
                "revenue": mr["revenue"]
            }
            for mr in results_dict.get("monthly_revenues", [])
        ]
        
        results = OptimizationResults(
            optimal_pv_size_mw=results_dict.get("optimal_pv_size_mw", 0),
            optimal_bess_size_mwh=results_dict.get("optimal_bess_size_mwh", 0),
            npv=results_dict.get("npv", 0),
            irr=results_dict.get("irr", 0),
            capex_total=results_dict.get("capex_total", 0),
            monthly_revenues=monthly_revenues,
            total_revenue_25_years=results_dict.get("total_revenue_25_years", 0),
        )
        
        return results
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting results: {str(e)}")
