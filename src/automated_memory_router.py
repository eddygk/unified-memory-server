"""
Automated Memory System Router

Implements intelligent routing to appropriate memory systems based on 
automated analysis of request patterns, intent, and performance metrics.
"""
import logging
import re
import time
from typing import Dict, List, Optional, Any, Tuple, NamedTuple
from enum import Enum
from dataclasses import dataclass, field
from collections import defaultdict, Counter

from .memory_selector import MemorySelector, MemorySystem, TaskType

logger = logging.getLogger(__name__)


class IntentType(Enum):
    """Types of user intents for memory operations"""
    # Relationship-focused intents
    CREATE_RELATION = "create_relation"
    QUERY_RELATION = "query_relation" 
    TRAVERSE_GRAPH = "traverse_graph"
    
    # Documentation intents
    WRITE_DOC = "write_doc"
    READ_DOC = "read_doc"
    UPDATE_DOC = "update_doc"
    
    # Search intents
    SEMANTIC_SEARCH = "semantic_search"
    CONTEXT_RETRIEVAL = "context_retrieval"
    MEMORY_LOOKUP = "memory_lookup"
    
    # Multi-system intents
    SYNC_DATA = "sync_data"
    CROSS_REFERENCE = "cross_reference"
    COMPREHENSIVE_STORE = "comprehensive_store"
    
    # General
    UNKNOWN = "unknown"


class Operation(Enum):
    """Types of memory operations"""
    STORE = "store"
    QUERY = "query"
    RETRIEVE = "retrieve"
    SEARCH = "search"


@dataclass
class Entity:
    """Represents an extracted entity"""
    name: str
    entity_type: str
    confidence: float = 1.0
    context: Optional[str] = None


@dataclass
class MemoryRequest:
    """Represents a memory operation request
    
    Supported operations: store, query, retrieve, search
    """
    operation: Operation
    content: str
    context: Optional[Dict[str, Any]] = None
    entities: List[Entity] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RoutingDecision:
    """Represents a routing decision"""
    primary_system: MemorySystem
    secondary_systems: List[MemorySystem] = field(default_factory=list)
    confidence: float = 1.0
    reasoning: str = ""
    multi_system: bool = False


class IntentAnalyzer:
    """Analyzes requests to determine user intent"""
    
    def __init__(self):
        self.intent_patterns = self._initialize_patterns()
    
    def _initialize_patterns(self) -> Dict[IntentType, List[str]]:
        """Initialize pattern matching rules for intent detection"""
        return {
            # Relationship patterns
            IntentType.CREATE_RELATION: [
                r'\b(connect|link|associate|relate|tie)\b.*\b(to|with)\b',
                r'\b(create|establish|build)\b.*\b(relationship|connection|link)\b',
                r'\b(add|insert)\b.*\b(relationship|edge|connection)\b'
            ],
            IntentType.QUERY_RELATION: [
                r'\b(who|what|which).*\b(connected|linked|related|associated)\b',
                r'\b(find|show|get).*\b(relationships|connections|links)\b',
                r'\b(how.*related|connected.*to)\b'
            ],
            IntentType.TRAVERSE_GRAPH: [
                r'\b(path|route|journey).*\b(from|to|between)\b',
                r'\b(traverse|walk|follow).*\b(graph|network|connections)\b',
                r'\b(degrees?.*separation|shortest.*path)\b'
            ],
            
            # Documentation patterns  
            IntentType.WRITE_DOC: [
                r'\b(write|create|compose|document|note)\b.*\b(about|on|regarding|documentation|doc|file)\b',
                r'\b(save|store|record).*\b(document|note|information)\b',
                r'\b(take.*notes?|make.*note)\b',
                r'\b(create|make).*\b(documentation|doc)\b'
            ],
            IntentType.READ_DOC: [
                r'\b(read|show|display|get).*\b(document|note|file)\b',
                r'\b(open|view|access).*\b(note|document)\b',
                r'\b(what.*written|content.*of)\b',
                r'\bread.*\b(document|file|note)\b.*\babout\b'
            ],
            
            # Search patterns
            IntentType.SEMANTIC_SEARCH: [
                r'\b(find|search|look.*for).*\b(similar|like|related)\b',
                r'\b(semantic|meaning|context).*\b(search|find)\b',
                r'\b(what.*means|similar.*to)\b',
                r'\b(search|find).*\b(information|documents?|data)\b'
            ],
            IntentType.CONTEXT_RETRIEVAL: [
                r'\b(remember|recall|what.*said)\b',
                r'\b(conversation.*about|discussed.*earlier)\b',
                r'\b(context|background|history)\b'
            ],
            IntentType.MEMORY_LOOKUP: [
                r'\b(retrieve|get|fetch).*\b(memory|information|data)\b',
                r'\b(lookup|check|find).*\b(stored|saved)\b',
                r'\bretrieve.*\b(stored|saved|user|preferences)\b'
            ],
            
            # Multi-system patterns
            IntentType.COMPREHENSIVE_STORE: [
                r'\b(complete|full|comprehensive).*\b(profile|record|information)\b',
                r'\b(everything.*about|all.*information)\b',
                r'\b(store.*everywhere|save.*all.*systems)\b',
                r'\b(save|store).*\b(complete|comprehensive|full)\b',
                r'\b(get|retrieve).*\b(all.*information|everything.*about|complete.*profile)\b'
            ]
        }
    
    def analyze(self, request: MemoryRequest) -> IntentType:
        """Analyze request to determine intent"""
        content_lower = request.content.lower()
        
        # Score each intent type
        scores = defaultdict(float)
        
        for intent_type, patterns in self.intent_patterns.items():
            for pattern in patterns:
                matches = re.findall(pattern, content_lower)
                if matches:
                    scores[intent_type] += len(matches) * 1.0
        
        # Add context-based scoring
        if request.context:
            self._add_context_scores(scores, request.context)
        
        # Return highest scoring intent or UNKNOWN
        if scores:
            best_intent = max(scores.items(), key=lambda x: x[1])[0]
            logger.debug(f"Intent analysis: {best_intent.value} (score: {scores[best_intent]})")
            return best_intent
        
        return IntentType.UNKNOWN
    
    def _add_context_scores(self, scores: Dict[IntentType, float], context: Dict[str, Any]) -> None:
        """Add context-based scoring to intent analysis"""
        operation = context.get('operation', '').lower()
        
        if operation in ['store', 'save', 'create']:
            scores[IntentType.WRITE_DOC] += 0.5
            scores[IntentType.COMPREHENSIVE_STORE] += 0.3
        elif operation in ['search', 'find', 'query']:
            scores[IntentType.SEMANTIC_SEARCH] += 0.7
            scores[IntentType.MEMORY_LOOKUP] += 0.5
        elif operation in ['retrieve', 'get', 'recall']:
            scores[IntentType.CONTEXT_RETRIEVAL] += 0.7
            scores[IntentType.MEMORY_LOOKUP] += 0.3


class EntityExtractor:
    """Extracts entities and their relationships from requests"""
    
    def __init__(self):
        self.entity_patterns = self._initialize_entity_patterns()
    
    def _initialize_entity_patterns(self) -> Dict[str, List[str]]:
        """Initialize patterns for entity extraction"""
        return {
            'person': [
                r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b(?:\s+(?:said|mentioned|told|asked))',
                r'\b(?:user|person|individual|someone)\s+named\s+([A-Z][a-z]+)',
                r'\b@([a-zA-Z0-9_]+)\b'  # Mentions
            ],
            'project': [
                r'\b(project|initiative)\s+([A-Z][a-zA-Z0-9\s]+)',
                r'\b([A-Z][a-zA-Z0-9\s]+)\s+project\b',
                r'\bworking\s+on\s+([A-Z][a-zA-Z0-9\s]+)'
            ],
            'document': [
                r'\b(document|file|note|report)\s+([a-zA-Z0-9\s\-_\.]+)',
                r'\b([a-zA-Z0-9\-_]+\.(?:md|txt|doc|pdf))\b'
            ],
            'concept': [
                r'\bconcept\s+(?:of\s+)?([a-zA-Z0-9\s]+)',
                r'\bidea\s+(?:of\s+)?([a-zA-Z0-9\s]+)',
                r'\bnotion\s+(?:of\s+)?([a-zA-Z0-9\s]+)'
            ],
            'organization': [
                r'\b([A-Z][a-zA-Z0-9]*(?:\s+[A-Z][a-zA-Z0-9]*)*)\s+(?:company|corp|inc|ltd|organization)',
                r'\bcompany\s+([A-Z][a-zA-Z0-9\s]+)',
                r'\borganization\s+([A-Z][a-zA-Z0-9\s]+)'
            ]
        }
    
    def extract(self, request: MemoryRequest) -> List[Entity]:
        """Extract entities from request"""
        entities = []
        content = request.content
        
        for entity_type, patterns in self.entity_patterns.items():
            for pattern in patterns:
                matches = re.finditer(pattern, content, re.IGNORECASE)
                for match in matches:
                    entity_name = match.group(1).strip()
                    if len(entity_name) > 1 and entity_name.lower() not in ['the', 'and', 'or', 'but']:
                        entities.append(Entity(
                            name=entity_name,
                            entity_type=entity_type,
                            confidence=0.8,
                            context=match.group(0)
                        ))
        
        # Add entities from context if available
        if request.context and 'entities' in request.context:
            for entity_data in request.context['entities']:
                entities.append(Entity(**entity_data))
        
        return entities


class PerformanceTracker:
    """Tracks performance metrics for routing decisions"""
    
    def __init__(self):
        self.metrics = {
            'neo4j': {'success_rate': 0.9, 'avg_response_time': 150.0, 'operations': 0},
            'redis': {'success_rate': 0.95, 'avg_response_time': 50.0, 'operations': 0},
            'basic_memory': {'success_rate': 0.85, 'avg_response_time': 200.0, 'operations': 0}
        }
        self.recent_operations = []
    
    def record_operation(self, system: str, success: bool, response_time: float) -> None:
        """Record operation result for performance tracking"""
        if system not in self.metrics:
            self.metrics[system] = {'success_rate': 0.5, 'avg_response_time': 1000.0, 'operations': 0}
        
        # Update metrics with exponential moving average
        alpha = 0.1  # Weight for new observations
        current_success = 1.0 if success else 0.0
        
        self.metrics[system]['success_rate'] = (
            (1 - alpha) * self.metrics[system]['success_rate'] + 
            alpha * current_success
        )
        
        self.metrics[system]['avg_response_time'] = (
            (1 - alpha) * self.metrics[system]['avg_response_time'] + 
            alpha * response_time
        )
        
        self.metrics[system]['operations'] += 1
        
        # Keep recent operations for analysis
        self.recent_operations.append({
            'system': system,
            'success': success,
            'response_time': response_time,
            'timestamp': time.time()
        })
        
        # Keep only last 100 operations
        if len(self.recent_operations) > 100:
            self.recent_operations.pop(0)
    
    def get_metrics(self) -> Dict[str, Dict[str, float]]:
        """Get current performance metrics"""
        return self.metrics.copy()
    
    def get_system_score(self, system: str) -> float:
        """Calculate overall score for a system based on performance"""
        if system not in self.metrics:
            return 0.5
        
        metrics = self.metrics[system]
        # Combine success rate and response time (lower is better for response time)
        response_score = max(0.1, 1.0 - (metrics['avg_response_time'] / 1000.0))
        overall_score = (metrics['success_rate'] * 0.7) + (response_score * 0.3)
        
        return min(1.0, max(0.0, overall_score))


class RoutingEngine:
    """Makes routing decisions based on analysis and performance data"""
    
    def __init__(self, performance_tracker: PerformanceTracker):
        self.performance_tracker = performance_tracker
        self.intent_system_mapping = self._initialize_intent_mapping()
    
    def _initialize_intent_mapping(self) -> Dict[IntentType, List[MemorySystem]]:
        """Initialize mapping from intents to preferred systems"""
        return {
            # Relationship intents -> Neo4j primary
            IntentType.CREATE_RELATION: [MemorySystem.NEO4J, MemorySystem.REDIS],
            IntentType.QUERY_RELATION: [MemorySystem.NEO4J, MemorySystem.REDIS],
            IntentType.TRAVERSE_GRAPH: [MemorySystem.NEO4J],
            
            # Documentation intents -> Basic Memory primary
            IntentType.WRITE_DOC: [MemorySystem.BASIC_MEMORY, MemorySystem.REDIS],
            IntentType.READ_DOC: [MemorySystem.BASIC_MEMORY, MemorySystem.REDIS],
            IntentType.UPDATE_DOC: [MemorySystem.BASIC_MEMORY],
            
            # Search intents -> Redis primary
            IntentType.SEMANTIC_SEARCH: [MemorySystem.REDIS, MemorySystem.NEO4J],
            IntentType.CONTEXT_RETRIEVAL: [MemorySystem.REDIS],
            IntentType.MEMORY_LOOKUP: [MemorySystem.REDIS, MemorySystem.BASIC_MEMORY],
            
            # Multi-system intents -> All systems
            IntentType.SYNC_DATA: [MemorySystem.NEO4J, MemorySystem.REDIS, MemorySystem.BASIC_MEMORY],
            IntentType.CROSS_REFERENCE: [MemorySystem.NEO4J, MemorySystem.REDIS, MemorySystem.BASIC_MEMORY],
            IntentType.COMPREHENSIVE_STORE: [MemorySystem.NEO4J, MemorySystem.REDIS, MemorySystem.BASIC_MEMORY],
            
            # Unknown -> Redis as safe default
            IntentType.UNKNOWN: [MemorySystem.REDIS]
        }
    
    def score_systems(self, intent: IntentType, entities: List[Entity], 
                     context: Optional[Dict[str, Any]] = None) -> Dict[str, float]:
        """Score each memory system for the given request characteristics"""
        scores = {'neo4j': 0.1, 'redis': 0.1, 'basic_memory': 0.1}  # Base scores to avoid zeros
        
        # Base scores from intent mapping
        preferred_systems = self.intent_system_mapping.get(intent, [MemorySystem.REDIS])
        for i, system in enumerate(preferred_systems):
            scores[system.value] += (1.0 - (i * 0.2))  # Decreasing preference
        
        # Entity-based scoring
        entity_boost = self._calculate_entity_boost(entities)
        for system, boost in entity_boost.items():
            scores[system] += boost
        
        # Performance-based scoring
        performance_metrics = self.performance_tracker.get_metrics()
        for system in scores:
            performance_score = self.performance_tracker.get_system_score(system)
            scores[system] *= performance_score
        
        # Context-based adjustments
        if context:
            context_adjustments = self._calculate_context_adjustments(context)
            for system, adjustment in context_adjustments.items():
                scores[system] *= adjustment
        
        return scores
    
    def _calculate_entity_boost(self, entities: List[Entity]) -> Dict[str, float]:
        """Calculate scoring boosts based on extracted entities"""
        boosts = {'neo4j': 0.0, 'redis': 0.0, 'basic_memory': 0.0}
        
        entity_counts = Counter(entity.entity_type for entity in entities)
        
        # Relationship-heavy entities boost Neo4j
        relationship_entities = entity_counts.get('person', 0) + entity_counts.get('organization', 0)
        if relationship_entities > 1:
            boosts['neo4j'] += 0.3
        
        # Document entities boost Basic Memory
        doc_entities = entity_counts.get('document', 0) + entity_counts.get('concept', 0)
        if doc_entities > 0:
            boosts['basic_memory'] += 0.2
        
        # High entity count suggests complex query -> Redis for fast retrieval
        if len(entities) > 3:
            boosts['redis'] += 0.1
        
        return boosts
    
    def _calculate_context_adjustments(self, context: Dict[str, Any]) -> Dict[str, float]:
        """Calculate scoring adjustments based on context"""
        adjustments = {'neo4j': 1.0, 'redis': 1.0, 'basic_memory': 1.0}
        
        # Content length affects system preference
        content_length = context.get('content_length', 0)
        if content_length > 1000:  # Long content -> Basic Memory
            adjustments['basic_memory'] *= 1.2
            adjustments['redis'] *= 0.9
        elif content_length < 100:  # Short content -> Redis
            adjustments['redis'] *= 1.1
        
        # Urgency affects system selection
        urgency = context.get('urgency', 'normal')
        if urgency == 'high':
            adjustments['redis'] *= 1.2  # Redis is fastest
            adjustments['neo4j'] *= 0.9
        
        return adjustments
    
    def route(self, request: MemoryRequest, scores: Dict[str, float]) -> RoutingDecision:
        """Make final routing decision based on scores"""
        # Sort systems by score
        sorted_systems = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        
        primary_system_name = sorted_systems[0][0]
        primary_system = MemorySystem(primary_system_name)
        primary_score = sorted_systems[0][1]
        
        # Determine if multi-system operation is needed
        secondary_systems = []
        multi_system = False
        
        # If top scores are close, use multiple systems
        if len(sorted_systems) > 1 and sorted_systems[1][1] / primary_score > 0.8:
            secondary_systems.append(MemorySystem(sorted_systems[1][0]))
            multi_system = True
        
        # Check for comprehensive operations
        if any(keyword in request.content.lower() for keyword in ['complete', 'full', 'comprehensive', 'everything']):
            secondary_systems = [MemorySystem(name) for name, _ in sorted_systems[1:]]
            multi_system = True
        
        reasoning = f"Intent-based routing with performance weighting. Primary score: {primary_score:.2f}"
        
        return RoutingDecision(
            primary_system=primary_system,
            secondary_systems=secondary_systems,
            confidence=primary_score,
            reasoning=reasoning,
            multi_system=multi_system
        )


class AutomatedMemoryRouter:
    """
    Automated Memory System Router that intelligently routes requests
    to appropriate memory systems based on analysis and performance.
    """
    
    def __init__(self, cab_tracker=None, config_path=None, validate_config=True):
        """Initialize the automated router"""
        # Initialize core memory selector for fallback and system management
        self.memory_selector = MemorySelector(cab_tracker, config_path, validate_config)
        
        # Initialize analysis components
        self.intent_analyzer = IntentAnalyzer()
        self.entity_extractor = EntityExtractor()
        self.performance_tracker = PerformanceTracker()
        self.routing_engine = RoutingEngine(self.performance_tracker)
        
        self.cab_tracker = cab_tracker
        
        logger.info("AutomatedMemoryRouter initialized")
    
    def route(self, request: MemoryRequest) -> RoutingDecision:
        """
        Main routing method that analyzes request and returns routing decision
        """
        start_time = time.time()
        
        # Step 1: Analyze intent
        intent = self.intent_analyzer.analyze(request)
        
        # Step 2: Extract entities
        entities = self.entity_extractor.extract(request)
        request.entities = entities  # Store for later use
        
        # Step 3: Score systems
        context = request.context or {}
        context['content_length'] = len(request.content)
        
        scores = self.routing_engine.score_systems(intent, entities, context)
        
        # Step 4: Make routing decision
        decision = self.routing_engine.route(request, scores)
        
        analysis_time = (time.time() - start_time) * 1000
        
        # Log routing decision
        if self.cab_tracker:
            self.cab_tracker.log_suggestion(
                "Automated Routing Decision",
                f"Routed to {decision.primary_system.value} with confidence {decision.confidence:.2f}",
                severity='LOW',
                context=f"Intent: {intent.value}, Entities: {len(entities)}, Analysis time: {analysis_time:.1f}ms",
                metrics={
                    'intent': intent.value,
                    'entity_count': len(entities),
                    'analysis_time_ms': analysis_time,
                    'confidence': decision.confidence,
                    'multi_system': decision.multi_system
                }
            )
        
        logger.debug(f"Routing decision: {decision.primary_system.value} (confidence: {decision.confidence:.2f})")
        
        return decision
    
    def execute_routed_operation(self, request: MemoryRequest, operation_func) -> Tuple[Any, MemorySystem, bool]:
        """
        Execute operation using automated routing with fallback
        """
        # Get routing decision
        decision = self.route(request)
        
        # Convert to legacy format for memory_selector compatibility
        task = request.content
        context = request.context
        
        # Try primary system first
        start_time = time.time()
        try:
            result = operation_func(decision.primary_system, task, context)
            duration = (time.time() - start_time) * 1000
            
            # Record successful operation
            self.performance_tracker.record_operation(
                decision.primary_system.value, True, duration
            )
            
            return result, decision.primary_system, False
            
        except Exception as e:
            duration = (time.time() - start_time) * 1000
            
            # Record failed operation
            self.performance_tracker.record_operation(
                decision.primary_system.value, False, duration
            )
            
            logger.warning(f"Primary system {decision.primary_system.value} failed: {e}")
            
            # Fall back to memory selector's fallback mechanism
            return self.memory_selector.execute_with_fallback(task, operation_func, context)
    
    def store_data(self, data: Dict[str, Any], content: str, context: Optional[Dict[str, Any]] = None) -> Tuple[Any, MemorySystem, bool]:
        """Store data using automated routing"""
        request = MemoryRequest(
            operation=Operation.STORE,
            content=content,
            context=context,
            metadata=data
        )
        
        def store_operation(system: MemorySystem, task: str, ctx: Optional[Dict[str, Any]]):
            return self.memory_selector._store_in_system(system, data, task, ctx)
        
        return self.execute_routed_operation(request, store_operation)
    
    def retrieve_data(self, query: Dict[str, Any], content: str, context: Optional[Dict[str, Any]] = None) -> Tuple[Any, MemorySystem, bool]:
        """Retrieve data using automated routing"""
        request = MemoryRequest(
            operation=Operation.RETRIEVE, 
            content=content,
            context=context,
            metadata=query
        )
        
        def retrieve_operation(system: MemorySystem, task: str, ctx: Optional[Dict[str, Any]]):
            return self.memory_selector._retrieve_from_system(system, query, task, ctx)
        
        return self.execute_routed_operation(request, retrieve_operation)
    
    def get_routing_stats(self) -> Dict[str, Any]:
        """Get statistics about routing performance"""
        metrics = self.performance_tracker.get_metrics()
        return {
            'system_performance': metrics,
            'recent_operations': len(self.performance_tracker.recent_operations),
            'router_version': '1.0.0-phase1'
        }