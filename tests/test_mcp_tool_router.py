"""
Tests for MCP Tool Router functionality
"""
import unittest
import os

import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from mcp_tool_router import MCPToolRouter, MCPToolIntent


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
        self.assertGreaterEqual(confidence, 0.3)
    
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
        self.assertIsNotNone(decision["primary_tool"], "Primary tool is unexpectedly None.")
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


if __name__ == '__main__':
    unittest.main()