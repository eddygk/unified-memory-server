"""
Tests for Startup Sequence Handler functionality
"""
import unittest
import os
from unittest.mock import Mock

import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from startup_sequence import StartupSequenceHandler


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
        result = self.startup_handler.force_user_identification("TestUser")
        
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


if __name__ == '__main__':
    unittest.main()