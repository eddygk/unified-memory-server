"""
Main FastAPI application for Unified Memory Server
"""
import os
import logging
from contextlib import asynccontextmanager
from typing import Dict, Any

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

from .api.routes import neo4j, basic_memory, redis_memory, health
from .core.config import get_settings
from .core.dependencies import get_memory_selector
from .memory_selector import MemorySelector
from .cab_tracker import CABTracker

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    logger.info("Starting Unified Memory Server")
    
    # Initialize CAB tracker
    try:
        cab_tracker = CABTracker()
    except Exception as e:
        logger.warning(f"Failed to initialize CAB tracker: {e}")
        cab_tracker = None
    
    # Initialize memory selector 
    try:
        memory_selector = MemorySelector(cab_tracker=cab_tracker, validate_config=False)
    except Exception as e:
        logger.error(f"Failed to initialize memory selector: {e}")
        # Create a minimal memory selector for basic functionality
        from .memory_selector import MockCabTracker
        mock_cab = MockCabTracker()
        memory_selector = MemorySelector(cab_tracker=mock_cab, validate_config=False)
    
    # Store in app state
    app.state.memory_selector = memory_selector
    app.state.cab_tracker = cab_tracker or memory_selector.cab_tracker
    
    logger.info("Unified Memory Server started successfully")
    yield
    
    # Shutdown
    logger.info("Shutting down Unified Memory Server")


def create_app() -> FastAPI:
    """Create and configure FastAPI application"""
    settings = get_settings()
    
    app = FastAPI(
        title="Unified Memory Server",
        description="""
A unified AI memory server integrating Neo4j, Basic Memory, and Redis Memory Server.

## Features

- **Neo4j Graph Database**: Store and query entities and relationships
- **Basic Memory System**: Manage notes, documents, and projects  
- **Redis Memory Server**: Semantic search and session management
- **Intelligent Routing**: Automatic selection of optimal memory system
- **Fallback Support**: Automatic failover between memory systems
- **MCP Protocol**: Model Context Protocol support for AI agents
- **Real-time Updates**: WebSocket and SSE support

## Memory Systems

### Neo4j (Graph Database)
Perfect for storing entities and relationships. Use for:
- User profiles and connections
- Project hierarchies and dependencies
- Knowledge graphs and semantic networks

### Basic Memory (Document Storage)
Ideal for structured content. Use for:
- Notes and documentation
- Project files and resources
- Canvas and creative work

### Redis Memory (Semantic Search)
Optimized for search and sessions. Use for:
- Conversational memory
- Semantic similarity search
- Session state management

## Authentication

Currently running in development mode with authentication disabled.
In production, OAuth2/JWT authentication will be required.
        """,
        version="1.0.0",
        lifespan=lifespan,
        docs_url="/docs" if settings.ENABLE_SWAGGER_UI else None,
        redoc_url="/redoc" if settings.ENABLE_SWAGGER_UI else None,
        contact={
            "name": "Unified Memory Server Team",
            "url": "https://github.com/eddygk/unified-memory-server",
            "email": "support@memory-server.local"
        },
        license_info={
            "name": "MIT",
            "url": "https://opensource.org/licenses/MIT"
        },
        openapi_tags=[
            {
                "name": "health",
                "description": "Health check and system status endpoints"
            },
            {
                "name": "neo4j", 
                "description": "Neo4j graph database operations - entities and relationships"
            },
            {
                "name": "basic-memory",
                "description": "Basic Memory system operations - notes and documents"
            },
            {
                "name": "redis-memory",
                "description": "Redis Memory operations - semantic search and sessions"
            }
        ]
    )
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Include routers
    app.include_router(health.router, prefix="/health", tags=["health"])
    app.include_router(neo4j.router, prefix="/api/v1", tags=["neo4j"])
    app.include_router(basic_memory.router, prefix="/api/v1", tags=["basic-memory"])
    app.include_router(redis_memory.router, prefix="/api/v1", tags=["redis-memory"])
    
    @app.exception_handler(Exception)
    async def global_exception_handler(request, exc):
        logger.error(f"Global exception handler caught: {exc}")
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"}
        )
    
    return app


def main():
    """Main entry point"""
    settings = get_settings()
    
    uvicorn.run(
        "src.main:create_app",
        factory=True,
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
        access_log=True,
    )


if __name__ == "__main__":
    main()