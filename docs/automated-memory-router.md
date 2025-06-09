# Automated Memory System Router

The Automated Memory System Router is an intelligent routing system that automatically selects the appropriate memory system (Neo4j, Basic Memory, or Redis) based on request analysis, eliminating the need for manual decision-making.

## Overview

The router analyzes incoming requests using multiple techniques:
- **Intent Analysis**: Identifies the purpose of the request using pattern matching
- **Entity Extraction**: Extracts relevant entities and their types
- **Performance Tracking**: Monitors system performance and adapts routing decisions
- **Context Awareness**: Uses request context to improve routing accuracy

## Key Components

### 1. IntentAnalyzer
Classifies requests into intent categories:
- **Relationship Operations**: CREATE_RELATION, QUERY_RELATION, TRAVERSE_GRAPH
- **Documentation Operations**: WRITE_DOC, READ_DOC, UPDATE_DOC  
- **Search Operations**: SEMANTIC_SEARCH, CONTEXT_RETRIEVAL, MEMORY_LOOKUP  
- **Multi-System Operations**: SYNC_DATA, CROSS_REFERENCE, COMPREHENSIVE_STORE  
- **General**: UNKNOWN  

### 2. EntityExtractor
Identifies entities in requests:
- **Person**: User names, mentions (@username)
- **Project**: Project names and initiatives
- **Document**: File names and documents
- **Concept**: Ideas and abstract concepts
- **Organization**: Company and organization names

### 3. PerformanceTracker
Monitors system performance:
- Success rates for each memory system
- Average response times
- Operation counts and recent history
- Adaptive scoring based on performance

### 4. RoutingEngine
Makes final routing decisions:
- Scores each system based on intent, entities, and performance
- Detects multi-system operations
- Provides reasoning for decisions

## Usage

### Basic Usage

```python
from src.automated_memory_router import AutomatedMemoryRouter, MemoryRequest, Operation

# Initialize router
router = AutomatedMemoryRouter()

# Create a request
request = MemoryRequest(
    operation=Operation.STORE,
    content="Connect John Smith to the Marketing project",
    context={'operation': Operation.STORE.value}
)

# Get routing decision
decision = router.route(request)
print(f"Route to: {decision.primary_system.value}")
print(f"Confidence: {decision.confidence:.2f}")
```

### Store Data

```python
# Store data with automatic routing
data = {"user": "John", "project": "Alpha"}
content = "Store user project relationship"

result, system, used_fallback = router.store_data(data, content)
print(f"Stored in: {system.value}")
```

### Retrieve Data

```python
# Retrieve data with automatic routing
query = {"search": "project relationships"}
content = "Find project relationships"

result, system, used_fallback = router.retrieve_data(query, content)
print(f"Retrieved from: {system.value}")
```

## Routing Examples

### Relationship Operations → Neo4j
```python
# These requests route to Neo4j for graph operations
requests = [
    "Connect Alice to the DevOps team",
    "How is John related to Project Alpha?",
    "Find the path from user to organization"
]
```

### Documentation Operations → Basic Memory
```python
# These requests route to Basic Memory for document storage
requests = [
    "Create comprehensive documentation for the API",
    "Write notes about the meeting",
    "Read the project requirements document"
]
```

### Search Operations → Redis
```python
# These requests route to Redis for fast search and context
requests = [
    "Find documents similar to machine learning",
    "Remember what we discussed yesterday",
    "Search for user preferences"
]
```

### Multi-System Operations
```python
# These requests use multiple systems
requests = [
    "Store complete profile information for this user",
    "Get everything about Project Alpha",
    "Save comprehensive user data"
]
```

## Performance Monitoring

```python
# Get routing statistics
stats = router.get_routing_stats()

# Check system performance
for system, metrics in stats['system_performance'].items():
    print(f"{system}: {metrics['success_rate']:.1%} success, "
          f"{metrics['avg_response_time']:.0f}ms avg")

# Performance tracking adapts routing decisions automatically
```

## Integration with Existing Systems

The AutomatedMemoryRouter builds on the existing MemorySelector:
- Uses existing fallback mechanisms
- Integrates with CAB tracking
- Maintains compatibility with current storage methods
- Preserves all configuration and validation logic

## Configuration

The router uses the same configuration as MemorySelector:
- Environment variables for system URLs and credentials
- CAB tracking settings
- Fallback chain configuration

## Benefits

1. **Zero Manual Decisions**: No need to choose memory systems manually
2. **Performance Adaptive**: Learns from system performance and adapts
3. **Consistent Routing**: Same patterns always route the same way
4. **Multi-System Intelligence**: Can use multiple systems when beneficial
5. **Automatic Fallbacks**: Built-in retry logic when systems fail
6. **Explainable Decisions**: Provides reasoning for each routing choice

## Migration from Manual Routing

To migrate from manual routing:

1. Replace `MemorySelector` with `AutomatedMemoryRouter`
2. Update code to use `MemoryRequest` objects
3. Remove manual system selection logic
4. Optionally add request context for better routing

```python
# Before (manual)
selector = MemorySelector()
system, task_type = selector.select_memory_system("Store user data")

# After (automated)
router = AutomatedMemoryRouter()
request = MemoryRequest(operation="store", content="Store user data")
decision = router.route(request)
```

## Success Metrics

The router aims to achieve:
- **Routing accuracy**: > 95%
- **Performance improvement**: > 20%
- **Zero manual routing decisions**: Fully automated
- **Reduced CAB suggestions**: Fewer routing-related issues

## Demo Script

Run the example script to see the router in action:

```bash
python example_automated_router.py
```

This demonstrates:
- Various routing scenarios
- Performance tracking and adaptation
- Entity extraction capabilities
- Multi-system coordination

## Future Enhancements

Phase 2+ enhancements will include:
- Machine learning for pattern recognition
- Advanced entity relationship modeling
- Cross-system data synchronization
- Real-time performance optimization
- Custom routing rules and overrides