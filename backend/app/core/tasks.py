"""Celery task definitions"""
from app.core.celery_app import celery_app
from typing import Dict, Any
import pandas as pd
from app.services.optimization_service import OptimizationService
from app.utils.progress import update_task_progress


@celery_app.task(bind=True, name="app.core.tasks.optimize_solar_storage")
def optimize_solar_storage_task(self, optimization_params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Celery task for optimizing solar + storage configuration.
    
    Args:
        self: Celery task instance (bound task)
        optimization_params: Dictionary containing optimization parameters
        
    Returns:
        Dictionary containing optimization results
    """
    task_id = self.request.id
    
    try:
        # Update task state
        update_task_progress(task_id, 5, "Initializing optimization...")
        self.update_state(
            state="PROCESSING",
            meta={"progress": 5, "message": "Initializing optimization..."}
        )
        
        # Convert pandas Series from dicts back to Series
        # (They were converted to dict for JSON serialization)
        pv_production_dict = optimization_params.pop('pv_production')
        pricing_dict = optimization_params.pop('pricing')
        
        pv_production = pd.Series(pv_production_dict, dtype=float)
        pricing = pd.Series(pricing_dict, dtype=float)
        
        # Ensure Series index starts at 1 (if it doesn't already)
        if pv_production.index.min() != 1:
            pv_production.index = range(1, len(pv_production) + 1)
        if pricing.index.min() != 1:
            pricing.index = range(1, len(pricing) + 1)
        
        update_task_progress(task_id, 10, "Building optimization model...")
        self.update_state(
            state="PROCESSING",
            meta={"progress": 10, "message": "Building optimization model..."}
        )
        
        # Create optimization service
        service = OptimizationService()
        
        # Progress callback that updates both Redis and Celery state
        def progress_callback(progress: int, message: str):
            update_task_progress(task_id, progress, message)
            self.update_state(
                state="PROCESSING",
                meta={"progress": progress, "message": message}
            )
        
        # Run optimization
        results = service.optimize(
            pv_production=pv_production,
            pricing=pricing,
            progress_callback=progress_callback,
            **optimization_params
        )
        
        # Update final state
        update_task_progress(task_id, 100, "Optimization completed successfully")
        self.update_state(
            state="SUCCESS",
            meta={
                "progress": 100,
                "message": "Optimization completed successfully",
                "results": results
            }
        )
        
        return {
            "status": "completed",
            "results": results
        }
        
    except Exception as e:
        # Update error state
        error_message = f"Optimization failed: {str(e)}"
        update_task_progress(task_id, 0, error_message, state="FAILED")
        self.update_state(
            state="FAILURE",
            meta={
                "progress": 0,
                "message": error_message,
                "error": str(e)
            }
        )
        
        # Re-raise to let Celery handle it
        raise
