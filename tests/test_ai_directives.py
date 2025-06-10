"""
Tests for AI Directives Integration Components
"""
import unittest
import tempfile
import os
from unittest.mock import Mock, patch

import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from mcp_tool_router import MCPToolRouter, MCPToolIntent
from startup_sequence import StartupSequenceHandler
from ai_directives_integration import AIDirectivesIntegration, DirectiveCompliance
from cab_tracker import CABTracker
from memory_selector import MemorySelector


class TestMCPToolRouter(unittest.TestCase):
    """Test MCP Tool Router functionality"""
    
    def setUp(self):
        self.router = MCPToolRouter()
    
    def test_tool_name_validation(self):
        """Test MCP tool name validation"""
        # Valid names
        self.assertTrue(self.router.validate_mcp_tool_name("local__neo4j-memory__create_entities"))
        self.assertTrue(self.router.validate_mcp_tool_name("local__redis-memory-server__search_long_term_memory"))
        self.assertTrue(self.router.validate_mcp_tool_name("local__basic-memory__write_note"))
        
        # Invalid names
        self.assertFalse(self.router.validate_mcp_tool_name("create_entities"))
        self.assertFalse(self.router.validate_mcp_tool_name("local__"))
        self.assertFalse(self.router.validate_mcp_tool_name("local__neo4j__"))
        self.assertFalse(self.router.validate_mcp_tool_name("neo4j__create_entities"))
    
    def test_intent_analysis_relationships(self):
        """Test intent analysis for relationship tasks"""
        intent, confidence = self.router.analyze_task_intent(
            "Find relationships between user and projects"
        )
        self.assertEqual(intent, MCPToolIntent.RELATIONSHIPS_CONNECTIONS)
        self.assertGreaterEqual(confidence, 0.3)
    
    def test_intent_analysis_documentation(self):
        """Test intent analysis for documentation tasks"""
        intent, confidence = self.router.analyze_task_intent(
            "Create comprehensive documentation for the project"
        )
        self.assertEqual(intent, MCPToolIntent.COMPREHENSIVE_DOCUMENTATION)
        self.assertGreater(confidence, 0.3)
    
    def test_intent_analysis_user_identification(self):
        """Test intent analysis for user identification"""
        intent, confidence = self.router.analyze_task_intent(
            "Find my user profile and preferences"
        )
        self.assertEqual(intent, MCPToolIntent.USER_IDENTIFICATION)
        self.assertGreater(confidence, 0.3)
    
    def test_routing_decision(self):
        """Test complete routing decision process"""
        decision = self.router.route_task("Create relationship between user and project")
        
        self.assertIn("intent", decision)
        self.assertIn("confidence", decision)
        self.assertIn("primary_tool", decision)
        self.assertIn("fallback_tools", decision)
        self.assertIn("reasoning", decision)
        
        # Should route to Neo4j for relationships
        if decision["primary_tool"]:
            self.assertEqual(decision["primary_tool"].system, "neo4j")
    
    def test_tool_recommendation_by_intent(self):
        """Test tool recommendations based on intent"""
        # Test user identification
        tools = self.router.get_recommended_tools(MCPToolIntent.USER_IDENTIFICATION)
        self.assertGreater(len(tools), 0)
        self.assertTrue(any("neo4j" in tool.mcp_name for tool in tools))
        
        # Test documentation
        tools = self.router.get_recommended_tools(MCPToolIntent.COMPREHENSIVE_DOCUMENTATION)
        self.assertGreater(len(tools), 0)
        self.assertTrue(any("basic-memory" in tool.mcp_name for tool in tools))
        
        # Test quick memories
        tools = self.router.get_recommended_tools(MCPToolIntent.QUICK_MEMORIES)
        self.assertGreater(len(tools), 0)
        self.assertTrue(any("redis-memory-server" in tool.mcp_name for tool in tools))


class TestStartupSequenceHandler(unittest.TestCase):
    """Test Startup Sequence Handler functionality"""
    
    def setUp(self):
        self.mock_memory_selector = Mock()
        self.mock_cab_tracker = Mock()
        self.mock_mcp_router = Mock()
        
        self.startup_handler = StartupSequenceHandler(
            self.mock_memory_selector,
            self.mock_cab_tracker,
            self.mock_mcp_router
        )
    
    def test_initialization(self):
        """Test startup handler initialization"""
        self.assertIsNotNone(self.startup_handler)
        self.assertFalse(self.startup_handler.startup_completed)
        self.assertIsNone(self.startup_handler.user_profile_data)
    
    def test_startup_sequence_execution(self):
        """Test startup sequence execution"""
        # Mock CAB tracker behavior
        self.mock_cab_tracker.initialized = False
        self.mock_cab_tracker.initialize_session = Mock()
        self.mock_cab_tracker.session_id = "test_session_123"
        
        result = self.startup_handler.execute_startup_sequence("TestUser", "Claude")
        
        self.assertIn("step_0_completed", result)
        self.assertIn("step_1_completed", result)
        self.assertIn("user_profile_found", result)
        self.assertTrue(self.startup_handler.startup_completed)
    
    def test_user_identification_fallback_chain(self):
        """Test user identification tries all systems in order"""
        result = self.startup_handler._execute_step_1("TestUser")
        
        self.assertIn("systems_checked", result)
        self.assertIn("user_profile_found", result)
        self.assertIn("user_profile_source", result)
        
        # Should check all systems
        expected_systems = ["neo4j", "redis", "basic_memory"]
        for system in expected_systems:
            self.assertIn(system, result["systems_checked"])
    
    def test_force_user_identification(self):
        """Test forced user identification"""
        result = self.startup_handler.force_user_identification("TestUser")
        
        self.assertIn("systems_checked", result)
        self.assertIn("user_profile_found", result)


class TestAIDirectivesIntegration(unittest.TestCase):
    """Test AI Directives Integration layer"""
    
    def setUp(self):
        # Create temporary CAB file
        self.temp_cab_file = tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False)
        self.temp_cab_file.close()
        
        self.cab_tracker = CABTracker(self.temp_cab_file.name)
        self.memory_selector = Mock()
        
        self.integration = AIDirectivesIntegration(
            memory_selector=self.memory_selector,
            cab_tracker=self.cab_tracker,
            enable_startup_sequence=True
        )
    
    def tearDown(self):
        # Clean up temporary file
        if os.path.exists(self.temp_cab_file.name):
            os.unlink(self.temp_cab_file.name)
    
    def test_initialization(self):
        """Test integration initialization"""
        self.assertIsNotNone(self.integration.memory_selector)
        self.assertIsNotNone(self.integration.cab_tracker)
        self.assertIsNotNone(self.integration.mcp_router)
        self.assertIsNotNone(self.integration.startup_handler)
        
        self.assertEqual(self.integration.compliance_level, DirectiveCompliance.BASIC_FUNCTIONALITY)
    
    def test_mcp_tool_name_generation(self):
        """Test MCP tool name generation"""
        # Test valid combinations
        tool_name = self.integration.get_mcp_tool_name("create_entities", "neo4j")
        self.assertEqual(tool_name, "local__neo4j-memory__create_entities")
        
        tool_name = self.integration.get_mcp_tool_name("search_memory", "redis")
        self.assertIn("local__redis-memory-server", tool_name)
        
        tool_name = self.integration.get_mcp_tool_name("write_note", "basic_memory") 
        self.assertEqual(tool_name, "local__basic-memory__write_note")
    
    def test_mcp_compliance_validation(self):
        """Test MCP compliance validation"""
        # Valid MCP names
        self.assertTrue(self.integration.validate_mcp_compliance("local__neo4j-memory__create_entities"))
        self.assertTrue(self.integration.validate_mcp_compliance("local__redis-memory-server__search_memory"))
        
        # Invalid names
        self.assertFalse(self.integration.validate_mcp_compliance("create_entities"))
        self.assertFalse(self.integration.validate_mcp_compliance("local__invalid"))
    
    def test_directive_routing(self):
        """Test routing with AI directives"""
        # Mock memory selector responses
        from memory_selector import MemorySystem, TaskType, TaskAnalysis, OperationType
        
        mock_analysis = TaskAnalysis(
            task_type=TaskType.RELATIONSHIP_QUERY,
            operation_type=OperationType.READ,
            entities=["user", "project"],
            confidence=0.8,
            reasoning="Mock analysis",
            patterns_matched=["relationship"]
        )
        
        self.memory_selector.get_task_analysis.return_value = mock_analysis
        self.memory_selector.select_memory_system.return_value = (MemorySystem.NEO4J, TaskType.RELATIONSHIP_QUERY)
        self.memory_selector.get_fallback_chain.return_value = [MemorySystem.REDIS, MemorySystem.BASIC_MEMORY]
        
        routing = self.integration.route_with_directives("Find relationships between user and project")
        
        self.assertIn("mcp_decision", routing)
        self.assertIn("traditional_decision", routing)
        self.assertIn("directive_compliance", routing)
        self.assertIn("recommended_action", routing)
        self.assertIn("fallback_chain", routing)
    
    def test_enhanced_data_storage(self):
        """Test data storage with directive compliance"""
        # Mock memory selector responses
        from memory_selector import MemorySystem, TaskType, TaskAnalysis, OperationType
        
        mock_analysis = TaskAnalysis(
            task_type=TaskType.USER_IDENTITY,
            operation_type=OperationType.CREATE,
            entities=["user"],
            confidence=0.8,
            reasoning="Mock analysis",
            patterns_matched=["user"]
        )
        
        self.memory_selector.get_task_analysis.return_value = mock_analysis
        self.memory_selector.select_memory_system.return_value = (MemorySystem.NEO4J, TaskType.USER_IDENTITY)
        self.memory_selector.get_fallback_chain.return_value = [MemorySystem.REDIS, MemorySystem.BASIC_MEMORY]
        self.memory_selector.store_data.return_value = ("success", "neo4j", False)
        
        test_data = {"user_id": "123", "preferences": {"theme": "dark"}}
        result, system, fallback = self.integration.store_data_with_directives(
            test_data, "Store user preferences"
        )
        
        self.assertEqual(result, "success")
        self.assertEqual(system, "neo4j")
        self.memory_selector.store_data.assert_called_once()
    
    def test_enhanced_data_retrieval(self):
        """Test data retrieval with directive compliance"""
        # Mock memory selector responses
        from memory_selector import MemorySystem, TaskType, TaskAnalysis, OperationType
        
        mock_analysis = TaskAnalysis(
            task_type=TaskType.SEMANTIC_SEARCH,
            operation_type=OperationType.SEARCH,
            entities=["user"],
            confidence=0.8,
            reasoning="Mock analysis",
            patterns_matched=["search"]
        )
        
        self.memory_selector.get_task_analysis.return_value = mock_analysis
        self.memory_selector.select_memory_system.return_value = (MemorySystem.REDIS, TaskType.SEMANTIC_SEARCH)
        self.memory_selector.get_fallback_chain.return_value = [MemorySystem.BASIC_MEMORY, MemorySystem.NEO4J]
        self.memory_selector.retrieve_data.return_value = ({"user": "data"}, "redis", False)
        
        test_query = {"search": "user preferences"}
        result, system, fallback = self.integration.retrieve_data_with_directives(
            test_query, "Find user preferences"
        )
        
        self.assertEqual(result, {"user": "data"})
        self.assertEqual(system, "redis")
        self.memory_selector.retrieve_data.assert_called_once()
    
    def test_directive_summary(self):
        """Test directive compliance summary"""
        summary = self.integration.get_directive_summary()
        
        expected_keys = [
            "compliance_level", "startup_completed", "user_profile_available",
            "mcp_tools_available", "cab_tracking_active", "startup_sequence_enabled",
            "supported_systems", "tool_naming_compliant"
        ]
        
        for key in expected_keys:
            self.assertIn(key, summary)
        
        self.assertEqual(summary["supported_systems"], ["neo4j", "redis", "basic_memory"])
        self.assertTrue(summary["tool_naming_compliant"])
    
    def test_startup_sequence_integration(self):
        """Test startup sequence execution through integration"""
        result = self.integration.execute_startup_sequence("TestUser", "Claude")
        
        self.assertIn("step_0_completed", result)
        self.assertIn("step_1_completed", result)
        self.assertTrue(self.integration.startup_completed)


class TestDirectiveDecisionTree(unittest.TestCase):
    """Test the AI directive decision tree implementation"""
    
    def setUp(self):
        self.router = MCPToolRouter()
    
    def test_decision_tree_relationships(self):
        """Test: Does the task involve relationships/connections between entities? -> Neo4j"""
        tasks = [
            "Find relationships between user and projects",
            "Create connection between entities",
            "Link user to preferences",
            "Show entity relationships"
        ]
        
        for task in tasks:
            intent, confidence = self.router.analyze_task_intent(task)
            self.assertEqual(intent, MCPToolIntent.RELATIONSHIPS_CONNECTIONS)
            self.assertGreater(confidence, 0.2)
    
    def test_decision_tree_documentation(self):
        """Test: Does task require comprehensive documentation/structured notes? -> Basic Memory"""
        tasks = [
            "Create comprehensive documentation",
            "Write structured notes about project",
            "Document the process",
            "Save project documentation"
        ]
        
        for task in tasks:
            intent, confidence = self.router.analyze_task_intent(task)
            self.assertEqual(intent, MCPToolIntent.COMPREHENSIVE_DOCUMENTATION)
            self.assertGreater(confidence, 0.2)
    
    def test_decision_tree_conversational_context(self):
        """Test: Does task need conversational context/semantic search? -> Redis"""
        tasks = [
            "Get conversation context",
            "Retrieve session information",
            "Search for similar topics",
            "Find related memories"
        ]
        
        for task in tasks:
            intent, confidence = self.router.analyze_task_intent(task)
            # Should be either conversational context or semantic search
            self.assertIn(intent, [MCPToolIntent.CONVERSATIONAL_CONTEXT, MCPToolIntent.SEMANTIC_SEARCH])
            self.assertGreater(confidence, 0.2)


if __name__ == '__main__':
    unittest.main()