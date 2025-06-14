"""
Dependency injection for FastAPI
"""
from typing import Annotated
from fastapi import Depends, Request

from ..memory_selector import MemorySelector
from ..cab_tracker import CABTracker


def get_memory_selector(request: Request) -> MemorySelector:
    """Get memory selector instance from app state"""
    return request.app.state.memory_selector


def get_cab_tracker(request: Request) -> CABTracker:
    """Get CAB tracker instance from app state"""
    return request.app.state.cab_tracker


# Type annotations for dependency injection
MemorySelectorDep = Annotated[MemorySelector, Depends(get_memory_selector)]
CABTrackerDep = Annotated[CABTracker, Depends(get_cab_tracker)]