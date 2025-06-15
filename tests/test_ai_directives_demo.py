"""
Tests for AI Directives Demo cleanup behavior
Tests the DEMO_CLEANUP_TEMP_FILES environment flag functionality
"""
import unittest
import tempfile
import os
from unittest.mock import patch, MagicMock
import sys

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# Mock the AI directives integration to avoid complex dependencies in tests
with patch('ai_directives_demo.AIDirectivesIntegration'), \
     patch('ai_directives_demo.CABTracker'):
    import ai_directives_demo


class TestAIDirectivesDemoCleanup(unittest.TestCase):
    """Test cleanup behavior in AI directives demo"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Store original environment
        self.original_env = os.environ.get('DEMO_CLEANUP_TEMP_FILES')
        
    def tearDown(self):
        """Clean up test fixtures"""
        # Restore original environment
        if self.original_env is not None:
            os.environ['DEMO_CLEANUP_TEMP_FILES'] = self.original_env
        elif 'DEMO_CLEANUP_TEMP_FILES' in os.environ:
            del os.environ['DEMO_CLEANUP_TEMP_FILES']
    
    @patch('ai_directives_demo.AIDirectivesIntegration')
    @patch('ai_directives_demo.CABTracker')
    def test_cleanup_enabled_flow(self, mock_cab_tracker, mock_integration):
        """Test cleanup enabled flow removes temporary file"""
        # Set environment variable to enable cleanup
        os.environ['DEMO_CLEANUP_TEMP_FILES'] = 'true'
        
        # Mock the integration and tracker to avoid actual initialization
        mock_integration_instance = MagicMock()
        mock_integration.return_value = mock_integration_instance
        mock_integration_instance.execute_startup_sequence.return_value = {
            'step_0_completed': True,
            'step_1_completed': True,
            'user_profile_found': False
        }
        mock_integration_instance.route_with_directives.return_value = {
            'mcp_decision': {'intent': 'test', 'confidence': 0.8}
        }
        mock_integration_instance.get_mcp_tool_name.return_value = 'test_tool'
        mock_integration_instance.validate_mcp_compliance.return_value = True
        mock_integration_instance.get_directive_summary.return_value = {
            'compliance_level': 'FULL_COMPLIANCE',
            'tool_naming_compliant': True
        }
        
        # Capture print output to verify cleanup messages
        with patch('builtins.print') as mock_print:
            ai_directives_demo.demonstrate_ai_directives()
            
        # Check that cleanup messages were printed
        print_calls = [call[0][0] for call in mock_print.call_args_list if call[0]]
        cleanup_messages = [msg for msg in print_calls if 'Cleaning up CAB file:' in str(msg)]
        success_messages = [msg for msg in print_calls if '✓ Temporary file cleaned up' in str(msg)]
        
        self.assertGreater(len(cleanup_messages), 0, "Should print cleanup message when enabled")
        self.assertGreater(len(success_messages), 0, "Should print success message when cleanup works")
    
    @patch('ai_directives_demo.AIDirectivesIntegration')
    @patch('ai_directives_demo.CABTracker')
    def test_cleanup_disabled_flow(self, mock_cab_tracker, mock_integration):
        """Test cleanup disabled flow retains temporary file"""
        # Set environment variable to disable cleanup (or leave unset)
        os.environ['DEMO_CLEANUP_TEMP_FILES'] = 'false'
        
        # Mock the integration and tracker to avoid actual initialization
        mock_integration_instance = MagicMock()
        mock_integration.return_value = mock_integration_instance
        mock_integration_instance.execute_startup_sequence.return_value = {
            'step_0_completed': True,
            'step_1_completed': True,
            'user_profile_found': False
        }
        mock_integration_instance.route_with_directives.return_value = {
            'mcp_decision': {'intent': 'test', 'confidence': 0.8}
        }
        mock_integration_instance.get_mcp_tool_name.return_value = 'test_tool'
        mock_integration_instance.validate_mcp_compliance.return_value = True
        mock_integration_instance.get_directive_summary.return_value = {
            'compliance_level': 'FULL_COMPLIANCE',
            'tool_naming_compliant': True
        }
        
        # Capture print output to verify retention messages
        with patch('builtins.print') as mock_print:
            ai_directives_demo.demonstrate_ai_directives()
            
        # Check that retention messages were printed
        print_calls = [call[0][0] for call in mock_print.call_args_list if call[0]]
        retention_messages = [msg for msg in print_calls if 'CAB file retained for inspection:' in str(msg)]
        instruction_messages = [msg for msg in print_calls if 'Set DEMO_CLEANUP_TEMP_FILES=true' in str(msg)]
        
        self.assertGreater(len(retention_messages), 0, "Should print retention message when disabled")
        self.assertGreater(len(instruction_messages), 0, "Should print instruction message when disabled")
    
    @patch('ai_directives_demo.AIDirectivesIntegration')
    @patch('ai_directives_demo.CABTracker')
    def test_cleanup_default_behavior(self, mock_cab_tracker, mock_integration):
        """Test default behavior (cleanup disabled) when environment variable not set"""
        # Ensure environment variable is not set
        if 'DEMO_CLEANUP_TEMP_FILES' in os.environ:
            del os.environ['DEMO_CLEANUP_TEMP_FILES']
        
        # Mock the integration and tracker to avoid actual initialization
        mock_integration_instance = MagicMock()
        mock_integration.return_value = mock_integration_instance
        mock_integration_instance.execute_startup_sequence.return_value = {
            'step_0_completed': True,
            'step_1_completed': True,
            'user_profile_found': False
        }
        mock_integration_instance.route_with_directives.return_value = {
            'mcp_decision': {'intent': 'test', 'confidence': 0.8}
        }
        mock_integration_instance.get_mcp_tool_name.return_value = 'test_tool'
        mock_integration_instance.validate_mcp_compliance.return_value = True
        mock_integration_instance.get_directive_summary.return_value = {
            'compliance_level': 'FULL_COMPLIANCE',
            'tool_naming_compliant': True
        }
        
        # Capture print output to verify default behavior (retention)
        with patch('builtins.print') as mock_print:
            ai_directives_demo.demonstrate_ai_directives()
            
        # Check that retention messages were printed (default behavior)
        print_calls = [call[0][0] for call in mock_print.call_args_list if call[0]]
        retention_messages = [msg for msg in print_calls if 'CAB file retained for inspection:' in str(msg)]
        
        self.assertGreater(len(retention_messages), 0, "Should default to retention when env var not set")


if __name__ == '__main__':
    unittest.main()