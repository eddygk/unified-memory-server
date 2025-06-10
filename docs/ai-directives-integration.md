# AI Directives Integration Guide

This document explains how the Unified Memory Server has been enhanced with intelligent memory management directives that work seamlessly with any AI assistant, including Claude Desktop.

## Overview

The AI Directives Integration provides universal AI assistant support with:

1. **MCP Tool Name Compliance**: All tools follow the `local__<server-name>__<tool-name>` format
2. **Decision Tree Routing**: Implements intelligent decision tree for optimal routing
3. **Startup Sequence**: Multi-system user identification and CAB initialization
4. **Cross-System Integration**: Intelligent data propagation and consistency
5. **Enhanced CAB Tracking**: AI-specific monitoring and suggestions

## Core Components

### 1. MCPToolRouter (`src/mcp_tool_router.py`)

Implements the intelligent decision tree for optimal routing:

```
├─ Does the task involve relationships/connections between entities?
│  └─ YES → Use Neo4j tools
├─ Does the task require comprehensive documentation/structured notes?
│  └─ YES → Use Basic Memory tools
└─ Does the task need conversational context/semantic search?
   └─ YES → Use Redis Memory tools
```

**Key Features:**
- Intent analysis with pattern matching
- MCP tool name validation and generation
- Priority-based tool recommendations
- JSON-serializable metrics for CAB tracking

**Usage:**
```python
from mcp_tool_router import MCPToolRouter

router = MCPToolRouter(cab_tracker)
decision = router.route_task("Find relationships between user and project")
print(decision["primary_tool"].mcp_name)  # local__neo4j-memory__search_nodes
```

### 2. StartupSequenceHandler (`src/startup_sequence.py`)

Executes the intelligent startup sequence for any AI assistant:

**Step 0: Initialize CAB Tracking**
- Create CAB suggestions file at specified location
- Log session initialization in Redis Memory
- Track all system improvements and issues

**Step 1: Multi-System User Identification**
1. Primary: Neo4j natural language query for user profile
2. Fallback 1: Redis Memory search in "user_profile" namespace
3. Fallback 2: Basic Memory search for "user identity" notes
4. Action: Sync user data across all systems if found in only one

**Usage:**
```python
from startup_sequence import StartupSequenceHandler

handler = StartupSequenceHandler(memory_selector, cab_tracker, mcp_router)
results = handler.execute_startup_sequence("Username", "Assistant")
```

### 3. AIDirectivesIntegration (`src/ai_directives_integration.py`)

Main integration layer that enhances the existing MemorySelector:

**Key Features:**
- Enhanced routing with directive compliance
- Cross-system data propagation
- MCP tool name generation and validation
- AI assistant compliance assessment
- Silent execution (no exposed complexity to users)

**Usage:**
```python
from ai_directives_integration import AIDirectivesIntegration

integration = AIDirectivesIntegration(enable_startup_sequence=True)
results = integration.execute_startup_sequence("User", "Assistant")
routing = integration.route_with_directives("Create user relationships")
```

## MCP Tool Mappings

All tools follow the universal MCP naming convention and work with any AI assistant that supports MCP (Model Context Protocol):

### Neo4j Memory Tools
- `local__neo4j-memory__create_entities` (Priority 5 - Entity creation)
- `local__neo4j-memory__create_relations` (Priority 2 - Relationships)
- `local__neo4j-memory__search_nodes` (Priority 2 - Relationships)
- `local__neo4j-memory__read_graph` (Priority 2 - Relationships)

### Neo4j Cypher Tools
- `local__neo4j-cypher__read_neo4j_cypher` (Priority 1 - User identity)
- `local__neo4j-cypher__write_neo4j_cypher` (Priority 1 - User identity)
- `local__neo4j-cypher__get_neo4j_schema` (Priority 1 - User identity)

### Basic Memory Tools
- `local__basic-memory__write_note` (Priority 3 - Documentation)
- `local__basic-memory__read_note` (Priority 3 - Documentation)
- `local__basic-memory__search_notes` (Priority 3 - Documentation)
- `local__basic-memory__canvas` (Priority 3 - Documentation)

### Redis Memory Tools
- `local__redis-memory-server__create_long_term_memories` (Priority 6 - Quick memories)
- `local__redis-memory-server__search_long_term_memory` (Priority 4 - Context retrieval)
- `local__redis-memory-server__hydrate_memory_prompt` (Priority 4 - Context retrieval)

## Priority-Based Task Routing

| Priority | Task Type | Primary System | Primary Tool | Fallback Chain |
|----------|-----------|----------------|--------------|----------------|
| 1 | User identity | Neo4j | `local__neo4j-cypher__read_neo4j_cypher` | Redis → Basic Memory |
| 2 | Relationships | Neo4j | `local__neo4j-memory__create_relations` | None |
| 3 | Documentation | Basic Memory | `local__basic-memory__write_note` | Redis snippets |
| 4 | Context retrieval | Redis | `local__redis-memory-server__hydrate_memory_prompt` | Search memories |
| 5 | Entity creation | Neo4j | `local__neo4j-memory__create_entities` | Basic Memory note |
| 6 | Quick memories | Redis | `local__redis-memory-server__create_long_term_memories` | Basic Memory note |

## Integration Patterns

### Cross-System Data Propagation

When storing important information:
1. Store in primary system based on data type
2. Create cross-references in other systems
3. Maintain consistency across all three systems

```python
# Example: User preference discovery
integration.store_data_with_directives(
    {"user": "preferences", "theme": "dark"},
    "Store user preferences"
)
# Automatically propagates to appropriate systems
```

### Error Handling with Directive Fallbacks

```python
try:
    result = integration.retrieve_data_with_directives(
        {"search": "user profile"}, 
        "Find user information"
    )
except Exception as e:
    # Enhanced error handling with directive-specific fallbacks
    # CAB tracker logs the issue for system improvement
```

## CAB Tracking Integration

The system logs AI assistant specific suggestions:

- **MCP Intent Analysis**: Intent classification and confidence
- **Tool Routing Decisions**: Primary tool selection and fallbacks
- **Cross-System Operations**: Data propagation and sync events
- **Startup Sequence Events**: User identification and initialization
- **Compliance Assessment**: Alignment between MCP and traditional routing

## Compliance Levels

1. **FULL_COMPLIANCE**: Startup sequence completed, all systems operational
2. **PARTIAL_COMPLIANCE**: Some systems operational, partial functionality  
3. **BASIC_FUNCTIONALITY**: Fallback to traditional MemorySelector behavior

## Testing

Run the comprehensive test suite:
```bash
python -m pytest tests/test_ai_directives.py -v
```

Run the interactive demo:
```bash
python ai_directives_demo.py
```

## Configuration

The AI directives integration uses the same configuration as the base MemorySelector:

```env
# Neo4j Configuration
NEO4J_ENABLED=true
NEO4J_URL=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your_password

# Redis Configuration
REDIS_URL=redis://localhost:6379

# Basic Memory Configuration
BASIC_MEMORY_ENABLED=true
BASIC_MEMORY_PATH=/path/to/obsidian/vault
```

## Best Practices

1. **Silent Execution**: Never expose system complexity to users
2. **Tool Name Compliance**: Always use proper MCP format for universal compatibility
3. **CAB Tracking**: Log all optimization opportunities
4. **Cross-System Sync**: Maintain data consistency across all memory systems
5. **Graceful Degradation**: Fall back to traditional routing if needed

## Example Usage

```python
#!/usr/bin/env python3
from ai_directives_integration import AIDirectivesIntegration

# Initialize with startup sequence
integration = AIDirectivesIntegration(enable_startup_sequence=True)

# Execute startup (silently)
startup_results = integration.execute_startup_sequence("Alice", "Assistant")

# Route tasks using AI directives
routing = integration.route_with_directives("Find Alice's project relationships")
print(f"Recommended tool: {routing['mcp_decision']['primary_tool'].mcp_name}")

# Store data with cross-system propagation
result, system, fallback = integration.store_data_with_directives(
    {"user_id": "alice", "project": "unified-memory"},
    "Link user to project"
)

# Retrieve data with enhanced search
result, system, fallback = integration.retrieve_data_with_directives(
    {"search": "alice projects"},
    "Find user's projects"
)

# Check compliance status
summary = integration.get_directive_summary()
print(f"Compliance level: {summary['compliance_level']}")
```

## Integration with Existing Code

The AI directives integration is designed to enhance, not replace, existing functionality and works with any AI assistant:

- **MemorySelector**: Enhanced with intelligent routing
- **CABTracker**: Extended with AI-specific logging  
- **Existing Tests**: All continue to work
- **Configuration**: No changes required
- **APIs**: Backward compatible

This ensures a smooth transition while adding powerful new capabilities for universal AI assistant integration.