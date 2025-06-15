"""
Generate Postman collection for Unified Memory Server API
"""
import json
from typing import Dict, Any, List


def create_postman_collection() -> Dict[str, Any]:
    """Create a Postman collection for the Unified Memory Server API"""
    
    collection = {
        "info": {
            "name": "Unified Memory Server",
            "description": "A unified AI memory server integrating Neo4j, Basic Memory, and Redis Memory Server",
            "version": "1.0.0",
            "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
        },
        "variable": [
            {
                "key": "baseUrl",
                "value": "http://localhost:8000",
                "type": "string"
            },
            {
                "key": "mcpUrl", 
                "value": "http://localhost:9000",
                "type": "string"
            }
        ],
        "item": []
    }
    
    # Health Check endpoints
    health_folder = {
        "name": "Health Checks",
        "description": "System health and status endpoints",
        "item": [
            {
                "name": "Health Check",
                "request": {
                    "method": "GET",
                    "header": [],
                    "url": {
                        "raw": "{{baseUrl}}/health/",
                        "host": ["{{baseUrl}}"],
                        "path": ["health", ""]
                    },
                    "description": "Get overall system health status"
                },
                "response": []
            },
            {
                "name": "Readiness Check",
                "request": {
                    "method": "GET", 
                    "header": [],
                    "url": {
                        "raw": "{{baseUrl}}/health/ready",
                        "host": ["{{baseUrl}}"],
                        "path": ["health", "ready"]
                    },
                    "description": "Check if server is ready to accept requests"
                },
                "response": []
            },
            {
                "name": "Liveness Check",
                "request": {
                    "method": "GET",
                    "header": [],
                    "url": {
                        "raw": "{{baseUrl}}/health/live",
                        "host": ["{{baseUrl}}"], 
                        "path": ["health", "live"]
                    },
                    "description": "Check if server is alive"
                },
                "response": []
            }
        ]
    }
    
    # Neo4j endpoints
    neo4j_folder = {
        "name": "Neo4j Graph Database",
        "description": "Neo4j graph database operations for entities and relationships",
        "item": [
            {
                "name": "Create Entity",
                "request": {
                    "method": "POST",
                    "header": [
                        {
                            "key": "Content-Type",
                            "value": "application/json"
                        }
                    ],
                    "body": {
                        "mode": "raw",
                        "raw": json.dumps({
                            "name": "John Doe",
                            "type": "Person", 
                            "properties": {
                                "email": "john.doe@example.com",
                                "role": "Software Engineer",
                                "department": "Engineering"
                            }
                        }, indent=2)
                    },
                    "url": {
                        "raw": "{{baseUrl}}/api/v1/entities",
                        "host": ["{{baseUrl}}"],
                        "path": ["api", "v1", "entities"]
                    },
                    "description": "Create a new entity in the Neo4j graph database"
                },
                "response": []
            },
            {
                "name": "Create Relationship", 
                "request": {
                    "method": "POST",
                    "header": [
                        {
                            "key": "Content-Type",
                            "value": "application/json"
                        }
                    ],
                    "body": {
                        "mode": "raw",
                        "raw": json.dumps({
                            "from_entity": "John Doe",
                            "to_entity": "AI Project Alpha",
                            "relation_type": "WORKS_ON",
                            "properties": {
                                "start_date": "2024-01-15",
                                "role": "Lead Developer",
                                "commitment": "full-time"
                            }
                        }, indent=2)
                    },
                    "url": {
                        "raw": "{{baseUrl}}/api/v1/relations",
                        "host": ["{{baseUrl}}"],
                        "path": ["api", "v1", "relations"]
                    },
                    "description": "Create a relationship between entities"
                },
                "response": []
            },
            {
                "name": "Search Graph",
                "request": {
                    "method": "POST",
                    "header": [
                        {
                            "key": "Content-Type", 
                            "value": "application/json"
                        }
                    ],
                    "body": {
                        "mode": "raw",
                        "raw": json.dumps({
                            "query": "Find all people working on AI projects",
                            "limit": 10,
                            "node_types": ["Person", "Project"]
                        }, indent=2)
                    },
                    "url": {
                        "raw": "{{baseUrl}}/api/v1/graph/search",
                        "host": ["{{baseUrl}}"],
                        "path": ["api", "v1", "graph", "search"]
                    },
                    "description": "Search the graph using natural language queries"
                },
                "response": []
            }
        ]
    }
    
    # Redis Memory endpoints
    redis_folder = {
        "name": "Redis Memory Server",
        "description": "Redis memory operations for semantic search and sessions",
        "item": [
            {
                "name": "Create Memory",
                "request": {
                    "method": "POST",
                    "header": [
                        {
                            "key": "Content-Type",
                            "value": "application/json"
                        }
                    ],
                    "body": {
                        "mode": "raw",
                        "raw": json.dumps({
                            "text": "Python is a high-level programming language known for its simplicity and readability",
                            "namespace": "programming",
                            "topics": ["python", "programming", "languages"],
                            "entities": ["Python"],
                            "metadata": {
                                "source": "user_input",
                                "importance": "high"
                            }
                        }, indent=2)
                    },
                    "url": {
                        "raw": "{{baseUrl}}/api/v1/memories",
                        "host": ["{{baseUrl}}"],
                        "path": ["api", "v1", "memories"]
                    },
                    "description": "Create a new memory in Redis memory system"
                },
                "response": []
            },
            {
                "name": "Search Memories",
                "request": {
                    "method": "POST",
                    "header": [
                        {
                            "key": "Content-Type",
                            "value": "application/json"
                        }
                    ],
                    "body": {
                        "mode": "raw",
                        "raw": json.dumps({
                            "query": "programming languages",
                            "namespace": "programming",
                            "limit": 5
                        }, indent=2)
                    },
                    "url": {
                        "raw": "{{baseUrl}}/api/v1/memories/search",
                        "host": ["{{baseUrl}}"],
                        "path": ["api", "v1", "memories", "search"]
                    },
                    "description": "Search memories using semantic search"
                },
                "response": []
            }
        ]
    }
    
    # Basic Memory endpoints  
    basic_memory_folder = {
        "name": "Basic Memory System",
        "description": "Basic Memory operations for notes and documents",
        "item": [
            {
                "name": "Create Note",
                "request": {
                    "method": "POST",
                    "header": [
                        {
                            "key": "Content-Type",
                            "value": "application/json"
                        }
                    ],
                    "body": {
                        "mode": "raw",
                        "raw": json.dumps({
                            "title": "Project Meeting Notes",
                            "content": "# Meeting Notes\n\n## Attendees\n- John Doe\n- Jane Smith\n\n## Discussion\n- Project timeline\n- Resource allocation",
                            "tags": ["meeting", "project", "notes"]
                        }, indent=2)
                    },
                    "url": {
                        "raw": "{{baseUrl}}/api/v1/notes",
                        "host": ["{{baseUrl}}"],
                        "path": ["api", "v1", "notes"]
                    },
                    "description": "Create a new note in Basic Memory"
                },
                "response": []
            },
            {
                "name": "Search Notes",
                "request": {
                    "method": "POST",
                    "header": [
                        {
                            "key": "Content-Type",
                            "value": "application/json"
                        }
                    ],
                    "body": {
                        "mode": "raw",
                        "raw": json.dumps({
                            "query": "meeting notes",
                            "limit": 10
                        }, indent=2)
                    },
                    "url": {
                        "raw": "{{baseUrl}}/api/v1/search/notes",
                        "host": ["{{baseUrl}}"],
                        "path": ["api", "v1", "search", "notes"]
                    },
                    "description": "Search notes using full-text search"
                },
                "response": []
            }
        ]
    }
    
    # MCP Server endpoints
    mcp_folder = {
        "name": "MCP Server",
        "description": "Model Context Protocol server endpoints",
        "item": [
            {
                "name": "MCP Health Check",
                "request": {
                    "method": "GET",
                    "header": [],
                    "url": {
                        "raw": "{{mcpUrl}}/health",
                        "host": ["{{mcpUrl}}"],
                        "path": ["health"]
                    },
                    "description": "Check MCP server health"
                },
                "response": []
            },
            {
                "name": "MCP Tools List",
                "request": {
                    "method": "POST",
                    "header": [
                        {
                            "key": "Content-Type",
                            "value": "application/json"
                        }
                    ],
                    "body": {
                        "mode": "raw",
                        "raw": json.dumps({
                            "jsonrpc": "2.0",
                            "id": 1,
                            "method": "tools/list",
                            "params": {}
                        }, indent=2)
                    },
                    "url": {
                        "raw": "{{mcpUrl}}/sse",
                        "host": ["{{mcpUrl}}"],
                        "path": ["sse"]
                    },
                    "description": "Get list of available MCP tools"
                },
                "response": []
            },
            {
                "name": "WebSocket Status",
                "request": {
                    "method": "GET",
                    "header": [],
                    "url": {
                        "raw": "{{mcpUrl}}/ws/status",
                        "host": ["{{mcpUrl}}"],
                        "path": ["ws", "status"]
                    },
                    "description": "Get WebSocket connection status"
                },
                "response": []
            }
        ]
    }
    
    # Add all folders to collection
    collection["item"] = [
        health_folder,
        neo4j_folder,
        redis_folder,
        basic_memory_folder,
        mcp_folder
    ]
    
    return collection


def save_postman_collection(filename: str = "unified-memory-server.postman_collection.json"):
    """Save Postman collection to file"""
    collection = create_postman_collection()
    
    with open(filename, 'w') as f:
        json.dump(collection, f, indent=2)
    
    print(f"✓ Postman collection saved to {filename}")
    return filename


if __name__ == "__main__":
    save_postman_collection()