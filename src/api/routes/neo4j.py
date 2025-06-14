"""
Neo4j graph database endpoints
"""
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from ...core.dependencies import MemorySelectorDep
from ...memory_selector import TaskType

router = APIRouter()


class EntityCreate(BaseModel):
    """Entity creation request"""
    name: str = Field(..., description="Entity name")
    type: str = Field(..., description="Entity type")
    properties: Dict[str, Any] = Field(default_factory=dict, description="Entity properties")


class EntityResponse(BaseModel):
    """Entity response"""
    id: str
    name: str
    type: str
    properties: Dict[str, Any]


class RelationCreate(BaseModel):
    """Relation creation request"""
    from_entity: str = Field(..., description="Source entity name")
    to_entity: str = Field(..., description="Target entity name")
    relation_type: str = Field(..., description="Relationship type")
    properties: Dict[str, Any] = Field(default_factory=dict, description="Relationship properties")


class RelationResponse(BaseModel):
    """Relation response"""
    id: str
    from_entity: str
    to_entity: str
    relation_type: str
    properties: Dict[str, Any]


class GraphSearchRequest(BaseModel):
    """Graph search request"""
    query: str = Field(..., description="Natural language search query")
    limit: int = Field(default=10, description="Maximum number of results")
    node_types: Optional[List[str]] = Field(default=None, description="Filter by node types")


class GraphSearchResponse(BaseModel):
    """Graph search response"""
    results: List[Dict[str, Any]]
    total_count: int
    query_time_ms: float


@router.post("/entities", response_model=EntityResponse, status_code=status.HTTP_201_CREATED)
async def create_entity(
    entity: EntityCreate,
    memory_selector: MemorySelectorDep
) -> EntityResponse:
    """
    Create a new entity in the Neo4j graph database
    """
    try:
        # Prepare data for storage
        entity_data = {
            "entities": [{
                "name": entity.name,
                "type": entity.type,
                "properties": entity.properties
            }]
        }
        
        # Store in Neo4j using memory selector
        result = memory_selector.store(
            data=entity_data,
            task_type=TaskType.STORE_ENTITY,
            context={"operation": "create_entity"}
        )
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create entity in Neo4j"
            )
        
        # Return created entity
        return EntityResponse(
            id=result.get("entity_id", "unknown"),
            name=entity.name,
            type=entity.type,
            properties=entity.properties
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating entity: {str(e)}"
        )


@router.post("/relations", response_model=RelationResponse, status_code=status.HTTP_201_CREATED)
async def create_relation(
    relation: RelationCreate,
    memory_selector: MemorySelectorDep
) -> RelationResponse:
    """
    Create a new relationship between entities in the Neo4j graph
    """
    try:
        # Prepare data for storage
        relation_data = {
            "relations": [{
                "from": relation.from_entity,
                "to": relation.to_entity,
                "type": relation.relation_type,
                "properties": relation.properties
            }]
        }
        
        # Store in Neo4j using memory selector
        result = memory_selector.store(
            data=relation_data,
            task_type=TaskType.STORE_RELATION,
            context={"operation": "create_relation"}
        )
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create relationship in Neo4j"
            )
        
        return RelationResponse(
            id=result.get("relation_id", "unknown"),
            from_entity=relation.from_entity,
            to_entity=relation.to_entity,
            relation_type=relation.relation_type,
            properties=relation.properties
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating relationship: {str(e)}"
        )


@router.post("/graph/search", response_model=GraphSearchResponse)
async def search_graph(
    search_request: GraphSearchRequest,
    memory_selector: MemorySelectorDep
) -> GraphSearchResponse:
    """
    Search the Neo4j graph using natural language queries
    """
    try:
        import time
        start_time = time.time()
        
        # Retrieve from Neo4j using memory selector
        result = memory_selector.retrieve(
            query=search_request.query,
            task_type=TaskType.SEARCH_NODES,
            context={
                "operation": "graph_search",
                "limit": search_request.limit,
                "node_types": search_request.node_types
            }
        )
        
        end_time = time.time()
        query_time_ms = (end_time - start_time) * 1000
        
        if not result:
            return GraphSearchResponse(
                results=[],
                total_count=0,
                query_time_ms=query_time_ms
            )
        
        # Extract results
        results = result.get("results", [])
        total_count = len(results)
        
        # Limit results if requested
        if search_request.limit and search_request.limit < total_count:
            results = results[:search_request.limit]
        
        return GraphSearchResponse(
            results=results,
            total_count=total_count,
            query_time_ms=query_time_ms
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error searching graph: {str(e)}"
        )


@router.get("/entities/{entity_name}")
async def get_entity(
    entity_name: str,
    memory_selector: MemorySelectorDep
) -> EntityResponse:
    """
    Get a specific entity by name
    """
    try:
        # Retrieve entity from Neo4j
        result = memory_selector.retrieve(
            query=f"Find entity named {entity_name}",
            task_type=TaskType.SEARCH_NODES,
            context={
                "operation": "get_entity",
                "entity_name": entity_name
            }
        )
        
        if not result or not result.get("results"):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Entity '{entity_name}' not found"
            )
        
        entity_data = result["results"][0]
        
        return EntityResponse(
            id=entity_data.get("id", "unknown"),
            name=entity_data.get("name", entity_name),
            type=entity_data.get("type", "unknown"),
            properties=entity_data.get("properties", {})
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving entity: {str(e)}"
        )