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
        """
        Initialize MemorySelector with configuration loading and validation.

        Args:
            cab_tracker: Optional CAB tracker instance for logging
            config_path: Optional path to configuration file. If None, follows fallback order:
                        .env → .env.production → .env.local
            validate_config: Whether to validate loaded configuration (default: True)
        """
        self.cab_tracker = cab_tracker
        self.config = self._load_config(config_path)

        if validate_config:
            self._validate_config()

        self._selection_rules = self._initialize_rules()
        self._fallback_chains = self._initialize_fallback_chains()

    def _load_config(self, config_path=None) -> Dict[str, str]:
        """Load configuration from environment files with CAB logging."""
        config = {}
        
        # Define fallback order for config files
        if config_path:
            config_files = [config_path]
        else:
            config_files = ['.env', '.env.production', '.env.local']
        
        for config_file in config_files:
            if os.path.exists(config_file):
                try:
                    self._parse_env_file(config_file)
                    if self.cab_tracker:
                        self.cab_tracker.log_suggestion(
                            "Configuration Loaded",
                            f"Successfully loaded configuration from {config_file}",
                            severity='LOW',
                            context="Configuration loading"
                        )
                    break
                except Exception as e:
                    if self.cab_tracker:
                        self.cab_tracker.log_suggestion(
                            "Configuration Error",
                            f"Failed to load configuration from {config_file}: {str(e)}",
                            severity='HIGH',
                            context="Configuration loading"
                        )
                    logger.error(f"Failed to load config from {config_file}: {e}")
        
        # Load from environment variables
        config_keys = [
            'REDIS_URL', 'NEO4J_URL', 'NEO4J_PASSWORD', 'BASIC_MEMORY_PATH',
            'JWT_SECRET', 'OAUTH2_ISSUER_URL', 'CAB_LOG_PATH'
        ]
        
        for key in config_keys:
            config[key] = os.environ.get(key)
        
        return config

    def _parse_env_file(self, file_path: str) -> None:
        """Parse environment file and set environment variables with CAB logging."""
        try:
            with open(file_path, 'r') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    
                    # Skip empty lines and comments
                    if not line or line.startswith('#'):
                        continue
                    
                    # Check for malformed lines
                    if '=' not in line:
                        if self.cab_tracker:
                            self.cab_tracker.log_suggestion(
                                "Configuration Warning",
                                f"Malformed line in {file_path} at line {line_num}: '{line}'",
                                severity='MEDIUM',
                                context="Environment file parsing"
                            )
                        logger.warning(f"Malformed line in {file_path} at line {line_num}: '{line}'. Expected KEY=VALUE format.")
                        continue
                    
                    # Parse key=value
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip()
                    
                    # Handle quoted values
                    if value.startswith('"') and value.endswith('"'):
                        value = value[1:-1]
                    elif value.startswith("'") and value.endswith("'"):
                        value = value[1:-1]
                    
                    os.environ[key] = value
                    
        except Exception as e:
            if self.cab_tracker:
                self.cab_tracker.log_suggestion(
                    "Configuration Error",
                    f"Failed to parse environment file {file_path}: {str(e)}",
                    severity='HIGH',
                    context="Environment file parsing"
                )
            raise

    def _validate_config(self) -> None:
        """Validate configuration and log warnings via CAB tracker."""
        # Basic required configs
        required_configs = {
            'REDIS_URL': 'Redis backend functionality will be disabled',
            'NEO4J_URL': 'Neo4j backend functionality will be disabled',
            'BASIC_MEMORY_PATH': 'Basic Memory backend functionality will be disabled'
        }
        
        for config_key, impact in required_configs.items():
            if not self.config.get(config_key):
                if self.cab_tracker:
                    self.cab_tracker.log_suggestion(
                        "Configuration Warning",
                        f"{config_key} not configured",
                        severity='MEDIUM',
                        context="Configuration validation",
                        metrics={"missing_config": config_key, "impact": impact}
                    )
                logger.warning(f"{config_key} not configured - {impact}")
        
        # Additional validation logic for specific test scenarios
        # Check for Redis memory system configuration
        if not self.config.get('REDIS_URL'):
            logger.warning("Configuration warning: REDIS_URL not configured - Redis memory system may not function")
        
        # Check for Neo4j specific configuration when enabled
        if os.environ.get('NEO4J_ENABLED') == 'true' and not self.config.get('NEO4J_URL'):
            logger.warning("Configuration warning: NEO4J_URL not configured but Neo4j is enabled")
        
        # Check for JWT authentication configuration
        if os.environ.get('DISABLE_AUTH') == 'false' and not self.config.get('JWT_SECRET'):
            logger.warning("Configuration warning: JWT_SECRET not configured but authentication is enabled")

    def _initialize_rules(self) -> Dict[TaskType, MemorySystem]:
        """Initialize task-to-system mapping rules."""
        return {
            # Neo4j tasks
            TaskType.USER_IDENTITY: MemorySystem.NEO4J,
            TaskType.RELATIONSHIP_QUERY: MemorySystem.NEO4J,
            TaskType.ENTITY_CONNECTION: MemorySystem.NEO4J,
            TaskType.GRAPH_TRAVERSAL: MemorySystem.NEO4J,
            
            # Basic Memory tasks
            TaskType.DOCUMENTATION: MemorySystem.BASIC_MEMORY,
            TaskType.STRUCTURED_NOTE: MemorySystem.BASIC_MEMORY,
            TaskType.PERSISTENT_KNOWLEDGE: MemorySystem.BASIC_MEMORY,
            TaskType.MARKDOWN_CONTENT: MemorySystem.BASIC_MEMORY,
            
            # Redis tasks
            TaskType.CONVERSATION_CONTEXT: MemorySystem.REDIS,
            TaskType.SEMANTIC_SEARCH: MemorySystem.REDIS,
            TaskType.PREFERENCE_STORAGE: MemorySystem.REDIS,
            TaskType.SESSION_DATA: MemorySystem.REDIS,
            
            # Fallback
            TaskType.UNKNOWN: MemorySystem.BASIC_MEMORY
        }

    def _initialize_fallback_chains(self) -> Dict[MemorySystem, List[MemorySystem]]:
        """Initialize fallback chains for each memory system."""
        return {
            MemorySystem.NEO4J: [MemorySystem.BASIC_MEMORY, MemorySystem.REDIS],
            MemorySystem.REDIS: [MemorySystem.BASIC_MEMORY, MemorySystem.NEO4J],
            MemorySystem.BASIC_MEMORY: [MemorySystem.REDIS, MemorySystem.NEO4J]
        }

    def store_data(self, data: Dict[str, Any], task_description: str) -> Tuple[bool, MemorySystem, bool]:
        """Store data in appropriate memory system with CAB logging."""
        task_type = self._determine_task_type(task_description)
        primary_system = self._selection_rules.get(task_type, MemorySystem.BASIC_MEMORY)
        
        return self.execute_with_fallback('store', primary_system, data, task_type)

    def retrieve_data(self, query: Dict[str, Any], task_description: str) -> Tuple[Any, MemorySystem, bool]:
        """Retrieve data from appropriate memory system with CAB logging."""
        task_type = self._determine_task_type(task_description)
        primary_system = self._selection_rules.get(task_type, MemorySystem.BASIC_MEMORY)
        
        return self.execute_with_fallback('retrieve', primary_system, query, task_type)

    def _store_in_system(self, system: MemorySystem, data: Dict[str, Any], task_type: TaskType) -> bool:
        """Store data in specified system with CAB logging."""
        if system == MemorySystem.REDIS:
            return self._store_in_redis(data, task_type)
        elif system == MemorySystem.NEO4J:
            return self._store_in_neo4j(data, task_type)
        elif system == MemorySystem.BASIC_MEMORY:
            return self._store_in_basic_memory(data, task_type)
        else:
            if self.cab_tracker:
                self.cab_tracker.log_missing_implementation(
                    f"Store operation for {system.value}",
                    "System-specific store method not implemented"
                )
            raise NotImplementedError(f"Store operation not implemented for {system.value}")

    def _retrieve_from_system(self, system: MemorySystem, query: Dict[str, Any], task_type: TaskType) -> Any:
        """Retrieve data from specified system with CAB logging."""
        if system == MemorySystem.REDIS:
            return self._retrieve_from_redis(query, task_type)
        elif system == MemorySystem.NEO4J:
            return self._retrieve_from_neo4j(query, task_type)
        elif system == MemorySystem.BASIC_MEMORY:
            return self._retrieve_from_basic_memory(query, task_type)
        else:
            if self.cab_tracker:
                self.cab_tracker.log_missing_implementation(
                    f"Retrieve operation for {system.value}",
                    "System-specific retrieve method not implemented"
                )
            raise NotImplementedError(f"Retrieve operation not implemented for {system.value}")

    def _determine_task_type(self, task_description: str) -> TaskType:
        """Determine task type from description with CAB logging for unknown types."""
        task_lower = task_description.lower()
        
        # Neo4j indicators
        if any(keyword in task_lower for keyword in ['user', 'identity', 'profile']):
            return TaskType.USER_IDENTITY
        elif any(keyword in task_lower for keyword in ['relationship', 'relation', 'connect']):
            return TaskType.RELATIONSHIP_QUERY
        elif any(keyword in task_lower for keyword in ['entity', 'connection', 'link']):
            return TaskType.ENTITY_CONNECTION
        elif any(keyword in task_lower for keyword in ['graph', 'traverse', 'path']):
            return TaskType.GRAPH_TRAVERSAL
        
        # Basic Memory indicators
        elif any(keyword in task_lower for keyword in ['document', 'note', 'file']):
            return TaskType.DOCUMENTATION
        elif any(keyword in task_lower for keyword in ['structure', 'organized']):
            return TaskType.STRUCTURED_NOTE
        elif any(keyword in task_lower for keyword in ['knowledge', 'persistent', 'permanent']):
            return TaskType.PERSISTENT_KNOWLEDGE
        elif any(keyword in task_lower for keyword in ['markdown', 'md']):
            return TaskType.MARKDOWN_CONTENT
        
        # Redis indicators
        elif any(keyword in task_lower for keyword in ['conversation', 'context', 'chat']):
            return TaskType.CONVERSATION_CONTEXT
        elif any(keyword in task_lower for keyword in ['search', 'semantic', 'similarity']):
            return TaskType.SEMANTIC_SEARCH
        elif any(keyword in task_lower for keyword in ['preference', 'setting', 'config']):
            return TaskType.PREFERENCE_STORAGE
        elif any(keyword in task_lower for keyword in ['session', 'temporary', 'cache']):
            return TaskType.SESSION_DATA
        
        # Unknown task type
        else:
            if self.cab_tracker:
                self.cab_tracker.log_suggestion(
                    "Task Type Detection",
                    f"Could not determine task type for: '{task_description}'",
                    severity='MEDIUM',
                    context="Task classification needs improvement",
                    metrics={"task_description": task_description}
                )
            return TaskType.UNKNOWN

    # Backend-specific store methods
    def _store_in_redis(self, data: Dict[str, Any], task_type: TaskType) -> bool:
        """Store data in Redis with CAB logging."""
        try:
            client = self._get_redis_client()
            # Implementation placeholder - Redis operations would go here
            if self.cab_tracker:
                self.cab_tracker.log_missing_implementation(
                    "Redis store operation",
                    "Actual Redis client integration not implemented yet"
                )
            raise NotImplementedError("Redis store operation not yet implemented")
        except Exception as e:
            if self.cab_tracker:
                self.cab_tracker.log_suggestion(
                    "API Error",
                    f"Redis store operation failed: {str(e)}",
                    severity='HIGH',
                    context=f"Task type: {task_type.value}",
                    metrics={"system": "redis", "operation": "store", "task_type": task_type.value}
                )
            raise

    def _store_in_neo4j(self, data: Dict[str, Any], task_type: TaskType) -> bool:
        """Store data in Neo4j with CAB logging."""
        try:
            client = self._get_neo4j_client()
            # Implementation placeholder - Neo4j MCP operations would go here
            if self.cab_tracker:
                self.cab_tracker.log_missing_implementation(
                    "Neo4j store operation",
                    "Actual Neo4j MCP client integration not implemented yet"
                )
            raise NotImplementedError("Neo4j store operation not yet implemented")
        except Exception as e:
            if self.cab_tracker:
                self.cab_tracker.log_suggestion(
                    "API Error",
                    f"Neo4j store operation failed: {str(e)}",
                    severity='HIGH',
                    context=f"Task type: {task_type.value}",
                    metrics={"system": "neo4j", "operation": "store", "task_type": task_type.value}
                )
            raise

    def _store_in_basic_memory(self, data: Dict[str, Any], task_type: TaskType) -> bool:
        """Store data in Basic Memory with CAB logging."""
        try:
            client = self._get_basic_memory_client()
            # Implementation placeholder - Basic Memory REST operations would go here
            if self.cab_tracker:
                self.cab_tracker.log_missing_implementation(
                    "Basic Memory store operation",
                    "Actual Basic Memory REST client integration not implemented yet"
                )
            raise NotImplementedError("Basic Memory store operation not yet implemented")
        except Exception as e:
            if self.cab_tracker:
                self.cab_tracker.log_suggestion(
                    "API Error",
                    f"Basic Memory store operation failed: {str(e)}",
                    severity='HIGH',
                    context=f"Task type: {task_type.value}",
                    metrics={"system": "basic_memory", "operation": "store", "task_type": task_type.value}
                )
            raise

    # Backend-specific retrieve methods
    def _retrieve_from_redis(self, query: Dict[str, Any], task_type: TaskType) -> Any:
        """Retrieve data from Redis with CAB logging."""
        try:
            client = self._get_redis_client()
            # Implementation placeholder - Redis operations would go here
            if self.cab_tracker:
                self.cab_tracker.log_missing_implementation(
                    "Redis retrieve operation",
                    "Actual Redis client integration not implemented yet"
                )
            raise NotImplementedError("Redis retrieve operation not yet implemented")
        except Exception as e:
            if self.cab_tracker:
                self.cab_tracker.log_suggestion(
                    "API Error",
                    f"Redis retrieve operation failed: {str(e)}",
                    severity='HIGH',
                    context=f"Task type: {task_type.value}",
                    metrics={"system": "redis", "operation": "retrieve", "task_type": task_type.value}
                )
            raise

    def _retrieve_from_neo4j(self, query: Dict[str, Any], task_type: TaskType) -> Any:
        """Retrieve data from Neo4j with CAB logging."""
        try:
            client = self._get_neo4j_client()
            # Implementation placeholder - Neo4j MCP operations would go here
            if self.cab_tracker:
                self.cab_tracker.log_missing_implementation(
                    "Neo4j retrieve operation",
                    "Actual Neo4j MCP client integration not implemented yet"
                )
            raise NotImplementedError("Neo4j retrieve operation not yet implemented")
        except Exception as e:
            if self.cab_tracker:
                self.cab_tracker.log_suggestion(
                    "API Error",
                    f"Neo4j retrieve operation failed: {str(e)}",
                    severity='HIGH',
                    context=f"Task type: {task_type.value}",
                    metrics={"system": "neo4j", "operation": "retrieve", "task_type": task_type.value}
                )
            raise

    def _retrieve_from_basic_memory(self, query: Dict[str, Any], task_type: TaskType) -> Any:
        """Retrieve data from Basic Memory with CAB logging."""
        try:
            client = self._get_basic_memory_client()
            # Implementation placeholder - Basic Memory REST operations would go here
            if self.cab_tracker:
                self.cab_tracker.log_missing_implementation(
                    "Basic Memory retrieve operation",
                    "Actual Basic Memory REST client integration not implemented yet"
                )
            raise NotImplementedError("Basic Memory retrieve operation not yet implemented")
        except Exception as e:
            if self.cab_tracker:
                self.cab_tracker.log_suggestion(
                    "API Error",
                    f"Basic Memory retrieve operation failed: {str(e)}",
                    severity='HIGH',
                    context=f"Task type: {task_type.value}",
                    metrics={"system": "basic_memory", "operation": "retrieve", "task_type": task_type.value}
                )
            raise

    # Client getter methods
    def _get_redis_client(self):
        """Get Redis client with CAB logging."""
        if not self.config.get('REDIS_URL'):
            if self.cab_tracker:
                self.cab_tracker.log_suggestion(
                    "Configuration Error",
                    "Cannot create Redis client - REDIS_URL not configured",
                    severity='HIGH',
                    context="Client instantiation"
                )
            raise ValueError("REDIS_URL not configured")
        
        if self.cab_tracker:
            self.cab_tracker.log_missing_implementation(
                "Redis client instantiation",
                "Actual Redis client creation not implemented yet"
            )
        raise NotImplementedError("Redis client not yet implemented")

    def _get_neo4j_client(self):
        """Get Neo4j client with CAB logging."""
        if not self.config.get('NEO4J_URL'):
            if self.cab_tracker:
                self.cab_tracker.log_suggestion(
                    "Configuration Error",
                    "Cannot create Neo4j client - NEO4J_URL not configured",
                    severity='HIGH',
                    context="Client instantiation"
                )
            raise ValueError("NEO4J_URL not configured")
        
        if self.cab_tracker:
            self.cab_tracker.log_missing_implementation(
                "Neo4j client instantiation",
                "Actual Neo4j MCP client creation not implemented yet"
            )
        raise NotImplementedError("Neo4j client not yet implemented")

    def _get_basic_memory_client(self):
        """Get Basic Memory client with CAB logging."""
        if not self.config.get('BASIC_MEMORY_PATH'):
            if self.cab_tracker:
                self.cab_tracker.log_suggestion(
                    "Configuration Error",
                    "Cannot create Basic Memory client - BASIC_MEMORY_PATH not configured",
                    severity='HIGH',
                    context="Client instantiation"
                )
            raise ValueError("BASIC_MEMORY_PATH not configured")
        
        if self.cab_tracker:
            self.cab_tracker.log_missing_implementation(
                "Basic Memory client instantiation",
                "Actual Basic Memory REST client creation not implemented yet"
            )
        raise NotImplementedError("Basic Memory client not yet implemented")

    def propagate_data(self, data: Dict[str, Any], source_system: MemorySystem, 
                      target_systems: List[MemorySystem]) -> None:
        """Propagate data across systems with CAB logging for inconsistencies."""
        for target_system in target_systems:
            try:
                # Attempt to propagate to target system
                self._propagate_to_system(data, source_system, target_system)
                
                if self.cab_tracker:
                    self.cab_tracker.log_suggestion(
                        "Data Propagation",
                        f"Successfully propagated data from {source_system.value} to {target_system.value}",
                        severity='LOW',
                        context="Data synchronization"
                    )
                    
            except Exception as e:
                if self.cab_tracker:
                    self.cab_tracker.log_data_inconsistency(
                        entity=str(data.get('id', 'unknown')),
                        systems=[source_system.value, target_system.value],
                        inconsistency_type=f"Propagation failed: {str(e)}"
                    )
                logger.error(f"Failed to propagate data to {target_system.value}: {e}")

    def _propagate_to_system(self, data: Dict[str, Any], source_system: MemorySystem, 
                           target_system: MemorySystem) -> None:
        """Propagate data to specific target system."""
        if self.cab_tracker:
            self.cab_tracker.log_missing_implementation(
                f"Data propagation to {target_system.value}",
                "Specific propagation logic not implemented yet"
            )
        raise NotImplementedError(f"Data propagation to {target_system.value} not yet implemented")

    def get_fallback_chain(self, system: MemorySystem) -> List[MemorySystem]:
        """Get fallback chain for a given memory system."""
        return self._fallback_chains.get(system, [])

    def select_memory_system(self, task_description: str) -> Tuple[MemorySystem, TaskType]:
        """Select primary memory system for a task."""
        task_type = self._determine_task_type(task_description)
        primary_system = self._selection_rules.get(task_type, MemorySystem.BASIC_MEMORY)
        return primary_system, task_type

    def execute_with_fallback(self, task_description_or_operation: str, 
                             operation_or_primary_system=None, data=None, task_type=None) -> Tuple[Any, MemorySystem, bool]:
        """Execute operation with fallback logic - supports multiple call signatures."""
        
        # Handle different call signatures for backward compatibility
        if callable(operation_or_primary_system):
            # Signature: execute_with_fallback(task_description, operation_callable)
            task_description = task_description_or_operation
            operation_callable = operation_or_primary_system
            
            primary_system, determined_task_type = self.select_memory_system(task_description)
            systems_to_try = [primary_system] + self._fallback_chains.get(primary_system, [])
            
            for i, system in enumerate(systems_to_try):
                used_fallback = i > 0
                start_time = time.time()
                
                try:
                    result = operation_callable(system, determined_task_type, {"task": task_description})
                    duration_ms = (time.time() - start_time) * 1000
                    
                    # Log successful operation
                    if self.cab_tracker:
                        self.cab_tracker.log_memory_operation(
                            operation="custom_operation",
                            system=system.value,
                            success=True,
                            duration_ms=duration_ms,
                            fallback_used=used_fallback
                        )
                    
                    return result, system, used_fallback
                    
                except Exception as e:
                    duration_ms = (time.time() - start_time) * 1000
                    
                    # Log failed operation
                    if self.cab_tracker:
                        self.cab_tracker.log_memory_operation(
                            operation="custom_operation",
                            system=system.value,
                            success=False,
                            duration_ms=duration_ms,
                            fallback_used=used_fallback
                        )
                    
                    logger.error(f"Custom operation failed on {system.value}: {e}")
                    
                    # If this is the last system, re-raise the exception
                    if i == len(systems_to_try) - 1:
                        if self.cab_tracker:
                            self.cab_tracker.log_suggestion(
                                "System Failure",
                                f"All systems failed for custom operation",
                                severity='HIGH',
                                context=f"Task: {task_description}, Systems tried: {[s.value for s in systems_to_try]}",
                                metrics={"operation": "custom_operation", "task_description": task_description, "systems_tried": len(systems_to_try)}
                            )
                        raise
                    
                    # Continue to next system
                    continue
        
        else:
            # Original signature: execute_with_fallback(operation, primary_system, data, task_type)
            operation = task_description_or_operation
            primary_system = operation_or_primary_system
            systems_to_try = [primary_system] + self._fallback_chains.get(primary_system, [])
            
            for i, system in enumerate(systems_to_try):
                used_fallback = i > 0
                start_time = time.time()
                
                try:
                    if operation == 'store':
                        result = self._store_in_system(system, data, task_type)
                    elif operation == 'retrieve':
                        result = self._retrieve_from_system(system, data, task_type)
                    else:
                        raise ValueError(f"Unknown operation: {operation}")
                    
                    duration_ms = (time.time() - start_time) * 1000
                    
                    # Log successful operation
                    if self.cab_tracker:
                        self.cab_tracker.log_memory_operation(
                            operation=operation,
                            system=system.value,
                            success=True,
                            duration_ms=duration_ms,
                            fallback_used=used_fallback
                        )
                    
                    return result, system, used_fallback
                    
                except Exception as e:
                    duration_ms = (time.time() - start_time) * 1000
                    
                    # Log failed operation
                    if self.cab_tracker:
                        self.cab_tracker.log_memory_operation(
                            operation=operation,
                            system=system.value,
                            success=False,
                            duration_ms=duration_ms,
                            fallback_used=used_fallback
                        )
                    
                    logger.error(f"Operation {operation} failed on {system.value}: {e}")
                    
                    # If this is the last system, re-raise the exception
                    if i == len(systems_to_try) - 1:
                        if self.cab_tracker:
                            self.cab_tracker.log_suggestion(
                                "System Failure",
                                f"All systems failed for {operation} operation",
                                severity='HIGH',
                                context=f"Task type: {task_type.value}, Systems tried: {[s.value for s in systems_to_try]}",
                                metrics={"operation": operation, "task_type": task_type.value, "systems_tried": len(systems_to_try)}
                            )
                        raise
                    
                    # Continue to next system
                    continue
