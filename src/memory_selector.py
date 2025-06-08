"""
Memory System Selector
Implements intelligent routing to appropriate memory systems based on task type
"""
import logging
import os
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
import time

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
    
    def _load_config(self, config_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Load configuration from .env files with fallback order.
        
        Fallback order:
        1. config_path (if provided)
        2. .env
        3. .env.production  
        4. .env.local
        
        Args:
            config_path: Optional specific path to config file
            
        Returns:
            Dictionary containing configuration values
        """
        # Discover configuration files
        config_files = self._discover_config_files(config_path)
        
        # Parse configuration files
        config = self._parse_config_files(config_files)
        
        return config
    
    def _discover_config_files(self, config_path: Optional[str]) -> List[str]:
        """Determine the order of configuration files to load."""
        config_files = []
        if config_path:
            config_files.append(config_path)
        config_files.extend(['.env', '.env.production', '.env.local'])
        return config_files
    
    def _parse_config_files(self, config_files: List[str]) -> Dict[str, Any]:
        """Parse configuration files and merge their contents."""
        config = {}
        dotenv_available = False
        try:
            from dotenv import load_dotenv
            dotenv_available = True
        except ImportError:
            logger.warning("python-dotenv not available, falling back to manual .env parsing")
        
        # Load configuration files in order
        for config_file in config_files:
            if os.path.isfile(config_file):
                logger.info(f"Loading configuration from {config_file}")
                
                if dotenv_available:
                    # Use python-dotenv for proper parsing
                    load_dotenv(config_file, override=True)
                else:
                    # Manual parsing fallback
                    self._parse_env_file(config_file)
                
                break
        else:
            logger.warning("No configuration file found, using environment variables only")
        
        # Load from environment variables (these take precedence)
        config.update({
            # Network Configuration
            'PORT': os.getenv('PORT', '8000'),
            'MCP_PORT': os.getenv('MCP_PORT', '9000'),
            'HOST': os.getenv('HOST', '0.0.0.0'),
            'SERVER_IP': os.getenv('SERVER_IP'),
            
            # Redis Configuration
            'REDIS_URL': os.getenv('REDIS_URL'),
            'REDIS_PASSWORD': os.getenv('REDIS_PASSWORD'),
            'REDIS_MAX_MEMORY': os.getenv('REDIS_MAX_MEMORY', '4gb'),
            'REDIS_TLS_ENABLED': os.getenv('REDIS_TLS_ENABLED', 'false').lower() == 'true',
            
            # Neo4j Configuration
            'NEO4J_ENABLED': os.getenv('NEO4J_ENABLED', 'true').lower() == 'true',
            'NEO4J_URL': os.getenv('NEO4J_URL'),
            'NEO4J_USERNAME': os.getenv('NEO4J_USERNAME', 'neo4j'),
            'NEO4J_PASSWORD': os.getenv('NEO4J_PASSWORD'),
            'NEO4J_DATABASE': os.getenv('NEO4J_DATABASE', 'neo4j'),
            'NEO4J_ENCRYPTION': os.getenv('NEO4J_ENCRYPTION', 'false').lower() == 'true',
            
            # Basic Memory Configuration  
            'BASIC_MEMORY_ENABLED': os.getenv('BASIC_MEMORY_ENABLED', 'true').lower() == 'true',
            'BASIC_MEMORY_PATH': os.getenv('BASIC_MEMORY_PATH', '/data/obsidian'),
            'BASIC_MEMORY_SYNC': os.getenv('BASIC_MEMORY_SYNC', 'true').lower() == 'true',
            'BASIC_MEMORY_GIT_SYNC': os.getenv('BASIC_MEMORY_GIT_SYNC', 'false').lower() == 'true',
            
            # CAB Configuration
            'CAB_MONITORING_ENABLED': os.getenv('CAB_MONITORING_ENABLED', 'true').lower() == 'true',
            'CAB_LOG_PATH': os.getenv('CAB_LOG_PATH', '/var/log/unified-memory/cab-suggestions.log'),
            'CAB_SEVERITY_THRESHOLD': os.getenv('CAB_SEVERITY_THRESHOLD', 'MEDIUM'),
            
            # Authentication
            'DISABLE_AUTH': os.getenv('DISABLE_AUTH', 'false').lower() == 'true',
            'OAUTH2_ISSUER_URL': os.getenv('OAUTH2_ISSUER_URL'),
            'JWT_SECRET': os.getenv('JWT_SECRET'),
            
            # AI Service Keys
            'OPENAI_API_KEY': os.getenv('OPENAI_API_KEY'),
            'ANTHROPIC_API_KEY': os.getenv('ANTHROPIC_API_KEY'),
        })
        
        return config
    
    def _parse_env_file(self, env_file: str) -> None:
        """
        Manual parsing of .env file when python-dotenv is not available.
        
        Malformed lines are logged as warnings and skipped rather than causing an error.
        
        Args:
            env_file: Path to .env file
        """
        try:
            with open(env_file, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    
                    # Skip empty lines and comments
                    if not line or line.startswith('#'):
                        continue
                    
                    # Parse KEY=VALUE format
                    if '=' in line:
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip()
                        
                        # Remove quotes if present
                        if value.startswith('"') and value.endswith('"'):
                            value = value[1:-1]
                        elif value.startswith("'") and value.endswith("'"):
                            value = value[1:-1]
                        
                        # Set environment variable for consistent access
                        os.environ[key] = value
                    else:
                        # Log warning for malformed lines instead of raising an error
                        # This allows the application to continue running with partial configuration
                        # rather than failing completely due to a single malformed line
                        logger.warning(f"Malformed line in {env_file} at line {line_num}: '{line}'. Expected KEY=VALUE format.")
                        
        except FileNotFoundError as e:
            logger.warning(f"File not found: {env_file}. Ensure the file exists. Error: {e}")
        except PermissionError as e:
            logger.warning(f"Permission denied when accessing {env_file}. Check file permissions. Error: {e}")
        except ValueError as e:
            logger.warning(f"Value error while parsing {env_file}. Check the file format. Error: {e}")
        except Exception as e:
            logger.warning(f"Unexpected error while parsing {env_file}: {e}")
    
    def _validate_config(self) -> None:
        """
        Validate loaded configuration and log warnings for missing essential settings.
        """
        config_warnings = []
        
        # Validate Redis configuration
        if not self.config.get('REDIS_URL'):
            config_warnings.append("REDIS_URL not configured - Redis memory system may not function")
        
        # Validate Neo4j configuration
        if self.config.get('NEO4J_ENABLED') and not self.config.get('NEO4J_URL'):
            config_warnings.append("NEO4J_URL not configured but Neo4j is enabled")
        
        if self.config.get('NEO4J_ENABLED') and not self.config.get('NEO4J_PASSWORD'):
            config_warnings.append("NEO4J_PASSWORD not configured but Neo4j is enabled")
        
        # Validate Basic Memory configuration
        if self.config.get('BASIC_MEMORY_ENABLED'):
            basic_path = self.config.get('BASIC_MEMORY_PATH')
            if not basic_path:
                config_warnings.append("BASIC_MEMORY_PATH not configured but Basic Memory is enabled")
            elif not os.path.exists(basic_path):
                config_warnings.append(f"BASIC_MEMORY_PATH does not exist: {basic_path}")
        
        # Validate CAB configuration
        if self.config.get('CAB_MONITORING_ENABLED'):
            cab_log_path = self.config.get('CAB_LOG_PATH')
            if cab_log_path:
                cab_dir = os.path.dirname(cab_log_path)
                if cab_dir and not os.path.exists(cab_dir):
                    config_warnings.append(f"CAB log directory does not exist: {cab_dir}")
        
        # Validate authentication configuration for production
        if not self.config.get('DISABLE_AUTH'):
            if not self.config.get('JWT_SECRET'):
                config_warnings.append("JWT_SECRET not configured but authentication is enabled")
            if not self.config.get('OAUTH2_ISSUER_URL'):
                config_warnings.append("OAUTH2_ISSUER_URL not configured but authentication is enabled")
        
        # Log warnings via CAB tracker if available
        for warning in config_warnings:
            logger.warning(f"Configuration warning: {warning}")
            if self.cab_tracker:
                self.cab_tracker.log_suggestion(
                    "Configuration Warning",
                    warning,
                    severity='MEDIUM',
                    context="Configuration validation"
                )
        
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
    
    def _get_redis_client(self):
        """
        Get Redis client using loaded configuration.
        
        Returns:
            Redis client instance (placeholder implementation)
        """
        if not self.config.get('REDIS_URL'):
            raise ValueError("Redis URL not configured")
        
        # Placeholder implementation
        # In actual implementation, this would:
        # - Import appropriate Redis client (e.g., MemoryAPIClient, redis-py)
        # - Initialize with URL, password, and other settings from config
        # - Return configured client instance
        logger.info("Creating Redis client (placeholder)")
        raise NotImplementedError("This method is a placeholder and needs to be implemented.")
    
    def _get_basic_memory_client(self):
        """
        Get Basic Memory client using loaded configuration.
        
        Returns:
            Basic Memory client instance (placeholder implementation)
        """
        if not self.config.get('BASIC_MEMORY_ENABLED'):
            raise ValueError("Basic Memory not enabled")
        
        if not self.config.get('BASIC_MEMORY_PATH'):
            raise ValueError("Basic Memory path not configured")
        
        # Placeholder implementation
        # In actual implementation, this would:
        # - Use httpx or requests for REST API interaction
        # - Configure with base URL and auth from loaded parameters
        # - Or implement MCP client for /mcp endpoint
        logger.info("Creating Basic Memory client (placeholder)")
        raise NotImplementedError("This method is a placeholder and needs to be implemented.")
    
    def _get_neo4j_client(self):
        """
        Get Neo4j client using loaded configuration.
        
        Returns:
            Neo4j client instance (placeholder implementation)
        """
        if not self.config.get('NEO4J_ENABLED'):
            raise ValueError("Neo4j not enabled")
        
        if not self.config.get('NEO4J_URL'):
            raise ValueError("Neo4j URL not configured")
        
        if not self.config.get('NEO4J_PASSWORD'):
            raise ValueError("Neo4j password not configured")
        
        # Placeholder implementation  
        # In actual implementation, this would:
        # - Create helper/wrapper for MCP requests (JSON payloads via HTTP POST)
        # - Configure with Neo4j server URLs from config
        # - Handle authentication and connection pooling
        logger.info("Creating Neo4j client (placeholder)")
        return None


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
