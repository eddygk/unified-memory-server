"""
Basic Memory (Obsidian) endpoints
"""
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from ...core.dependencies import MemorySelectorDep
from ...memory_selector import TaskType

router = APIRouter()


class NoteCreate(BaseModel):
    """Note creation request"""
    title: str = Field(..., description="Note title")
    content: str = Field(..., description="Note content in markdown")
    tags: Optional[List[str]] = Field(default=None, description="Note tags")
    path: Optional[str] = Field(default=None, description="File path within vault")


class NoteResponse(BaseModel):
    """Note response"""
    id: str
    title: str
    content: str
    tags: List[str]
    path: str
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class NoteUpdate(BaseModel):
    """Note update request"""
    title: Optional[str] = Field(default=None, description="Note title")
    content: Optional[str] = Field(default=None, description="Note content in markdown")
    tags: Optional[List[str]] = Field(default=None, description="Note tags")


class NotesSearchRequest(BaseModel):
    """Notes search request"""
    query: str = Field(..., description="Search query")
    limit: int = Field(default=10, description="Maximum number of results")
    tags: Optional[List[str]] = Field(default=None, description="Filter by tags")


class NotesSearchResponse(BaseModel):
    """Notes search response"""
    results: List[NoteResponse]
    total_count: int
    query_time_ms: float


class CanvasCreate(BaseModel):
    """Canvas creation request"""
    name: str = Field(..., description="Canvas name")
    nodes: List[Dict[str, Any]] = Field(default_factory=list, description="Canvas nodes")
    edges: List[Dict[str, Any]] = Field(default_factory=list, description="Canvas edges")


class CanvasResponse(BaseModel):
    """Canvas response"""
    id: str
    name: str
    nodes: List[Dict[str, Any]]
    edges: List[Dict[str, Any]]
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


@router.post("/notes", response_model=NoteResponse, status_code=status.HTTP_201_CREATED)
async def create_note(
    note: NoteCreate,
    memory_selector: MemorySelectorDep
) -> NoteResponse:
    """
    Create a new note in Basic Memory
    """
    try:
        # Prepare data for storage
        note_data = {
            "title": note.title,
            "content": note.content,
            "tags": note.tags or [],
            "path": note.path
        }
        
        # Store in Basic Memory using memory selector
        result = memory_selector.store(
            data=note_data,
            task_type=TaskType.STORE_NOTE,
            context={"operation": "create_note"}
        )
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create note in Basic Memory"
            )
        
        return NoteResponse(
            id=result.get("note_id", "unknown"),
            title=note.title,
            content=note.content,
            tags=note.tags or [],
            path=result.get("path", note.path or ""),
            created_at=result.get("created_at"),
            updated_at=result.get("updated_at")
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating note: {str(e)}"
        )


@router.get("/notes/{note_id}", response_model=NoteResponse)
async def get_note(
    note_id: str,
    memory_selector: MemorySelectorDep
) -> NoteResponse:
    """
    Get a specific note by ID
    """
    try:
        # Retrieve note from Basic Memory
        result = memory_selector.retrieve(
            query=f"Get note with ID {note_id}",
            task_type=TaskType.RETRIEVE_NOTE,
            context={
                "operation": "get_note",
                "note_id": note_id
            }
        )
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Note '{note_id}' not found"
            )
        
        return NoteResponse(
            id=result.get("id", note_id),
            title=result.get("title", ""),
            content=result.get("content", ""),
            tags=result.get("tags", []),
            path=result.get("path", ""),
            created_at=result.get("created_at"),
            updated_at=result.get("updated_at")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving note: {str(e)}"
        )


@router.put("/notes/{note_id}", response_model=NoteResponse)
async def update_note(
    note_id: str,
    note_update: NoteUpdate,
    memory_selector: MemorySelectorDep
) -> NoteResponse:
    """
    Update an existing note
    """
    try:
        # Prepare update data
        update_data = {
            "note_id": note_id,
            **{k: v for k, v in note_update.dict().items() if v is not None}
        }
        
        # Update in Basic Memory using memory selector
        result = memory_selector.store(
            data=update_data,
            task_type=TaskType.UPDATE_NOTE,
            context={"operation": "update_note"}
        )
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update note in Basic Memory"
            )
        
        return NoteResponse(
            id=note_id,
            title=result.get("title", ""),
            content=result.get("content", ""),
            tags=result.get("tags", []),
            path=result.get("path", ""),
            created_at=result.get("created_at"),
            updated_at=result.get("updated_at")
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating note: {str(e)}"
        )


@router.post("/search/notes", response_model=NotesSearchResponse)
async def search_notes(
    search_request: NotesSearchRequest,
    memory_selector: MemorySelectorDep
) -> NotesSearchResponse:
    """
    Search notes using full-text search
    """
    try:
        import time
        start_time = time.time()
        
        # Search in Basic Memory using memory selector
        result = memory_selector.retrieve(
            query=search_request.query,
            task_type=TaskType.SEARCH_NOTES,
            context={
                "operation": "search_notes",
                "limit": search_request.limit,
                "tags": search_request.tags
            }
        )
        
        end_time = time.time()
        query_time_ms = (end_time - start_time) * 1000
        
        if not result:
            return NotesSearchResponse(
                results=[],
                total_count=0,
                query_time_ms=query_time_ms
            )
        
        # Convert results to response format
        notes = []
        for note_data in result.get("results", []):
            notes.append(NoteResponse(
                id=note_data.get("id", ""),
                title=note_data.get("title", ""),
                content=note_data.get("content", ""),
                tags=note_data.get("tags", []),
                path=note_data.get("path", ""),
                created_at=note_data.get("created_at"),
                updated_at=note_data.get("updated_at")
            ))
        
        return NotesSearchResponse(
            results=notes,
            total_count=len(notes),
            query_time_ms=query_time_ms
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error searching notes: {str(e)}"
        )


@router.post("/canvas", response_model=CanvasResponse, status_code=status.HTTP_201_CREATED)
async def create_canvas(
    canvas: CanvasCreate,
    memory_selector: MemorySelectorDep
) -> CanvasResponse:
    """
    Create a new canvas in Basic Memory
    """
    try:
        # Prepare data for storage
        canvas_data = {
            "name": canvas.name,
            "nodes": canvas.nodes,
            "edges": canvas.edges
        }
        
        # Store in Basic Memory using memory selector
        result = memory_selector.store(
            data=canvas_data,
            task_type=TaskType.STORE_CANVAS,
            context={"operation": "create_canvas"}
        )
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create canvas in Basic Memory"
            )
        
        return CanvasResponse(
            id=result.get("canvas_id", "unknown"),
            name=canvas.name,
            nodes=canvas.nodes,
            edges=canvas.edges,
            created_at=result.get("created_at"),
            updated_at=result.get("updated_at")
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating canvas: {str(e)}"
        )


@router.delete("/notes/{note_id}")
async def delete_note(
    note_id: str,
    memory_selector: MemorySelectorDep
) -> Dict[str, str]:
    """
    Delete a note
    """
    try:
        # Delete from Basic Memory using memory selector
        result = memory_selector.delete(
            item_id=note_id,
            task_type=TaskType.DELETE_NOTE,
            context={"operation": "delete_note"}
        )
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Note '{note_id}' not found"
            )
        
        return {"message": f"Note '{note_id}' deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting note: {str(e)}"
        )