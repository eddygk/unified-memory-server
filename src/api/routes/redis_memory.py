"""
Redis Memory Server endpoints
"""
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from ...core.dependencies import MemorySelectorDep
from ...memory_selector import TaskType

router = APIRouter()


class MemoryCreate(BaseModel):
    """Memory creation request"""
    text: str = Field(..., description="Memory text content")
    namespace: str = Field(default="default", description="Memory namespace")
    topics: Optional[List[str]] = Field(default=None, description="Memory topics")
    entities: Optional[List[str]] = Field(default=None, description="Associated entities")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata")
    session_id: Optional[str] = Field(default=None, description="Session ID for working memory")


class MemoryResponse(BaseModel):
    """Memory response"""
    id: str
    text: str
    namespace: str
    topics: List[str]
    entities: List[str]
    created_at: float
    updated_at: float
    metadata: Dict[str, Any]


class MemorySearchRequest(BaseModel):
    """Memory search request"""
    query: str = Field(..., description="Search query")
    namespace: str = Field(default="default", description="Search namespace")
    limit: int = Field(default=10, description="Maximum number of results")
    threshold: float = Field(default=0.7, description="Similarity threshold (0.0-1.0)")
    session_id: Optional[str] = Field(default=None, description="Session ID for context")


class MemorySearchResponse(BaseModel):
    """Memory search response"""
    results: List[Dict[str, Any]]
    total_count: int
    query_time_ms: float


class SessionCreate(BaseModel):
    """Session creation request"""
    session_id: str = Field(..., description="Unique session ID")
    namespace: str = Field(default="default", description="Session namespace")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Session metadata")


class SessionResponse(BaseModel):
    """Session response"""
    session_id: str
    namespace: str
    created_at: float
    metadata: Dict[str, Any]


class HydrateRequest(BaseModel):
    """Hydrate prompt request"""
    prompt: str = Field(..., description="Base prompt to hydrate")
    namespace: str = Field(default="default", description="Memory namespace")
    session_id: Optional[str] = Field(default=None, description="Session ID for context")
    limit: int = Field(default=10, description="Maximum memories to include")


class HydrateResponse(BaseModel):
    """Hydrate prompt response"""
    hydrated_prompt: str
    memories_used: List[Dict[str, Any]]
    total_memories: int


@router.post("/memories", response_model=MemoryResponse, status_code=status.HTTP_201_CREATED)
async def create_memory(
    memory: MemoryCreate,
    memory_selector: MemorySelectorDep
) -> MemoryResponse:
    """
    Create a new memory in Redis Memory Server
    """
    try:
        # Prepare data for storage
        memory_data = {
            "text": memory.text,
            "namespace": memory.namespace,
            "topics": memory.topics or [],
            "entities": memory.entities or [],
            "metadata": memory.metadata or {},
            "session_id": memory.session_id
        }
        
        # Store in Redis using memory selector
        result = memory_selector.store(
            data=memory_data,
            task_type=TaskType.STORE_MEMORY,
            context={"operation": "create_memory"}
        )
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create memory in Redis"
            )
        
        return MemoryResponse(
            id=result.get("memory_id", "unknown"),
            text=memory.text,
            namespace=memory.namespace,
            topics=memory.topics or [],
            entities=memory.entities or [],
            created_at=result.get("created_at", 0),
            updated_at=result.get("updated_at", 0),
            metadata=memory.metadata or {}
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating memory: {str(e)}"
        )


@router.post("/memories/search", response_model=MemorySearchResponse)
async def search_memories(
    search_request: MemorySearchRequest,
    memory_selector: MemorySelectorDep
) -> MemorySearchResponse:
    """
    Search memories using semantic search
    """
    try:
        import time
        start_time = time.time()
        
        # Search in Redis using memory selector
        result = memory_selector.retrieve(
            query=search_request.query,
            task_type=TaskType.SEARCH_MEMORY,
            context={
                "operation": "search_memories",
                "namespace": search_request.namespace,
                "limit": search_request.limit,
                "threshold": search_request.threshold,
                "session_id": search_request.session_id
            }
        )
        
        end_time = time.time()
        query_time_ms = (end_time - start_time) * 1000
        
        if not result:
            return MemorySearchResponse(
                results=[],
                total_count=0,
                query_time_ms=query_time_ms
            )
        
        results = result.get("results", [])
        
        return MemorySearchResponse(
            results=results,
            total_count=len(results),
            query_time_ms=query_time_ms
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error searching memories: {str(e)}"
        )


@router.post("/memories/batch", response_model=List[MemoryResponse], status_code=status.HTTP_201_CREATED)
async def batch_create_memories(
    memories: List[MemoryCreate],
    memory_selector: MemorySelectorDep
) -> List[MemoryResponse]:
    """
    Create multiple memories in batch
    """
    try:
        created_memories = []
        
        for memory in memories:
            # Prepare data for storage
            memory_data = {
                "text": memory.text,
                "namespace": memory.namespace,
                "topics": memory.topics or [],
                "entities": memory.entities or [],
                "metadata": memory.metadata or {},
                "session_id": memory.session_id
            }
            
            # Store in Redis using memory selector
            result = memory_selector.store(
                data=memory_data,
                task_type=TaskType.STORE_MEMORY,
                context={"operation": "batch_create_memory"}
            )
            
            if result:
                created_memories.append(MemoryResponse(
                    id=result.get("memory_id", "unknown"),
                    text=memory.text,
                    namespace=memory.namespace,
                    topics=memory.topics or [],
                    entities=memory.entities or [],
                    created_at=result.get("created_at", 0),
                    updated_at=result.get("updated_at", 0),
                    metadata=memory.metadata or {}
                ))
        
        return created_memories
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating batch memories: {str(e)}"
        )


@router.delete("/memories/{memory_id}")
async def delete_memory(
    memory_id: str,
    memory_selector: MemorySelectorDep
) -> Dict[str, str]:
    """
    Delete a specific memory
    """
    try:
        # Delete from Redis using memory selector
        result = memory_selector.delete(
            item_id=memory_id,
            task_type=TaskType.DELETE_MEMORY,
            context={"operation": "delete_memory"}
        )
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Memory '{memory_id}' not found"
            )
        
        return {"message": f"Memory '{memory_id}' deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting memory: {str(e)}"
        )


@router.post("/sessions", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
async def create_session(
    session: SessionCreate,
    memory_selector: MemorySelectorDep
) -> SessionResponse:
    """
    Create a new session for working memory
    """
    try:
        # Prepare data for storage
        session_data = {
            "session_id": session.session_id,
            "namespace": session.namespace,
            "metadata": session.metadata or {}
        }
        
        # Store session in Redis using memory selector
        result = memory_selector.store(
            data=session_data,
            task_type=TaskType.CREATE_SESSION,
            context={"operation": "create_session"}
        )
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create session in Redis"
            )
        
        return SessionResponse(
            session_id=session.session_id,
            namespace=session.namespace,
            created_at=result.get("created_at", 0),
            metadata=session.metadata or {}
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating session: {str(e)}"
        )


@router.post("/hydrate", response_model=HydrateResponse)
async def hydrate_prompt(
    hydrate_request: HydrateRequest,
    memory_selector: MemorySelectorDep
) -> HydrateResponse:
    """
    Hydrate a prompt with relevant memories for context
    """
    try:
        # Retrieve memories for prompt hydration
        result = memory_selector.retrieve(
            query=hydrate_request.prompt,
            task_type=TaskType.HYDRATE_PROMPT,
            context={
                "operation": "hydrate_prompt",
                "namespace": hydrate_request.namespace,
                "session_id": hydrate_request.session_id,
                "limit": hydrate_request.limit
            }
        )
        
        if not result:
            return HydrateResponse(
                hydrated_prompt=hydrate_request.prompt,
                memories_used=[],
                total_memories=0
            )
        
        hydrated_prompt = result.get("hydrated_prompt", hydrate_request.prompt)
        memories_used = result.get("memories", [])
        
        return HydrateResponse(
            hydrated_prompt=hydrated_prompt,
            memories_used=memories_used,
            total_memories=len(memories_used)
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error hydrating prompt: {str(e)}"
        )


@router.get("/memories/{memory_id}", response_model=MemoryResponse)
async def get_memory(
    memory_id: str,
    memory_selector: MemorySelectorDep
) -> MemoryResponse:
    """
    Get a specific memory by ID
    """
    try:
        # Retrieve memory from Redis
        result = memory_selector.retrieve(
            query=f"Get memory with ID {memory_id}",
            task_type=TaskType.RETRIEVE_MEMORY,
            context={
                "operation": "get_memory",
                "memory_id": memory_id
            }
        )
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Memory '{memory_id}' not found"
            )
        
        return MemoryResponse(
            id=result.get("id", memory_id),
            text=result.get("text", ""),
            namespace=result.get("namespace", "default"),
            topics=result.get("topics", []),
            entities=result.get("entities", []),
            created_at=result.get("created_at", 0),
            updated_at=result.get("updated_at", 0),
            metadata=result.get("metadata", {})
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving memory: {str(e)}"
        )