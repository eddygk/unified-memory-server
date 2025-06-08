"""
Memory System Selector
Implements intelligent routing to appropriate memory systems based on task type
"""
import logging
import os
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
import time

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None

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
    
    def __init__(self, cab_tracker=None, config_path=None, validate_config=True):
        self.cab_tracker = cab_tracker
        self._selection_rules = self._initialize_rules()
        self._fallback_chains = self._initialize_fallback_chains()
        
        # Load configuration
        self.config = self._load_config(config_path)
        if validate_config:
            self._validate_config()
        
        # Initialize clients (placeholders for now)
        self._redis_client = None
        self._basic_memory_client = None
        self._neo4j_client = None
        
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
    
    def _load_config(self, config_path: Optional[str] = None) -> Dict[str, Any]:
        """Load configuration from .env file"""
        config = {}
        
        # Load from .env file if python-dotenv is available
        if load_dotenv is not None:
            # Try different .env file locations
            env_files = [
                config_path,
                '.env',
                '.env.production',
                '.env.local'
            ]
            
            for env_file in env_files:
                if env_file and os.path.exists(env_file):
                    logger.info(f"Loading configuration from {env_file}")
                    load_dotenv(env_file)
                    break
            else:
                logger.warning("No .env file found, using environment variables only")
        else:
            logger.warning("python-dotenv not available, using environment variables only")
        
        # Load Redis configuration
        config['redis'] = {
            'url': os.getenv('REDIS_URL', 'redis://localhost:6379'),
            'password': os.getenv('REDIS_PASSWORD'),
            'enabled': os.getenv('REDIS_ENABLED', 'true').lower() == 'true'
        }
        
        # Load Neo4j configuration
        config['neo4j'] = {
            'url': os.getenv('NEO4J_URL', 'bolt://localhost:7687'),
            'username': os.getenv('NEO4J_USERNAME', 'neo4j'),
            'password': os.getenv('NEO4J_PASSWORD'),
            'database': os.getenv('NEO4J_DATABASE', 'neo4j'),
            'enabled': os.getenv('NEO4J_ENABLED', 'true').lower() == 'true'
        }
        
        # Load Basic Memory configuration
        config['basic_memory'] = {
            'path': os.getenv('BASIC_MEMORY_PATH', '/data/obsidian'),
            'url': os.getenv('BASIC_MEMORY_URL', 'http://localhost:8080'),
            'enabled': os.getenv('BASIC_MEMORY_ENABLED', 'true').lower() == 'true'
        }
        
        # Load CAB configuration
        config['cab'] = {
            'enabled': os.getenv('CAB_MONITORING_ENABLED', 'true').lower() == 'true',
            'log_path': os.getenv('CAB_LOG_PATH', '/var/log/unified-memory/cab-suggestions.log')
        }
        
        return config
    
    def _validate_config(self) -> None:
        """Validate that essential configuration is present"""
        missing_config = []
        warnings = []
        
        # Check Redis configuration
        if self.config['redis']['enabled']:
            if not self.config['redis']['url']:
                missing_config.append("REDIS_URL")
            if not self.config['redis']['password']:
                warnings.append("REDIS_PASSWORD not set - using default authentication")
        
        # Check Neo4j configuration
        if self.config['neo4j']['enabled']:
            if not self.config['neo4j']['url']:
                missing_config.append("NEO4J_URL")
            if not self.config['neo4j']['password']:
                missing_config.append("NEO4J_PASSWORD")
            if not self.config['neo4j']['username']:
                warnings.append("NEO4J_USERNAME not set - using default 'neo4j'")
        
        # Check Basic Memory configuration
        if self.config['basic_memory']['enabled']:
            if not self.config['basic_memory']['path'] and not self.config['basic_memory']['url']:
                missing_config.append("BASIC_MEMORY_PATH or BASIC_MEMORY_URL")
        
        # Log warnings
        for warning in warnings:
            logger.warning(f"Configuration warning: {warning}")
            if self.cab_tracker:
                self.cab_tracker.log_suggestion(
                    "Configuration Warning",
                    warning,
                    severity='LOW',
                    context="Configuration validation"
                )
        
        # Log and raise errors for missing essential config
        if missing_config:
            error_msg = f"Missing essential configuration: {', '.join(missing_config)}"
            logger.error(error_msg)
            
            if self.cab_tracker:
                self.cab_tracker.log_suggestion(
                    "Missing Configuration",
                    error_msg,
                    severity='HIGH',
                    context="Essential backend connection parameters missing"
                )
            
            raise ValueError(f"Configuration validation failed: {error_msg}")
        
        logger.info("Configuration validation passed")
    
    def _get_redis_client(self):
        """Get Redis client instance"""
        if not self._redis_client and self.config['redis']['enabled']:
            redis_config = self.config['redis']
            self._redis_client = self._initialize_client(
                client_type="Redis",
                config=redis_config,
                create_client=lambda: f"RedisClient({redis_config['url']})"
            )
        return self._redis_client
    
    def _initialize_client(self, client_type: str, config: Dict[str, Any], create_client: callable):
        """Helper to initialize a client with shared logic"""
        try:
            logger.info(f"Initializing {client_type} client")
            logger.info(f"{client_type} URL: {config['url']}")
            
            client = create_client()
            
            if self.cab_tracker:
                self.cab_tracker.log_suggestion(
                    "Client Initialization",
                    f"{client_type} client initialized successfully",
                    severity='LOW',
                    context="Backend client setup"
                )
            return client
        except Exception as e:
            error_msg = f"Failed to initialize {client_type} client: {e}"
            logger.error(error_msg)
            
            if self.cab_tracker:
                self.cab_tracker.log_suggestion(
                    "Client Initialization Error",
                    error_msg,
                    severity='HIGH',
                    context=f"{client_type} backend unavailable"
                )
            raise
    
    def _get_basic_memory_client(self):
        """Get Basic Memory client instance"""
        if not self._basic_memory_client and self.config['basic_memory']['enabled']:
            try:
                # This is a placeholder for actual Basic Memory client instantiation
                logger.info("Initializing Basic Memory client")
                
                basic_config = self.config['basic_memory']
                logger.info(f"Basic Memory path: {basic_config['path']}")
                
                # Placeholder for actual client creation
                # import httpx or requests for REST API interaction
                # self._basic_memory_client = httpx.Client(base_url=basic_config['url'])
                
                # For now, just log that we would create the client
                self._basic_memory_client = f"BasicMemoryClient({basic_config['path']})"
                
                if self.cab_tracker:
                    self.cab_tracker.log_suggestion(
                        "Client Initialization",
                        "Basic Memory client initialized successfully",
                        severity='LOW',
                        context="Backend client setup"
                    )
                
            except Exception as e:
                error_msg = f"Failed to initialize Basic Memory client: {e}"
                logger.error(error_msg)
                
                if self.cab_tracker:
                    self.cab_tracker.log_suggestion(
                        "Client Initialization Error",
                        error_msg,
                        severity='HIGH',
                        context="Basic Memory backend unavailable"
                    )
                raise
        
        return self._basic_memory_client
    
    def _get_neo4j_client(self):
        """Get Neo4j client instance"""
        if not self._neo4j_client and self.config['neo4j']['enabled']:
            try:
                # This is a placeholder for actual Neo4j MCP client instantiation
                logger.info("Initializing Neo4j client")
                
                neo4j_config = self.config['neo4j']
                logger.info(f"Neo4j URL: {neo4j_config['url']}")
                
                # Placeholder for actual MCP client creation
                # This would create a helper/wrapper for MCP requests to Neo4j
                # self._neo4j_client = Neo4jMCPClient(
                #     url=neo4j_config['url'],
                #     username=neo4j_config['username'],
                #     password=neo4j_config['password'],
                #     database=neo4j_config['database']
                # )
                
                # For now, just log that we would create the client
                self._neo4j_client = f"Neo4jClient({neo4j_config['url']})"
                
                if self.cab_tracker:
                    self.cab_tracker.log_suggestion(
                        "Client Initialization",
                        "Neo4j client initialized successfully",
                        severity='LOW',
                        context="Backend client setup"
                    )
                
            except Exception as e:
                error_msg = f"Failed to initialize Neo4j client: {e}"
                logger.error(error_msg)
                
                if self.cab_tracker:
                    self.cab_tracker.log_suggestion(
                        "Client Initialization Error",
                        error_msg,
                        severity='HIGH',
                        context="Neo4j backend unavailable"
                    )
                raise
        
        return self._neo4j_client
    
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
