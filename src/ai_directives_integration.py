"""
AI Directives Integration Layer
Integrates MCP Tool Router and Startup Sequence with existing MemorySelector
for universal AI client MCP tool compliance and intelligent memory routing
"""
import logging
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum

from memory_selector import MemorySelector, MemorySystem, TaskType
from cab_tracker import CABTracker, get_cab_tracker
from mcp_tool_router import MCPToolRouter, MCPToolIntent
from startup_sequence import StartupSequenceHandler

logger = logging.getLogger(__name__)


class DirectiveCompliance(Enum):
    """Compliance levels with AI directives"""
    FULL_COMPLIANCE = "full_compliance"
    PARTIAL_COMPLIANCE = "partial_compliance"
    BASIC_FUNCTIONALITY = "basic_functionality"


class AIDirectivesIntegration:
    """
    Integration layer that enhances existing MemorySelector with AI directive compliance
    
    This layer provides:
    1. MCP tool name compliance (local__<server-name>__<tool-name>)
    2. Decision tree routing per AI directives
    3. Startup sequence execution
    4. Cross-system integration patterns
    5. Enhanced CAB tracking for directive compliance
    """
    
    def __init__(self, memory_selector: MemorySelector = None, cab_tracker: CABTracker = None, 
                 enable_startup_sequence: bool = True):
        """
        Initialize AI Directives Integration
        
        Args:
            memory_selector: Existing MemorySelector instance (or create new one)
            cab_tracker: CAB tracker instance (or use singleton)
            enable_startup_sequence: Whether to enable startup sequence execution
        """
        # Initialize components
        self.memory_selector = memory_selector or MemorySelector()
        self.cab_tracker = cab_tracker or get_cab_tracker()
        
        # Initialize MCP Tool Router with CAB tracking
        self.mcp_router = MCPToolRouter(self.cab_tracker)
        
        # Initialize Startup Sequence Handler
        self.startup_handler = StartupSequenceHandler(
            self.memory_selector, 
            self.cab_tracker, 
            self.mcp_router
        ) if enable_startup_sequence else None
        
        # Track integration state
        self.startup_completed = False
        self.compliance_level = DirectiveCompliance.BASIC_FUNCTIONALITY
        
        # Log integration initialization
        if self.cab_tracker:
            self.cab_tracker.log_suggestion(
                "AI Directives Integration Initialized",
                "Enhanced memory system with AI directive compliance layer",
                severity='LOW',
                context="System initialization",
                metrics={"startup_enabled": enable_startup_sequence}
            )
    
    def execute_startup_sequence(self, user: str = "Unknown", primary_ai: str = "Assistant") -> Dict[str, Any]:
        """
        Execute the AI directive startup sequence silently
        
        Step 0: Initialize CAB Tracking
        Step 1: Multi-System User Identification
        
        Returns startup results
        """
        if not self.startup_handler:
            logger.warning("Startup sequence handler not initialized")
            return {"error": "Startup sequence disabled"}
        
        logger.info(f"Executing AI directive startup sequence for {user}")
        
        startup_results = self.startup_handler.execute_startup_sequence(user, primary_ai)
        self.startup_completed = True
        
        # Update compliance level based on startup success
        if startup_results.get("step_0_completed") and startup_results.get("step_1_completed"):
            self.compliance_level = DirectiveCompliance.FULL_COMPLIANCE
        elif startup_results.get("step_0_completed") or startup_results.get("step_1_completed"):
            self.compliance_level = DirectiveCompliance.PARTIAL_COMPLIANCE
        
        return startup_results
    
    def route_with_directives(self, task: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Route task using AI directive decision tree and MCP tool compliance
        
        This method applies the AI directive decision tree:
        ├─ Does the task involve relationships/connections between entities?
        │  └─ YES → Use Neo4j tools
        ├─ Does the task require comprehensive documentation/structured notes?
        │  └─ YES → Use Basic Memory tools
        └─ Does the task need conversational context/semantic search?
           └─ YES → Use Redis Memory tools
        """
        # Get MCP routing decision
        mcp_decision = self.mcp_router.route_task(task, context)
        
        # Get traditional routing decision from MemorySelector
        traditional_analysis = self.memory_selector.get_task_analysis(task, context)
        traditional_system, _ = self.memory_selector.select_memory_system(task, context)
        
        # Combine decisions for enhanced routing
        enhanced_routing = {
            "task": task,
            "mcp_decision": mcp_decision,
            "traditional_decision": {
                "system": traditional_system.value,
                "task_type": traditional_analysis.task_type.value,
                "confidence": traditional_analysis.confidence,
                "reasoning": traditional_analysis.reasoning
            },
            "directive_compliance": self._assess_compliance(mcp_decision, traditional_system),
            "recommended_action": self._get_recommended_action(mcp_decision, traditional_system),
            "fallback_chain": self._build_enhanced_fallback_chain(mcp_decision, traditional_system)
        }
        
        # Log routing decision
        if self.cab_tracker:
            # Create JSON-serializable metrics for CAB logging
            serializable_metrics = {
                "mcp_intent": mcp_decision["intent"],
                "mcp_confidence": mcp_decision["confidence"],
                "traditional_system": traditional_system.value,
                "traditional_confidence": traditional_analysis.confidence,
                "directive_compliance": enhanced_routing["directive_compliance"]
            }
            
            self.cab_tracker.log_suggestion(
                "Enhanced Routing Decision",
                f"Applied AI directive routing for task: {task[:50]}...",
                severity='LOW',
                context=f"MCP Intent: {mcp_decision['intent']}, Traditional: {traditional_system.value}",
                metrics=serializable_metrics
            )
        
        return enhanced_routing
    
    def store_data_with_directives(self, data: Dict[str, Any], task: str, 
                                  context: Optional[Dict[str, Any]] = None) -> Tuple[Any, str, bool]:
        """
        Store data using AI directive patterns and cross-system integration
        
        Implements the cross-system integration rules:
        1. Store in primary system based on data type
        2. Create cross-references in other systems
        3. Maintain consistency across all three systems
        """
        # Get enhanced routing decision
        routing = self.route_with_directives(task, context)
        
        # Determine if cross-system propagation is needed
        propagation_needed = self._should_propagate_data(data, routing, context)
        
        try:
            # Store using traditional method first
            result, successful_system, used_fallback = self.memory_selector.store_data(data, task, context)
            
            # Apply cross-system propagation if needed
            if propagation_needed:
                propagation_result = self._propagate_with_directives(
                    data, successful_system, routing, context
                )
                
                if self.cab_tracker:
                    self.cab_tracker.log_suggestion(
                        "Cross-System Data Propagation",
                        f"Propagated data across systems per AI directives",
                        severity='LOW',
                        context=f"Source: {successful_system}, Propagated: {propagation_result}",
                        metrics={"propagation_success": propagation_result}
                    )
            
            return result, successful_system, used_fallback
            
        except Exception as e:
            # Enhanced error handling with directive-specific fallbacks
            if self.cab_tracker:
                self.cab_tracker.log_suggestion(
                    "Directive-Enhanced Storage Error",
                    f"Storage failed despite AI directive routing: {str(e)}",
                    severity='HIGH',
                    context=f"Task: {task}, Routing: {routing}",
                    metrics={"error": str(e)}
                )
            raise
    
    def retrieve_data_with_directives(self, query: Dict[str, Any], task: str,
                                    context: Optional[Dict[str, Any]] = None) -> Tuple[Any, str, bool]:
        """
        Retrieve data using AI directive patterns and cross-system search
        """
        # Get enhanced routing decision
        routing = self.route_with_directives(task, context)
        
        try:
            # Try traditional retrieval first
            result, successful_system, used_fallback = self.memory_selector.retrieve_data(query, task, context)
            
            # If no results and directive suggests cross-system search, try that
            if (not result or (isinstance(result, list) and len(result) == 0)) and \
               routing["mcp_decision"]["intent"] in ["semantic_search", "user_identification"]:
                
                cross_system_result = self._cross_system_search(query, routing, context)
                if cross_system_result:
                    return cross_system_result, "cross_system", True
            
            return result, successful_system, used_fallback
            
        except Exception as e:
            if self.cab_tracker:
                self.cab_tracker.log_suggestion(
                    "Directive-Enhanced Retrieval Error",
                    f"Retrieval failed despite AI directive routing: {str(e)}",
                    severity='HIGH',
                    context=f"Task: {task}, Query: {query}",
                    metrics={"error": str(e)}
                )
            raise
    
    def get_mcp_tool_name(self, operation: str, system: str) -> Optional[str]:
        """
        Get the proper MCP tool name in local__<server-name>__<tool-name> format
        """
        # Map system names to server names
        system_to_server = {
            "neo4j": "neo4j-memory",
            "redis": "redis-memory-server", 
            "basic_memory": "basic-memory"
        }
        
        server_name = system_to_server.get(system)
        if not server_name:
            return None
        
        # Get tool mapping
        tool_mapping = self.mcp_router.get_tool_by_name(operation)
        if tool_mapping:
            return tool_mapping.mcp_name
        
        # Generate standard MCP name if not in mappings
        return f"local__{server_name}__{operation}"
    
    def validate_mcp_compliance(self, tool_name: str) -> bool:
        """
        Validate MCP tool name compliance with AI directives
        Format: local__<server-name>__<tool-name>
        """
        return self.mcp_router.validate_mcp_tool_name(tool_name)
    
    def get_directive_summary(self) -> Dict[str, Any]:
        """
        Get summary of AI directive compliance and current state
        """
        user_profile = None
        if self.startup_handler:
            user_profile = self.startup_handler.get_user_profile()
        
        return {
            "compliance_level": self.compliance_level.value,
            "startup_completed": self.startup_completed,
            "user_profile_available": user_profile is not None,
            "mcp_tools_available": len(self.mcp_router.tool_mappings),
            "cab_tracking_active": self.cab_tracker.initialized if self.cab_tracker else False,
            "startup_sequence_enabled": self.startup_handler is not None,
            "supported_systems": ["neo4j", "redis", "basic_memory"],
            "tool_naming_compliant": True  # Always true since we enforce it
        }
    
    # Private helper methods
    
    def _assess_compliance(self, mcp_decision: Dict[str, Any], traditional_system: MemorySystem) -> str:
        """Assess how well the routing decisions align"""
        mcp_intent = mcp_decision["intent"]
        
        # Check alignment between MCP decision and traditional routing
        alignment_map = {
            "user_identification": MemorySystem.NEO4J,
            "relationships_connections": MemorySystem.NEO4J,
            "entity_creation": MemorySystem.NEO4J,
            "comprehensive_documentation": MemorySystem.BASIC_MEMORY,
            "conversational_context": MemorySystem.REDIS,
            "semantic_search": MemorySystem.REDIS,
            "quick_memories": MemorySystem.REDIS,
        }
        
        expected_system = alignment_map.get(mcp_intent)
        if expected_system == traditional_system:
            return "high_alignment"
        else:
            return "moderate_alignment"
    
    def _get_recommended_action(self, mcp_decision: Dict[str, Any], traditional_system: MemorySystem) -> str:
        """Get recommended action based on routing decisions"""
        if mcp_decision["confidence"] > 0.7:
            return f"use_mcp_routing_{mcp_decision['primary_tool'].system if mcp_decision['primary_tool'] else 'default'}"
        else:
            return f"use_traditional_routing_{traditional_system.value}"
    
    def _build_enhanced_fallback_chain(self, mcp_decision: Dict[str, Any], traditional_system: MemorySystem) -> List[str]:
        """Build enhanced fallback chain combining both approaches"""
        fallback_chain = []
        
        # Add MCP primary tool
        if mcp_decision["primary_tool"]:
            fallback_chain.append(mcp_decision["primary_tool"].mcp_name)
        
        # Add MCP fallback tools
        for tool in mcp_decision["fallback_tools"]:
            fallback_chain.append(tool.mcp_name)
        
        # Add traditional fallback systems
        traditional_fallbacks = self.memory_selector.get_fallback_chain(traditional_system)
        for system in traditional_fallbacks:
            system_name = f"traditional_{system.value}"
            if system_name not in fallback_chain:
                fallback_chain.append(system_name)
        
        return fallback_chain
    
    def _should_propagate_data(self, data: Dict[str, Any], routing: Dict[str, Any], 
                             context: Optional[Dict[str, Any]]) -> bool:
        """Determine if data should be propagated across systems"""
        # Important data types that should be propagated
        important_types = ["user_profile", "preferences", "relationships", "important_documents"]
        
        # Check if data contains important information
        if context and context.get("importance") == "high":
            return True
        
        # Check for user-related data
        if any(key in str(data).lower() for key in ["user", "profile", "preference", "identity"]):
            return True
        
        # Check MCP intent for cross-system operations
        if routing["mcp_decision"]["intent"] in ["user_identification", "relationships_connections"]:
            return True
        
        return False
    
    def _propagate_with_directives(self, data: Dict[str, Any], source_system: str, 
                                 routing: Dict[str, Any], context: Optional[Dict[str, Any]]) -> bool:
        """Propagate data using AI directive patterns"""
        try:
            # Use existing propagation functionality
            source_memory_system = MemorySystem(source_system.lower())
            self.memory_selector.propagate_data(
                data, source_memory_system, "directive_propagation", 
                context=context
            )
            return True
        except Exception as e:
            logger.error(f"Directive propagation failed: {str(e)}")
            return False
    
    def _cross_system_search(self, query: Dict[str, Any], routing: Dict[str, Any],
                           context: Optional[Dict[str, Any]]) -> Optional[Any]:
        """Perform cross-system search when primary system fails"""
        try:
            # This would implement the cross-system search logic
            # For now, return None (placeholder)
            logger.info("Cross-system search attempted (placeholder implementation)")
            return None
        except Exception as e:
            logger.error(f"Cross-system search failed: {str(e)}")
            return None