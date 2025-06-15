"""
Health check endpoints
"""
import time
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from ...core.dependencies import MemorySelectorDep, CABTrackerDep
from ...core.config import get_settings

router = APIRouter()


class HealthResponse(BaseModel):
    """Health check response model"""
    status: str
    timestamp: float
    version: str = "1.0.0"
    services: Dict[str, str]


@router.get("/", response_model=HealthResponse)
async def health_check(
    memory_selector: MemorySelectorDep,
    cab_tracker: CABTrackerDep
) -> HealthResponse:
    """
    Health check endpoint
    
    Returns the overall health status of the unified memory server
    """
    settings = get_settings()
    
    # Check service health
    services = {}
    
    # Check Redis connectivity
    try:
        redis_client = memory_selector._get_redis_client()
        if redis_client:
            services["redis"] = "healthy"
        else:
            services["redis"] = "disabled"
    except Exception as e:
        services["redis"] = f"unhealthy: {str(e)}"
    
    # Check Neo4j connectivity  
    try:
        if settings.NEO4J_ENABLED:
            neo4j_client = memory_selector._get_neo4j_client()
            if neo4j_client:
                services["neo4j"] = "healthy"
            else:
                services["neo4j"] = "disabled"
        else:
            services["neo4j"] = "disabled"
    except Exception as e:
        services["neo4j"] = f"unhealthy: {str(e)}"
        
    # Check Basic Memory connectivity
    try:
        if settings.BASIC_MEMORY_ENABLED:
            basic_memory_client = memory_selector._get_basic_memory_client()
            if basic_memory_client:
                services["basic_memory"] = "healthy"
            else:
                services["basic_memory"] = "disabled"
        else:
            services["basic_memory"] = "disabled"
    except Exception as e:
        services["basic_memory"] = f"unhealthy: {str(e)}"
    
    # Check CAB tracker
    try:
        if cab_tracker and cab_tracker.initialized:
            services["cab_tracker"] = "healthy"
        else:
            services["cab_tracker"] = "not_initialized"
    except Exception as e:
        services["cab_tracker"] = f"unhealthy: {str(e)}"
    
    # Determine overall status
    unhealthy_services = [name for name, status in services.items() 
                         if status.startswith("unhealthy")]
    
    overall_status = "healthy" if not unhealthy_services else "degraded"
    
    return HealthResponse(
        status=overall_status,
        timestamp=time.time(),
        services=services
    )


@router.get("/ready")
async def readiness_check() -> Dict[str, Any]:
    """
    Readiness check endpoint for Kubernetes/Docker health checks
    """
    return {
        "status": "ready",
        "timestamp": time.time()
    }


@router.get("/live") 
async def liveness_check() -> Dict[str, Any]:
    """
    Liveness check endpoint for Kubernetes/Docker health checks
    """
    return {
        "status": "alive", 
        "timestamp": time.time()
    }