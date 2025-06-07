# Automated Memory Router - Phase 1 Implementation

## Overview

The Automated Memory Router replaces the previous manual decision-making process for memory system selection with intelligent, pattern-based routing. This implementation represents Phase 1 of the enhancement proposal.

## Key Features

### 1. Enhanced Intent Analysis

The router now uses sophisticated pattern matching to classify requests into 15+ intent categories:

#### Relationship Operations (→ Neo4j)
- `CREATE_RELATION`: "Create connection between user and project"
- `QUERY_RELATION`: "Find relationships between entities" 
- `TRAVERSE_GRAPH`: "Show path from user to task"

#### Documentation Operations (→ Basic Memory)
- `WRITE_DOC`: "Write a comprehensive document"
- `READ_DOC`: "Read the user manual"
- `UPDATE_DOC`: "Update existing documentation"

#### Search Operations (→ Redis)
- `SEMANTIC_SEARCH`: "Find similar conversations"
- `CONTEXT_RETRIEVAL`: "Get recent context"
- `MEMORY_LOOKUP`: "Remember my preferences"

#### Multi-System Operations
- `COMPREHENSIVE_STORE`: "Store complete profile"
- `CROSS_REFERENCE`: "Sync across systems"

### 2. Pattern Matching Rules

The router uses multiple pattern types for intent detection:

```python
# Keywords: Direct word matching
keywords=["create", "establish", "link", "connect"]

# Entity Patterns: Regex-based entity relationship detection  
entity_patterns=["user.* connects to .*", ".* works on .*"]

# Query Types: Question pattern recognition
query_types=["who", "how are .* related", "what connects"]

# Temporal Markers: Time-based context
temporal_markers=["recent", "today", "this session"]

# Content Indicators: Document/content type hints
content_indicators=["markdown", "formatted text", "long form"]
```

### 3. Enhanced CAB Integration

The router provides detailed tracking and suggestions:

- **Routing Decisions**: Logs intent classification and system selection
- **Performance Metrics**: Tracks analysis time and system performance
- **Unknown Patterns**: Identifies requests that need new pattern rules
- **Fallback Analysis**: Reports when primary systems fail

## Usage

### Basic Usage

```python
from memory_selector import AutomatedMemoryRouter

# Initialize router
router = AutomatedMemoryRouter(cab_tracker)

# Automatic routing
system, intent = router.select_memory_system("Find user relationships")
print(f"Intent: {intent.value}, System: {system.value}")
# Output: Intent: query_relation, System: neo4j
```

### With Fallback

```python
def operation(system, task, context):
    # Your operation logic here
    return f"Result from {system.value}"

result, successful_system, used_fallback = router.execute_with_fallback(
    "Create user profile",
    operation
)
```

### Context-Based Routing

```python
# Context provides additional hints
context = {
    "needs_persistence": True,
    "is_relational": False,
    "is_temporary": False
}

system, intent = router.select_memory_system(
    "Store this information", 
    context
)
```

## Backward Compatibility

The router maintains full backward compatibility:

```python
# Old code continues to work
from memory_selector import MemorySelector

selector = MemorySelector()  # Actually creates AutomatedMemoryRouter
system, task_type = selector.select_memory_system("Find relationships")
```

## Performance Benefits

- **Consistent Routing**: Same patterns always route the same way
- **Enhanced Accuracy**: Pattern matching improves over simple keywords
- **Better Fallbacks**: Intelligent error handling and reporting
- **CAB Analytics**: Detailed insights for optimization

## Testing

Run the test suite to validate functionality:

```bash
python3 tests/test_automated_router.py
```

Test coverage includes:
- Intent analysis accuracy
- Pattern matching capabilities  
- Routing decision validation
- Fallback mechanism testing
- Backward compatibility verification

## Configuration

No configuration changes required. The router uses the same system selection rules with enhanced intelligence.

## Next Steps (Phase 2)

1. **Entity Extraction**: Identify and classify entities in requests
2. **Scoring Algorithms**: Weighted scoring for system selection
3. **Performance Tracking**: Historical data-based optimization
4. **ML Enhancements**: Machine learning for pattern recognition

## CAB Tracking

The router generates these CAB suggestion types:

- `Routing Analysis`: Intent detection results
- `Automated Routing Decision`: System selection rationale
- `Unknown Routing Pattern`: Requests needing new patterns
- `Slow Routing Analysis`: Performance optimization opportunities
- `Successful Routing`: Pattern validation
- `Complete System Failure`: Critical error analysis

## Troubleshooting

### Unknown Intents

If tasks are frequently classified as `UNKNOWN`:

1. Check CAB suggestions for common unmatched patterns
2. Add new pattern rules to `IntentAnalyzer._initialize_patterns()`
3. Test new patterns with the test suite

### Incorrect Routing

If routing decisions seem wrong:

1. Review pattern matching scores in CAB logs
2. Adjust pattern weights or add more specific patterns
3. Use context parameters to provide additional hints

### Performance Issues

If routing is slow:

1. Check CAB suggestions for "Slow Routing Analysis"
2. Optimize regex patterns for efficiency
3. Consider caching for repeated requests