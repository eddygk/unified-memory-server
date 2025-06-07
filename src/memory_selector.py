"""
Memory System Selector
Implements intelligent routing to appropriate memory systems based on task type
"""
import logging
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
import time
import os
import json

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


class MemorySelector:
    """Selects appropriate memory system based on task characteristics"""
    
    def __init__(self, cab_tracker=None):
        self.cab_tracker = cab_tracker
        self._selection_rules = self._initialize_rules()
        self._fallback_chains = self._initialize_fallback_chains()
        self._clients = {}  # Cache for instantiated clients
        
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
        """Analyze task to determine its type"""
        task_lower = task.lower()
        
        # Check for relationship/connection indicators
        relationship_keywords = ['relationship', 'connection', 'linked', 'related', 
                               'connects', 'graph', 'network', 'association']
        if any(keyword in task_lower for keyword in relationship_keywords):
            return TaskType.RELATIONSHIP_QUERY
        
        # Check for user identity
        if 'user' in task_lower and any(word in task_lower for word in ['identity', 'profile', 'who']):
            return TaskType.USER_IDENTITY
        
        # Check for semantic search indicators
        semantic_keywords = ['search', 'find', 'lookup', 'query', 'retrieve']
        if any(keyword in task_lower for keyword in semantic_keywords):
            return TaskType.SEMANTIC_SEARCH
        
        # Check for preference storage indicators
        preference_keywords = ['preference', 'setting', 'config', 'option', 'choice', 'like', 'dislike']
        if any(keyword in task_lower for keyword in preference_keywords):
            return TaskType.PREFERENCE_STORAGE
        
        # Check for session data indicators
        session_keywords = ['session', 'current', 'active', 'temporary', 'cache']
        if any(keyword in task_lower for keyword in session_keywords):
            return TaskType.SESSION_DATA
        
        # Check for documentation
        doc_keywords = ['document', 'note', 'write', 'comprehensive', 'detailed', 
                       'guide', 'report', 'structured']
        if any(keyword in task_lower for keyword in doc_keywords):
            return TaskType.DOCUMENTATION
        
        # Check for conversation/context indicators
        conv_keywords = ['conversation', 'context', 'remember', 'previous', 'history', 'chat']
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
            if context.get('is_search'):
                return TaskType.SEMANTIC_SEARCH
        
        return TaskType.UNKNOWN
    
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
    
    def _get_redis_client(self):
        """Get or create Redis memory client"""
        if MemorySystem.REDIS in self._clients:
            return self._clients[MemorySystem.REDIS]
        
        try:
            # Import Redis memory client dependencies
            # Based on the documentation, we need MemoryAPIClient and MemoryClientConfig
            # For now, we'll create a mock implementation that follows the expected interface
            from dataclasses import dataclass
            from urllib.parse import urlparse
            
            @dataclass
            class MemoryClientConfig:
                """Configuration for Redis memory client"""
                base_url: str = "http://10.10.20.100:8000"
                api_key: str = ""
                timeout: int = 30
            
            class MemoryAPIClient:
                """Mock Redis Memory API Client following redis-developer/agent-memory-server interface"""
                
                def __init__(self, config: MemoryClientConfig):
                    self.config = config
                    self.base_url = config.base_url.rstrip('/')
                    
                    # Validate URL format
                    try:
                        parsed = urlparse(self.base_url)
                        if not parsed.scheme or not parsed.netloc:
                            raise ValueError(f"Invalid URL format: {self.base_url}")
                    except Exception as e:
                        raise ValueError(f"Invalid Redis memory server URL: {e}")
                    
                def set_working_memory(self, session_id: str, content: str, metadata: Dict = None):
                    """Set working memory for a session"""
                    # Mock implementation - in real scenario this would make HTTP requests
                    return {"success": True, "session_id": session_id}
                
                def get_working_memory(self, session_id: str):
                    """Get working memory for a session"""
                    return {"content": f"Working memory for {session_id}", "metadata": {}}
                
                def create_long_term_memory(self, payload: Dict):
                    """Create long-term memory entry"""
                    return {"id": "mock_memory_id", "success": True}
                
                def search_long_term_memory(self, query: str, namespace: str = "default", limit: int = 10):
                    """Search long-term memories"""
                    return {
                        "memories": [
                            {"id": "mock_id", "text": f"Mock result for: {query}", "score": 0.9}
                        ],
                        "total": 1
                    }
                
                def hydrate_memory_prompt(self, text: str, session_id: str = None, **kwargs):
                    """Get conversation context for prompt hydration"""
                    return {
                        "hydrated_prompt": f"[Context: Mock context] {text}",
                        "context_memories": []
                    }
            
            # Load configuration from environment
            base_url = os.getenv("REDIS_MEMORY_URL", "http://10.10.20.100:8000")
            
            config = MemoryClientConfig(
                base_url=base_url,
                api_key=os.getenv("REDIS_MEMORY_API_KEY", ""),
                timeout=int(os.getenv("REDIS_MEMORY_TIMEOUT", "30"))
            )
            
            client = MemoryAPIClient(config)
            self._clients[MemorySystem.REDIS] = client
            
            logger.info("Redis memory client initialized successfully")
            return client
            
        except Exception as e:
            error_msg = f"Failed to initialize Redis client: {str(e)}"
            logger.error(error_msg)
            if self.cab_tracker:
                self.cab_tracker.log_suggestion(
                    "Redis Client Initialization Failed",
                    error_msg,
                    severity='HIGH',
                    context="Check Redis memory server configuration and availability"
                )
            raise
    
    def _store_in_redis(self, data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Store data in Redis memory system"""
        start_time = time.time()
        
        try:
            client = self._get_redis_client()
            
            # Determine task type from context or analyze data
            task_type = context.get('task_type') if context else TaskType.UNKNOWN
            if task_type == TaskType.UNKNOWN and isinstance(data, str):
                task_type = self.analyze_task(data, context)
            
            # Map TaskType to appropriate Redis storage method
            if task_type in [TaskType.CONVERSATION_CONTEXT, TaskType.SESSION_DATA]:
                # Use working memory for temporary/session data
                session_id = context.get('session_id', 'default') if context else 'default'
                
                # Prepare data for working memory
                if isinstance(data, dict):
                    content = data.get('text', str(data))
                    metadata = data.get('metadata', {})
                else:
                    content = str(data)
                    metadata = context.get('metadata', {}) if context else {}
                
                result = client.set_working_memory(
                    session_id=session_id,
                    content=content,
                    metadata=metadata
                )
                
                operation_type = "working_memory_store"
                
            else:
                # Use long-term memory for persistent data (semantic search, preferences, etc.)
                payload = self._prepare_long_term_memory_payload(data, context, task_type)
                result = client.create_long_term_memory(payload)
                operation_type = "long_term_memory_store"
            
            duration_ms = (time.time() - start_time) * 1000
            
            # Log successful operation
            if self.cab_tracker:
                self.cab_tracker.log_memory_operation(
                    operation=operation_type,
                    system=MemorySystem.REDIS.value,
                    success=True,
                    duration_ms=duration_ms
                )
            
            logger.info(f"Successfully stored data in Redis ({operation_type}) - {duration_ms:.2f}ms")
            return result
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            error_msg = f"Failed to store data in Redis: {str(e)}"
            logger.error(error_msg)
            
            if self.cab_tracker:
                self.cab_tracker.log_memory_operation(
                    operation="redis_store",
                    system=MemorySystem.REDIS.value,
                    success=False,
                    duration_ms=duration_ms
                )
                self.cab_tracker.log_suggestion(
                    "Redis Store Operation Failed",
                    error_msg,
                    severity='HIGH',
                    context=f"Task type: {task_type.value if 'task_type' in locals() else 'unknown'}"
                )
            
            raise
    
    def _retrieve_from_redis(self, query: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Retrieve data from Redis memory system"""
        start_time = time.time()
        
        try:
            client = self._get_redis_client()
            
            # Determine task type and query type
            task_type = context.get('task_type') if context else TaskType.UNKNOWN
            if task_type == TaskType.UNKNOWN and isinstance(query, str):
                task_type = self.analyze_task(query, context)
            
            # Map TaskType to appropriate Redis retrieval method
            if task_type in [TaskType.CONVERSATION_CONTEXT, TaskType.SESSION_DATA]:
                # Retrieve from working memory
                session_id = context.get('session_id', 'default') if context else 'default'
                result = client.get_working_memory(session_id)
                operation_type = "working_memory_retrieve"
                
            elif task_type == TaskType.SEMANTIC_SEARCH:
                # Use semantic search in long-term memory
                namespace = context.get('namespace', 'default') if context else 'default'
                limit = context.get('limit', 10) if context else 10
                
                query_text = query if isinstance(query, str) else str(query)
                result = client.search_long_term_memory(
                    query=query_text,
                    namespace=namespace,
                    limit=limit
                )
                operation_type = "semantic_search"
                
            elif task_type == TaskType.PREFERENCE_STORAGE:
                # Search preferences in long-term memory
                namespace = context.get('namespace', 'preferences') if context else 'preferences'
                query_text = query if isinstance(query, str) else str(query)
                
                result = client.search_long_term_memory(
                    query=query_text,
                    namespace=namespace,
                    limit=context.get('limit', 5) if context else 5
                )
                operation_type = "preference_retrieve"
                
            else:
                # Default to hydrating prompt with context
                session_id = context.get('session_id') if context else None
                query_text = query if isinstance(query, str) else str(query)
                
                result = client.hydrate_memory_prompt(
                    text=query_text,
                    session_id=session_id,
                    **({k: v for k, v in context.items() if k not in ['task_type', 'session_id']} if context else {})
                )
                operation_type = "prompt_hydration"
            
            duration_ms = (time.time() - start_time) * 1000
            
            # Log successful operation
            if self.cab_tracker:
                self.cab_tracker.log_memory_operation(
                    operation=operation_type,
                    system=MemorySystem.REDIS.value,
                    success=True,
                    duration_ms=duration_ms
                )
            
            logger.info(f"Successfully retrieved data from Redis ({operation_type}) - {duration_ms:.2f}ms")
            return result
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            error_msg = f"Failed to retrieve data from Redis: {str(e)}"
            logger.error(error_msg)
            
            if self.cab_tracker:
                self.cab_tracker.log_memory_operation(
                    operation="redis_retrieve",
                    system=MemorySystem.REDIS.value,
                    success=False,
                    duration_ms=duration_ms
                )
                self.cab_tracker.log_suggestion(
                    "Redis Retrieve Operation Failed",
                    error_msg,
                    severity='HIGH',
                    context=f"Query: {str(query)[:100]}..."
                )
            
            raise
    
    def _prepare_long_term_memory_payload(self, data: Any, context: Optional[Dict[str, Any]], task_type: TaskType) -> Dict[str, Any]:
        """Prepare data for long-term memory storage with appropriate MemoryRecord format"""
        
        # Extract text content
        if isinstance(data, dict):
            text = data.get('text', str(data))
            metadata = data.get('metadata', {})
            topics = data.get('topics', [])
            entities = data.get('entities', [])
        else:
            text = str(data)
            metadata = {}
            topics = []
            entities = []
        
        # Add context information to metadata
        if context:
            metadata.update({
                'task_type': task_type.value,
                'source': context.get('source', 'unified_memory_server'),
                **{k: v for k, v in context.items() if k not in ['task_type', 'session_id', 'metadata']}
            })
        
        # Prepare namespace based on task type
        namespace_mapping = {
            TaskType.PREFERENCE_STORAGE: 'preferences',
            TaskType.SEMANTIC_SEARCH: 'semantic',
            TaskType.CONVERSATION_CONTEXT: 'conversations',
            TaskType.SESSION_DATA: 'sessions'
        }
        namespace = context.get('namespace') if context else namespace_mapping.get(task_type, 'default')
        
        # Create LongTermMemoryPayload-compatible structure
        payload = {
            "text": text,
            "namespace": namespace,
            "topics": topics,
            "entities": entities,
            "metadata": metadata
        }
        
        # Add session_id if available
        if context and context.get('session_id'):
            payload["session_id"] = context['session_id']
        
        return payload


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
        """Propagate data to Redis using MemorySelector's Redis backend logic"""
        try:
            # Use MemorySelector's Redis implementation if available
            if hasattr(self, '_memory_selector') and self._memory_selector:
                context = {
                    'entity_id': entity_id,
                    'data_type': data_type,
                    'source': 'propagation'
                }
                result = self._memory_selector._store_in_redis(data, context)
                return result.get('success', True)
            else:
                # Fallback to direct client usage
                if hasattr(client, 'create_long_term_memory'):
                    payload = {
                        'text': str(data),
                        'namespace': 'propagation',
                        'metadata': {
                            'data_type': data_type,
                            'entity_id': entity_id,
                            'source': 'cross_system_propagation'
                        }
                    }
                    result = client.create_long_term_memory(payload)
                    return result.get('success', True)
                return False
        except Exception as e:
            logger.error(f"Failed to propagate to Redis: {e}")
            return False
    
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
