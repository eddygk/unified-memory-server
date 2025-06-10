"""
MCP Tool Router for AI Directives Compliance
Implements intelligent decision tree routing and tool naming conventions for AI assistants
"""
import logging
import re
from typing import Dict, List, Optional, Any, Tuple, NamedTuple
from enum import Enum
from dataclasses import dataclass

logger = logging.getLogger(__name__)


class MCPToolIntent(Enum):
    """MCP Tool routing intents based on AI directives"""
    RELATIONSHIPS_CONNECTIONS = "relationships_connections"
    COMPREHENSIVE_DOCUMENTATION = "comprehensive_documentation"
    CONVERSATIONAL_CONTEXT = "conversational_context"
    SEMANTIC_SEARCH = "semantic_search"
    USER_IDENTIFICATION = "user_identification"
    ENTITY_CREATION = "entity_creation"
    QUICK_MEMORIES = "quick_memories"


@dataclass
class MCPToolMapping:
    """Mapping of tools to their MCP names and systems"""
    tool_name: str
    mcp_name: str
    system: str
    description: str
    priority: int
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "tool_name": self.tool_name,
            "mcp_name": self.mcp_name,
            "system": self.system,
            "description": self.description,
            "priority": self.priority
        }


class MCPToolRouter:
    """
    Routes operations to specific MCP tools using intelligent decision tree
    Implements the decision tree:
    ├─ Does the task involve relationships/connections between entities?
    │  └─ YES → Use Neo4j tools
    ├─ Does the task require comprehensive documentation/structured notes?
    │  └─ YES → Use Basic Memory tools
    └─ Does the task need conversational context/semantic search?
       └─ YES → Use Redis Memory tools
    """
    
    def __init__(self, cab_tracker=None):
        self.cab_tracker = cab_tracker
        self.tool_mappings = self._initialize_tool_mappings()
        self.decision_patterns = self._initialize_decision_patterns()
        
    def _initialize_tool_mappings(self) -> Dict[str, MCPToolMapping]:
        """Initialize MCP tool mappings for intelligent routing"""
        mappings = {}
        
        # Neo4j Memory Tools (Priority 1 - User identity, Priority 2 - Relationships, Priority 5 - Entity creation)
        neo4j_tools = [
            ("create_entities", "local__neo4j-memory__create_entities", "Entity creation and management", 5),
            ("create_relations", "local__neo4j-memory__create_relations", "Relationship creation", 2),
            ("add_observations", "local__neo4j-memory__add_observations", "Add entity observations", 5),
            ("delete_entities", "local__neo4j-memory__delete_entities", "Entity deletion", 5),
            ("delete_relations", "local__neo4j-memory__delete_relations", "Relationship deletion", 2),
            ("delete_observations", "local__neo4j-memory__delete_observations", "Observation deletion", 5),
            ("read_graph", "local__neo4j-memory__read_graph", "Graph reading", 2),
            ("search_nodes", "local__neo4j-memory__search_nodes", "Node searching", 2),
            ("find_nodes", "local__neo4j-memory__find_nodes", "Find specific nodes", 2),
        ]
        
        for tool_name, mcp_name, description, priority in neo4j_tools:
            mappings[tool_name] = MCPToolMapping(tool_name, mcp_name, "neo4j", description, priority)
            
        # Neo4j Cypher Tools (Priority 1 - User identity)
        cypher_tools = [
            ("get_neo4j_schema", "local__neo4j-cypher__get_neo4j_schema", "Schema retrieval", 1),
            ("read_neo4j_cypher", "local__neo4j-cypher__read_neo4j_cypher", "Cypher query execution", 1),
            ("write_neo4j_cypher", "local__neo4j-cypher__write_neo4j_cypher", "Cypher write operations", 1),
        ]
        
        for tool_name, mcp_name, description, priority in cypher_tools:
            mappings[tool_name] = MCPToolMapping(tool_name, mcp_name, "neo4j", description, priority)
            
        # Basic Memory Tools (Priority 3 - Documentation)
        basic_tools = [
            ("write_note", "local__basic-memory__write_note", "Note creation and writing", 3),
            ("read_note", "local__basic-memory__read_note", "Note reading", 3),
            ("delete_note", "local__basic-memory__delete_note", "Note deletion", 3),
            ("search_notes", "local__basic-memory__search_notes", "Note searching", 3),
            ("build_context", "local__basic-memory__build_context", "Context building", 3),
            ("recent_activity", "local__basic-memory__recent_activity", "Recent activity tracking", 3),
            ("canvas", "local__basic-memory__canvas", "Canvas operations", 3),
            ("project_info", "local__basic-memory__project_info", "Project information", 3),
            ("read_content", "local__basic-memory__read_content", "Content reading", 3),
        ]
        
        for tool_name, mcp_name, description, priority in basic_tools:
            mappings[tool_name] = MCPToolMapping(tool_name, mcp_name, "basic_memory", description, priority)
            
        # Redis Memory Tools (Priority 4 - Context retrieval, Priority 6 - Quick memories)
        redis_tools = [
            ("create_long_term_memories", "local__redis-memory-server__create_long_term_memories", "Long-term memory creation", 6),
            ("search_long_term_memory", "local__redis-memory-server__search_long_term_memory", "Memory searching", 4),
            ("hydrate_memory_prompt", "local__redis-memory-server__hydrate_memory_prompt", "Context retrieval", 4),
        ]
        
        for tool_name, mcp_name, description, priority in redis_tools:
            mappings[tool_name] = MCPToolMapping(tool_name, mcp_name, "redis", description, priority)
            
        return mappings
    
    def _initialize_decision_patterns(self) -> Dict[MCPToolIntent, List[re.Pattern]]:
        """Initialize regex patterns for decision tree classification"""
        return {
            MCPToolIntent.RELATIONSHIPS_CONNECTIONS: [
                re.compile(r'\b(relationship|relation|connect|link|between|associated|related)\b', re.IGNORECASE),
                re.compile(r'\b(entity|entities|node|nodes|graph|traversal|connection)\b', re.IGNORECASE),
                re.compile(r'\b(find.*relationship|create.*relation|link.*entities)\b', re.IGNORECASE),
            ],
            MCPToolIntent.COMPREHENSIVE_DOCUMENTATION: [
                re.compile(r'\b(document|documentation|note|notes|markdown|structured)\b', re.IGNORECASE),
                re.compile(r'\b(write|create|save|store).*\b(note|document|content)\b', re.IGNORECASE),
                re.compile(r'\b(project|canvas|persistent|knowledge)\b', re.IGNORECASE),
            ],
            MCPToolIntent.CONVERSATIONAL_CONTEXT: [
                re.compile(r'\b(context|conversation|session|chat|dialogue)\b', re.IGNORECASE),
                re.compile(r'\b(hydrate|prompt|working memory|short.?term)\b', re.IGNORECASE),
            ],
            MCPToolIntent.SEMANTIC_SEARCH: [
                re.compile(r'\b(search|find|query|lookup|retrieve)\b', re.IGNORECASE),
                re.compile(r'\b(semantic|similar|related|topics)\b', re.IGNORECASE),
            ],
            MCPToolIntent.USER_IDENTIFICATION: [
                re.compile(r'\b(user|profile|identity|preferences|personal)\b', re.IGNORECASE),
                re.compile(r'\b(who.*am.*i|my.*profile|user.*data)\b', re.IGNORECASE),
            ],
            MCPToolIntent.ENTITY_CREATION: [
                re.compile(r'\b(create|add|new).*\b(entity|entities|node|nodes)\b', re.IGNORECASE),
                re.compile(r'\b(observation|add.*observation)\b', re.IGNORECASE),
            ],
            MCPToolIntent.QUICK_MEMORIES: [
                re.compile(r'\b(remember|memory|memories|quick|temporary)\b', re.IGNORECASE),
                re.compile(r'\b(store.*quickly|remember.*this|quick.*note)\b', re.IGNORECASE),
            ],
        }
    
    def analyze_task_intent(self, task: str, context: Optional[Dict[str, Any]] = None) -> Tuple[MCPToolIntent, float]:
        """
        Analyze task intent using intelligent decision tree
        Returns the intent and confidence score
        """
        task_lower = task.lower()
        intent_scores = {}
        
        # Score each intent based on pattern matches
        for intent, patterns in self.decision_patterns.items():
            score = 0.0
            matches = 0
            
            for pattern in patterns:
                if pattern.search(task):
                    matches += 1
                    score += 0.3  # Base score per pattern match
            
            # Boost score based on number of matches
            if matches > 1:
                score += 0.2 * (matches - 1)
            
            intent_scores[intent] = min(score, 1.0)  # Cap at 1.0
        
        # Context-based adjustments
        if context:
            # Priority adjustments based on context
            if context.get('user_context'):
                intent_scores[MCPToolIntent.USER_IDENTIFICATION] += 0.3
            if context.get('relationship_context'):
                intent_scores[MCPToolIntent.RELATIONSHIPS_CONNECTIONS] += 0.3
            if context.get('documentation_context'):
                intent_scores[MCPToolIntent.COMPREHENSIVE_DOCUMENTATION] += 0.3
        
        # Find highest scoring intent
        if not intent_scores or max(intent_scores.values()) == 0:
            return MCPToolIntent.SEMANTIC_SEARCH, 0.1  # Default fallback
        
        best_intent = max(intent_scores, key=intent_scores.get)
        confidence = intent_scores[best_intent]
        
        if self.cab_tracker:
            # Create JSON-serializable metrics for CAB logging
            serializable_scores = {intent.value: score for intent, score in intent_scores.items()}
            
            self.cab_tracker.log_suggestion(
                "MCP Intent Analysis",
                f"Classified task '{task[:50]}...' as {best_intent.value} with confidence {confidence:.2f}",
                severity='LOW',
                context=f"Intent scores: {serializable_scores}",
                metrics={"intent": best_intent.value, "confidence": confidence}
            )
        
        return best_intent, confidence
    
    def get_recommended_tools(self, intent: MCPToolIntent, operation_type: str = "read") -> List[MCPToolMapping]:
        """
        Get recommended MCP tools based on intent and operation type
        Follows the priority-based task routing for optimal performance
        """
        recommended_tools = []
        
        if intent == MCPToolIntent.USER_IDENTIFICATION:
            # Priority 1 - User identity (Neo4j primary)
            recommended_tools.extend([
                self.tool_mappings["read_neo4j_cypher"],
                self.tool_mappings["search_long_term_memory"],  # Fallback 1
                self.tool_mappings["search_notes"],  # Fallback 2
            ])
            
        elif intent == MCPToolIntent.RELATIONSHIPS_CONNECTIONS:
            # Priority 2 - Relationships (Neo4j primary)
            if operation_type.lower() in ["create", "write", "add"]:
                recommended_tools.append(self.tool_mappings["create_relations"])
            else:
                recommended_tools.extend([
                    self.tool_mappings["search_nodes"],
                    self.tool_mappings["read_graph"],
                ])
                
        elif intent == MCPToolIntent.COMPREHENSIVE_DOCUMENTATION:
            # Priority 3 - Documentation (Basic Memory primary)
            if operation_type.lower() in ["create", "write", "add"]:
                recommended_tools.append(self.tool_mappings["write_note"])
            else:
                recommended_tools.extend([
                    self.tool_mappings["read_note"],
                    self.tool_mappings["search_notes"],
                ])
                
        elif intent == MCPToolIntent.CONVERSATIONAL_CONTEXT:
            # Priority 4 - Context retrieval (Redis primary)
            recommended_tools.append(self.tool_mappings["hydrate_memory_prompt"])
            
        elif intent == MCPToolIntent.ENTITY_CREATION:
            # Priority 5 - Entity creation (Neo4j primary)
            recommended_tools.extend([
                self.tool_mappings["create_entities"],
                self.tool_mappings["add_observations"],
            ])
            
        elif intent == MCPToolIntent.QUICK_MEMORIES:
            # Priority 6 - Quick memories (Redis primary)
            recommended_tools.append(self.tool_mappings["create_long_term_memories"])
            
        elif intent == MCPToolIntent.SEMANTIC_SEARCH:
            # Search operations (Redis primary with fallbacks)
            recommended_tools.extend([
                self.tool_mappings["search_long_term_memory"],
                self.tool_mappings["search_nodes"],
                self.tool_mappings["search_notes"],
            ])
        
        return recommended_tools
    
    def route_task(self, task: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Main routing function that applies the intelligent decision tree
        Returns routing decision with recommended tools and fallback chain
        """
        intent, confidence = self.analyze_task_intent(task, context)
        
        # Determine operation type
        operation_type = "read"  # default
        if any(word in task.lower() for word in ["create", "add", "new", "write", "store"]):
            operation_type = "create"
        elif any(word in task.lower() for word in ["update", "modify", "change"]):
            operation_type = "update"
        elif any(word in task.lower() for word in ["delete", "remove"]):
            operation_type = "delete"
        elif any(word in task.lower() for word in ["search", "find", "query"]):
            operation_type = "search"
        
        recommended_tools = self.get_recommended_tools(intent, operation_type)
        
        # Build routing decision
        routing_decision = {
            "intent": intent.value,
            "confidence": confidence,
            "operation_type": operation_type,
            "primary_tool": recommended_tools[0] if recommended_tools else None,
            "fallback_tools": recommended_tools[1:] if len(recommended_tools) > 1 else [],
            "all_tools": recommended_tools,
            "reasoning": f"Decision tree classified task as {intent.value} with {confidence:.2f} confidence"
        }
        
        if self.cab_tracker:
            # Create JSON-serializable metrics
            serializable_metrics = {
                "intent": routing_decision["intent"],
                "confidence": routing_decision["confidence"],
                "operation_type": routing_decision["operation_type"],
                "primary_tool_name": routing_decision["primary_tool"].mcp_name if routing_decision["primary_tool"] else None,
                "fallback_count": len(routing_decision["fallback_tools"]),
                "reasoning": routing_decision["reasoning"]
            }
            
            self.cab_tracker.log_suggestion(
                "MCP Tool Routing",
                f"Routed task to {routing_decision['primary_tool'].mcp_name if routing_decision['primary_tool'] else 'no tool'}",
                severity='LOW',
                context=f"Task: {task[:100]}...",
                metrics=serializable_metrics
            )
        
        return routing_decision
    
    def get_tool_by_name(self, tool_name: str) -> Optional[MCPToolMapping]:
        """Get tool mapping by name"""
        return self.tool_mappings.get(tool_name)
    
    def get_all_tools_by_system(self, system: str) -> List[MCPToolMapping]:
        """Get all tools for a specific system"""
        return [tool for tool in self.tool_mappings.values() if tool.system == system]
    
    def validate_mcp_tool_name(self, tool_name: str) -> bool:
        """
        Validate that a tool name follows the MCP format: local__<server-name>__<tool-name>
        """
        pattern = re.compile(r'^local__[a-zA-Z0-9\-_]+__[a-zA-Z0-9\-_]+$')
        return bool(pattern.match(tool_name))