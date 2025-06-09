# /src/memory_selector.py

"""
Memory System Selector
Implements intelligent routing to appropriate memory systems based on task type
"""
import logging
import os
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum

# Initialize logger for the module
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

        # Initialize clients to None. They will be created on-demand.
        self._redis_client = None
        self._basic_memory_client = None
        self._neo4j_client = None

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
        config_files = self._discover_config_files(config_path)
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

        # Load configuration from the first file found
        for config_file in config_files:
            if os.path.isfile(config_file):
                logger.info(f"Loading configuration from {config_file}")
                if dotenv_available:
                    # Use python-dotenv for proper parsing, loading into environment
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
        Malformed lines are logged as warnings and skipped.
        """
        try:
            with open(env_file, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    if '=' in line:
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip()
                        if value.startswith('"') and value.endswith('"') or \
                           value.startswith("'") and value.endswith("'"):
                            value = value[1:-1]
                        os.environ[key] = value
                    else:
                        logger.warning(f"Malformed line in {env_file} at line {line_num}: '{line}'. Expected KEY=VALUE format.")
        except Exception as e:
            logger.warning(f"Error parsing {env_file}: {e}")

    def _validate_config(self) -> None:
        """Validate loaded configuration and log warnings for missing settings."""
        config_warnings = []

        if not self.config.get('REDIS_URL'):
            config_warnings.append("REDIS_URL not configured - Redis memory system may not function")

        if self.config.get('NEO4J_ENABLED'):
            if not self.config.get('NEO4J_URL'):
                config_warnings.append("NEO4J_URL not configured but Neo4j is enabled")
            if not self.config.get('NEO4J_PASSWORD'):
                config_warnings.append("NEO4J_PASSWORD not configured but Neo4j is enabled")

        if self.config.get('BASIC_MEMORY_ENABLED'):
            basic_path = self.config.get('BASIC_MEMORY_PATH')
            if not basic_path:
                config_warnings.append("BASIC_MEMORY_PATH not configured but Basic Memory is enabled")
            elif not os.path.exists(basic_path):
                config_warnings.append(f"BASIC_MEMORY_PATH does not exist: {basic_path}")

        if not self.config.get('DISABLE_AUTH'):
            if not self.config.get('JWT_SECRET'):
                config_warnings.append("JWT_SECRET not configured but authentication is enabled")
            if not self.config.get('OAUTH2_ISSUER_URL'):
                config_warnings.append("OAUTH2_ISSUER_URL not configured but authentication is enabled")

        for warning in config_warnings:
            logger.warning(f"Configuration warning: {warning}")
            if self.cab_tracker:
                self.cab_tracker.log_suggestion("Configuration Warning", warning, severity='MEDIUM')

    def _initialize_rules(self) -> Dict[TaskType, MemorySystem]:
        """Initialize task type to memory system mapping"""
        return {
            TaskType.USER_IDENTITY: MemorySystem.NEO4J,
            TaskType.RELATIONSHIP_QUERY: MemorySystem.NEO4J,
            TaskType.ENTITY_CONNECTION: MemorySystem.NEO4J,
            TaskType.GRAPH_TRAVERSAL: MemorySystem.NEO4J,

            TaskType.DOCUMENTATION: MemorySystem.BASIC_MEMORY,
            TaskType.STRUCTURED_NOTE: MemorySystem.BASIC_MEMORY,
            TaskType.PERSISTENT_KNOWLEDGE: MemorySystem.BASIC_MEMORY,
            TaskType.MARKDOWN_CONTENT: MemorySystem.BASIC_MEMORY,

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

    def _initialize_client(self, client_type: str, config: Dict[str, Any], create_client: callable):
        """Helper to initialize a client with shared logic"""
        try:
            logger.info(f"Initializing {client_type} client")
            logger.info(f"{client_type} URL/Path: {config.get('url') or config.get('path')}")
            client = create_client()
            if self.cab_tracker:
                self.cab_tracker.log_suggestion(
                    "Client Initialization", f"{client_type} client initialized successfully",
                    severity='LOW', context="Backend client setup"
                )
            return client
        except Exception as e:
            error_msg = f"Failed to initialize {client_type} client: {e}"
            logger.error(error_msg)
            if self.cab_tracker:
                self.cab_tracker.log_suggestion(
                    "Client Initialization Error", error_msg,
                    severity='HIGH', context=f"{client_type} backend unavailable"
                )
            raise

    def _get_redis_client(self):
        """Get Redis client instance (lazy initialization)"""
        if not self._redis_client and self.config.get('REDIS_URL'):
            self._redis_client = self._initialize_client(
                client_type="Redis",
                config={'url': self.config.get('REDIS_URL')},
                create_client=lambda: f"RedisClient({self.config.get('REDIS_URL')})"  # Placeholder
            )
        return self._redis_client

    def _get_basic_memory_client(self):
        """Get Basic Memory client instance (lazy initialization)"""
        if not self._basic_memory_client and self.config.get('BASIC_MEMORY_ENABLED'):
            self._basic_memory_client = self._initialize_client(
                client_type="Basic Memory",
                config={'path': self.config.get('BASIC_MEMORY_PATH')},
                create_client=lambda: f"BasicMemoryClient({self.config.get('BASIC_MEMORY_PATH')})"  # Placeholder
            )
        return self._basic_memory_client

    def _get_neo4j_client(self):
        """Get Neo4j client instance (lazy initialization)"""
        if not self._neo4j_client and self.config.get('NEO4J_ENABLED'):
            self._neo4j_client = self._initialize_client(
                client_type="Neo4j",
                config={'url': self.config.get('NEO4J_URL')},
                create_client=lambda: f"Neo4jClient({self.config.get('NEO4J_URL')})"  # Placeholder
            )
        return self._neo4j_client

    def analyze_task(self, task: str, context: Optional[Dict[str, Any]] = None) -> TaskType:
        """Analyze task to determine its type"""
        # (Implementation not in conflict, retained from original)
        task_lower = task.lower()
        if any(k in task_lower for k in ['relationship', 'connection', 'graph']):
            return TaskType.RELATIONSHIP_QUERY
        if 'user' in task_lower and 'identity' in task_lower:
            return TaskType.USER_IDENTITY
        if any(k in task_lower for k in ['document', 'note', 'report']):
            return TaskType.DOCUMENTATION
        if any(k in task_lower for k in ['conversation', 'semantic', 'remember']):
            return TaskType.CONVERSATION_CONTEXT
        return TaskType.UNKNOWN

    def select_memory_system(self, task: str, context: Optional[Dict[str, Any]] = None) -> Tuple[MemorySystem, TaskType]:
        """Select appropriate memory system for task"""
        # (Implementation not in conflict, retained from original)
        task_type = self.analyze_task(task, context)
        if task_type == TaskType.UNKNOWN:
            primary_system = MemorySystem.REDIS
            logger.warning(f"Unknown task type for: {task[:50]}...")
        else:
            primary_system = self._selection_rules.get(task_type, MemorySystem.REDIS)
        return primary_system, task_type

    def execute_with_fallback(self, task: str, operation_func: callable, context: Optional[Dict[str, Any]] = None) -> Tuple[Any, MemorySystem, bool]:
        """Execute operation with automatic fallback"""
        # (Implementation not in conflict, retained from original)
        primary_system, task_type = self.select_memory_system(task, context)
        fallback_chain = [primary_system] + self._fallback_chains.get(primary_system, [])
        last_error = None
        for i, system in enumerate(fallback_chain):
            try:
                result = operation_func(system, task, context)
                if i > 0:
                    logger.info(f"Successfully used fallback system {system.value}")
                return result, system, (i > 0)
            except Exception as e:
                last_error = e
                logger.warning(f"System {system.value} failed: {str(e)}")
                continue
        logger.error(f"All systems failed for task: {task}")
        raise Exception(f"All memory systems failed. Last error: {last_error}")


class MemoryPropagator:
    """Handles cross-system data propagation"""
    # (Class not in conflict, retained from original)
    def __init__(self, memory_clients: Dict[MemorySystem, Any], cab_tracker=None):
        self.clients = memory_clients
        self.cab_tracker = cab_tracker

    def propagate_data(self, data: Any, source_system: MemorySystem, data_type: str, entity_id: Optional[str] = None):
        # Placeholder for propagation logic
        logger.info(f"Propagating '{data_type}' from {source_system.value} for entity '{entity_id}'")
        return {}


# Example usage pattern
if __name__ == "__main__":
    # Mock CAB tracker for demonstration purposes
    class MockCabTracker:
        def log_suggestion(self, *args, **kwargs):
            print(f"CAB LOG: {args} {kwargs}")

    # Initialize
    cab_tracker = MockCabTracker()
    selector = MemorySelector(cab_tracker=cab_tracker)
    print("Configuration loaded:")
    for key, value in selector.config.items():
        if 'KEY' in key or 'PASSWORD' in key or 'SECRET' in key:
             value = '********' # Avoid printing secrets
        print(f"  {key}: {value}")
    print("-" * 20)

    # Example task selection
    task = "Find all relationships between user and their projects"
    system, task_type = selector.select_memory_system(task)
    print(f"Selected {system.value} for task type {task_type.value}")
    print("-" * 20)

    # Example with fallback
    def mock_operation(system, task, context):
        print(f"Attempting operation on: {system.value}")
        if system == MemorySystem.NEO4J:
            raise Exception("Neo4j unavailable")
        return f"Result from {system.value}"

    result, successful_system, used_fallback = selector.execute_with_fallback(
        task, mock_operation
    )
    print(f"Final Result: {result}")
    print(f"Successful System: {successful_system.value}")
    print(f"Used Fallback: {used_fallback}")