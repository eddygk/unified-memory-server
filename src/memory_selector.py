# /src/memory_selector.py

"""
Memory System Selector
Implements intelligent routing to appropriate memory systems based on task type
"""
import logging
import os
import re
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
from dataclasses import dataclass
import time

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


class OperationType(Enum):
    """Types of operations that can be performed"""
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    SEARCH = "search"
    ANALYZE = "analyze"


@dataclass
class TaskAnalysis:
    """Detailed analysis of a task including confidence and reasoning"""
    task_type: TaskType
    operation_type: OperationType
    entities: List[str]
    confidence: float
    reasoning: str
    patterns_matched: List[str]


class IntentAnalyzer:
    """Advanced intent analyzer for sophisticated task determination"""
    
    def __init__(self):
        """Initialize the intent analyzer with compiled patterns"""
        self._compile_patterns()
        
    def _compile_patterns(self):
        """Compile regex patterns for efficient matching"""
        # Relationship patterns
        self.relationship_patterns = [
            re.compile(r'how are .+ connected to', re.IGNORECASE),
            re.compile(r'find relationships? between', re.IGNORECASE),
            re.compile(r'map the connections?', re.IGNORECASE),
            re.compile(r'trace the path from .+ to', re.IGNORECASE),
            re.compile(r'relationship|connection|graph', re.IGNORECASE),
        ]
        
        # User identity patterns
        self.user_identity_patterns = [
            re.compile(r'who is this user', re.IGNORECASE),
            re.compile(r'my profile information', re.IGNORECASE),
            re.compile(r'tell me about the user', re.IGNORECASE),
            re.compile(r'user.*identity', re.IGNORECASE),
        ]
        
        # Documentation patterns  
        self.documentation_patterns = [
            re.compile(r'create comprehensive documentation', re.IGNORECASE),
            re.compile(r'generate detailed guide', re.IGNORECASE),
            re.compile(r'write structured report', re.IGNORECASE),
            re.compile(r'document|note|report', re.IGNORECASE),
        ]
        
        # Conversation context patterns
        self.conversation_patterns = [
            re.compile(r'remember our previous conversation', re.IGNORECASE),
            re.compile(r'what did we discuss earlier', re.IGNORECASE),
            re.compile(r'conversation history', re.IGNORECASE),
            re.compile(r'what did .+ discuss', re.IGNORECASE),
            re.compile(r'conversation|semantic|remember|discuss', re.IGNORECASE),
        ]
        
        # Search patterns
        self.search_patterns = [
            re.compile(r'find similar content', re.IGNORECASE),
            re.compile(r'search for related documents', re.IGNORECASE),
            re.compile(r'semantic search', re.IGNORECASE),
            re.compile(r'find.*similar|search.*related', re.IGNORECASE),
        ]
        
        # Entity patterns
        self.entity_patterns = {
            'user': re.compile(r'\b(user|person|individual|me|myself|i)\b', re.IGNORECASE),
            'project': re.compile(r'\b(projects?|tasks?|assignments?|work|jobs?)\b', re.IGNORECASE), 
            'document': re.compile(r'\b(documents?|files?|notes?|papers?|reports?|guides?|documentation)\b', re.IGNORECASE),
            'relationship': re.compile(r'\b(relationships?|connections?|links?|associations?|bonds?)\b', re.IGNORECASE),
            'conversation': re.compile(r'\b(conversations?|chats?|discussions?|talks?|dialogues?)\b', re.IGNORECASE),
            'memory': re.compile(r'\b(memory|memories|remember|recall|stored)\b', re.IGNORECASE),
        }
        
        # Operation patterns
        self.operation_patterns = {
            OperationType.CREATE: re.compile(r'\b(create|make|generate|add|new|build|establish|form)\b', re.IGNORECASE),
            OperationType.READ: re.compile(r'\b(get|retrieve|fetch|show|display|read|view|see|find)\b', re.IGNORECASE),
            OperationType.UPDATE: re.compile(r'\b(update|modify|change|edit|revise|alter|adjust)\b', re.IGNORECASE),
            OperationType.DELETE: re.compile(r'\b(delete|remove|clear|erase|drop|eliminate)\b', re.IGNORECASE),
            OperationType.SEARCH: re.compile(r'\b(search|look|locate|seek|query|explore)\b', re.IGNORECASE),
            OperationType.ANALYZE: re.compile(r'\b(analyze|examine|investigate|study|assess|evaluate)\b', re.IGNORECASE),
        }
        
        # Confidence boosters
        self.confidence_boosters = [
            re.compile(r'\b(between|connected|linked)\b', re.IGNORECASE),
        ]
    
    def analyze(self, task: str, context: Optional[Dict[str, Any]] = None) -> TaskAnalysis:
        """Perform detailed analysis of a task"""
        task_lower = task.lower()
        entities = self._extract_entities(task)
        operation_type = self._detect_operation_type(task)
        patterns_matched = []
        confidence = 0.0
        
        # Determine task type and build confidence
        task_type = TaskType.UNKNOWN
        reasoning_parts = []
        
        # Check search patterns first if we detected search operation
        if operation_type == OperationType.SEARCH:
            for pattern in self.search_patterns:
                if pattern.search(task):
                    task_type = TaskType.SEMANTIC_SEARCH
                    patterns_matched.append(pattern.pattern)
                    confidence += 0.3
                    reasoning_parts.append("search pattern with search operation matched")
                    break
            
            # If no specific search pattern matched but we detected search operation, 
            # still classify as semantic search with lower confidence
            if task_type == TaskType.UNKNOWN:
                task_type = TaskType.SEMANTIC_SEARCH
                confidence += 0.2
                reasoning_parts.append("search operation detected")
        
        # Check relationship patterns
        if task_type == TaskType.UNKNOWN:
            for pattern in self.relationship_patterns:
                if pattern.search(task):
                    task_type = TaskType.RELATIONSHIP_QUERY
                    patterns_matched.append(pattern.pattern)
                    confidence += 0.3
                    reasoning_parts.append("relationship pattern matched")
                    break
        
        # Check user identity patterns
        if task_type == TaskType.UNKNOWN:
            for pattern in self.user_identity_patterns:
                if pattern.search(task):
                    task_type = TaskType.USER_IDENTITY
                    patterns_matched.append(pattern.pattern)
                    confidence += 0.3
                    reasoning_parts.append("user identity pattern matched")
                    break
        
        # Check conversation patterns
        if task_type == TaskType.UNKNOWN:
            for pattern in self.conversation_patterns:
                if pattern.search(task):
                    task_type = TaskType.CONVERSATION_CONTEXT
                    patterns_matched.append(pattern.pattern)
                    confidence += 0.3
                    reasoning_parts.append("conversation pattern matched")
                    break
        
        # Check documentation patterns
        if task_type == TaskType.UNKNOWN:
            for pattern in self.documentation_patterns:
                if pattern.search(task):
                    task_type = TaskType.DOCUMENTATION
                    patterns_matched.append(pattern.pattern)
                    confidence += 0.3
                    reasoning_parts.append("documentation pattern matched")
                    break
        
        # Add confidence for entities
        entity_confidence = min(len(entities) * 0.2, 0.4)
        confidence += entity_confidence
        if entities:
            reasoning_parts.append(f"entities found: {', '.join(entities)}")
        
        # Add confidence for operation type
        if operation_type != OperationType.READ:  # READ is default, so less significant
            confidence += 0.2
            reasoning_parts.append(f"operation type: {operation_type.value}")
        
        # Check confidence boosters
        for pattern in self.confidence_boosters:
            if pattern.search(task):
                confidence += 0.2
                reasoning_parts.append("confidence boosting language detected")
                break
        
        # Consider context hints
        if context:
            if context.get('needs_persistence'):
                if task_type == TaskType.UNKNOWN:
                    task_type = TaskType.PERSISTENT_KNOWLEDGE
                confidence += 0.2
                reasoning_parts.append("persistence context hint")
        
        # Cap confidence at 1.0
        confidence = min(confidence, 1.0)
        
        reasoning = f"Analysis based on: {'; '.join(reasoning_parts)}" if reasoning_parts else "No clear patterns identified"
        
        return TaskAnalysis(
            task_type=task_type,
            operation_type=operation_type,
            entities=entities,
            confidence=confidence,
            reasoning=reasoning,
            patterns_matched=patterns_matched
        )
    
    def _extract_entities(self, task: str) -> List[str]:
        """Extract entities from task text"""
        entities = []
        for entity_type, pattern in self.entity_patterns.items():
            if pattern.search(task):
                entities.append(entity_type)
        return entities
    
    def _detect_operation_type(self, task: str) -> OperationType:
        """Detect the operation type from task text"""
        task_lower = task.lower()
        
        # Check for search-related context first (more specific)
        if any(word in task_lower for word in ['similar', 'related', 'like', 'semantic']):
            # If we have search context words, check for search operations
            if any(word in task_lower for word in ['find', 'search', 'look', 'locate', 'seek']):
                return OperationType.SEARCH
        
        # Check other operation types in order of specificity
        for op_type, pattern in self.operation_patterns.items():
            if op_type == OperationType.SEARCH:
                continue  # Already handled above
            if pattern.search(task):
                return op_type
                
        return OperationType.READ  # Default operation type


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
        
        # Initialize the intent analyzer for enhanced task determination
        self._intent_analyzer = IntentAnalyzer()

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

    def get_task_analysis(self, task: str, context: Optional[Dict[str, Any]] = None) -> TaskAnalysis:
        """
        Get detailed task analysis including confidence and reasoning.
        
        Returns detailed analysis including:
        - task_type: Determined TaskType
        - operation_type: Detected OperationType  
        - entities: List of extracted entities
        - confidence: Confidence score (0.0-1.0)
        - reasoning: Human-readable explanation
        - patterns_matched: List of matched patterns
        """
        return self._intent_analyzer.analyze(task, context)

    def analyze_task(self, task: str, context: Optional[Dict[str, Any]] = None) -> TaskType:
        """Analyze task to determine its type"""
        # Use enhanced analysis with confidence-based fallback
        try:
            analysis = self._intent_analyzer.analyze(task, context)
            
            # If confidence is too low, fall back to legacy analysis
            if analysis.confidence < 0.3:
                if self.cab_tracker:
                    self.cab_tracker.log_suggestion(
                        "Enhanced Analysis Fallback", 
                        f"Low confidence ({analysis.confidence:.2f}) for task: {task[:50]}..., using legacy analysis",
                        severity='LOW', context="Task determination fallback"
                    )
                return self._legacy_analyze_task(task, context)
            
            # Log low confidence analyses for monitoring
            if analysis.confidence < 0.5 and self.cab_tracker:
                self.cab_tracker.log_suggestion(
                    "Low Confidence Analysis",
                    f"Task analysis confidence: {analysis.confidence:.2f} for task: {task[:50]}...",
                    severity='MEDIUM', context="Task determination monitoring"
                )
            
            return analysis.task_type
            
        except Exception as e:
            logger.warning(f"Enhanced analysis failed: {e}, falling back to legacy")
            if self.cab_tracker:
                self.cab_tracker.log_suggestion(
                    "Enhanced Analysis Error",
                    f"Enhanced analysis failed with error: {e}, using legacy fallback",
                    severity='HIGH', context="Task determination error"
                )
            return self._legacy_analyze_task(task, context)

    def _legacy_analyze_task(self, task: str, context: Optional[Dict[str, Any]] = None) -> TaskType:
        """Legacy task analysis using simple keyword matching"""
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