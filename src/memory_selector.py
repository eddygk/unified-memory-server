"""
Memory System Selector
Implements intelligent routing to appropriate memory systems based on task type
"""
import logging
import re
from typing import Dict, List, Optional, Any, Tuple, Set
from enum import Enum
import time
from dataclasses import dataclass

logger = logging.getLogger(__name__)


class MemorySystem(Enum):
    """Available memory systems"""
    NEO4J = "neo4j"
    REDIS = "redis"
    BASIC_MEMORY = "basic_memory"


class TaskType(Enum):
    """Types of memory tasks"""
    # Neo4j tasks
    USER_IDENTITY = "user_identity"
    RELATIONSHIP_QUERY = "relationship_query"
    ENTITY_CONNECTION = "entity_connection"
    GRAPH_TRAVERSAL = "graph_traversal"
    
    # Basic Memory tasks
    DOCUMENTATION = "documentation"
    STRUCTURED_NOTE = "structured_note"
    PERSISTENT_KNOWLEDGE = "persistent_knowledge"
    MARKDOWN_CONTENT = "markdown_content"
    
    # Redis tasks
    CONVERSATION_CONTEXT = "conversation_context"
    SEMANTIC_SEARCH = "semantic_search"
    PREFERENCE_STORAGE = "preference_storage"
    SESSION_DATA = "session_data"
    
    # General
    UNKNOWN = "unknown"


class OperationType(Enum):
    """Types of operations"""
    CREATE = "create"
    READ = "read" 
    UPDATE = "update"
    DELETE = "delete"
    SEARCH = "search"
    ANALYZE = "analyze"


@dataclass
class TaskAnalysis:
    """Results of task analysis"""
    task_type: TaskType
    operation_type: OperationType
    entities: List[str]
    confidence: float
    reasoning: str
    patterns_matched: List[str]


class IntentAnalyzer:
    """Advanced intent analyzer for sophisticated task determination"""
    
    def __init__(self):
        self._compile_patterns()
        
    def _compile_patterns(self):
        """Compile regex patterns for efficient matching"""
        # Relationship patterns
        self.relationship_patterns = [
            re.compile(r'\b(?:how\s+(?:is|are|does|do)?|what\s+(?:is|are)?)\s+.*?\b(?:related|connected|linked|associated)\b', re.I),
            re.compile(r'\b(?:find|show|get)\s+.*?\b(?:relationships?|connections?|links?|associations?)\b', re.I),
            re.compile(r'\b(?:who|what)\s+.*?\b(?:works?\s+(?:with|on|for)|collaborates?\s+with|is\s+connected\s+to)\b', re.I),
            re.compile(r'\b(?:map|trace|follow)\s+.*?\b(?:path|route|connection)\b', re.I)
        ]
        
        # User identity patterns
        self.user_identity_patterns = [
            re.compile(r'\b(?:who\s+(?:is|am)\s+(?:this\s+)?user|user\s+(?:profile|identity|information))\b', re.I),
            re.compile(r'\b(?:my|user\'s?)\s+(?:profile|identity|details|information)\b', re.I),
            re.compile(r'\b(?:about\s+(?:me|user)|tell\s+me\s+about)\b', re.I)
        ]
        
        # Documentation patterns  
        self.documentation_patterns = [
            re.compile(r'\b(?:create|write|generate|make)\s+.*?\b(?:document|documentation|guide|manual|report)\b', re.I),
            re.compile(r'\b(?:comprehensive|detailed|structured|formal)\s+.*?\b(?:note|document|guide)\b', re.I),
            re.compile(r'\b(?:draft|compose|author)\s+.*?\b(?:article|paper|documentation)\b', re.I)
        ]
        
        # Conversation context patterns
        self.conversation_patterns = [
            re.compile(r'\b(?:remember|recall|what\s+did\s+(?:we|i)|previous(?:ly)?)\b', re.I),
            re.compile(r'\b(?:conversation|chat|discussion)\s+(?:context|history|log)\b', re.I),
            re.compile(r'\b(?:earlier|before|previously)\s+(?:mentioned|said|discussed)\b', re.I)
        ]
        
        # Search patterns
        self.search_patterns = [
            re.compile(r'\b(?:search|find|look\s+(?:for|up)|locate)\s+.*?\b(?:similar|like|matching|related)\b', re.I),
            re.compile(r'\b(?:semantic|contextual|intelligent)\s+search\b', re.I),
            re.compile(r'\b(?:find\s+me|show\s+me|get\s+me)\s+.*?\b(?:about|regarding)\b', re.I)
        ]
        
        # Operation type patterns
        self.create_patterns = [
            re.compile(r'\b(?:create|make|generate|add|new|build|establish|form)\b', re.I),
        ]
        
        self.read_patterns = [
            re.compile(r'\b(?:get|retrieve|fetch|show|display|find|read|view|see)\b', re.I),
        ]
        
        self.update_patterns = [
            re.compile(r'\b(?:update|modify|change|edit|revise|alter|adjust)\b', re.I),
        ]
        
        self.delete_patterns = [
            re.compile(r'\b(?:delete|remove|clear|erase|drop|eliminate)\b', re.I),
        ]
        
        self.search_patterns_op = [
            re.compile(r'\b(?:search|find|look|locate|seek|query|explore)\b', re.I),
        ]
        
        self.analyze_patterns = [
            re.compile(r'\b(?:analyze|examine|investigate|study|assess|evaluate)\b', re.I),
        ]
        
        # Entity extraction patterns - made more precise
        self.entity_patterns = {
            'user': re.compile(r'\b(?:user|person|individual|me|myself|i)\b', re.I),
            'project': re.compile(r'\b(?:projects?|tasks?|assignments?|work|jobs?)\b', re.I),
            'document': re.compile(r'\b(?:documents?|files?|notes?|papers?|reports?|guides?|documentation)\b', re.I),
            'relationship': re.compile(r'\b(?:relationships?|connections?|links?|associations?|bonds?)\b', re.I),
            'conversation': re.compile(r'\b(?:conversations?|chats?|discussions?|talks?|dialogues?)\b', re.I),
            'memory': re.compile(r'\b(?:memory|memories|remember|recall|stored)\b', re.I),
        }
        
        # Temporal patterns
        self.temporal_patterns = [
            re.compile(r'\b(?:today|now|current|recent|latest|this\s+(?:week|month|year))\b', re.I),
            re.compile(r'\b(?:yesterday|last\s+(?:week|month|year)|previous|earlier|before)\b', re.I),
            re.compile(r'\b(?:always|never|frequently|often|sometimes|rarely)\b', re.I),
        ]
        
    def analyze(self, task: str, context: Optional[Dict[str, Any]] = None) -> TaskAnalysis:
        """Analyze task with sophisticated pattern matching and entity extraction"""
        task_clean = task.strip()
        entities = self._extract_entities(task_clean)
        operation_type = self._determine_operation_type(task_clean)
        
        # Pattern-based task type determination
        task_type, confidence, reasoning, patterns = self._determine_task_type_advanced(task_clean, entities, context)
        
        return TaskAnalysis(
            task_type=task_type,
            operation_type=operation_type,
            entities=entities,
            confidence=confidence,
            reasoning=reasoning,
            patterns_matched=patterns
        )
    
    def _extract_entities(self, task: str) -> List[str]:
        """Extract entities from task text"""
        entities = []
        for entity_type, pattern in self.entity_patterns.items():
            if pattern.search(task):
                entities.append(entity_type)
        return entities
    
    def _determine_operation_type(self, task: str) -> OperationType:
        """Determine the type of operation from task text"""
        # Check patterns in order of specificity
        if any(pattern.search(task) for pattern in self.create_patterns):
            return OperationType.CREATE
        elif any(pattern.search(task) for pattern in self.update_patterns):
            return OperationType.UPDATE  
        elif any(pattern.search(task) for pattern in self.delete_patterns):
            return OperationType.DELETE
        elif any(pattern.search(task) for pattern in self.search_patterns_op):
            # Check if it's a search for something specific vs general retrieval
            if any(word in task.lower() for word in ['similar', 'like', 'matching', 'related']):
                return OperationType.SEARCH
            else:
                return OperationType.READ
        elif any(pattern.search(task) for pattern in self.analyze_patterns):
            return OperationType.ANALYZE
        else:
            return OperationType.READ
    
    def _determine_task_type_advanced(self, task: str, entities: List[str], context: Optional[Dict[str, Any]]) -> Tuple[TaskType, float, str, List[str]]:
        """Advanced task type determination with confidence scoring"""
        scores = {}
        matched_patterns = []
        reasoning_parts = []
        
        # Relationship analysis
        relationship_score = 0
        for pattern in self.relationship_patterns:
            if pattern.search(task):
                relationship_score += 0.3
                matched_patterns.append("relationship_pattern")
        
        if 'relationship' in entities:
            relationship_score += 0.3
        if any(entity in entities for entity in ['user', 'project']):
            relationship_score += 0.1
        
        # Boost for explicit relationship language  
        if any(word in task.lower() for word in ['between', 'connected', 'linked']):
            relationship_score += 0.2
            matched_patterns.append("connection_language")
            
        scores[TaskType.RELATIONSHIP_QUERY] = min(relationship_score, 1.0)
        
        # User identity analysis
        user_identity_score = 0
        for pattern in self.user_identity_patterns:
            if pattern.search(task):
                user_identity_score += 0.4
                matched_patterns.append("user_identity_pattern")
        
        if 'user' in entities:
            user_identity_score += 0.3
            
        scores[TaskType.USER_IDENTITY] = min(user_identity_score, 1.0)
        
        # Documentation analysis
        doc_score = 0
        for pattern in self.documentation_patterns:
            if pattern.search(task):
                doc_score += 0.3
                matched_patterns.append("documentation_pattern")
        
        if 'document' in entities:
            doc_score += 0.2
        
        # Look for complexity indicators
        if any(word in task.lower() for word in ['comprehensive', 'detailed', 'structured', 'formal']):
            doc_score += 0.2
            matched_patterns.append("complexity_indicator")
            
        scores[TaskType.DOCUMENTATION] = min(doc_score, 1.0)
        
        # Conversation context analysis
        conv_score = 0
        for pattern in self.conversation_patterns:
            if pattern.search(task):
                conv_score += 0.3
                matched_patterns.append("conversation_pattern")
        
        if 'conversation' in entities or 'memory' in entities:
            conv_score += 0.2
        
        # Temporal indicators boost conversation score
        if any(pattern.search(task) for pattern in self.temporal_patterns):
            conv_score += 0.2
            matched_patterns.append("temporal_indicator")
            
        scores[TaskType.CONVERSATION_CONTEXT] = min(conv_score, 1.0)
        
        # Semantic search analysis
        search_score = 0
        for pattern in self.search_patterns:
            if pattern.search(task):
                search_score += 0.4
                matched_patterns.append("search_pattern")
        
        # Boost search score if looking for "related documents" or similar content
        if any(word in task.lower() for word in ['similar', 'related']) and 'document' in entities:
            search_score += 0.2
            matched_patterns.append("similarity_search")
        
        scores[TaskType.SEMANTIC_SEARCH] = min(search_score, 1.0)
        
        # Context-based hints
        if context:
            if context.get('needs_persistence'):
                scores[TaskType.PERSISTENT_KNOWLEDGE] = 0.8
                matched_patterns.append("context_persistence")
            if context.get('is_relational'):
                scores[TaskType.ENTITY_CONNECTION] = 0.8
                matched_patterns.append("context_relational")
            if context.get('is_temporary'):
                scores[TaskType.SESSION_DATA] = 0.8
                matched_patterns.append("context_temporary")
        
        # Find best match
        if not scores or max(scores.values()) < 0.2:
            return TaskType.UNKNOWN, 0.0, "No significant patterns matched", []
        
        best_task_type = max(scores.items(), key=lambda x: x[1])
        task_type, confidence = best_task_type
        
        # Build reasoning
        reasoning = f"Best match: {task_type.value} (confidence: {confidence:.2f})"
        if matched_patterns:
            reasoning += f" - Patterns: {', '.join(set(matched_patterns))}"
        if entities:
            reasoning += f" - Entities: {', '.join(entities)}"
            
        return task_type, confidence, reasoning, matched_patterns


class MemorySelector:
    """Selects appropriate memory system based on task characteristics"""
    
    def __init__(self, cab_tracker=None):
        self.cab_tracker = cab_tracker
        self._selection_rules = self._initialize_rules()
        self._fallback_chains = self._initialize_fallback_chains()
        self._intent_analyzer = IntentAnalyzer()
        
    def _initialize_rules(self) -> Dict[TaskType, MemorySystem]:
        """Initialize task type to memory system mapping"""
        return {
            # Neo4j mappings
            TaskType.USER_IDENTITY: MemorySystem.NEO4J,
            TaskType.RELATIONSHIP_QUERY: MemorySystem.NEO4J,
            TaskType.ENTITY_CONNECTION: MemorySystem.NEO4J,
            TaskType.GRAPH_TRAVERSAL: MemorySystem.NEO4J,
            
            # Basic Memory mappings
            TaskType.DOCUMENTATION: MemorySystem.BASIC_MEMORY,
            TaskType.STRUCTURED_NOTE: MemorySystem.BASIC_MEMORY,
            TaskType.PERSISTENT_KNOWLEDGE: MemorySystem.BASIC_MEMORY,
            TaskType.MARKDOWN_CONTENT: MemorySystem.BASIC_MEMORY,
            
            # Redis mappings
            TaskType.CONVERSATION_CONTEXT: MemorySystem.REDIS,
            TaskType.SEMANTIC_SEARCH: MemorySystem.REDIS,
            TaskType.PREFERENCE_STORAGE: MemorySystem.REDIS,
            TaskType.SESSION_DATA: MemorySystem.REDIS,
        }
    
    def _initialize_fallback_chains(self) -> Dict[MemorySystem, List[MemorySystem]]:
        """Initialize fallback chains for each system"""
        return {
            MemorySystem.NEO4J: [MemorySystem.REDIS, MemorySystem.BASIC_MEMORY],
            MemorySystem.REDIS: [MemorySystem.BASIC_MEMORY, MemorySystem.NEO4J],
            MemorySystem.BASIC_MEMORY: [MemorySystem.REDIS, MemorySystem.NEO4J],
        }
    
    def analyze_task(self, task: str, context: Optional[Dict[str, Any]] = None) -> TaskType:
        """Analyze task to determine its type using sophisticated intent recognition"""
        # Use advanced intent analyzer
        analysis = self._intent_analyzer.analyze(task, context)
        
        # Log analysis for CAB tracking
        if self.cab_tracker and analysis.confidence < 0.5:
            self.cab_tracker.log_suggestion(
                "Low Confidence Task Analysis",
                f"Task analysis had low confidence ({analysis.confidence:.2f}): {analysis.reasoning}",
                severity='MEDIUM',
                context=f"Task: {task[:50]}... | Patterns: {', '.join(analysis.patterns_matched)}"
            )
        
        # Fallback to legacy keyword matching if confidence is very low
        if analysis.confidence < 0.3:
            legacy_task_type = self._analyze_task_legacy(task, context)
            if legacy_task_type != TaskType.UNKNOWN:
                if self.cab_tracker:
                    self.cab_tracker.log_suggestion(
                        "Fallback to Legacy Analysis",
                        f"Advanced analysis failed (confidence: {analysis.confidence:.2f}), used legacy keyword matching",
                        severity='LOW',
                        context=f"Advanced: {analysis.task_type.value} -> Legacy: {legacy_task_type.value}"
                    )
                return legacy_task_type
        
        return analysis.task_type
    
    def _analyze_task_legacy(self, task: str, context: Optional[Dict[str, Any]] = None) -> TaskType:
        """Legacy keyword-based task analysis for fallback"""
        task_lower = task.lower()
        
        # Check for relationship/connection indicators
        relationship_keywords = ['relationship', 'connection', 'linked', 'related', 
                               'connects', 'graph', 'network', 'association']
        if any(keyword in task_lower for keyword in relationship_keywords):
            return TaskType.RELATIONSHIP_QUERY
        
        # Check for user identity
        if 'user' in task_lower and any(word in task_lower for word in ['identity', 'profile', 'who']):
            return TaskType.USER_IDENTITY
        
        # Check for documentation
        doc_keywords = ['document', 'note', 'write', 'comprehensive', 'detailed', 
                       'guide', 'report', 'structured']
        if any(keyword in task_lower for keyword in doc_keywords):
            return TaskType.DOCUMENTATION
        
        # Check for conversation/semantic
        conv_keywords = ['conversation', 'context', 'semantic', 'search', 
                        'remember', 'previous', 'history']
        if any(keyword in task_lower for keyword in conv_keywords):
            return TaskType.CONVERSATION_CONTEXT
        
        # Check context for additional hints
        if context:
            if context.get('needs_persistence'):
                return TaskType.PERSISTENT_KNOWLEDGE
            if context.get('is_relational'):
                return TaskType.ENTITY_CONNECTION
            if context.get('is_temporary'):
                return TaskType.SESSION_DATA
        
        return TaskType.UNKNOWN
    
    def get_task_analysis(self, task: str, context: Optional[Dict[str, Any]] = None) -> TaskAnalysis:
        """Get detailed task analysis including confidence and reasoning"""
        return self._intent_analyzer.analyze(task, context)
    
    def select_memory_system(
        self, 
        task: str,
        context: Optional[Dict[str, Any]] = None,
        allow_fallback: bool = True
    ) -> Tuple[MemorySystem, TaskType]:
        """
        Select appropriate memory system for task
        
        Returns:
            Tuple of (selected_system, task_type)
        """
        start_time = time.time()
        
        # Analyze task type
        task_type = self.analyze_task(task, context)
        
        # Get primary system
        if task_type == TaskType.UNKNOWN:
            # Default fallback logic
            primary_system = MemorySystem.REDIS  # Default to Redis for unknown tasks
            logger.warning(f"Unknown task type for: {task[:50]}...")
        else:
            primary_system = self._selection_rules.get(task_type, MemorySystem.REDIS)
        
        # Log selection
        duration_ms = (time.time() - start_time) * 1000
        logger.info(f"Selected {primary_system.value} for {task_type.value} "
                   f"(took {duration_ms:.2f}ms)")
        
        # Log to CAB if slow
        if self.cab_tracker and duration_ms > 100:
            self.cab_tracker.log_suggestion(
                "Slow Memory Selection",
                f"Memory selection took {duration_ms:.2f}ms",
                severity='LOW',
                context=f"Task: {task[:50]}..."
            )
        
        return primary_system, task_type
    
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
        primary_system, task_type = self.select_memory_system(task, context)
        fallback_chain = [primary_system] + self.get_fallback_chain(primary_system)
        
        last_error = None
        for i, system in enumerate(fallback_chain):
            try:
                start_time = time.time()
                result = operation_func(system, task, context)
                duration_ms = (time.time() - start_time) * 1000
                
                # Log metrics
                if self.cab_tracker:
                    self.cab_tracker.log_memory_operation(
                        operation=task_type.value,
                        system=system.value,
                        success=True,
                        duration_ms=duration_ms,
                        fallback_used=(i > 0)
                    )
                
                # Log fallback usage
                if i > 0:
                    logger.info(f"Successfully used fallback system {system.value}")
                    if self.cab_tracker:
                        self.cab_tracker.log_suggestion(
                            "Fallback Success",
                            f"Primary system {primary_system.value} failed, "
                            f"fallback to {system.value} succeeded",
                            severity='MEDIUM',
                            context=f"Consider investigating primary system issue"
                        )
                
                return result, system, (i > 0)
                
            except Exception as e:
                last_error = e
                logger.warning(f"System {system.value} failed: {str(e)}")
                
                if self.cab_tracker:
                    self.cab_tracker.log_memory_operation(
                        operation=task_type.value,
                        system=system.value,
                        success=False,
                        duration_ms=0,
                        fallback_used=False
                    )
                
                # Continue to next system in fallback chain
                continue
        
        # All systems failed
        logger.error(f"All systems failed for task: {task}")
        raise Exception(f"All memory systems failed. Last error: {last_error}")


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


# Example usage pattern
if __name__ == "__main__":
    from cab_tracker import get_cab_tracker
    
    # Initialize
    cab_tracker = get_cab_tracker()
    selector = MemorySelector(cab_tracker)
    
    # Example task selection
    task = "Find all relationships between user and their projects"
    system, task_type = selector.select_memory_system(task)
    print(f"Selected {system.value} for task type {task_type.value}")
    
    # Example with fallback
    def mock_operation(system, task, context):
        if system == MemorySystem.NEO4J:
            raise Exception("Neo4j unavailable")
        return f"Result from {system.value}"
    
    result, successful_system, used_fallback = selector.execute_with_fallback(
        task,
        mock_operation
    )
    print(f"Result: {result}, Used fallback: {used_fallback}")
