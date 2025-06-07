"""
Memory System Selector
Implements intelligent routing to appropriate memory systems based on task type
"""
import logging
import os
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
import time
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class MemoryClientConfig:
    """Configuration for Redis Memory API Client"""
    redis_url: str
    redis_password: Optional[str] = None
    max_memory: str = "4gb"
    tls_enabled: bool = False
    window_size: int = 20
    embedding_model: str = "text-embedding-3-small"
    embedding_dimension: int = 1536
    enable_topic_extraction: bool = True
    enable_ner: bool = True


class MemoryAPIClient:
    """Simplified Redis Memory API Client (adapted from redis-developer/agent-memory-server)"""
    
    def __init__(self, config: MemoryClientConfig):
        self.config = config
        self._initialized = False
        self._redis_client = None
    
    def initialize(self):
        """Initialize the Redis client connection"""
        try:
            # In a real implementation, this would connect to Redis
            # For now, we'll simulate the connection
            self._initialized = True
            logger.info(f"Redis client initialized with URL: {self.config.redis_url}")
        except Exception as e:
            logger.error(f"Failed to initialize Redis client: {e}")
            raise
    
    def set_working_memory(self, session_id: str, content: str, metadata: Optional[Dict] = None):
        """Store content in working memory (Redis)"""
        if not self._initialized:
            raise Exception("Client not initialized")
        # Placeholder implementation
        return {"status": "success", "session_id": session_id}
    
    def create_long_term_memory(self, content: str, metadata: Optional[Dict] = None):
        """Create long-term memory entry"""
        if not self._initialized:
            raise Exception("Client not initialized")
        # Placeholder implementation
        return {"status": "success", "memory_id": f"mem_{int(time.time())}"}
    
    def search_long_term_memory(self, query: str, limit: int = 10, filters: Optional[Dict] = None):
        """Search long-term memory"""
        if not self._initialized:
            raise Exception("Client not initialized")
        # Placeholder implementation
        return {"results": [], "total": 0}
    
    def close(self):
        """Close the Redis connection"""
        self._initialized = False
        logger.info("Redis client connection closed")


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
        self._config = self._load_configuration()
        self._redis_client = None
        
    def _load_configuration(self) -> Dict[str, Any]:
        """Load backend configuration parameters from environment variables"""
        try:
            config = {
                # Redis configuration
                'redis_url': os.getenv('REDIS_URL', 'redis://localhost:6379'),
                'redis_password': os.getenv('REDIS_PASSWORD'),
                'redis_max_memory': os.getenv('REDIS_MAX_MEMORY', '4gb'),
                'redis_tls_enabled': os.getenv('REDIS_TLS_ENABLED', 'false').lower() == 'true',
                'window_size': int(os.getenv('WINDOW_SIZE', '20')),
                'embedding_model': os.getenv('EMBEDDING_MODEL', 'text-embedding-3-small'),
                'embedding_dimension': int(os.getenv('EMBEDDING_DIMENSION', '1536')),
                'enable_topic_extraction': os.getenv('ENABLE_TOPIC_EXTRACTION', 'true').lower() == 'true',
                'enable_ner': os.getenv('ENABLE_NER', 'true').lower() == 'true',
            }
            
            # Validate essential configuration
            if not config['redis_url']:
                if self.cab_tracker:
                    self.cab_tracker.log_suggestion(
                        "Configuration Error",
                        "Redis URL not configured",
                        severity='HIGH',
                        context="Set REDIS_URL environment variable"
                    )
                logger.error("Redis URL not configured")
            
            return config
            
        except Exception as e:
            if self.cab_tracker:
                self.cab_tracker.log_suggestion(
                    "Configuration Loading Error",
                    f"Failed to load configuration: {str(e)}",
                    severity='HIGH',
                    context="Check environment variables and configuration"
                )
            logger.error(f"Failed to load configuration: {e}")
            raise
    
    def _get_redis_client(self) -> MemoryAPIClient:
        """Get configured Redis memory client"""
        if self._redis_client is not None:
            return self._redis_client
        
        try:
            # Create configuration
            config = MemoryClientConfig(
                redis_url=self._config['redis_url'],
                redis_password=self._config['redis_password'],
                max_memory=self._config['redis_max_memory'],
                tls_enabled=self._config['redis_tls_enabled'],
                window_size=self._config['window_size'],
                embedding_model=self._config['embedding_model'],
                embedding_dimension=self._config['embedding_dimension'],
                enable_topic_extraction=self._config['enable_topic_extraction'],
                enable_ner=self._config['enable_ner']
            )
            
            # Create and initialize client
            client = MemoryAPIClient(config)
            client.initialize()
            
            self._redis_client = client
            logger.info("Redis client successfully instantiated and configured")
            
            return client
            
        except Exception as e:
            error_msg = f"Failed to instantiate Redis client: {str(e)}"
            logger.error(error_msg)
            
            if self.cab_tracker:
                self.cab_tracker.log_suggestion(
                    "Redis Client Instantiation Error",
                    error_msg,
                    severity='HIGH',
                    context="Check Redis configuration and connectivity",
                    metrics={"redis_url": self._config.get('redis_url', 'not configured')}
                )
            
            raise Exception(error_msg)
    
    def test_redis_connection(self) -> bool:
        """Test Redis client connection and basic operations"""
        try:
            client = self._get_redis_client()
            
            # Test basic operations
            result = client.set_working_memory("test_session", "test content")
            if result.get("status") == "success":
                logger.info("Redis client connection test successful")
                return True
            else:
                logger.warning("Redis client connection test failed")
                return False
                
        except Exception as e:
            logger.error(f"Redis connection test failed: {e}")
            if self.cab_tracker:
                self.cab_tracker.log_suggestion(
                    "Redis Connection Test Failed",
                    f"Connection test error: {str(e)}",
                    severity='MEDIUM',
                    context="Verify Redis server availability and configuration"
                )
            return False
        
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
    cab_tracker.initialize_session("TestUser", "Claude")
    selector = MemorySelector(cab_tracker)
    
    # Test Redis client
    print("Testing Redis client instantiation...")
    success = selector.test_redis_connection()
    print(f"Redis client test: {'PASSED' if success else 'FAILED'}")
    
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
