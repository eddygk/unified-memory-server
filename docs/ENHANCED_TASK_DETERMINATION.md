# Enhanced Task Determination Logic

## Overview

The enhanced task determination logic in `memory_selector.py` provides sophisticated intent recognition that goes beyond simple keyword matching. This implementation addresses the requirements outlined in Section 5 of the `IMPLEMENTATION_AND_ACCURACY_PLAN.md`.

## Key Improvements

### 1. IntentAnalyzer Class

The new `IntentAnalyzer` class provides advanced pattern matching and entity extraction capabilities:

```python
class IntentAnalyzer:
    """Advanced intent analyzer for sophisticated task determination"""
```

#### Features:
- **Regex Pattern Matching**: Uses compiled regular expressions for efficient pattern recognition
- **Entity Extraction**: Identifies key entities (user, project, document, relationship, conversation, memory)
- **Operation Type Detection**: Classifies operations as CREATE, READ, UPDATE, DELETE, SEARCH, or ANALYZE
- **Confidence Scoring**: Provides confidence levels for better decision making
- **Contextual Analysis**: Considers temporal markers and complexity indicators

## 2. Analyze Patterns
- "analyze the data"
- "examine the relationships"
- "investigate the patterns"
- "study the connections"
- "assess the information"
- "evaluate the results"

## 3. Pattern-Based Recognition

#### Relationship Patterns
- "how are X connected to Y"
- "find relationships between"
- "map the connections"
- "trace the path from X to Y"

#### User Identity Patterns  
- "who is this user"
- "my profile information"
- "tell me about the user"

#### Documentation Patterns
- "create comprehensive documentation"
- "generate detailed guide"
- "write structured report"

#### Conversation Context Patterns
- "remember our previous conversation"
- "what did we discuss earlier"
- "conversation history"

#### Search Patterns
- "find similar content"
- "search for related documents"
- "semantic search"

## 4. Entity Extraction

The system identifies key entities from task text:
- **User**: user, person, individual, me, myself, i
- **Project**: projects, tasks, assignments, work, jobs
- **Document**: documents, files, notes, papers, reports, guides, documentation
- **Relationship**: relationships, connections, links, associations, bonds
- **Conversation**: conversations, chats, discussions, talks, dialogues
- **Memory**: memory, memories, remember, recall, stored

## 5. Operation Type Classification

Operations are automatically classified:
- **CREATE**: create, make, generate, add, new, build, establish, form
- **READ**: get, retrieve, fetch, show, display, find, read, view, see
- **UPDATE**: update, modify, change, edit, revise, alter, adjust
- **DELETE**: delete, remove, clear, erase, drop, eliminate
- **SEARCH**: search, find, look, locate, seek, query, explore (with similarity keywords)
- **ANALYZE**: analyze, examine, investigate, study, assess, evaluate

## 6. Confidence Scoring

The system provides confidence scores (0.0 to 1.0) based on:
- Pattern matches (each pattern adds 0.2-0.4 to confidence)
- Entity presence (each relevant entity adds 0.1-0.3)
- Context indicators (complexity, temporal markers add 0.2)
- Explicit language ("between", "connected", "linked" add 0.2)

## 7. Fallback Mechanism

- Enhanced analysis is used by default
- If confidence < 0.3, falls back to legacy keyword matching
- Logs fallback usage via CAB tracker for monitoring
- Maintains backward compatibility

## API Changes

### New Methods

#### `get_task_analysis(task, context=None) -> TaskAnalysis`
Returns detailed analysis including:
- `task_type`: Determined TaskType
- `operation_type`: Detected OperationType
- `entities`: List of extracted entities
- `confidence`: Confidence score (0.0-1.0)
- `reasoning`: Human-readable explanation
- `patterns_matched`: List of matched patterns

### Enhanced Methods

#### `analyze_task(task, context=None) -> TaskType`
- Now uses sophisticated pattern matching
- Provides confidence-based fallback
- Integrates with CAB tracker for monitoring
- Maintains same interface for backward compatibility

## Examples

### Basic Usage
```python
from src.memory_selector import MemorySelector

selector = MemorySelector()

# Simple task type determination
task_type = selector.analyze_task("Find relationships between users and projects")
# Returns: TaskType.RELATIONSHIP_QUERY

# Detailed analysis
analysis = selector.get_task_analysis("Create comprehensive documentation")
print(f"Type: {analysis.task_type.value}")           # documentation
print(f"Operation: {analysis.operation_type.value}") # create
print(f"Confidence: {analysis.confidence:.2f}")      # 1.00
print(f"Entities: {analysis.entities}")              # ['document']
```

### Context-Based Hints
```python
# Using context for better determination
context = {"needs_persistence": True}
task_type = selector.analyze_task("Store this data", context)
# Returns: TaskType.PERSISTENT_KNOWLEDGE
```

### Complex Examples
```python
# Complex relationship query
analysis = selector.get_task_analysis("How are team members connected to this project?")
# Type: relationship_query, Operation: read, Confidence: 0.60

# Temporal conversation context
analysis = selector.get_task_analysis("What did we discuss yesterday?")
# Type: conversation_context, Operation: read, Confidence: 0.70

# Semantic search with entities
analysis = selector.get_task_analysis("Find documents similar to this one")
# Type: semantic_search, Operation: search, Confidence: 0.60
```

## Integration with CAB Tracker

The enhanced system integrates with the CAB tracker to log:
- Low confidence analyses (< 0.5)
- Fallback usage to legacy analysis
- Performance metrics for continuous improvement

## Performance Characteristics

- **Accuracy**: Significantly improved over keyword matching
- **Speed**: Compiled regex patterns ensure fast execution
- **Confidence**: Provides measurable confidence for decision making
- **Extensibility**: Easy to add new patterns and entity types
- **Monitoring**: Full integration with CAB tracker for optimization

## Testing

Comprehensive test suite available in `test_enhanced_memory_selector.py`:
- Basic functionality tests
- Operation type detection tests
- Confidence scoring validation
- Context hint testing
- Entity extraction verification
- Fallback mechanism validation
- Legacy vs enhanced comparison

Run tests with:
```bash
python test_enhanced_memory_selector.py
```

## Future Enhancements

Potential areas for further improvement:
1. **Machine Learning Integration**: Train models on historical routing decisions
2. **Semantic Embeddings**: Use vector similarity for intent matching
3. **Multi-language Support**: Extend patterns for other languages
4. **Domain-specific Patterns**: Add patterns for specific use cases
5. **User Feedback Integration**: Learn from user corrections and preferences

## Migration Guide

The enhanced system is fully backward compatible:
- Existing code using `analyze_task()` will work unchanged
- Enhanced features are opt-in via `get_task_analysis()`
- Legacy analysis remains available as fallback
- No breaking changes to existing APIs

## Conclusion

The enhanced task determination logic provides a significant improvement over simple keyword matching while maintaining compatibility and providing detailed insights into the decision-making process. The pattern-based approach with confidence scoring enables more intelligent routing decisions and better system observability.