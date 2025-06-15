"""
MCP (Model Context Protocol) Server for Unified Memory Server

This module implements an MCP server that provides SSE (Server-Sent Events) endpoint
for AI agents to connect and interact with the unified memory systems.
"""
import asyncio
import json
import logging
import time
from typing import Any, Dict, List, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, HTTPException, BackgroundTasks, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from .core.config import get_settings
from .core.dependencies import get_memory_selector
from .memory_selector import MemorySelector, TaskType, MockCabTracker

logger = logging.getLogger(__name__)


class MCPServer:
    """MCP Server implementation for unified memory access"""
    
    def __init__(self, memory_selector: MemorySelector):
        self.memory_selector = memory_selector
        self.active_connections: Dict[str, WebSocket] = {}
        self.connection_counter = 0
        
    async def connect_websocket(self, websocket: WebSocket) -> str:
        """Connect a new WebSocket client"""
        await websocket.accept()
        connection_id = f"conn_{self.connection_counter}"
        self.connection_counter += 1
        self.active_connections[connection_id] = websocket
        logger.info(f"WebSocket client connected: {connection_id}")
        return connection_id
    
    async def disconnect_websocket(self, connection_id: str):
        """Disconnect a WebSocket client"""
        if connection_id in self.active_connections:
            del self.active_connections[connection_id]
            logger.info(f"WebSocket client disconnected: {connection_id}")
    
    async def broadcast_event(self, event: Dict[str, Any]):
        """Broadcast an event to all connected WebSocket clients"""
        if not self.active_connections:
            return
        
        message = json.dumps(event)
        disconnected_clients = []
        
        for connection_id, websocket in self.active_connections.items():
            try:
                await websocket.send_text(message)
            except Exception as e:
                logger.warning(f"Failed to send message to {connection_id}: {e}")
                disconnected_clients.append(connection_id)
        
        # Clean up disconnected clients
        for connection_id in disconnected_clients:
            await self.disconnect_websocket(connection_id)
        
    async def handle_websocket_message(self, websocket: WebSocket, message: str) -> Optional[Dict[str, Any]]:
        """Handle incoming WebSocket message"""
        try:
            request_data = json.loads(message)
            response = await self.handle_mcp_request(request_data)
            return response
        except json.JSONDecodeError:
            return {
                "jsonrpc": "2.0",
                "id": None,
                "error": {
                    "code": -32700,
                    "message": "Parse error: Invalid JSON"
                }
            }
        except Exception as e:
            logger.error(f"Error handling WebSocket message: {e}")
            return {
                "jsonrpc": "2.0",
                "id": None,
                "error": {
                    "code": -32603,
                    "message": f"Internal error: {str(e)}"
                }
            }
    async def handle_mcp_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle incoming MCP request and route to appropriate memory system"""
        try:
            # Validate basic MCP structure
            if not isinstance(request_data, dict):
                return self._create_error_response(None, -32600, "Invalid Request: not a dict")
            
            method = request_data.get("method", "")
            params = request_data.get("params", {})
            request_id = request_data.get("id", 1)
            jsonrpc = request_data.get("jsonrpc", "")
            
            # Validate JSON-RPC version
            if jsonrpc != "2.0":
                return self._create_error_response(request_id, -32600, "Invalid Request: jsonrpc must be '2.0'")
            
            # Validate method
            if not method or not isinstance(method, str):
                return self._create_error_response(request_id, -32600, "Invalid Request: method required")
            
            # Log the request for monitoring
            logger.info(f"Processing MCP request: {method} (id: {request_id})")
            
            # Route based on method name
            if method == "tools/list":
                return await self._handle_tools_list(request_id)
            elif method == "tools/call":
                return await self._handle_tool_call(request_id, params)
            elif method == "resources/list":
                return await self._handle_resources_list(request_id)
            elif method == "resources/read":
                return await self._handle_resource_read(request_id, params)
            else:
                return self._create_error_response(request_id, -32601, f"Method not found: {method}")
                
        except Exception as e:
            logger.error(f"Error handling MCP request: {e}")
            return self._create_error_response(
                request_data.get("id", 1) if isinstance(request_data, dict) else 1,
                -32603,
                f"Internal error: {str(e)}"
            )
    
    def _create_error_response(self, request_id: Any, code: int, message: str) -> Dict[str, Any]:
        """Create a standardized error response"""
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {
                "code": code,
                "message": message
            }
        }
    
    async def _handle_tools_list(self, request_id: int) -> Dict[str, Any]:
        """Return list of available tools"""
        tools = [
            {
                "name": "create_memory",
                "description": "Create a new memory in Redis memory system",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "text": {"type": "string", "description": "Memory text content"},
                        "namespace": {"type": "string", "description": "Memory namespace", "default": "default"},
                        "topics": {"type": "array", "items": {"type": "string"}, "description": "Memory topics"},
                        "entities": {"type": "array", "items": {"type": "string"}, "description": "Associated entities"}
                    },
                    "required": ["text"]
                }
            },
            {
                "name": "search_memories",
                "description": "Search memories using semantic search",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Search query"},
                        "namespace": {"type": "string", "description": "Search namespace", "default": "default"},
                        "limit": {"type": "integer", "description": "Maximum results", "default": 10}
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "create_entity",
                "description": "Create a new entity in Neo4j graph database",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string", "description": "Entity name"},
                        "type": {"type": "string", "description": "Entity type"},
                        "properties": {"type": "object", "description": "Entity properties"}
                    },
                    "required": ["name", "type"]
                }
            },
            {
                "name": "create_relation",
                "description": "Create a relationship between entities in Neo4j",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "from_entity": {"type": "string", "description": "Source entity name"},
                        "to_entity": {"type": "string", "description": "Target entity name"},
                        "relation_type": {"type": "string", "description": "Relationship type"},
                        "properties": {"type": "object", "description": "Relationship properties"}
                    },
                    "required": ["from_entity", "to_entity", "relation_type"]
                }
            },
            {
                "name": "search_graph",
                "description": "Search the Neo4j graph using natural language",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Natural language search query"},
                        "limit": {"type": "integer", "description": "Maximum results", "default": 10}
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "create_note",
                "description": "Create a new note in Basic Memory",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string", "description": "Note title"},
                        "content": {"type": "string", "description": "Note content in markdown"},
                        "tags": {"type": "array", "items": {"type": "string"}, "description": "Note tags"}
                    },
                    "required": ["title", "content"]
                }
            },
            {
                "name": "search_notes",
                "description": "Search notes in Basic Memory",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Search query"},
                        "limit": {"type": "integer", "description": "Maximum results", "default": 10}
                    },
                    "required": ["query"]
                }
            }
        ]
        
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {"tools": tools}
        }
    
    async def _handle_tool_call(self, request_id: int, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle tool call and execute the requested operation"""
        tool_name = params.get("name", "")
        arguments = params.get("arguments", {})
        
        try:
            if tool_name == "create_memory":
                result = await self._create_memory(arguments)
            elif tool_name == "search_memories":
                result = await self._search_memories(arguments)
            elif tool_name == "create_entity":
                result = await self._create_entity(arguments)
            elif tool_name == "create_relation":
                result = await self._create_relation(arguments)
            elif tool_name == "search_graph":
                result = await self._search_graph(arguments)
            elif tool_name == "create_note":
                result = await self._create_note(arguments)
            elif tool_name == "search_notes":
                result = await self._search_notes(arguments)
            else:
                raise ValueError(f"Unknown tool: {tool_name}")
            
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps(result, indent=2)
                        }
                    ]
                }
            }
            
        except Exception as e:
            logger.error(f"Error executing tool {tool_name}: {e}")
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": -32603,
                    "message": f"Tool execution error: {str(e)}"
                }
            }
    
    async def _create_memory(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Create memory using memory selector"""
        memory_data = {
            "text": args["text"],
            "namespace": args.get("namespace", "default"),
            "topics": args.get("topics", []),
            "entities": args.get("entities", []),
            "metadata": args.get("metadata", {})
        }
        
        result = self.memory_selector.store(
            data=memory_data,
            task_type=TaskType.STORE_MEMORY,
            context={"operation": "mcp_create_memory"}
        )
        
        return {"status": "created", "result": result}
    
    async def _search_memories(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Search memories using memory selector"""
        result = self.memory_selector.retrieve(
            query=args["query"],
            task_type=TaskType.SEARCH_MEMORY,
            context={
                "operation": "mcp_search_memories",
                "namespace": args.get("namespace", "default"),
                "limit": args.get("limit", 10)
            }
        )
        
        return {"results": result.get("results", []) if result else []}
    
    async def _create_entity(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Create entity using memory selector"""
        entity_data = {
            "entities": [{
                "name": args["name"],
                "type": args["type"],
                "properties": args.get("properties", {})
            }]
        }
        
        result = self.memory_selector.store(
            data=entity_data,
            task_type=TaskType.STORE_ENTITY,
            context={"operation": "mcp_create_entity"}
        )
        
        return {"status": "created", "result": result}
    
    async def _create_relation(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Create relation using memory selector"""
        relation_data = {
            "relations": [{
                "from": args["from_entity"],
                "to": args["to_entity"],
                "type": args["relation_type"],
                "properties": args.get("properties", {})
            }]
        }
        
        result = self.memory_selector.store(
            data=relation_data,
            task_type=TaskType.STORE_RELATION,
            context={"operation": "mcp_create_relation"}
        )
        
        return {"status": "created", "result": result}
    
    async def _search_graph(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Search graph using memory selector"""
        result = self.memory_selector.retrieve(
            query=args["query"],
            task_type=TaskType.SEARCH_NODES,
            context={
                "operation": "mcp_search_graph",
                "limit": args.get("limit", 10)
            }
        )
        
        return {"results": result.get("results", []) if result else []}
    
    async def _create_note(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Create note using memory selector"""
        note_data = {
            "title": args["title"],
            "content": args["content"],
            "tags": args.get("tags", [])
        }
        
        result = self.memory_selector.store(
            data=note_data,
            task_type=TaskType.STORE_NOTE,
            context={"operation": "mcp_create_note"}
        )
        
        return {"status": "created", "result": result}
    
    async def _search_notes(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Search notes using memory selector"""
        result = self.memory_selector.retrieve(
            query=args["query"],
            task_type=TaskType.SEARCH_NOTES,
            context={
                "operation": "mcp_search_notes",
                "limit": args.get("limit", 10)
            }
        )
        
        return {"results": result.get("results", []) if result else []}
    
    async def _handle_resources_list(self, request_id: int) -> Dict[str, Any]:
        """Return list of available resources"""
        resources = [
            {
                "uri": "memory://system/status",
                "name": "System Status",
                "description": "Current status of all memory systems",
                "mimeType": "application/json"
            },
            {
                "uri": "memory://config/settings",
                "name": "Configuration Settings",
                "description": "Current configuration settings",
                "mimeType": "application/json"
            }
        ]
        
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {"resources": resources}
        }
    
    async def _handle_resource_read(self, request_id: int, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle resource read request"""
        uri = params.get("uri", "")
        
        if uri == "memory://system/status":
            # Return system status
            status = {
                "timestamp": time.time(),
                "systems": {
                    "redis": "available",
                    "neo4j": "available",
                    "basic_memory": "available"
                }
            }
            content = json.dumps(status, indent=2)
        elif uri == "memory://config/settings":
            # Return configuration (excluding sensitive data)
            settings = get_settings()
            safe_config = {
                "host": settings.HOST,
                "port": settings.PORT,
                "mcp_port": settings.MCP_PORT,
                "debug": settings.DEBUG,
                "neo4j_enabled": settings.NEO4J_ENABLED,
                "basic_memory_enabled": settings.BASIC_MEMORY_ENABLED
            }
            content = json.dumps(safe_config, indent=2)
        else:
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": -32601,
                    "message": f"Resource not found: {uri}"
                }
            }
        
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "contents": [
                    {
                        "uri": uri,
                        "mimeType": "application/json",
                        "text": content
                    }
                ]
            }
        }


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    logger.info("Starting MCP Server")
    
    # Initialize CAB tracker
    try:
        from .cab_tracker import CABTracker
        cab_tracker = CABTracker()
    except Exception as e:
        logger.warning(f"Failed to initialize CAB tracker: {e}")
        cab_tracker = MockCabTracker()
    
    # Initialize memory selector
    memory_selector = MemorySelector(cab_tracker=cab_tracker, validate_config=False)
    
    # Initialize MCP server
    mcp_server = MCPServer(memory_selector)
    
    # Store in app state
    app.state.mcp_server = mcp_server
    app.state.memory_selector = memory_selector
    app.state.cab_tracker = cab_tracker
    
    logger.info("MCP Server started successfully")
    yield
    
    # Shutdown
    logger.info("Shutting down MCP Server")


def create_mcp_app() -> FastAPI:
    """Create and configure MCP FastAPI application"""
    settings = get_settings()
    
    app = FastAPI(
        title="Unified Memory Server - MCP",
        description="MCP (Model Context Protocol) server for unified memory access",
        version="1.0.0",
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc"
    )
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # More permissive for MCP clients
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    @app.get("/health")
    async def health_check():
        """Health check endpoint"""
        return {"status": "healthy", "timestamp": time.time()}
    
    @app.post("/sse")
    async def sse_endpoint(request: Request):
        """SSE (Server-Sent Events) endpoint for MCP communication"""
        try:
            body = await request.json()
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid JSON")
        
        mcp_server = request.app.state.mcp_server
        response = await mcp_server.handle_mcp_request(body)
        
        return response
    
    @app.get("/sse/stream")
    async def sse_stream(request: Request):
        """Streaming SSE endpoint for real-time communication"""
        async def event_generator():
            try:
                while True:
                    # Send periodic ping to keep connection alive
                    yield f"data: {json.dumps({'type': 'ping', 'timestamp': time.time()})}\n\n"
                    await asyncio.sleep(30)
            except asyncio.CancelledError:
                logger.info("SSE connection closed")
                raise
        
        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "*",
            }
        )
    
    @app.websocket("/ws")
    async def websocket_endpoint(websocket: WebSocket):
        """WebSocket endpoint for real-time MCP communication"""
        mcp_server = websocket.app.state.mcp_server
        connection_id = await mcp_server.connect_websocket(websocket)
        
        try:
            while True:
                # Receive message from client
                message = await websocket.receive_text()
                
                # Process the message
                response = await mcp_server.handle_websocket_message(websocket, message)
                
                # Send response back if needed
                if response:
                    await websocket.send_text(json.dumps(response))
                    
        except WebSocketDisconnect:
            await mcp_server.disconnect_websocket(connection_id)
        except Exception as e:
            logger.error(f"WebSocket error: {e}")
            await mcp_server.disconnect_websocket(connection_id)
    
    @app.get("/ws/status")
    async def websocket_status(request: Request):
        """Get WebSocket connection status"""
        mcp_server = request.app.state.mcp_server
        return {
            "active_connections": len(mcp_server.active_connections),
            "connection_ids": list(mcp_server.active_connections.keys())
        }
    
    return app


def main():
    """Main entry point for MCP server"""
    settings = get_settings()
    
    uvicorn.run(
        "src.mcp_server:create_mcp_app",
        factory=True,
        host=settings.HOST,
        port=settings.MCP_PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
        access_log=True,
    )


if __name__ == "__main__":
    main()