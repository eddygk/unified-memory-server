"""
Tests for AI Directives Integration layer and directive decision tree
"""
import unittest
import tempfile
import os
from unittest.mock import Mock

import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from mcp_tool_router import MCPToolRouter, MCPToolIntent
from ai_directives_integration import AIDirectivesIntegration, DirectiveCompliance
from cab_tracker import CABTracker


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