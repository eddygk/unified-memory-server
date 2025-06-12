# /src/memory_selector.py

"""
Memory System Selector
Implements intelligent routing to appropriate memory systems based on task type
"""
import logging
import os
import re
import socket
import sys
import textwrap
from typing import Dict, List, Optional, Any, Tuple, NamedTuple
from enum import Enum
import requests


class ConnectivityError(Exception):
    """Custom exception for connectivity issues in test mode"""
    pass


class Neo4jClientUnavailableError(Exception):
    """Custom exception for Neo4j MCP client unavailability"""
    pass

# Initialize logger for the module
logger = logging.getLogger(__name__)

# Configuration constants
FALLBACK_THRESHOLD = 0.3  # Confidence threshold below which fallback to legacy analysis is used
INTERNAL_HOSTNAMES = ['basic-memory', 'neo4j', 'redis', 'localhost']  # Internal Docker hostnames


def format_cypher_query(query: str) -> str:
    """
    Format a Cypher query by removing common indentation and leading/trailing whitespace.
    
    This helper function encapsulates the repeated pattern of textwrap.dedent(...).strip()
    used throughout the codebase for Cypher query formatting.
    
    Args:
        query: The raw Cypher query string (typically an f-string with multiline content)
        
    Returns:
        The formatted query string with consistent indentation removed and stripped
    """
    return textwrap.dedent(query).strip()


def check_connectivity_in_test_mode(url: str, operation_name: str, test_mode: bool, service_name: str = None) -> None:
    """
    Check connectivity in test mode for internal hostnames.
    
    Args:
        url: The URL to check connectivity for
        operation_name: Name of the operation being performed (for logging)
        test_mode: Whether test mode is enabled
        service_name: Optional service name for error messages (defaults to "Server")
        
    Returns:
        None if connectivity check should be skipped or server is reachable
        
    Raises:
        ConnectivityError: If server is unreachable in test mode
    """
    if not test_mode:
        return None
        
    from urllib.parse import urlparse
    parsed_url = urlparse(url)
    hostname = parsed_url.hostname
    
    # Check if the hostname is in the list of internal Docker hostnames
    if hostname in INTERNAL_HOSTNAMES:
        try:
            socket.gethostbyname(hostname)
        except (socket.gaierror, socket.error):
            logger.warning(f"Test mode: Skipping {operation_name} to unreachable hostname '{hostname}'")
            service_prefix = service_name if service_name else "Server"
            raise ConnectivityError(f"Test mode: {service_prefix} at {hostname} is not reachable (expected in development/CI environment)")
    
    return None


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


class TaskAnalysis(NamedTuple):
    """Detailed analysis of a task"""
    task_type: TaskType
    operation_type: OperationType
    entities: List[str]
    confidence: float
    reasoning: str
    patterns_matched: List[str]


class Neo4jMCPClient:
    """Client for interacting with Neo4j MCP servers (mcp-neo4j-memory and mcp-neo4j-cypher)"""
    
    def __init__(self, memory_server_url: str, cypher_server_url: str, timeout: int = 30, test_mode: bool = False):
        """
        Initialize Neo4j MCP client
        
        Args:
            memory_server_url: URL for the mcp-neo4j-memory server
            cypher_server_url: URL for the mcp-neo4j-cypher server
            timeout: Request timeout in seconds
            test_mode: If True, avoid actual network calls (for testing/development)
        """
        self.memory_server_url = memory_server_url.rstrip('/')
        self.cypher_server_url = cypher_server_url.rstrip('/')
        self.timeout = timeout
        self.test_mode = test_mode
        self.session = requests.Session()
        
        # Set common headers for MCP requests
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
    
    def send_memory_request(self, method: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Send request to mcp-neo4j-memory server"""
        return self._send_mcp_request(self.memory_server_url, method, params)
    
    def send_cypher_request(self, method: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Send request to mcp-neo4j-cypher server"""
        return self._send_mcp_request(self.cypher_server_url, method, params)
    
    def _send_mcp_request(self, url: str, method: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Send MCP request to specified server"""
        # Check connectivity in test mode
        check_connectivity_in_test_mode(url, "network call", self.test_mode, "Neo4j MCP server")
        
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": method,
            "params": params or {}
        }
        
        response = self.session.post(url, json=payload, timeout=self.timeout)
        response.raise_for_status()
        
        result = response.json()
        
        # Check for JSON-RPC errors
        if "error" in result:
            raise Exception(f"MCP Error: {result['error']}")
        
        return result.get("result", {})
    
    def create_entities(self, entities: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create entities using mcp-neo4j-memory"""
        return self.send_memory_request("create_entities", {"entities": entities})
    
    def search_nodes(self, query: str, filters: Dict[str, Any] = None) -> Dict[str, Any]:
        """Search nodes using mcp-neo4j-memory"""
        params = {"query": query}
        if filters:
            params.update(filters)
        return self.send_memory_request("search_nodes", params)
    
    def execute_cypher(self, query: str, parameters: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute raw Cypher query using mcp-neo4j-cypher"""
        params = {"query": query}
        if parameters:
            params["parameters"] = parameters
        return self.send_cypher_request("execute_cypher", params)
    
    def health_check(self) -> bool:
        """Check if both MCP servers are healthy"""
        try:
            # Try a simple request to both servers
            self.send_memory_request("health_check")
            self.send_cypher_request("health_check")
            return True
        except requests.exceptions.RequestException as e:
            logger.error("Health check failed due to a RequestException: %s", e, exc_info=True)
            return False
        except (ValueError, TypeError) as e:
            logger.error("Health check failed due to a known exception: %s", e, exc_info=True)
            return False
        except Exception as e:
            logger.critical("Health check failed due to an unexpected exception: %s", e, exc_info=True)
            raise


class BasicMemoryClient:
    """Client for interacting with basicmachines-co/basic-memory REST API"""
    
    def __init__(self, base_url: str, auth_token: Optional[str] = None, timeout: int = 30, test_mode: bool = False):
        """
        Initialize Basic Memory client
        
        Args:
            base_url: Base URL for the Basic Memory API
            auth_token: Optional authentication token
            timeout: Request timeout in seconds
            test_mode: If True, avoid actual network calls (for testing/development)
        """
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.test_mode = test_mode
        self.session = requests.Session()
        
        # Set up authentication if provided
        if auth_token:
            self.session.headers.update({'Authorization': f'Bearer {auth_token}'})
        
        # Set common headers
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
    
    def _check_connectivity_or_skip(self, operation_name: str) -> Optional[Dict[str, Any]]:
        """
        Check connectivity in test mode, raise exception if server is unreachable.
        
        Returns:
            None if server is reachable or test mode is disabled
            
        Raises:
            ConnectivityError if server is unreachable in test mode
        """
        check_connectivity_in_test_mode(self.base_url, operation_name, self.test_mode, "Basic Memory server")
        return None

    def store_entity(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Store an entity in Basic Memory"""
        self._check_connectivity_or_skip("store_entity")
            
        url = f"{self.base_url}/entities"
        response = self.session.post(url, json=data, timeout=self.timeout)
        response.raise_for_status()
        return response.json()
    
    def search_entities(self, query: str, filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Search for entities in Basic Memory"""
        self._check_connectivity_or_skip("search_entities")
            
        url = f"{self.base_url}/search"
        payload = {'query': query}
        if filters:
            payload.update(filters)
        
        response = self.session.post(url, json=payload, timeout=self.timeout)
        response.raise_for_status()
        return response.json()
    
    def get_entity(self, entity_id: str) -> Dict[str, Any]:
        """Retrieve a specific entity by ID"""
        self._check_connectivity_or_skip("get_entity")
            
        url = f"{self.base_url}/entities/{entity_id}"
        response = self.session.get(url, timeout=self.timeout)
        response.raise_for_status()
        return response.json()
    
    def update_entity(self, entity_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing entity"""
        self._check_connectivity_or_skip("update_entity")
            
        url = f"{self.base_url}/entities/{entity_id}"
        response = self.session.put(url, json=data, timeout=self.timeout)
        response.raise_for_status()
        return response.json()
    
    def delete_entity(self, entity_id: str) -> None:
        """Delete an entity by ID"""
        self._check_connectivity_or_skip("delete_entity")
            
        url = f"{self.base_url}/entities/{entity_id}"
        response = self.session.delete(url, timeout=self.timeout)
        response.raise_for_status()
    
    def get_tree(self) -> Dict[str, Any]:
        """Get the tree structure of entities"""
        self._check_connectivity_or_skip("get_tree")
            
        url = f"{self.base_url}/tree"
        response = self.session.get(url, timeout=self.timeout)
        response.raise_for_status()
        return response.json()
    
    def health_check(self) -> bool:
        """Check if the Basic Memory service is healthy"""
        if self.test_mode:
            try:
                self._check_connectivity_or_skip("health_check")
            except (socket.error, ConnectivityError):
                return False  # Unreachable in test mode
        
        try:
            url = f"{self.base_url}/health"
            response = self.session.get(url, timeout=5)
            return response.status_code == 200
        except requests.exceptions.RequestException as e:
            logger.error("Health check failed due to a request exception: %s", e, exc_info=True)
            return False
        except ValueError as e:
            logger.error("Health check failed due to a ValueError: %s", e, exc_info=True)
            return False


class IntentAnalyzer:
    """Advanced intent analyzer for sophisticated task determination"""
    
    def __init__(self):
        """Initialize the intent analyzer with compiled patterns"""
        self._compile_patterns()
        
    def _compile_patterns(self):
        """Compile regex patterns for efficient matching"""
        self.relationship_patterns = [
            re.compile(r'how\s+are\s+\w+\s+connected\s+to\s+\w+', re.IGNORECASE),
            re.compile(r'find\s+relationships?\s+between', re.IGNORECASE),
            re.compile(r'map\s+the\s+connections?', re.IGNORECASE),
            re.compile(r'trace\s+the\s+path\s+from\s+\w+\s+to\s+\w+', re.IGNORECASE),
            re.compile(r'connected\s+to\s+(this|the)', re.IGNORECASE),
            re.compile(r'members?\s+connected\s+to', re.IGNORECASE),
            re.compile(r'relationship|connection|graph', re.IGNORECASE)
        ]
        
        self.user_identity_patterns = [
            re.compile(r'who\s+is\s+this\s+user', re.IGNORECASE),
            re.compile(r'my\s+profile\s+information', re.IGNORECASE),
            re.compile(r'tell\s+me\s+about\s+the\s+user', re.IGNORECASE),
            re.compile(r'user.*identity', re.IGNORECASE)
        ]
        
        self.documentation_patterns = [
            re.compile(r'create\s+comprehensive\s+documentation', re.IGNORECASE),
            re.compile(r'generate\s+detailed\s+guide', re.IGNORECASE),
            re.compile(r'write\s+structured\s+report', re.IGNORECASE),
            re.compile(r'document|note|report', re.IGNORECASE)
        ]
        
        self.conversation_context_patterns = [
            re.compile(r'remember\s+our\s+previous\s+conversation', re.IGNORECASE),
            re.compile(r'what\s+did\s+we\s+discuss\s+earlier', re.IGNORECASE),
            re.compile(r'what\s+did\s+we\s+discuss\s+yesterday', re.IGNORECASE),
            re.compile(r'conversation\s+history', re.IGNORECASE),
            re.compile(r'previous\s+discussion', re.IGNORECASE),
            re.compile(r'conversation|semantic|remember', re.IGNORECASE)
        ]
        
        self.search_patterns = [
            re.compile(r'find\s+similar\s+content', re.IGNORECASE),
            re.compile(r'search\s+for\s+related\s+documents', re.IGNORECASE),
            re.compile(r'semantic\s+search', re.IGNORECASE)
        ]
        
        self.analyze_patterns = [
            re.compile(r'analyze\s+the\s+data', re.IGNORECASE),
            re.compile(r'examine\s+the\s+relationships', re.IGNORECASE),
            re.compile(r'investigate\s+the\s+patterns', re.IGNORECASE),
            re.compile(r'study\s+the\s+connections', re.IGNORECASE),
            re.compile(r'assess\s+the\s+information', re.IGNORECASE),
            re.compile(r'evaluate\s+the\s+results', re.IGNORECASE)
        ]
        
        # Entity patterns
        self.entity_patterns = {
            'user': re.compile(r'\b(user|person|individual|me|myself|i)\b', re.IGNORECASE),
            'project': re.compile(r'\b(projects?|tasks?|assignments?|work|jobs?)\b', re.IGNORECASE),
            'document': re.compile(r'\b(documents?|files?|notes?|papers?|reports?|guides?|documentation)\b', re.IGNORECASE),
            'relationship': re.compile(r'\b(relationships?|connections?|links?|associations?|bonds?)\b', re.IGNORECASE),
            'conversation': re.compile(r'\b(conversations?|chats?|discussions?|talks?|dialogues?)\b', re.IGNORECASE),
            'memory': re.compile(r'\b(memory|memories|remember|recall|stored)\b', re.IGNORECASE),
            'team': re.compile(r'\b(team|members?|colleagues?|staff)\b', re.IGNORECASE)
        }
        
        # Operation patterns
        self.operation_patterns = {
            OperationType.CREATE: re.compile(r'\b(create|make|generate|add|new|build|establish|form)\b', re.IGNORECASE),
            OperationType.READ: re.compile(r'\b(get|retrieve|fetch|show|display|find|read|view|see)\b', re.IGNORECASE),
            OperationType.UPDATE: re.compile(r'\b(update|modify|change|edit|revise|alter|adjust)\b', re.IGNORECASE),
            OperationType.DELETE: re.compile(r'\b(delete|remove|clear|erase|drop|eliminate)\b', re.IGNORECASE),
            OperationType.SEARCH: re.compile(r'\b(search|find|look|locate|seek|query|explore)\b', re.IGNORECASE),
            OperationType.ANALYZE: re.compile(r'\b(analyze|examine|investigate|study|assess|evaluate)\b', re.IGNORECASE)
        }
    
    def analyze_intent(self, task: str, context: Optional[Dict[str, Any]] = None) -> TaskAnalysis:
        """Analyze task intent with advanced pattern matching"""
        task_lower = task.lower()
        matched_patterns = []
        confidence = 0.0
        entities = []
        reasoning_parts = []
        
        # Extract entities
        for entity_name, pattern in self.entity_patterns.items():
            if pattern.search(task):
                entities.append(entity_name)
                confidence += 0.15
                reasoning_parts.append(f"detected {entity_name} entity")
        
        # Determine operation type
        operation_type = OperationType.READ  # default
        operation_confidence = 0.0
        for op_type, pattern in self.operation_patterns.items():
            if pattern.search(task):
                if op_type == OperationType.ANALYZE and any(p.search(task) for p in self.analyze_patterns):
                    operation_type = op_type
                    operation_confidence = 0.4
                    matched_patterns.append(f"analyze operation: {op_type.value}")
                    break
                elif operation_confidence < 0.3:
                    operation_type = op_type
                    operation_confidence = 0.3
                    matched_patterns.append(f"operation: {op_type.value}")
        
        confidence += operation_confidence
        
        # Determine task type with pattern matching
        task_type = TaskType.UNKNOWN
        task_confidence = 0.0
        
        # Check relationship patterns
        for pattern in self.relationship_patterns:
            if pattern.search(task):
                task_type = TaskType.RELATIONSHIP_QUERY
                task_confidence = 0.4
                matched_patterns.append("relationship pattern matched")
                reasoning_parts.append("relationship query patterns matched")
                break
        
        # Check user identity patterns
        if task_confidence < 0.4:
            for pattern in self.user_identity_patterns:
                if pattern.search(task):
                    task_type = TaskType.USER_IDENTITY
                    task_confidence = 0.4
                    matched_patterns.append("user identity pattern matched")
                    reasoning_parts.append("user identity patterns matched")
                    break
        
        # Check documentation patterns
        if task_confidence < 0.4:
            for pattern in self.documentation_patterns:
                if pattern.search(task):
                    task_type = TaskType.DOCUMENTATION
                    task_confidence = 0.4
                    matched_patterns.append("documentation pattern matched")
                    reasoning_parts.append("documentation patterns matched")
                    break
        
        # Check conversation context patterns
        if task_confidence < 0.4:
            for pattern in self.conversation_context_patterns:
                if pattern.search(task):
                    task_type = TaskType.CONVERSATION_CONTEXT
                    task_confidence = 0.4
                    matched_patterns.append("conversation context pattern matched")
                    reasoning_parts.append("conversation context patterns matched")
                    break
        
        # Check search patterns for semantic search
        if task_confidence < 0.4:
            for pattern in self.search_patterns:
                if pattern.search(task):
                    task_type = TaskType.SEMANTIC_SEARCH
                    task_confidence = 0.3
                    matched_patterns.append("search pattern matched")
                    reasoning_parts.append("semantic search patterns matched")
                    break
        
        confidence += task_confidence
        
        # Context-based adjustments
        if context:
            if context.get('needs_persistence'):
                if task_type == TaskType.UNKNOWN:
                    task_type = TaskType.PERSISTENT_KNOWLEDGE
                    reasoning_parts.append("context indicates persistence needed")
                confidence += 0.2
        
        # Explicit relationship language
        if any(word in task_lower for word in ['between', 'connected', 'linked']):
            confidence += 0.2
            reasoning_parts.append("explicit relationship language detected")
        
        # Cap confidence at 1.0
        confidence = min(confidence, 1.0)
        
        reasoning = "; ".join(reasoning_parts) if reasoning_parts else "basic pattern matching applied"
        
        return TaskAnalysis(
            task_type=task_type,
            operation_type=operation_type,
            entities=entities,
            confidence=confidence,
            reasoning=reasoning,
            patterns_matched=matched_patterns
        )


class MemorySelector:
    """Selects appropriate memory system based on task characteristics"""

    def __init__(self, cab_tracker=None, *, config_path=None, validate_config=True):
        """
        Initialize MemorySelector with configuration loading and validation.

        Args:
            cab_tracker: Optional CAB tracker instance for logging
            config_path: Optional path to configuration file. If None, follows fallback order:
                         .env → .env.production → .env.local
            validate_config: Whether to validate loaded configuration (default: True)
        """
        self.cab_tracker = cab_tracker
        
        # Initialize CAB tracker session if provided
        if self.cab_tracker and not self.cab_tracker.initialized:
            self.cab_tracker.initialize_session()
        
        self.config = self._load_config(config_path)

        if validate_config:
            self._validate_config()

        self._selection_rules = self._initialize_rules()
        self._fallback_chains = self._initialize_fallback_chains()

        # Initialize clients to None. They will be created on-demand.
        self._redis_client = None
        self._basic_memory_client = None
        self._neo4j_client = None
        
        # Initialize intent analyzer for enhanced task determination
        self._intent_analyzer = IntentAnalyzer()
        
        # Detect if we're in a test/development environment
        self._test_mode = self._detect_test_environment()

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

    def _detect_test_environment(self) -> bool:
        """
        Detect if we're running in a test/development environment where external services may not be available.
        
        Returns:
            True if we're in a test/development environment, False otherwise
        """
        # Check for common CI/testing environment indicators
        ci_indicators = [
            'CI', 'GITHUB_ACTIONS', 'JENKINS_URL', 'TRAVIS', 'CIRCLE_CI', 'GITLAB_CI',
            'BUILDKITE', 'AZURE_PIPELINES', 'TF_BUILD'
        ]
        
        # Check for testing frameworks
        test_indicators = [
            'PYTEST_CURRENT_TEST', 'UNITTEST_CURRENT_TEST', '_PYTEST_CAPTURE_OPTION'
        ]
        
        # Check for development mode indicators
        dev_indicators = [
            'DEBUG', 'DEVELOPMENT', 'DEV_MODE'
        ]
        
        # Check if any CI/test/dev indicators are present
        for indicator in ci_indicators + test_indicators + dev_indicators:
            if os.getenv(indicator):
                logger.info(f"Test environment detected via {indicator} environment variable")
                return True
        
        # Check if we're running tests by looking at sys.modules
        test_modules = ['pytest', 'unittest', 'nose', 'nose2']
        for module in test_modules:
            if module in sys.modules:
                logger.info(f"Test environment detected via {module} module")
                return True
        
        # Check if the TEST_MODE environment variable is explicitly set
        if os.getenv('TEST_MODE', 'false').lower() == 'true':
            logger.info("Test environment detected via TEST_MODE environment variable")
            return True
        
        return False

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
            
            # Neo4j MCP Server Configuration
            'NEO4J_MCP_MEMORY_URL': os.getenv('NEO4J_MCP_MEMORY_URL', 'http://neo4j:8001'),
            'NEO4J_MCP_CYPHER_URL': os.getenv('NEO4J_MCP_CYPHER_URL', 'http://neo4j:8002'),

            # Basic Memory Configuration
            'BASIC_MEMORY_ENABLED': os.getenv('BASIC_MEMORY_ENABLED', 'true').lower() == 'true',
            'BASIC_MEMORY_URL': os.getenv('BASIC_MEMORY_URL'),
            'BASIC_MEMORY_AUTH_TOKEN': os.getenv('BASIC_MEMORY_AUTH_TOKEN'),
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
            
            # Test Mode
            'TEST_MODE': os.getenv('TEST_MODE', 'false').lower() == 'true',
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
            basic_url = self.config.get('BASIC_MEMORY_URL')
            basic_path = self.config.get('BASIC_MEMORY_PATH')
            
            if not basic_url and not basic_path:
                config_warnings.append("Either BASIC_MEMORY_URL or BASIC_MEMORY_PATH must be configured when Basic Memory is enabled")
            elif basic_path and not os.path.exists(basic_path):
                config_warnings.append(f"BASIC_MEMORY_PATH does not exist: {basic_path}")

        if not self.config.get('DISABLE_AUTH'):
            if not self.config.get('JWT_SECRET'):
                config_warnings.append("JWT_SECRET not configured but authentication is enabled")
            if not self.config.get('OAUTH2_ISSUER_URL'):
                config_warnings.append("OAUTH2_ISSUER_URL not configured but authentication is enabled")

        for warning in config_warnings:
            logger.warning(f"Configuration warning: {warning}")
            if self.cab_tracker:
                self.cab_tracker.log_suggestion("Configuration Warning", warning, severity='MEDIUM', context="Configuration validation")

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
            base_url = self.config.get('BASIC_MEMORY_URL')
            if base_url:
                # Use REST API client
                self._basic_memory_client = self._initialize_client(
                    client_type="Basic Memory",
                    config={
                        'url': base_url,
                        'auth_token': self.config.get('BASIC_MEMORY_AUTH_TOKEN')
                    },
                    create_client=lambda: BasicMemoryClient(
                        base_url=base_url,
                        auth_token=self.config.get('BASIC_MEMORY_AUTH_TOKEN'),
                        test_mode=self._test_mode
                    )
                )
            else:
                # Log that we need a URL for REST API access
                if self.cab_tracker:
                    self.cab_tracker.log_suggestion(
                        "Configuration Warning",
                        "BASIC_MEMORY_URL not configured - cannot create REST API client",
                        severity='MEDIUM',
                        context="Basic Memory enabled but no API URL provided"
                    )
                logger.warning("BASIC_MEMORY_URL not configured - cannot create REST API client")
        return self._basic_memory_client

    def _get_neo4j_client(self):
        """Get Neo4j MCP client instance (lazy initialization)"""
        if not self._neo4j_client and self.config.get('NEO4J_ENABLED'):
            memory_url = self.config.get('NEO4J_MCP_MEMORY_URL')
            cypher_url = self.config.get('NEO4J_MCP_CYPHER_URL')
            
            if not memory_url or not cypher_url or memory_url.strip() == '' or cypher_url.strip() == '':
                error_msg = "NEO4J_MCP_MEMORY_URL and NEO4J_MCP_CYPHER_URL must be configured when Neo4j is enabled"
                logger.error(error_msg)
                if self.cab_tracker:
                    self.cab_tracker.log_suggestion(
                        "Configuration Error",
                        error_msg,
                        severity='HIGH',
                        context="Neo4j MCP client initialization"
                    )
                return None
            
            self._neo4j_client = self._initialize_client(
                client_type="Neo4j MCP",
                config={
                    'memory_url': memory_url,
                    'cypher_url': cypher_url
                },
                create_client=lambda: Neo4jMCPClient(
                    memory_server_url=memory_url,
                    cypher_server_url=cypher_url,
                    test_mode=self._test_mode
                )
            )
        return self._neo4j_client

    def _ensure_neo4j_client(self, operation_type: str, task: str):
        """
        Ensure Neo4j MCP client is available and return it.
        
        Args:
            operation_type: Type of operation (e.g., "storage", "retrieval") for logging
            task: Task context for logging
            
        Returns:
            Neo4jMCPClient instance
            
        Raises:
            Exception: If Neo4j MCP client is not available
        """
        # Get Neo4j client instance (performs lazy initialization and configuration validation)
        client = self._get_neo4j_client()
        if not client:
            if self.cab_tracker:
                self.cab_tracker.log_suggestion(
                    "Missing Implementation",
                    f"Neo4j MCP client not available for {operation_type} operation",
                    severity='HIGH',
                    context=f"Task: {task}"
                )
            raise Neo4jClientUnavailableError("Neo4j MCP client not available")
        
        return client

    def get_task_analysis(self, task: str, context: Optional[Dict[str, Any]] = None) -> TaskAnalysis:
        """Get detailed analysis of task using enhanced intent recognition
        
        Returns TaskAnalysis containing task_type, operation_type, entities, confidence, 
        reasoning, and patterns_matched. The patterns_matched field contains a list of
        pattern descriptions that were matched during the analysis to aid in debugging
        and understanding the classification decision.
        """
        return self._intent_analyzer.analyze_intent(task, context)
    
    def analyze_task(self, task: str, context: Optional[Dict[str, Any]] = None) -> TaskType:
        """Analyze task to determine its type using enhanced logic with fallback"""
        # Use enhanced analysis first
        analysis = self.get_task_analysis(task, context)
        
        # If confidence is low, fall back to legacy keyword matching
        if analysis.confidence < FALLBACK_THRESHOLD:
            if self.cab_tracker:
                self.cab_tracker.log_suggestion(
                    "Low Confidence Analysis", 
                    f"Enhanced analysis had low confidence ({analysis.confidence:.2f}) for task: {task[:50]}...",
                    severity='MEDIUM'
                )
            
            # Legacy keyword matching fallback
            task_lower = task.lower()
            if any(k in task_lower for k in ['relationship', 'connection', 'graph']):
                fallback_result = TaskType.RELATIONSHIP_QUERY
            elif 'user' in task_lower and 'identity' in task_lower:
                fallback_result = TaskType.USER_IDENTITY
            elif any(k in task_lower for k in ['document', 'note', 'report']):
                fallback_result = TaskType.DOCUMENTATION
            elif any(k in task_lower for k in ['conversation', 'semantic', 'remember']):
                fallback_result = TaskType.CONVERSATION_CONTEXT
            else:
                fallback_result = TaskType.UNKNOWN
                
            if self.cab_tracker:
                self.cab_tracker.log_suggestion(
                    "Fallback Analysis Used",
                    f"Fell back to legacy analysis, result: {fallback_result.value}",
                    severity='LOW'
                )
            
            return fallback_result
        else:
            # Log low confidence but still acceptable results
            if analysis.confidence < 0.5 and self.cab_tracker:
                self.cab_tracker.log_suggestion(
                    "Low Confidence Analysis",
                    f"Enhanced analysis confidence: {analysis.confidence:.2f}, task: {task[:50]}...",
                    severity='LOW'
                )
            
            return analysis.task_type

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
        import time
        start_time = time.time()
        
        primary_system, task_type = self.select_memory_system(task, context)
        fallback_chain = [primary_system] + self._fallback_chains.get(primary_system, [])
        last_error = None
        
        for i, system in enumerate(fallback_chain):
            operation_start = time.time()
            try:
                result = operation_func(system, task, context)
                operation_duration = (time.time() - operation_start) * 1000  # Convert to ms
                
                # Log successful operation
                if self.cab_tracker:
                    self.cab_tracker.log_memory_operation(
                        operation=operation_func.__name__ if hasattr(operation_func, '__name__') else "memory_operation",
                        system=system.value,
                        success=True,
                        duration_ms=operation_duration,
                        fallback_used=(i > 0)
                    )
                
                if i > 0:
                    logger.info(f"Successfully used fallback system {system.value}")
                    if self.cab_tracker:
                        self.cab_tracker.log_suggestion(
                            "Fallback Success",
                            f"Primary system failed, successfully fell back to {system.value}",
                            severity='MEDIUM',
                            context=f"Task: {task[:50]}...",
                            metrics={"primary_system": primary_system.value, "successful_system": system.value}
                        )
                
                return result, system, (i > 0)
                
            except Exception as e:
                operation_duration = (time.time() - operation_start) * 1000
                last_error = e
                logger.warning(f"System {system.value} failed: {str(e)}")
                
                # Log API error
                if self.cab_tracker:
                    self.cab_tracker.log_suggestion(
                        "API Error",
                        f"{system.value} operation failed: {str(e)}",
                        severity='HIGH' if i == 0 else 'MEDIUM',  # Primary failure is more severe
                        context=f"Task: {task[:50]}..., System: {system.value}",
                        metrics={"duration_ms": operation_duration, "error_type": type(e).__name__}
                    )
                continue
        
        total_duration = (time.time() - start_time) * 1000
        logger.error(f"All systems failed for task: {task}")
        
        # Log complete failure
        if self.cab_tracker:
            self.cab_tracker.log_suggestion(
                "Complete System Failure",
                f"All memory systems failed for task: {task[:50]}...",
                severity='CRITICAL',
                context=f"Systems tried: {[s.value for s in fallback_chain]}, Last error: {str(last_error)}",
                metrics={"total_duration_ms": total_duration, "systems_attempted": len(fallback_chain)}
            )
        
        raise Exception(f"All memory systems failed. Last error: {last_error}")

    def store_data(self, data: Dict[str, Any], task: str, context: Optional[Dict[str, Any]] = None) -> Tuple[Any, MemorySystem, bool]:
        """Store data in appropriate memory system with fallback"""
        def store_operation(system: MemorySystem, task: str, context: Optional[Dict[str, Any]]):
            return self._store_in_system(system, data, task, context)
        
        return self.execute_with_fallback(task, store_operation, context)

    def retrieve_data(self, query: Dict[str, Any], task: str, context: Optional[Dict[str, Any]] = None) -> Tuple[Any, MemorySystem, bool]:
        """Retrieve data from appropriate memory system with fallback"""
        def retrieve_operation(system: MemorySystem, task: str, context: Optional[Dict[str, Any]]):
            return self._retrieve_from_system(system, query, task, context)
        
        return self.execute_with_fallback(task, retrieve_operation, context)

    def _store_in_system(self, system: MemorySystem, data: Dict[str, Any], task: str, context: Optional[Dict[str, Any]] = None) -> Any:
        """Store data in specific memory system"""
        if system == MemorySystem.REDIS:
            return self._store_in_redis(data, task, context)
        elif system == MemorySystem.NEO4J:
            return self._store_in_neo4j(data, task, context)
        elif system == MemorySystem.BASIC_MEMORY:
            return self._store_in_basic_memory(data, task, context)
        else:
            if self.cab_tracker:
                self.cab_tracker.log_missing_implementation(
                    f"Storage operation for {system.value}",
                    f"Cannot store data in {system.value} - implementation missing"
                )
            raise NotImplementedError(f"Storage not implemented for {system.value}")

    def _retrieve_from_system(self, system: MemorySystem, query: Dict[str, Any], task: str, context: Optional[Dict[str, Any]] = None) -> Any:
        """Retrieve data from specific memory system"""
        if system == MemorySystem.REDIS:
            return self._retrieve_from_redis(query, task, context)
        elif system == MemorySystem.NEO4J:
            return self._retrieve_from_neo4j(query, task, context)
        elif system == MemorySystem.BASIC_MEMORY:
            return self._retrieve_from_basic_memory(query, task, context)
        else:
            if self.cab_tracker:
                self.cab_tracker.log_missing_implementation(
                    f"Retrieval operation for {system.value}",
                    f"Cannot retrieve data from {system.value} - implementation missing"
                )
            raise NotImplementedError(f"Retrieval not implemented for {system.value}")

    def _store_in_redis(self, data: Dict[str, Any], task: str, context: Optional[Dict[str, Any]] = None) -> Any:
        """Store data in Redis memory system"""
        client = self._get_redis_client()
        if not client:
            if self.cab_tracker:
                self.cab_tracker.log_suggestion(
                    "Missing Implementation",
                    "Redis client not available for storage operation",
                    severity='HIGH',
                    context=f"Task: {task}"
                )
            raise Exception("Redis client not available")
        
        # Placeholder implementation - would call actual Redis operations
        logger.info(f"Storing data in Redis for task: {task}")
        # In real implementation, this would fail if Redis is not configured properly
        if not self.config.get('REDIS_URL'):
            raise Exception("Redis URL not configured")
        
        return {"status": "stored", "system": "redis", "data_id": "mock_redis_id"}

    def _store_in_neo4j(self, data: Dict[str, Any], task: str, context: Optional[Dict[str, Any]] = None) -> Any:
        """
        Store data in Neo4j memory system using MCP.
        
        Targets mcp-neo4j-memory for entity/relation operations or mcp-neo4j-cypher for raw queries.
        Constructs appropriate MCP JSON payloads and handles responses and errors.
        """
        # Ensure Neo4j MCP client is available
        client = self._ensure_neo4j_client("storage", task)
        
        try:
            logger.info(f"Storing data in Neo4j via MCP for task: {task}")
            
            # Determine storage strategy based on data type and task context
            task_analysis = self.get_task_analysis(task, context)
            
            # Check if this is a raw Cypher operation
            if "cypher" in data or "query" in data:
                # Use mcp-neo4j-cypher for raw Cypher queries
                cypher_query = data.get("cypher") or data.get("query")
                parameters = data.get("parameters", {})
                
                if self.cab_tracker:
                    self.cab_tracker.log_suggestion(
                        "Neo4j Cypher Storage",
                        f"Executing raw Cypher query for task: {task[:50]}...",
                        severity='LOW',
                        context=f"Query: {cypher_query[:100]}..."
                    )
                
                result = client.execute_cypher(cypher_query, parameters)
                return {"status": "stored", "system": "neo4j_mcp_cypher", "result": result}
            
            # Otherwise, use mcp-neo4j-memory for entity/relation operations
            entities = []
            relations = []
            
            # Handle different data structures
            if "entities" in data:
                # Direct entity data
                entities = data["entities"]
            elif "relations" in data:
                # Direct relation data - store relations separately
                relations = data["relations"]
            else:
                # Convert general data to entity format
                entity_labels = ["Entity"]
                
                # Determine entity type based on task analysis
                if task_analysis.task_type == TaskType.USER_IDENTITY:
                    entity_labels = ["User", "Entity"]
                elif task_analysis.task_type == TaskType.RELATIONSHIP_QUERY:
                    entity_labels = ["Relationship", "Entity"]
                elif "user" in data or "user_id" in data:
                    entity_labels = ["User", "Entity"]
                elif "project" in data or "task" in str(data).lower():
                    entity_labels = ["Project", "Entity"]
                
                entity = {
                    "labels": entity_labels,
                    "properties": {
                        "content": data.get("content", str(data)),
                        "title": data.get("title", f"Entity for task: {task}"),
                        "task": task,
                        "task_type": task_analysis.task_type.value,
                        "created_at": data.get("timestamp") or data.get("created_at"),
                        **data.get("metadata", {}),
                        **{k: v for k, v in data.items() if k not in ["content", "title", "metadata", "timestamp"]}
                    }
                }
                entities.append(entity)
            
            result = {}
            
            # Store entities if any
            if entities:
                if self.cab_tracker:
                    self.cab_tracker.log_suggestion(
                        "Neo4j Entity Storage",
                        f"Storing {len(entities)} entities for task: {task[:50]}...",
                        severity='LOW',
                        context=f"Entity types: {[e.get('labels', []) for e in entities]}"
                    )
                entity_result = client.create_entities(entities)
                result["entities"] = entity_result
            
            # Store relations if any
            if relations:
                if self.cab_tracker:
                    self.cab_tracker.log_suggestion(
                        "Neo4j Relation Storage",
                        f"Storing {len(relations)} relations for task: {task[:50]}...",
                        severity='LOW',
                        context=f"Relations: {', '.join([str(r.get('source')) + '->' + str(r.get('target')) for r in relations[:3]])}"
                    )
                # Use create_relations method if available, otherwise execute as Cypher
                try:
                    relation_result = client.send_memory_request("create_relations", {"relations": relations})
                    result["relations"] = relation_result
                except Exception:
                    # Fallback to Cypher for relations
                    for relation in relations:
                        cypher = format_cypher_query(f"""
                        MATCH (source {{name: $source_name}})
                        MATCH (target {{name: $target_name}})
                        CREATE (source)-[r:{relation.get('relation_type', 'RELATED_TO')}]->(target)
                        SET r += $properties
                        RETURN r
                        """)
                        params = {
                            "source_name": relation.get("source"),
                            "target_name": relation.get("target"),
                            "properties": relation.get("properties", {})
                        }
                        client.execute_cypher(cypher, params)
                    result["relations"] = {"created": len(relations)}
            
            return {"status": "stored", "system": "neo4j_mcp", "result": result}
            
        except ConnectivityError as e:
            # Re-raise connectivity errors without additional wrapping
            raise e
        except requests.exceptions.RequestException as e:
            error_msg = f"Neo4j MCP API request failed: {str(e)}"
            if self.cab_tracker:
                self.cab_tracker.log_suggestion(
                    "API Error",
                    error_msg,
                    severity='HIGH',
                    context=f"Task: {task}, Memory URL: {self.config.get('NEO4J_MCP_MEMORY_URL')}",
                    metrics={"error_type": type(e).__name__}
                )
            raise Exception(error_msg)
        except Exception as e:
            error_msg = f"Neo4j MCP storage failed: {str(e)}"
            if self.cab_tracker:
                self.cab_tracker.log_suggestion(
                    "Storage Error",
                    error_msg,
                    severity='HIGH',
                    context=f"Task: {task}"
                )
            raise Exception(error_msg)

    def _store_in_basic_memory(self, data: Dict[str, Any], task: str, context: Optional[Dict[str, Any]] = None) -> Any:
        """Store data in Basic Memory system"""
        client = self._get_basic_memory_client()
        if not client:
            if self.cab_tracker:
                self.cab_tracker.log_suggestion(
                    "Missing Implementation",
                    "Basic Memory client not available for storage operation", 
                    severity='HIGH',
                    context=f"Task: {task}"
                )
            raise Exception("Basic Memory client not available")
        
        try:
            # Use the actual Basic Memory client to store data
            logger.info(f"Storing data in Basic Memory for task: {task}")
            
            # Map the data to Basic Memory entity format
            entity_data = {
                "content": data.get("content", str(data)),
                "title": data.get("title", f"Entity for task: {task}"),
                "tags": data.get("tags", []),
                "metadata": {
                    "task": task,
                    "stored_at": data.get("timestamp"),
                    "context": context
                }
            }
            
            result = client.store_entity(entity_data)
            return {"status": "stored", "system": "basic_memory", "entity_id": result.get("id"), "result": result}
            
        except requests.exceptions.RequestException as e:
            error_msg = f"Basic Memory API request failed: {str(e)}"
            if self.cab_tracker:
                self.cab_tracker.log_suggestion(
                    "API Error",
                    error_msg,
                    severity='HIGH',
                    context=f"Task: {task}, URL: {self.config.get('BASIC_MEMORY_URL')}",
                    metrics={"error_type": type(e).__name__}
                )
            raise Exception(error_msg)
        except Exception as e:
            error_msg = f"Basic Memory storage failed: {str(e)}"
            if self.cab_tracker:
                self.cab_tracker.log_suggestion(
                    "Storage Error",
                    error_msg,
                    severity='HIGH',
                    context=f"Task: {task}"
                )
            raise Exception(error_msg)

    def _retrieve_from_redis(self, query: Dict[str, Any], task: str, context: Optional[Dict[str, Any]] = None) -> Any:
        """Retrieve data from Redis memory system"""
        client = self._get_redis_client()
        if not client:
            if self.cab_tracker:
                self.cab_tracker.log_suggestion(
                    "Missing Implementation",
                    "Redis client not available for retrieval operation",
                    severity='HIGH', 
                    context=f"Task: {task}"
                )
            raise Exception("Redis client not available")
        
        # Placeholder implementation - would call actual Redis operations
        logger.info(f"Retrieving data from Redis for task: {task}")
        if not self.config.get('REDIS_URL'):
            raise Exception("Redis URL not configured")
        
        return {"status": "retrieved", "system": "redis", "results": ["mock_redis_result"]}

    def _retrieve_from_neo4j(self, query: Dict[str, Any], task: str, context: Optional[Dict[str, Any]] = None) -> Any:
        """
        Retrieve data from Neo4j memory system using MCP.
        
        Targets mcp-neo4j-memory for entity/relation operations or mcp-neo4j-cypher for raw queries.
        Constructs appropriate MCP JSON payloads and handles responses and errors.
        """
        # Ensure Neo4j MCP client is available
        client = self._ensure_neo4j_client("retrieval", task)
        
        try:
            logger.info(f"Retrieving data from Neo4j via MCP for task: {task}")
            
            # Determine retrieval strategy based on query type and task context
            task_analysis = self.get_task_analysis(task, context)
            
            # Handle different types of queries
            if "cypher" in query:
                # Direct Cypher query - use mcp-neo4j-cypher
                cypher_query = query["cypher"]
                parameters = query.get("parameters", {})
                
                if self.cab_tracker:
                    self.cab_tracker.log_suggestion(
                        "Neo4j Cypher Query",
                        f"Executing raw Cypher query for task: {task[:50]}...",
                        severity='LOW',
                        context=f"Query: {cypher_query[:100]}..."
                    )
                
                result = client.execute_cypher(cypher_query, parameters)
                results = result.get("records", [])
                
            elif "search" in query or "query" in query:
                # Search query using mcp-neo4j-memory
                search_term = query.get("search") or query.get("query", "")
                filters = query.get("filters", {})
                
                # Add task-specific context to filters
                if task_analysis.task_type == TaskType.USER_IDENTITY:
                    filters.setdefault("labels", []).append("User")
                elif task_analysis.task_type == TaskType.RELATIONSHIP_QUERY:
                    # For relationship queries, we might want to search for both nodes and relationships
                    pass
                
                if self.cab_tracker:
                    self.cab_tracker.log_suggestion(
                        "Neo4j Node Search",
                        f"Searching nodes for: '{search_term[:50]}...' with task: {task[:50]}...",
                        severity='LOW',
                        context=f"Filters: {filters}"
                    )
                
                search_result = client.search_nodes(search_term, filters)
                results = search_result.get("nodes", [])
                
            elif "relationship" in query or "relation" in query:
                # Relationship-specific query using Cypher
                source = query.get("source")
                target = query.get("target")
                relation_type = query.get("relation_type", "")
                
                if source and target:
                    # Query for specific relationships between nodes
                    cypher_query = format_cypher_query(f"""
                    MATCH (source)-[r{f':{relation_type}' if relation_type else ''}]->(target)
                    WHERE source.name = $source_name AND target.name = $target_name
                    RETURN source, r, target
                    """)
                    parameters = {"source_name": source, "target_name": target}
                elif source:
                    # Query for all relationships from a source
                    cypher_query = format_cypher_query(f"""
                    MATCH (source)-[r{f':{relation_type}' if relation_type else ''}]->(target)
                    WHERE source.name = $source_name
                    RETURN source, r, target
                    """)
                    parameters = {"source_name": source}
                else:
                    # General relationship query
                    cypher_query = format_cypher_query(f"""
                    MATCH (source)-[r{f':{relation_type}' if relation_type else ''}]->(target)
                    RETURN source, r, target
                    LIMIT 100
                    """)
                    parameters = {}
                
                if self.cab_tracker:
                    self.cab_tracker.log_suggestion(
                        "Neo4j Relationship Query",
                        f"Querying relationships for task: {task[:50]}...",
                        severity='LOW',
                        context=f"Source: {source}, Target: {target}, Type: {relation_type}"
                    )
                
                result = client.execute_cypher(cypher_query, parameters)
                results = result.get("records", [])
                
            elif "entity_id" in query or "node_id" in query:
                # Direct entity lookup
                entity_id = query.get("entity_id") or query.get("node_id")
                cypher_query = "MATCH (n) WHERE id(n) = $node_id RETURN n"
                parameters = {"node_id": int(entity_id)}
                
                if self.cab_tracker:
                    self.cab_tracker.log_suggestion(
                        "Neo4j Entity Lookup",
                        f"Looking up entity by ID: {entity_id}",
                        severity='LOW',
                        context=f"Task: {task}"
                    )
                
                result = client.execute_cypher(cypher_query, parameters)
                results = result.get("records", [])
                
            else:
                # General query - convert to search using mcp-neo4j-memory
                search_term = str(query)
                
                # Try to extract meaningful search terms
                if isinstance(query, dict):
                    search_parts = []
                    for key, value in query.items():
                        if isinstance(value, str) and len(value) > 2:
                            search_parts.append(value)
                    search_term = " ".join(search_parts) if search_parts else str(query)
                
                if self.cab_tracker:
                    self.cab_tracker.log_suggestion(
                        "Neo4j General Search",
                        f"General search for: '{search_term[:50]}...' with task: {task[:50]}...",
                        severity='LOW',
                        context=f"Original query: {str(query)[:100]}..."
                    )
                
                search_result = client.search_nodes(search_term)
                results = search_result.get("nodes", [])
            
            # Log successful retrieval
            if self.cab_tracker:
                self.cab_tracker.log_suggestion(
                    "Neo4j Retrieval Success",
                    f"Retrieved {len(results)} results for task: {task[:50]}...",
                    severity='LOW',
                    context=f"Query type: {list(query.keys()) if isinstance(query, dict) else 'string'}"
                )
            
            return {"status": "retrieved", "system": "neo4j_mcp", "results": results, "count": len(results)}
            
        except ConnectivityError as e:
            # Re-raise connectivity errors without additional wrapping
            raise e
        except requests.exceptions.RequestException as e:
            error_msg = f"Neo4j MCP API request failed: {str(e)}"
            if self.cab_tracker:
                self.cab_tracker.log_suggestion(
                    "API Error",
                    error_msg,
                    severity='HIGH',
                    context=f"Task: {task}, Memory URL: {self.config.get('NEO4J_MCP_MEMORY_URL')}",
                    metrics={"error_type": type(e).__name__}
                )
            raise Exception(error_msg)
        except Exception as e:
            error_msg = f"Neo4j MCP retrieval failed: {str(e)}"
            if self.cab_tracker:
                self.cab_tracker.log_suggestion(
                    "Retrieval Error",
                    error_msg,
                    severity='HIGH',
                    context=f"Task: {task}"
                )
            raise Exception(error_msg)

    def _retrieve_from_basic_memory(self, query: Dict[str, Any], task: str, context: Optional[Dict[str, Any]] = None) -> Any:
        """Retrieve data from Basic Memory system"""
        client = self._get_basic_memory_client()
        if not client:
            if self.cab_tracker:
                self.cab_tracker.log_suggestion(
                    "Missing Implementation",
                    "Basic Memory client not available for retrieval operation",
                    severity='HIGH',
                    context=f"Task: {task}"
                )
            raise Exception("Basic Memory client not available")
        
        try:
            # Use the actual Basic Memory client to retrieve data
            logger.info(f"Retrieving data from Basic Memory for task: {task}")
            
            # Handle different types of queries
            if "id" in query:
                # Direct entity retrieval
                result = client.get_entity(query["id"])
                results = [result]
            elif "search" in query or "query" in query:
                # Search query
                search_term = query.get("search") or query.get("query", "")
                filters = query.get("filters")
                search_result = client.search_entities(search_term, filters)
                results = search_result.get("results", [])
            else:
                # General query - try searching with the whole query as a string
                search_term = str(query)
                search_result = client.search_entities(search_term)
                results = search_result.get("results", [])
            
            return {"status": "retrieved", "system": "basic_memory", "results": results}
            
        except requests.exceptions.RequestException as e:
            error_msg = f"Basic Memory API request failed: {str(e)}"
            if self.cab_tracker:
                self.cab_tracker.log_suggestion(
                    "API Error",
                    error_msg,
                    severity='HIGH',
                    context=f"Task: {task}, URL: {self.config.get('BASIC_MEMORY_URL')}",
                    metrics={"error_type": type(e).__name__}
                )
            raise Exception(error_msg)
        except Exception as e:
            error_msg = f"Basic Memory retrieval failed: {str(e)}"
            if self.cab_tracker:
                self.cab_tracker.log_suggestion(
                    "Retrieval Error",
                    error_msg,
                    severity='HIGH',
                    context=f"Task: {task}"
                )
            raise Exception(error_msg)

    def get_fallback_chain(self, system: MemorySystem) -> List[MemorySystem]:
        """Get the fallback chain for a given memory system"""
        return self._fallback_chains.get(system, [])

    def propagate_data(self, data: Dict[str, Any], source_system: MemorySystem, data_type: str, entity_id: Optional[str] = None, task: str = "data_propagation", context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Propagate data from source system to relevant destination systems.
        
        Implements logic to call _store_in_X for relevant systems when data needs to be synced.
        Logs inconsistencies via CABTracker as per Section 3.4 of implementation plan.
        
        Args:
            data: Data to propagate
            source_system: System where data originated
            data_type: Type of data being propagated (e.g., "user_profile", "relationship")
            entity_id: Optional entity identifier for tracking
            task: Task context for propagation operation
            context: Optional context for the propagation
            
        Returns:
            Dictionary containing propagation results for each target system
        """
        logger.info(f"Propagating '{data_type}' from {source_system.value} for entity '{entity_id}'")
        
        propagation_results = {}
        
        # Determine which systems should receive this data type
        target_systems = self._get_propagation_targets(source_system, data_type)
        
        if self.cab_tracker:
            self.cab_tracker.log_suggestion(
                "Data Propagation Started",
                f"Propagating {data_type} from {source_system.value} to {len(target_systems)} systems",
                severity='LOW',
                context=f"Entity: {entity_id}, Targets: {[s.value for s in target_systems]}",
                metrics={"source_system": source_system.value, "target_count": len(target_systems)}
            )
        
        for target_system in target_systems:
            try:
                # Use the specific propagation method for each system
                if target_system == MemorySystem.REDIS:
                    result = self._propagate_to_redis(data, data_type, entity_id, task, context)
                elif target_system == MemorySystem.NEO4J:
                    result = self._propagate_to_neo4j(data, data_type, entity_id, task, context)
                elif target_system == MemorySystem.BASIC_MEMORY:
                    result = self._propagate_to_basic_memory(data, data_type, entity_id, task, context)
                else:
                    logger.warning(f"Unknown target system for propagation: {target_system.value}")
                    continue
                
                propagation_results[target_system.value] = {"status": "success", "result": result}
                logger.info(f"Successfully propagated to {target_system.value}")
                
            except Exception as e:
                error_msg = f"Failed to propagate to {target_system.value}: {str(e)}"
                logger.error(error_msg)
                propagation_results[target_system.value] = {"status": "error", "error": str(e)}
                
                if self.cab_tracker:
                    self.cab_tracker.log_suggestion(
                        "Propagation Error",
                        f"Failed to propagate {data_type} from {source_system.value} to {target_system.value}",
                        severity='HIGH',
                        context=f"Entity: {entity_id}, Error: {str(e)}",
                        metrics={"source_system": source_system.value, "target_system": target_system.value}
                    )
        
        # Log successful propagation summary
        successful_systems = [k for k, v in propagation_results.items() if v["status"] == "success"]
        failed_systems = [k for k, v in propagation_results.items() if v["status"] == "error"]
        
        if self.cab_tracker:
            self.cab_tracker.log_suggestion(
                "Data Propagation Summary",
                f"Propagation completed: {len(successful_systems)} successful, {len(failed_systems)} failed",
                severity='LOW' if not failed_systems else 'MEDIUM',
                context=f"Entity: {entity_id}, Data type: {data_type}",
                metrics={
                    "successful_systems": successful_systems,
                    "failed_systems": failed_systems,
                    "total_targets": len(target_systems)
                }
            )
        
        return propagation_results

    def _enrich_with_propagation_metadata(self, data: Dict[str, Any], data_type: str, entity_id: Optional[str], task: str) -> Dict[str, Any]:
        """Enrich data with propagation metadata for cross-system synchronization"""
        return {
            **data,
            "_propagation_metadata": {
                "entity_id": entity_id,
                "data_type": data_type,
                "propagated_at": data.get("timestamp"),
                "propagation_task": task
            }
        }

    def _propagate_to_redis(self, data: Dict[str, Any], data_type: str, entity_id: Optional[str], task: str, context: Optional[Dict[str, Any]]) -> Any:
        """Propagate data to Redis system using existing _store_in_redis method"""
        logger.info(f"Propagating {data_type} to Redis for entity {entity_id}")
        
        # Enhance data with propagation metadata
        propagation_data = self._enrich_with_propagation_metadata(data, data_type, entity_id, task)
        
        return self._store_in_redis(propagation_data, task, context)

    def _propagate_to_neo4j(self, data: Dict[str, Any], data_type: str, entity_id: Optional[str], task: str, context: Optional[Dict[str, Any]]) -> Any:
        """Propagate data to Neo4j system using existing _store_in_neo4j method"""
        logger.info(f"Propagating {data_type} to Neo4j for entity {entity_id}")
        
        # Enhance data with propagation metadata
        propagation_data = self._enrich_with_propagation_metadata(data, data_type, entity_id, task)
        
        # If this is relationship data, ensure proper Neo4j structure
        if data_type == "relationship" and "relations" not in propagation_data:
            if "source" in data and "target" in data:
                propagation_data["relations"] = [{
                    "source": data["source"],
                    "target": data["target"],
                    "relation_type": data.get("relation_type", "RELATED_TO"),
                    "properties": data.get("properties", {})
                }]
        
        return self._store_in_neo4j(propagation_data, task, context)

    def _propagate_to_basic_memory(self, data: Dict[str, Any], data_type: str, entity_id: Optional[str], task: str, context: Optional[Dict[str, Any]]) -> Any:
        """Propagate data to Basic Memory system using existing _store_in_basic_memory method"""
        logger.info(f"Propagating {data_type} to Basic Memory for entity {entity_id}")
        
        # Enhance data with propagation metadata
        propagation_data = self._enrich_with_propagation_metadata(data, data_type, entity_id, task)
        
        # Ensure content is properly formatted for Basic Memory
        if "content" not in propagation_data:
            propagation_data["content"] = str(data)
        
        if "title" not in propagation_data:
            propagation_data["title"] = f"{data_type.title()} - {entity_id or 'Unknown Entity'}"
        
        return self._store_in_basic_memory(propagation_data, task, context)

    def _get_propagation_targets(self, source_system: MemorySystem, data_type: str) -> List[MemorySystem]:
        """
        Determine which systems should receive propagated data based on data type and source system.
        
        Args:
            source_system: System where data originated
            data_type: Type of data being propagated
            
        Returns:
            List of target systems for propagation
        """
        # Define propagation rules based on data type
        propagation_rules = {
            "user_profile": [MemorySystem.REDIS, MemorySystem.NEO4J, MemorySystem.BASIC_MEMORY],
            "user_identity": [MemorySystem.NEO4J, MemorySystem.REDIS],
            "relationship": [MemorySystem.NEO4J, MemorySystem.REDIS],
            "conversation": [MemorySystem.REDIS],
            "conversation_context": [MemorySystem.REDIS],
            "documentation": [MemorySystem.BASIC_MEMORY, MemorySystem.REDIS],
            "structured_note": [MemorySystem.BASIC_MEMORY],
            "persistent_knowledge": [MemorySystem.BASIC_MEMORY, MemorySystem.NEO4J],
            "entity_connection": [MemorySystem.NEO4J, MemorySystem.REDIS],
            "semantic_search": [MemorySystem.REDIS],
            "preference_storage": [MemorySystem.REDIS],
            "session_data": [MemorySystem.REDIS],
        }
        
        # Get target systems for this data type, excluding the source system
        all_targets = propagation_rules.get(data_type, [])
        target_systems = [system for system in all_targets if system != source_system]
        
        # Filter based on system availability
        available_targets = []
        for system in target_systems:
            if system == MemorySystem.REDIS and self.config.get('REDIS_URL'):
                available_targets.append(system)
            elif system == MemorySystem.NEO4J and self.config.get('NEO4J_ENABLED'):
                available_targets.append(system)
            elif system == MemorySystem.BASIC_MEMORY and self.config.get('BASIC_MEMORY_ENABLED'):
                available_targets.append(system)
        
        if self.cab_tracker and len(available_targets) != len(target_systems):
            unavailable_systems = [s.value for s in target_systems if s not in available_targets]
            self.cab_tracker.log_suggestion(
                "Propagation Target Unavailable",
                f"Some propagation targets unavailable for {data_type}",
                severity='MEDIUM',
                context=f"Unavailable systems: {unavailable_systems}",
                metrics={"data_type": data_type, "unavailable_systems": unavailable_systems}
            )
        
        return available_targets





# Example usage pattern
if __name__ == "__main__":
    # Mock CAB tracker for demonstration purposes
    class MockCabTracker:
        def __init__(self):
            self.initialized = True
        
        def log_suggestion(self, *args, **kwargs):
            print(f"CAB LOG: {args} {kwargs}")
            
        def log_memory_operation(self, *args, **kwargs):
            print(f"CAB MEMORY OP: {args} {kwargs}")
            
        def log_missing_implementation(self, *args, **kwargs):
            print(f"CAB MISSING IMPL: {args} {kwargs}")

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
            # Try to get the actual Neo4j client to test initialization
            try:
                client = selector._get_neo4j_client()
                if client:
                    print(f"Neo4j MCP client initialized successfully: {type(client).__name__}")
                    # This would be a real operation failing due to server unavailability
                    raise Exception("Neo4j MCP servers unavailable (expected - servers not running)")
                else:
                    raise Exception("Neo4j MCP client initialization failed")
            except Exception as e:
                raise Exception(f"Neo4j operation failed: {str(e)}")
        return f"Result from {system.value}"

    result, successful_system, used_fallback = selector.execute_with_fallback(
        task, mock_operation
    )
    print(f"Final Result: {result}")
    print(f"Successful System: {successful_system.value}")
    print(f"Used Fallback: {used_fallback}")