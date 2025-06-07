"""
Memory System Selector
Implements intelligent routing to appropriate memory systems based on task type
"""
import logging
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
import time

logger = logging.getLogger(__name__)

import re
from dataclasses import dataclass
from typing import List


class MemorySystem(Enum):
    """Available memory systems"""
    NEO4J = "neo4j"
    REDIS = "redis"
    BASIC_MEMORY = "basic_memory"


class IntentType(Enum):
    """Intent types for automated memory routing"""
    # Relationship Operations (Neo4j primary)
    CREATE_RELATION = "create_relation"
    QUERY_RELATION = "query_relation"
    TRAVERSE_GRAPH = "traverse_graph"
    
    # Documentation Operations (Basic Memory primary)
    WRITE_DOC = "write_doc"
    READ_DOC = "read_doc"
    UPDATE_DOC = "update_doc"
    
    # Search Operations (Redis primary)
    SEMANTIC_SEARCH = "semantic_search"
    CONTEXT_RETRIEVAL = "context_retrieval"
    MEMORY_LOOKUP = "memory_lookup"
    
    # Multi-System Operations
    SYNC_DATA = "sync_data"
    CROSS_REFERENCE = "cross_reference"
    COMPREHENSIVE_STORE = "comprehensive_store"
    
    # Legacy task types (for backward compatibility)
    USER_IDENTITY = "user_identity"
    ENTITY_CONNECTION = "entity_connection"
    DOCUMENTATION = "documentation"
    STRUCTURED_NOTE = "structured_note"
    PERSISTENT_KNOWLEDGE = "persistent_knowledge"
    MARKDOWN_CONTENT = "markdown_content"
    CONVERSATION_CONTEXT = "conversation_context"
    PREFERENCE_STORAGE = "preference_storage"
    SESSION_DATA = "session_data"
    
    # General
    UNKNOWN = "unknown"

# Keep TaskType as alias for backward compatibility
TaskType = IntentType


@dataclass
class RoutingPattern:
    """Pattern for routing decisions"""
    keywords: List[str]
    entity_patterns: List[str] = None
    query_types: List[str] = None
    content_indicators: List[str] = None
    temporal_markers: List[str] = None
    access_patterns: List[str] = None
    complexity_indicators: List[str] = None


class IntentAnalyzer:
    """Analyzes intent from requests using pattern matching"""
    
    def __init__(self):
        self.patterns = self._initialize_patterns()
    
    def _initialize_patterns(self) -> Dict[IntentType, RoutingPattern]:
        """Initialize pattern matching rules from proposal"""
        return {
            # Neo4j patterns
            IntentType.CREATE_RELATION: RoutingPattern(
                keywords=["create", "establish", "link", "connect", "associate", "relate", "add relationship"],
                entity_patterns=["user.* connects to .*", ".* works on .*", "relationship between", "create .* relationship"]
            ),
            IntentType.QUERY_RELATION: RoutingPattern(
                keywords=["relationship", "connection", "linked to", "associated with", "related", "how.*related", "show.*relationship"],
                query_types=["who", "how are .* related", "what connects", "find relationships", "show.*how.*related"]
            ),
            IntentType.TRAVERSE_GRAPH: RoutingPattern(
                keywords=["traverse", "path", "network", "graph", "connections", "navigate"],
                entity_patterns=["path from .* to .*", "all connections", "network of", "traverse.*graph"]
            ),
            
            # Basic Memory patterns
            IntentType.WRITE_DOC: RoutingPattern(
                keywords=["write", "create doc", "save document", "author", "compose"],
                content_indicators=["document", "comprehensive", "detailed", "write.*document"]
            ),
            IntentType.READ_DOC: RoutingPattern(
                keywords=["read", "get document", "retrieve note", "show document", "open"],
                content_indicators=["document", "note", "file", "read.*document"]
            ),
            IntentType.UPDATE_DOC: RoutingPattern(
                keywords=["update", "edit", "modify", "change document", "revise"],
                content_indicators=["document", "note", "existing", "update.*document"]
            ),
            
            # Redis patterns
            IntentType.SEMANTIC_SEARCH: RoutingPattern(
                keywords=["search", "find similar", "semantic", "meaning", "related content", "find.*related"],
                access_patterns=["find", "search", "similar", "like", "search.*similar"]
            ),
            IntentType.CONTEXT_RETRIEVAL: RoutingPattern(
                keywords=["context", "background", "history", "previous", "get.*context"],
                temporal_markers=["recent", "last", "previous", "earlier", "recent.*context"]
            ),
            IntentType.MEMORY_LOOKUP: RoutingPattern(
                keywords=["remember", "recall", "lookup", "retrieve memory", "my.*preference", "my.*setting"],
                access_patterns=["quick", "fast", "cache", "temporary", "remember.*my"]
            ),
            
            # Multi-system patterns
            IntentType.COMPREHENSIVE_STORE: RoutingPattern(
                keywords=["comprehensive", "complete", "full", "everything about"],
                complexity_indicators=["complete profile", "full context", "everything about"]
            ),
            IntentType.CROSS_REFERENCE: RoutingPattern(
                keywords=["cross reference", "link systems", "sync", "coordinate"],
                complexity_indicators=["across systems", "multiple sources"]
            ),
            
            # Legacy patterns for backward compatibility
            IntentType.USER_IDENTITY: RoutingPattern(
                keywords=["user", "identity", "profile", "who"],
                entity_patterns=["user profile", "identity"]
            ),
            IntentType.ENTITY_CONNECTION: RoutingPattern(
                keywords=["entity", "connection", "link entities"],
                entity_patterns=["entity.* connects", "link between entities"]
            ),
            IntentType.DOCUMENTATION: RoutingPattern(
                keywords=["documentation", "guide", "report", "manual"],
                content_indicators=["comprehensive", "detailed", "structured"]
            ),
            IntentType.STRUCTURED_NOTE: RoutingPattern(
                keywords=["structured", "note", "format"],
                content_indicators=["structured", "organized", "formatted"]
            ),
            IntentType.PERSISTENT_KNOWLEDGE: RoutingPattern(
                keywords=["persistent", "knowledge", "permanent", "store"],
                content_indicators=["permanent", "persistent", "long-term"]
            ),
            IntentType.MARKDOWN_CONTENT: RoutingPattern(
                keywords=["markdown", "md", "formatted text"],
                content_indicators=["markdown", "formatted", "text"]
            ),
            IntentType.CONVERSATION_CONTEXT: RoutingPattern(
                keywords=["conversation", "context", "chat", "discussion"],
                temporal_markers=["recent", "today", "this session", "current"]
            ),
            IntentType.PREFERENCE_STORAGE: RoutingPattern(
                keywords=["preference", "setting", "config", "option"],
                access_patterns=["user preference", "setting", "configuration"]
            ),
            IntentType.SESSION_DATA: RoutingPattern(
                keywords=["session", "temporary", "current session"],
                temporal_markers=["session", "temporary", "current"],
                access_patterns=["session", "temporary"]
            ),
        }
    
    def analyze(self, task: str, context: Optional[Dict[str, Any]] = None) -> IntentType:
        """Analyze task to determine intent using pattern matching"""
        task_lower = task.lower()
        
        # Score each intent type based on pattern matching
        intent_scores = {}
        
        for intent_type, pattern in self.patterns.items():
            score = 0
            
            # Check keywords
            for keyword in pattern.keywords:
                if keyword in task_lower:
                    score += 2
            
            # Check entity patterns
            if pattern.entity_patterns:
                for entity_pattern in pattern.entity_patterns:
                    if re.search(entity_pattern.lower(), task_lower):
                        score += 3
            
            # Check query types
            if pattern.query_types:
                for query_type in pattern.query_types:
                    if re.search(query_type.lower(), task_lower):
                        score += 3
            
            # Check content indicators
            if pattern.content_indicators:
                for indicator in pattern.content_indicators:
                    if indicator in task_lower:
                        score += 1
            
            # Check temporal markers
            if pattern.temporal_markers:
                for marker in pattern.temporal_markers:
                    if marker in task_lower:
                        score += 1
            
            # Check access patterns
            if pattern.access_patterns:
                for access_pattern in pattern.access_patterns:
                    if access_pattern in task_lower:
                        score += 1
            
            # Check complexity indicators
            if pattern.complexity_indicators:
                for indicator in pattern.complexity_indicators:
                    if indicator in task_lower:
                        score += 4  # Higher weight for multi-system operations
            
            intent_scores[intent_type] = score
        
        # Apply context-based scoring
        if context:
            if context.get('needs_persistence'):
                for intent in [IntentType.WRITE_DOC, IntentType.PERSISTENT_KNOWLEDGE]:
                    if intent in intent_scores:
                        intent_scores[intent] += 2
            if context.get('is_relational'):
                for intent in [IntentType.CREATE_RELATION, IntentType.QUERY_RELATION]:
                    if intent in intent_scores:
                        intent_scores[intent] += 2
            if context.get('is_temporary'):
                for intent in [IntentType.SESSION_DATA, IntentType.MEMORY_LOOKUP]:
                    if intent in intent_scores:
                        intent_scores[intent] += 2
        
        # Find highest scoring intent
        if intent_scores:
            best_intent = max(intent_scores.items(), key=lambda x: x[1])
            if best_intent[1] > 0:
                return best_intent[0]
        
        return IntentType.UNKNOWN


class AutomatedMemoryRouter:
    """
    Intelligent router that automatically selects memory systems
    based on request analysis and historical performance.
    
    Replaces manual decision-making with automated routing.
    """
    
    def __init__(self, cab_tracker=None):
        self.cab_tracker = cab_tracker
        self.intent_analyzer = IntentAnalyzer()
        self._selection_rules = self._initialize_rules()
        self._fallback_chains = self._initialize_fallback_chains()
        
    def _initialize_rules(self) -> Dict[IntentType, MemorySystem]:
        """Initialize intent type to memory system mapping"""
        return {
            # Neo4j mappings (relationship operations)
            IntentType.CREATE_RELATION: MemorySystem.NEO4J,
            IntentType.QUERY_RELATION: MemorySystem.NEO4J,
            IntentType.TRAVERSE_GRAPH: MemorySystem.NEO4J,
            IntentType.USER_IDENTITY: MemorySystem.NEO4J,
            IntentType.ENTITY_CONNECTION: MemorySystem.NEO4J,
            
            # Basic Memory mappings (documentation operations)
            IntentType.WRITE_DOC: MemorySystem.BASIC_MEMORY,
            IntentType.READ_DOC: MemorySystem.BASIC_MEMORY,
            IntentType.UPDATE_DOC: MemorySystem.BASIC_MEMORY,
            IntentType.DOCUMENTATION: MemorySystem.BASIC_MEMORY,
            IntentType.STRUCTURED_NOTE: MemorySystem.BASIC_MEMORY,
            IntentType.PERSISTENT_KNOWLEDGE: MemorySystem.BASIC_MEMORY,
            IntentType.MARKDOWN_CONTENT: MemorySystem.BASIC_MEMORY,
            
            # Redis mappings (search and context operations)
            IntentType.SEMANTIC_SEARCH: MemorySystem.REDIS,
            IntentType.CONTEXT_RETRIEVAL: MemorySystem.REDIS,
            IntentType.MEMORY_LOOKUP: MemorySystem.REDIS,
            IntentType.CONVERSATION_CONTEXT: MemorySystem.REDIS,
            IntentType.PREFERENCE_STORAGE: MemorySystem.REDIS,
            IntentType.SESSION_DATA: MemorySystem.REDIS,
            
            # Multi-system operations default to Redis for coordination
            IntentType.SYNC_DATA: MemorySystem.REDIS,
            IntentType.CROSS_REFERENCE: MemorySystem.REDIS,
            IntentType.COMPREHENSIVE_STORE: MemorySystem.REDIS,
        }
    
    def _initialize_fallback_chains(self) -> Dict[MemorySystem, List[MemorySystem]]:
        """Initialize fallback chains for each system"""
        return {
            MemorySystem.NEO4J: [MemorySystem.REDIS, MemorySystem.BASIC_MEMORY],
            MemorySystem.REDIS: [MemorySystem.BASIC_MEMORY, MemorySystem.NEO4J],
            MemorySystem.BASIC_MEMORY: [MemorySystem.REDIS, MemorySystem.NEO4J],
        }
    
    def analyze_task(self, task: str, context: Optional[Dict[str, Any]] = None) -> IntentType:
        """Analyze task to determine its intent (enhanced with pattern matching)"""
        # Use the new IntentAnalyzer for better pattern matching
        intent = self.intent_analyzer.analyze(task, context)
        
        # Log routing decision for CAB tracking
        if self.cab_tracker:
            self.cab_tracker.log_suggestion(
                "Routing Analysis",
                f"Intent '{intent.value}' detected for task",
                severity='LOW',
                context={
                    "task_preview": task[:100] + "..." if len(task) > 100 else task,
                    "detected_intent": intent.value,
                    "has_context": context is not None
                }
            )
        
        return intent
    
    def select_memory_system(
        self, 
        task: str,
        context: Optional[Dict[str, Any]] = None,
        allow_fallback: bool = True
    ) -> Tuple[MemorySystem, IntentType]:
        """
        Select appropriate memory system for task using automated routing
        
        Returns:
            Tuple of (selected_system, intent_type)
        """
        start_time = time.time()
        
        # Analyze task intent using enhanced pattern matching
        intent_type = self.analyze_task(task, context)
        
        # Get primary system based on intent
        if intent_type == IntentType.UNKNOWN:
            # Default fallback logic
            primary_system = MemorySystem.REDIS  # Default to Redis for unknown tasks
            logger.warning(f"Unknown intent type for: {task[:50]}...")
            
            # Log CAB suggestion for unknown pattern
            if self.cab_tracker:
                self.cab_tracker.log_suggestion(
                    "Unknown Routing Pattern",
                    f"Could not classify task intent",
                    severity='MEDIUM',
                    context={
                        "task_preview": task[:100] + "..." if len(task) > 100 else task,
                        "suggestion": "Consider adding new pattern rules for this task type"
                    }
                )
        else:
            primary_system = self._selection_rules.get(intent_type, MemorySystem.REDIS)
        
        # Log selection
        duration_ms = (time.time() - start_time) * 1000
        logger.info(f"Selected {primary_system.value} for {intent_type.value} "
                   f"(took {duration_ms:.2f}ms)")
        
        # Enhanced CAB tracking for routing decisions
        if self.cab_tracker:
            self.cab_tracker.log_suggestion(
                "Automated Routing Decision",
                f"Routed {intent_type.value} to {primary_system.value}",
                severity='LOW',
                context={
                    "intent": intent_type.value,
                    "selected_system": primary_system.value,
                    "analysis_time_ms": duration_ms,
                    "task_preview": task[:50] + "..." if len(task) > 50 else task
                }
            )
            
            # Log slow routing for optimization
            if duration_ms > 100:
                self.cab_tracker.log_suggestion(
                    "Slow Routing Analysis",
                    f"Intent analysis took {duration_ms:.2f}ms",
                    severity='MEDIUM',
                    context={
                        "duration_ms": duration_ms,
                        "task_length": len(task),
                        "suggestion": "Consider optimizing pattern matching algorithms"
                    }
                )
        
        return primary_system, intent_type
    
    def get_fallback_chain(self, primary_system: MemorySystem) -> List[MemorySystem]:
        """Get fallback chain for a memory system"""
        return self._fallback_chains.get(primary_system, [])
    
    def execute_with_fallback(
        self,
        task: str,
        operation_func: callable,
        context: Optional[Dict[str, Any]] = None
    ) -> Tuple[Any, MemorySystem, bool]:
        """
        Execute operation with automatic fallback
        
        Args:
            task: Task description
            operation_func: Function that takes (system, task, context) and returns result
            context: Optional context
            
        Returns:
            Tuple of (result, successful_system, used_fallback)
        """
        primary_system, intent_type = self.select_memory_system(task, context)
        fallback_chain = [primary_system] + self.get_fallback_chain(primary_system)
        
        last_error = None
        for i, system in enumerate(fallback_chain):
            try:
                start_time = time.time()
                result = operation_func(system, task, context)
                duration_ms = (time.time() - start_time) * 1000
                
                # Enhanced CAB tracking for successful operations
                if self.cab_tracker:
                    self.cab_tracker.log_memory_operation(
                        operation=intent_type.value,
                        system=system.value,
                        success=True,
                        duration_ms=duration_ms,
                        fallback_used=(i > 0)
                    )
                    
                    # Log routing success pattern
                    self.cab_tracker.log_suggestion(
                        "Successful Routing",
                        f"Intent '{intent_type.value}' successfully executed on {system.value}",
                        severity='LOW',
                        context={
                            "intent": intent_type.value,
                            "system": system.value,
                            "duration_ms": duration_ms,
                            "fallback_used": i > 0,
                            "fallback_position": i if i > 0 else None
                        }
                    )
                
                # Log fallback usage
                if i > 0:
                    logger.info(f"Successfully used fallback system {system.value}")
                    if self.cab_tracker:
                        self.cab_tracker.log_suggestion(
                            "Fallback Success",
                            f"Primary system {primary_system.value} failed, "
                            f"fallback to {system.value} succeeded for {intent_type.value}",
                            severity='MEDIUM',
                            context={
                                "primary_system": primary_system.value,
                                "fallback_system": system.value,
                                "intent": intent_type.value,
                                "suggestion": "Consider investigating primary system reliability"
                            }
                        )
                
                return result, system, (i > 0)
                
            except Exception as e:
                last_error = e
                logger.warning(f"System {system.value} failed: {str(e)}")
                
                if self.cab_tracker:
                    self.cab_tracker.log_memory_operation(
                        operation=intent_type.value,
                        system=system.value,
                        success=False,
                        duration_ms=0,
                        fallback_used=False
                    )
                
                # Continue to next system in fallback chain
                continue
        
        # All systems failed - enhanced error reporting
        error_msg = f"All systems failed for intent '{intent_type.value}'. Last error: {last_error}"
        logger.error(error_msg)
        
        if self.cab_tracker:
            self.cab_tracker.log_suggestion(
                "Complete System Failure",
                f"All systems failed for intent '{intent_type.value}'",
                severity='HIGH',
                context={
                    "intent": intent_type.value,
                    "attempted_systems": [s.value for s in fallback_chain],
                    "last_error": str(last_error),
                    "task_preview": task[:100] + "..." if len(task) > 100 else task,
                    "suggestion": "Investigate system availability and consider alternative routing"
                }
            )
        
        raise Exception(error_msg)


class MemoryPropagator:
    """Handles cross-system data propagation"""
    
    def __init__(self, memory_clients: Dict[MemorySystem, Any], cab_tracker=None):
        self.clients = memory_clients
        self.cab_tracker = cab_tracker
        
    def propagate_data(
        self,
        data: Any,
        source_system: MemorySystem,
        data_type: str,
        entity_id: Optional[str] = None
    ) -> Dict[MemorySystem, bool]:
        """
        Propagate data to appropriate systems based on type
        
        Returns:
            Dict mapping system to success status
        """
        propagation_rules = {
            'user_profile': [MemorySystem.NEO4J, MemorySystem.REDIS],
            'relationship': [MemorySystem.NEO4J],
            'documentation': [MemorySystem.BASIC_MEMORY],
            'preference': [MemorySystem.REDIS],
            'entity': [MemorySystem.NEO4J, MemorySystem.BASIC_MEMORY],
        }
        
        target_systems = propagation_rules.get(data_type, [])
        results = {}
        
        for system in target_systems:
            if system == source_system:
                continue  # Skip source system
                
            try:
                client = self.clients.get(system)
                if not client:
                    results[system] = False
                    continue
                
                # System-specific propagation logic
                if system == MemorySystem.NEO4J:
                    # Create or update entity/relationship
                    success = self._propagate_to_neo4j(client, data, data_type, entity_id)
                elif system == MemorySystem.REDIS:
                    # Store in long-term memory
                    success = self._propagate_to_redis(client, data, data_type, entity_id)
                elif system == MemorySystem.BASIC_MEMORY:
                    # Create or update note
                    success = self._propagate_to_basic_memory(client, data, data_type, entity_id)
                else:
                    success = False
                
                results[system] = success
                
                if success:
                    logger.info(f"Successfully propagated {data_type} to {system.value}")
                else:
                    logger.warning(f"Failed to propagate {data_type} to {system.value}")
                    
            except Exception as e:
                logger.error(f"Error propagating to {system.value}: {e}")
                results[system] = False
        
        # Log inconsistencies
        failed_systems = [s.value for s, success in results.items() if not success]
        if failed_systems and self.cab_tracker:
            self.cab_tracker.log_data_inconsistency(
                entity=entity_id or "unknown",
                systems=failed_systems,
                inconsistency_type="Propagation failure"
            )
        
        return results
    
    def _propagate_to_neo4j(self, client, data, data_type, entity_id):
        """Propagate data to Neo4j"""
        # Implementation would depend on actual Neo4j client
        # This is a placeholder
        return True
    
    def _propagate_to_redis(self, client, data, data_type, entity_id):
        """Propagate data to Redis"""
        # Implementation would depend on actual Redis client
        # This is a placeholder
        return True
    
    def _propagate_to_basic_memory(self, client, data, data_type, entity_id):
        """Propagate data to Basic Memory"""
        # Implementation would depend on actual Basic Memory client
        # This is a placeholder
        return True


# Backward compatibility alias
MemorySelector = AutomatedMemoryRouter


# Example usage pattern
if __name__ == "__main__":
    from cab_tracker import get_cab_tracker
    
    # Initialize
    cab_tracker = get_cab_tracker()
    router = AutomatedMemoryRouter(cab_tracker)
    
    # Example task selection with enhanced intent analysis
    tasks = [
        "Find all relationships between user and their projects",
        "Create a comprehensive document about the new API",
        "Search for similar conversations from today",
        "Establish connection between user John and project Alpha",
        "Remember my preference for dark mode"
    ]
    
    for task in tasks:
        system, intent_type = router.select_memory_system(task)
        print(f"Task: {task[:50]}...")
        print(f"  → Intent: {intent_type.value}")
        print(f"  → System: {system.value}")
        print()
    
    # Example with fallback
    def mock_operation(system, task, context):
        if system == MemorySystem.NEO4J:
            raise Exception("Neo4j unavailable")
        return f"Result from {system.value}"
    
    task = "Find relationships between users"
    result, successful_system, used_fallback = router.execute_with_fallback(
        task,
        mock_operation
    )
    print(f"Fallback example:")
    print(f"  Task: {task}")
    print(f"  Result: {result}")
    print(f"  Used fallback: {used_fallback}")
    print(f"  Successful system: {successful_system.value}")
