"""
Unified Memory Server Python SDK

A simple Python client library for interacting with the Unified Memory Server API.
"""
import json
import time
from typing import Dict, Any, List, Optional, Union
from enum import Enum

try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False
    import urllib.request
    import urllib.parse


class MemorySystem(Enum):
    """Available memory systems"""
    NEO4J = "neo4j"
    REDIS = "redis"
    BASIC_MEMORY = "basic_memory"


class UnifiedMemoryClient:
    """Client for Unified Memory Server API"""
    
    def __init__(self, base_url: str = "http://localhost:8000", mcp_url: str = "http://localhost:9000", 
                 timeout: int = 30, api_key: Optional[str] = None):
        """
        Initialize the client
        
        Args:
            base_url: Base URL for the REST API (default: http://localhost:8000)
            mcp_url: Base URL for the MCP server (default: http://localhost:9000)  
            timeout: Request timeout in seconds (default: 30)
            api_key: Optional API key for authentication
        """
        self.base_url = base_url.rstrip('/')
        self.mcp_url = mcp_url.rstrip('/')
        self.timeout = timeout
        self.api_key = api_key
        
        self.headers = {
            "Content-Type": "application/json",
            "User-Agent": "unified-memory-python-sdk/1.0.0"
        }
        
        if api_key:
            self.headers["Authorization"] = f"Bearer {api_key}"
        
        if HTTPX_AVAILABLE:
            self.client = httpx.Client(timeout=timeout, headers=self.headers)
        else:
            self.client = None
    
    def _make_request(self, method: str, url: str, data: Optional[Dict] = None) -> Dict[str, Any]:
        """Make HTTP request using available library"""
        if HTTPX_AVAILABLE and self.client:
            try:
                if method.upper() == "GET":
                    response = self.client.get(url)
                elif method.upper() == "POST":
                    response = self.client.post(url, json=data)
                else:
                    raise ValueError(f"Unsupported method: {method}")
                
                response.raise_for_status()
                return response.json()
            except httpx.HTTPError as e:
                raise ConnectionError(f"HTTP request failed: {e}")
        else:
            # Fallback to urllib
            try:
                req_data = None
                if data:
                    req_data = json.dumps(data).encode('utf-8')
                
                request = urllib.request.Request(
                    url, 
                    data=req_data,
                    headers=self.headers,
                    method=method.upper()
                )
                
                with urllib.request.urlopen(request, timeout=self.timeout) as response:
                    return json.loads(response.read().decode('utf-8'))
            except Exception as e:
                raise ConnectionError(f"HTTP request failed: {e}")
    
    # Health Check Methods
    def health_check(self) -> Dict[str, Any]:
        """Get system health status"""
        return self._make_request("GET", f"{self.base_url}/health/")
    
    def readiness_check(self) -> Dict[str, Any]:
        """Check if server is ready"""
        return self._make_request("GET", f"{self.base_url}/health/ready")
    
    def liveness_check(self) -> Dict[str, Any]:
        """Check if server is alive"""
        return self._make_request("GET", f"{self.base_url}/health/live")
    
    # Neo4j Graph Database Methods
    def create_entity(self, name: str, entity_type: str, properties: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Create a new entity in Neo4j
        
        Args:
            name: Entity name
            entity_type: Entity type (e.g., "Person", "Project")
            properties: Optional entity properties
            
        Returns:
            Created entity details
        """
        data = {
            "name": name,
            "type": entity_type,
            "properties": properties or {}
        }
        return self._make_request("POST", f"{self.base_url}/api/v1/entities", data)
    
    def create_relationship(self, from_entity: str, to_entity: str, relation_type: str, 
                          properties: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Create a relationship between entities in Neo4j
        
        Args:
            from_entity: Source entity name
            to_entity: Target entity name
            relation_type: Relationship type (e.g., "WORKS_ON", "BELONGS_TO")
            properties: Optional relationship properties
            
        Returns:
            Created relationship details
        """
        data = {
            "from_entity": from_entity,
            "to_entity": to_entity,
            "relation_type": relation_type,
            "properties": properties or {}
        }
        return self._make_request("POST", f"{self.base_url}/api/v1/relations", data)
    
    def search_graph(self, query: str, limit: int = 10, node_types: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Search the Neo4j graph using natural language
        
        Args:
            query: Natural language search query
            limit: Maximum number of results
            node_types: Optional filter by node types
            
        Returns:
            Search results
        """
        data = {
            "query": query,
            "limit": limit
        }
        if node_types:
            data["node_types"] = node_types
            
        return self._make_request("POST", f"{self.base_url}/api/v1/graph/search", data)
    
    # Redis Memory Methods
    def create_memory(self, text: str, namespace: str = "default", topics: Optional[List[str]] = None,
                     entities: Optional[List[str]] = None, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Create a new memory in Redis
        
        Args:
            text: Memory text content
            namespace: Memory namespace
            topics: Optional topics/tags
            entities: Optional associated entities
            metadata: Optional metadata
            
        Returns:
            Created memory details
        """
        data = {
            "text": text,
            "namespace": namespace,
            "topics": topics or [],
            "entities": entities or [],
            "metadata": metadata or {}
        }
        return self._make_request("POST", f"{self.base_url}/api/v1/memories", data)
    
    def search_memories(self, query: str, namespace: str = "default", limit: int = 10) -> Dict[str, Any]:
        """
        Search memories using semantic search
        
        Args:
            query: Search query
            namespace: Search namespace
            limit: Maximum number of results
            
        Returns:
            Search results
        """
        data = {
            "query": query,
            "namespace": namespace,
            "limit": limit
        }
        return self._make_request("POST", f"{self.base_url}/api/v1/memories/search", data)
    
    # Basic Memory Methods
    def create_note(self, title: str, content: str, tags: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Create a new note in Basic Memory
        
        Args:
            title: Note title
            content: Note content in markdown
            tags: Optional tags
            
        Returns:
            Created note details
        """
        data = {
            "title": title,
            "content": content,
            "tags": tags or []
        }
        return self._make_request("POST", f"{self.base_url}/api/v1/notes", data)
    
    def search_notes(self, query: str, limit: int = 10) -> Dict[str, Any]:
        """
        Search notes using full-text search
        
        Args:
            query: Search query
            limit: Maximum number of results
            
        Returns:
            Search results
        """
        data = {
            "query": query,
            "limit": limit
        }
        return self._make_request("POST", f"{self.base_url}/api/v1/search/notes", data)
    
    # MCP Methods
    def mcp_health_check(self) -> Dict[str, Any]:
        """Check MCP server health"""
        return self._make_request("GET", f"{self.mcp_url}/health")
    
    def mcp_tools_list(self) -> Dict[str, Any]:
        """Get list of available MCP tools"""
        data = {
            "jsonrpc": "2.0",
            "id": int(time.time()),
            "method": "tools/list",
            "params": {}
        }
        return self._make_request("POST", f"{self.mcp_url}/sse", data)
    
    def mcp_call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Call an MCP tool
        
        Args:
            tool_name: Name of the tool to call
            arguments: Tool arguments
            
        Returns:
            Tool execution result
        """
        data = {
            "jsonrpc": "2.0",
            "id": int(time.time()),
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments
            }
        }
        return self._make_request("POST", f"{self.mcp_url}/sse", data)
    
    def websocket_status(self) -> Dict[str, Any]:
        """Get WebSocket connection status"""
        return self._make_request("GET", f"{self.mcp_url}/ws/status")
    
    # Convenience Methods
    def store_knowledge(self, content: str, knowledge_type: str = "general", 
                       system: Optional[MemorySystem] = None) -> Dict[str, Any]:
        """
        Store knowledge using the most appropriate memory system
        
        Args:
            content: Content to store
            knowledge_type: Type of knowledge (affects system selection)
            system: Force specific memory system
            
        Returns:
            Storage result
        """
        if system == MemorySystem.NEO4J or ("entity" in knowledge_type.lower() or "relationship" in knowledge_type.lower()):
            # Use Neo4j for structured knowledge
            return self.create_entity(
                name=f"Knowledge-{int(time.time())}",
                entity_type="Knowledge",
                properties={"content": content, "type": knowledge_type}
            )
        elif system == MemorySystem.BASIC_MEMORY or ("note" in knowledge_type.lower() or "document" in knowledge_type.lower()):
            # Use Basic Memory for document-like content
            return self.create_note(
                title=f"Knowledge: {knowledge_type}",
                content=content,
                tags=[knowledge_type]
            )
        else:
            # Default to Redis for general memory
            return self.create_memory(
                text=content,
                topics=[knowledge_type],
                metadata={"type": knowledge_type}
            )
    
    def search_all(self, query: str, limit: int = 5) -> Dict[str, List[Dict[str, Any]]]:
        """
        Search across all memory systems
        
        Args:
            query: Search query
            limit: Results per system
            
        Returns:
            Combined search results from all systems
        """
        results = {
            "neo4j": [],
            "redis": [],
            "basic_memory": []
        }
        
        try:
            graph_results = self.search_graph(query, limit)
            results["neo4j"] = graph_results.get("results", [])
        except Exception as e:
            results["neo4j"] = [{"error": str(e)}]
        
        try:
            memory_results = self.search_memories(query, limit=limit)
            results["redis"] = memory_results.get("results", [])
        except Exception as e:
            results["redis"] = [{"error": str(e)}]
        
        try:
            note_results = self.search_notes(query, limit)
            results["basic_memory"] = note_results.get("results", [])
        except Exception as e:
            results["basic_memory"] = [{"error": str(e)}]
        
        return results
    
    def close(self):
        """Close the client and cleanup resources"""
        if HTTPX_AVAILABLE and self.client:
            self.client.close()


# Example usage
if __name__ == "__main__":
    # Create client
    client = UnifiedMemoryClient()
    
    try:
        # Check system health
        health = client.health_check()
        print(f"System Status: {health.get('status', 'unknown')}")
        
        # Create an entity
        entity = client.create_entity(
            name="Alice Johnson",
            entity_type="Person",
            properties={
                "role": "Data Scientist",
                "department": "AI Research"
            }
        )
        print(f"Created entity: {entity}")
        
        # Create a memory
        memory = client.create_memory(
            text="Alice is working on a new machine learning model for sentiment analysis",
            topics=["machine-learning", "sentiment-analysis"],
            entities=["Alice Johnson"]
        )
        print(f"Created memory: {memory}")
        
        # Search across all systems
        results = client.search_all("Alice machine learning")
        print(f"Search results: {results}")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        client.close()