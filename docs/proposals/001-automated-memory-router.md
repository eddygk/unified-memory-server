# Enhancement Proposal 001: Automated Memory System Router

**Status**: Draft  
**Date**: 2025-01-11  
**Author(s)**: Eddy Kawira, Claude AI  

## Summary

This proposal introduces an Automated Memory System Router to replace the current manual decision-making process for selecting which memory system (Neo4j, Basic Memory, or Redis) to use for each operation. The router would automatically analyze incoming requests, classify them based on intent and characteristics, and route them to the appropriate memory system(s) without requiring explicit tool selection.

## Motivation

Currently, the memory system selection follows a manual decision tree:
- IF relationships → Neo4j
- ELSE IF documentation → Basic Memory  
- ELSE IF semantic search → Redis

This manual process:
1. Requires cognitive overhead for each operation
2. Can lead to inconsistent routing decisions
3. Doesn't leverage historical performance data
4. May miss opportunities for multi-system optimization

## Detailed Design

### Architecture Overview

```python
class AutomatedMemoryRouter:
    """
    Intelligent router that automatically selects memory systems
    based on request analysis and historical performance.
    """
    
    def __init__(self):
        self.intent_analyzer = IntentAnalyzer()
        self.entity_extractor = EntityExtractor()
        self.performance_tracker = PerformanceTracker()
        self.routing_engine = RoutingEngine()
        
    def route(self, request: MemoryRequest) -> RoutingDecision:
        # 1. Analyze request
        intent = self.intent_analyzer.analyze(request)
        entities = self.entity_extractor.extract(request)
        context = self.get_conversation_context()
        
        # 2. Score each system
        scores = self.routing_engine.score_systems(
            intent=intent,
            entities=entities,
            context=context,
            historical_performance=self.performance_tracker.get_metrics()
        )
        
        # 3. Execute routing
        return self.routing_engine.route(request, scores)
```

### Core Components

#### 1. Intent Analyzer
Classifies requests into categories:
- **Relationship Operations**: CREATE_RELATION, QUERY_RELATION, TRAVERSE_GRAPH
- **Documentation Operations**: WRITE_DOC, READ_DOC, UPDATE_DOC
- **Search Operations**: SEMANTIC_SEARCH, CONTEXT_RETRIEVAL, MEMORY_LOOKUP
- **Multi-System Operations**: SYNC_DATA, CROSS_REFERENCE, COMPREHENSIVE_STORE

#### 2. Entity Extractor
Identifies key entities and their types:
- User profiles
- Projects, tasks, documents
- Relationships between entities
- Temporal markers
- Semantic concepts

#### 3. Routing Engine
Makes routing decisions based on:
```python
class RoutingEngine:
    def score_systems(self, intent, entities, context, historical_performance):
        scores = {}
        
        # Neo4j scoring
        scores['neo4j'] = self._score_neo4j(
            relationship_count=len(entities.relationships),
            graph_complexity=self._estimate_traversal_depth(intent),
            entity_types=entities.types,
            historical_success=historical_performance.neo4j_success_rate
        )
        
        # Basic Memory scoring  
        scores['basic_memory'] = self._score_basic_memory(
            content_length=len(intent.content),
            structure_complexity=self._analyze_structure(intent),
            persistence_need=intent.requires_persistence,
            historical_success=historical_performance.bm_success_rate
        )
        
        # Redis scoring
        scores['redis'] = self._score_redis(
            semantic_similarity_need=intent.requires_semantic_search,
            temporal_relevance=self._calculate_temporal_relevance(entities),
            access_frequency=self._estimate_access_frequency(intent),
            historical_success=historical_performance.redis_success_rate
        )
        
        return scores
```

#### 4. Performance Tracker
Monitors and learns from routing decisions:
- Success/failure rates per system
- Response times
- Resource utilization
- User satisfaction (via CAB tracking)

### Pattern Matching Rules

```yaml
routing_patterns:
  neo4j_primary:
    - keywords: ["relationship", "connection", "linked to", "associated with"]
    - entity_patterns: ["user.* connects to .*", ".* works on .*"]
    - query_types: ["who", "how are .* related"]
    
  basic_memory_primary:
    - keywords: ["document", "note", "write", "comprehensive", "detailed"]
    - content_indicators: ["markdown", "formatted text", "long form"]
    - persistence_level: "permanent"
    
  redis_primary:
    - keywords: ["remember", "recall", "search", "find similar"]
    - temporal_markers: ["recent", "today", "this session"]
    - access_patterns: ["frequent", "cache", "quick lookup"]
    
  multi_system:
    - indicators: ["complete profile", "full context", "everything about"]
    - complexity_score: "> 0.7"
```

### Multi-System Coordination

When multiple systems score highly:
```python
class MultiSystemCoordinator:
    def execute_multi_system_operation(self, request, system_scores):
        # Parallel execution for read operations
        if request.operation_type == "READ":
            results = asyncio.gather(
                self.neo4j_handler.execute(request),
                self.redis_handler.execute(request),
                self.bm_handler.execute(request)
            )
            return self.merge_results(results)
        
        # Sequential execution for writes with propagation
        elif request.operation_type == "WRITE":
            primary = self.select_primary_system(system_scores)
            result = primary.execute(request)
            
            # Propagate to secondary systems
            for secondary in self.get_secondary_systems(system_scores):
                secondary.propagate(result)
                
            return result
```

### CAB Integration

```python
class RouterCABTracker:
    def log_routing_decision(self, request, decision, outcome):
        suggestion = self.analyze_routing_performance(request, decision, outcome)
        
        if suggestion:
            log_cab_suggestion(
                suggestion_type="Routing Optimization",
                description=f"Pattern detected: {suggestion.pattern}",
                severity=suggestion.severity,
                context={
                    "request_type": request.intent,
                    "selected_system": decision.primary_system,
                    "performance": outcome.metrics
                }
            )
```

## Benefits

1. **Reduced Cognitive Load**: No manual decision-making required
2. **Consistent Routing**: Same patterns always route the same way
3. **Performance Optimization**: Learns from historical data to improve routing
4. **Automatic Fallbacks**: Built-in retry logic and failover
5. **Multi-System Intelligence**: Can leverage multiple systems when beneficial
6. **Transparent Operation**: Users unaware of routing complexity

## Drawbacks

1. **Initial Complexity**: More complex than manual routing
2. **Training Period**: Needs historical data to optimize effectively
3. **Debugging Challenges**: Automated decisions may be harder to trace
4. **Resource Overhead**: Additional processing for analysis

## Alternatives Considered

1. **Rule-Based Only**: Simpler but less adaptive
2. **ML-Only Approach**: More powerful but requires extensive training data
3. **User-Specified Routing**: Gives control but adds complexity for users

## Implementation Plan

### Phase 1: Foundation (Week 1-2)
- [ ] Create base `AutomatedMemoryRouter` class
- [ ] Implement basic intent analysis
- [ ] Set up pattern matching rules
- [ ] Add CAB tracking integration

### Phase 2: Intelligence (Week 3-4)
- [ ] Build entity extraction
- [ ] Implement scoring algorithms
- [ ] Add performance tracking
- [ ] Create test suite

### Phase 3: Integration (Week 5-6)
- [ ] Replace manual routing in codebase
- [ ] Add configuration options
- [ ] Implement monitoring dashboard
- [ ] Document usage patterns

### Phase 4: Optimization (Week 7-8)
- [ ] Collect performance data
- [ ] Tune scoring algorithms
- [ ] Add ML-based improvements
- [ ] Release v1.0

## Success Metrics

- Routing accuracy > 95%
- Performance improvement > 20%
- Zero manual routing decisions required
- CAB suggestion reduction for routing issues

## Open Questions

1. Should routing decisions be explainable to users on demand?
2. How much historical data is needed before enabling ML features?
3. Should there be an override mechanism for specific cases?
4. How to handle new patterns not seen before?

## References

- Current manual routing logic in `memory-selection.md`
- CAB tracking implementation
- Memory system performance benchmarks
