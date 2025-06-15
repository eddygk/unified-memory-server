# Unified Memory Server Python SDK

A Python client library for interacting with the Unified Memory Server API.

## Installation

```bash
# Copy the SDK file to your project
cp unified_memory_sdk.py /path/to/your/project/

# Optional: Install httpx for better HTTP handling
pip install httpx
```

## Quick Start

```python
from unified_memory_sdk import UnifiedMemoryClient

# Create client
client = UnifiedMemoryClient(
    base_url="http://localhost:8000",  # REST API
    mcp_url="http://localhost:9000"    # MCP Server
)

try:
    # Check system health
    health = client.health_check()
    print(f"System Status: {health['status']}")
    
    # Create an entity in Neo4j
    entity = client.create_entity(
        name="Alice Johnson",
        entity_type="Person",
        properties={
            "role": "Data Scientist",
            "department": "AI Research"
        }
    )
    
    # Create a memory in Redis
    memory = client.create_memory(
        text="Alice is working on a new machine learning model",
        topics=["machine-learning", "ai"],
        entities=["Alice Johnson"]
    )
    
    # Create a note in Basic Memory
    note = client.create_note(
        title="Project Meeting Notes",
        content="# Meeting Notes\n\n- Discussed ML model architecture\n- Next steps defined",
        tags=["meeting", "project"]
    )
    
    # Search across all systems
    results = client.search_all("Alice machine learning")
    print(f"Found results in:")
    for system, data in results.items():
        print(f"  {system}: {len(data)} results")

finally:
    client.close()
```

## Features

### Health Monitoring
```python
# Check overall system health
health = client.health_check()

# Check if server is ready for requests
ready = client.readiness_check()

# Check if server is alive
alive = client.liveness_check()
```

### Neo4j Graph Operations
```python
# Create entities
person = client.create_entity("John Doe", "Person", {"age": 30})
project = client.create_entity("AI Assistant", "Project", {"status": "active"})

# Create relationships
relationship = client.create_relationship(
    "John Doe", "AI Assistant", "WORKS_ON",
    {"role": "Lead Developer", "since": "2024-01-01"}
)

# Search graph
results = client.search_graph("Find all developers working on AI projects")
```

### Redis Memory Operations
```python
# Store memories
memory = client.create_memory(
    text="The team decided to use transformer architecture",
    namespace="project-alpha",
    topics=["architecture", "transformers"],
    entities=["team", "project-alpha"]
)

# Search memories
results = client.search_memories("transformer architecture", namespace="project-alpha")
```

### Basic Memory Notes
```python
# Create notes
note = client.create_note(
    title="Architecture Decision Record",
    content="# ADR-001: Use Transformer Architecture\n\n## Decision\nWe will use...",
    tags=["adr", "architecture"]
)

# Search notes
results = client.search_notes("transformer decision")
```

### MCP Protocol
```python
# Get available tools
tools = client.mcp_tools_list()

# Call MCP tools
result = client.mcp_call_tool("create_memory", {
    "text": "Important information",
    "namespace": "default"
})

# Check WebSocket status
ws_status = client.websocket_status()
```

### Convenience Methods

#### Smart Storage
```python
# Automatically choose the best memory system
client.store_knowledge("Alice is a data scientist", "entity")  # → Neo4j
client.store_knowledge("Meeting notes from today", "document")  # → Basic Memory  
client.store_knowledge("Important fact about AI", "general")   # → Redis
```

#### Cross-System Search
```python
# Search all memory systems at once
results = client.search_all("machine learning", limit=10)
# Returns: {"neo4j": [...], "redis": [...], "basic_memory": [...]}
```

## Configuration

### Authentication
```python
client = UnifiedMemoryClient(
    base_url="https://memory.your-domain.com",
    api_key="your-api-key-here"
)
```

### Custom Timeouts
```python
client = UnifiedMemoryClient(
    timeout=60  # 60 second timeout
)
```

### HTTP Library
The SDK automatically uses `httpx` if available, falls back to `urllib` otherwise:

```bash
# For better performance and features
pip install httpx
```

## Error Handling

```python
try:
    entity = client.create_entity("Test", "Person")
except ConnectionError as e:
    print(f"Network error: {e}")
except Exception as e:
    print(f"API error: {e}")
```

## API Reference

### Core Methods

#### Health
- `health_check()` - Get system health status
- `readiness_check()` - Check if server is ready
- `liveness_check()` - Check if server is alive

#### Neo4j
- `create_entity(name, type, properties)` - Create graph entity
- `create_relationship(from, to, type, properties)` - Create relationship
- `search_graph(query, limit, node_types)` - Search graph

#### Redis Memory
- `create_memory(text, namespace, topics, entities, metadata)` - Store memory
- `search_memories(query, namespace, limit)` - Search memories

#### Basic Memory
- `create_note(title, content, tags)` - Create note
- `search_notes(query, limit)` - Search notes

#### MCP
- `mcp_health_check()` - Check MCP server
- `mcp_tools_list()` - List available tools
- `mcp_call_tool(name, args)` - Call MCP tool
- `websocket_status()` - WebSocket connection status

#### Utilities
- `store_knowledge(content, type, system)` - Smart storage
- `search_all(query, limit)` - Cross-system search
- `close()` - Cleanup resources

## Examples

See the included example usage in the SDK file, or check the main repository for more comprehensive examples.