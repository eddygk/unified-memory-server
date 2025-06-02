# Memory System Selection Guide

## Overview

The Unified Memory Server provides three complementary memory systems, each optimized for different use cases. This guide helps you choose the right memory system for your specific needs.

## Quick Selection Matrix

| Use Case | Primary System | Secondary System | Rationale |
|----------|----------------|------------------|-----------|
| User identity & profile | Neo4j | Redis Memory | Graph relationships with cached access |
| Entity relationships | Neo4j | - | Native graph traversal capabilities |
| Conversation history | Redis Memory | - | Optimized for temporal data |
| User preferences | Redis Memory | Neo4j | Quick retrieval with relationship context |
| Documentation | Basic Memory | - | Structured markdown persistence |
| Semantic search | Redis Memory | Basic Memory | Vector embeddings with fallback |
| Complex queries | Neo4j | Redis Memory | Natural language graph queries |
| Session context | Redis Memory | - | Auto-summarization features |

## Decision Tree

```
IF task involves relationships or connections between entities
    → USE Neo4j (create_entities, create_relations, read_neo4j_cypher)
    
ELSE IF task requires comprehensive documentation or structured notes
    → USE Basic Memory (write_note, read_note)
    
ELSE IF task needs conversational context or semantic search
    → USE Redis Memory Server (hydrate_memory_prompt, search_long_term_memory)
```

## Detailed System Capabilities

### Neo4j Memory System

**Strengths:**
- Graph-based relationship modeling
- Natural language querying
- Complex relationship traversal
- Entity-centric data model
- ACID compliance for data integrity

**Best For:**
- User identity and profiles
- Social connections
- Knowledge graphs
- Hierarchical data
- Complex queries involving multiple relationships

**Example Use Cases:**
```python
# Finding all projects a user is involved in
query = "Find all projects where user Eddy has any role"
result = read_neo4j_cypher(query=query, query_type="natural_language")

# Creating entity relationships
create_relations(relations=[{
    "source": "Eddy",
    "target": "Unified Memory Project",
    "relationType": "CONTRIBUTES_TO"
}])
```

### Redis Memory Server

**Strengths:**
- High-performance caching
- Semantic similarity search
- Auto-summarization of older content
- Session management
- Real-time updates

**Best For:**
- Conversation history
- User preferences
- Quick semantic searches
- Session context
- Frequently accessed data

**Example Use Cases:**
```python
# Store conversation context
create_long_term_memories(payload={
    "memories": [{
        "text": "User prefers dark mode and serif fonts",
        "namespace": "preferences",
        "topics": ["ui", "settings"]
    }]
})

# Semantic search
results = search_long_term_memory(payload={
    "text": "What are the user's UI preferences?",
    "namespace": {"eq": "preferences"},
    "limit": 5
})
```

### Basic Memory (Obsidian)

**Strengths:**
- Markdown-based persistence
- Human-readable format
- Version control friendly
- Canvas support for visual thinking
- Folder organization

**Best For:**
- Comprehensive documentation
- Meeting notes
- Project documentation
- Knowledge base articles
- Visual concept mapping

**Example Use Cases:**
```python
# Create structured documentation
write_note(
    title="System Architecture",
    content="# System Architecture\n\n## Overview...",
    folder="docs/technical"
)

# Create visual canvas
canvas(
    title="Memory System Relationships",
    nodes=[...],
    edges=[...],
    folder="visualizations"
)
```

## Multi-System Patterns

### Pattern 1: User Profile Management
```python
# 1. Store core identity in Neo4j
create_entities(entities=[{
    "name": "user_123",
    "type": "User",
    "observations": ["Name: John Doe", "Role: Developer"]
}])

# 2. Cache preferences in Redis
create_long_term_memories(payload={
    "memories": [{
        "text": "Preferred IDE: VSCode, Theme: Dark",
        "namespace": "user_preferences",
        "user_id": "user_123"
    }]
})

# 3. Document detailed profile in Basic Memory
write_note(
    title="User Profile - John Doe",
    content="Comprehensive user documentation...",
    folder="users"
)
```

### Pattern 2: Project Documentation
```python
# 1. Create project entity in Neo4j
create_entities(entities=[{
    "name": "Project Alpha",
    "type": "Project",
    "observations": ["Status: Active", "Team Size: 5"]
}])

# 2. Link team members
create_relations(relations=[
    {"source": "John Doe", "target": "Project Alpha", "relationType": "MEMBER_OF"},
    {"source": "Jane Smith", "target": "Project Alpha", "relationType": "LEADS"}
])

# 3. Store project docs in Basic Memory
write_note(
    title="Project Alpha Specification",
    content="# Project Alpha\n\n## Overview...",
    folder="projects/alpha"
)

# 4. Cache frequently accessed info
create_long_term_memories(payload={
    "memories": [{
        "text": "Project Alpha deadline: Q2 2025, Priority: High",
        "namespace": "project_status",
        "topics": ["deadlines", "priorities"]
    }]
})
```

## Performance Considerations

### Response Time Expectations
- **Redis Memory**: 10-50ms (cached queries)
- **Neo4j**: 50-200ms (simple queries), 200-1000ms (complex traversals)
- **Basic Memory**: 100-500ms (file I/O dependent)

### Scalability Limits
- **Redis Memory**: Limited by available RAM (recommend 8-16GB)
- **Neo4j**: Handles millions of nodes/relationships
- **Basic Memory**: Limited by filesystem (thousands of documents)

## Troubleshooting Selection Issues

### Common Mistakes

1. **Using Basic Memory for frequently accessed data**
   - Problem: Slow retrieval times
   - Solution: Cache in Redis Memory

2. **Storing relationships in Redis**
   - Problem: No graph traversal capabilities
   - Solution: Move to Neo4j

3. **Using Neo4j for simple key-value storage**
   - Problem: Overhead for simple operations
   - Solution: Use Redis Memory

### Selection Checklist

Before choosing a memory system, ask:

- [ ] Does the data have relationships? → Consider Neo4j
- [ ] Is it accessed frequently? → Consider Redis
- [ ] Does it need to be human-readable? → Consider Basic Memory
- [ ] Is it conversational/temporal? → Use Redis
- [ ] Will it be searched semantically? → Use Redis
- [ ] Does it need visual representation? → Use Basic Memory canvas

## Integration with CAB Monitoring

The memory selection process is monitored for optimization opportunities:

```python
# Automatic CAB suggestions when:
- Same data queried >10 times/hour from Basic Memory → Suggest Redis caching
- Relationship queries in Redis → Suggest Neo4j migration
- Large documents in Redis → Suggest Basic Memory storage
- Orphaned entities detected → Suggest cleanup
```

## Best Practices

1. **Start with the primary system** for your use case
2. **Add secondary systems** only when needed
3. **Monitor performance** via CAB suggestions
4. **Sync critical data** across systems
5. **Document your memory strategy** in Basic Memory

Remember: The best memory system is the one that matches your data's natural structure and access patterns.