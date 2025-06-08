"""
Tests for MemorySelector configuration parsing and validation.

Tests malformed .env file handling, configuration validation,
and CAB tracker integration.
"""
import os
import tempfile
import unittest
from unittest.mock import Mock, patch, call
from src.memory_selector import MemorySelector


class TestMemorySelectorConfig(unittest.TestCase):
    """Test suite for MemorySelector configuration functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_cab_tracker = Mock()
        
    def tearDown(self):
        """Clean up after tests."""
        # Clean up any environment variables that might have been set
        env_vars_to_clean = [
            'REDIS_URL', 'NEO4J_URL', 'NEO4J_PASSWORD', 'BASIC_MEMORY_PATH',
            'JWT_SECRET', 'OAUTH2_ISSUER_URL', 'CAB_LOG_PATH'
        ]
        for var in env_vars_to_clean:
            if var in os.environ:
                del os.environ[var]
    
    def test_parse_env_file_with_malformed_lines(self):
        """Test that malformed lines in .env file generate warnings."""
        # Create a temporary .env file with malformed lines
        with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
            f.write("""# This is a comment
VALID_KEY=valid_value
malformed_line_without_equals
ANOTHER_VALID=another_value
  just_some_text  
KEY_WITH_QUOTES="quoted_value"
""")
            temp_env_file = f.name
        
        try:
            with patch('src.memory_selector.logger') as mock_logger:
                selector = MemorySelector(validate_config=False)
                selector._parse_env_file(temp_env_file)
                
                # Verify that warnings were logged for malformed lines
                warning_calls = [call for call in mock_logger.warning.call_args_list if 'Malformed line' in str(call)]
                self.assertEqual(len(warning_calls), 2)
                
                # Use assert_any_call for more explicit assertion
                mock_logger.warning.assert_any_call(
                    f"Malformed line in {temp_env_file} at line 3: 'malformed_line_without_equals'. Expected KEY=VALUE format."
                )
                mock_logger.warning.assert_any_call(
                    f"Malformed line in {temp_env_file} at line 5: 'just_some_text'. Expected KEY=VALUE format."
                )
                
                # Verify that valid lines were processed correctly
                self.assertEqual(os.environ.get('VALID_KEY'), 'valid_value')
                self.assertEqual(os.environ.get('ANOTHER_VALID'), 'another_value')
                self.assertEqual(os.environ.get('KEY_WITH_QUOTES'), 'quoted_value')
        finally:
            os.unlink(temp_env_file)
    
    def test_parse_env_file_with_comments_and_empty_lines(self):
        """Test that comments and empty lines are properly ignored."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
            f.write("""
# This is a comment
# Another comment

VALID_KEY=value
   # Indented comment

ANOTHER_KEY=another_value
""")
            temp_env_file = f.name
        
        try:
            with patch('src.memory_selector.logger') as mock_logger:
                selector = MemorySelector(validate_config=False)
                selector._parse_env_file(temp_env_file)
                
                # Verify no warnings were logged for comments or empty lines
                warning_calls = [call for call in mock_logger.warning.call_args_list if 'Malformed line' in str(call)]
                self.assertEqual(len(warning_calls), 0)
                
                # Verify valid keys were processed
                self.assertEqual(os.environ.get('VALID_KEY'), 'value')
                self.assertEqual(os.environ.get('ANOTHER_KEY'), 'another_value')
        finally:
            os.unlink(temp_env_file)
    
    def test_config_validation_warnings(self):
        """Test that configuration validation generates appropriate warnings."""
        with patch('src.memory_selector.logger') as mock_logger:
            # Clear relevant environment variables to trigger warnings
            env_vars_to_clear = ['REDIS_URL', 'NEO4J_URL', 'NEO4J_PASSWORD', 'JWT_SECRET', 'OAUTH2_ISSUER_URL']
            original_values = {}
            for var in env_vars_to_clear:
                original_values[var] = os.environ.get(var)
                if var in os.environ:
                    del os.environ[var]
            
            try:
                # Set up conditions to trigger specific warnings
                os.environ['NEO4J_ENABLED'] = 'true'
                os.environ['DISABLE_AUTH'] = 'false'
                
                selector = MemorySelector(self.mock_cab_tracker, validate_config=True)
                
                # Verify that configuration warnings were logged
                warning_calls = [call for call in mock_logger.warning.call_args_list 
                               if 'Configuration warning:' in str(call)]
                self.assertGreater(len(warning_calls), 0)
                
                # Verify specific warnings were generated
                mock_logger.warning.assert_any_call(
                    "Configuration warning: REDIS_URL not configured - Redis memory system may not function"
                )
                mock_logger.warning.assert_any_call(
                    "Configuration warning: NEO4J_URL not configured but Neo4j is enabled"
                )
                mock_logger.warning.assert_any_call(
                    "Configuration warning: JWT_SECRET not configured but authentication is enabled"
                )
                
            finally:
                # Restore original environment variable values
                for var, value in original_values.items():
                    if value is not None:
                        os.environ[var] = value
                    elif var in os.environ:
                        del os.environ[var]
    
    def test_cab_tracker_integration(self):
        """Test that CAB tracker is properly integrated for configuration warnings."""
        with patch('src.memory_selector.logger'):
            # Clear REDIS_URL to trigger a warning
            original_redis_url = os.environ.get('REDIS_URL')
            if 'REDIS_URL' in os.environ:
                del os.environ['REDIS_URL']
            
            try:
                selector = MemorySelector(self.mock_cab_tracker, validate_config=True)
                
                # Verify CAB tracker was called for configuration warnings
                self.mock_cab_tracker.log_suggestion.assert_called()
                
                # Check that at least one call was made with the expected parameters
                calls = self.mock_cab_tracker.log_suggestion.call_args_list
                redis_warning_call = None
                for call_args, call_kwargs in calls:
                    if "REDIS_URL not configured" in call_args[1]:
                        redis_warning_call = (call_args, call_kwargs)
                        break
                
                self.assertIsNotNone(redis_warning_call)
                call_args, call_kwargs = redis_warning_call
                self.assertEqual(call_args[0], "Configuration Warning")
                self.assertTrue("REDIS_URL not configured" in call_args[1])
                self.assertEqual(call_kwargs.get('severity'), 'MEDIUM')
                self.assertEqual(call_kwargs.get('context'), "Configuration validation")
                
            finally:
                # Restore original REDIS_URL if it existed
                if original_redis_url is not None:
                    os.environ['REDIS_URL'] = original_redis_url
    
    def test_env_file_parsing_with_quotes(self):
        """Test that quoted values are properly handled."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
            f.write("""DOUBLE_QUOTED="value with spaces"
SINGLE_QUOTED='another value'
NO_QUOTES=simple_value
EMPTY_QUOTED=""
""")
            temp_env_file = f.name
        
        try:
            selector = MemorySelector(validate_config=False)
            selector._parse_env_file(temp_env_file)
            
            # Verify that quoted values are properly parsed
            self.assertEqual(os.environ.get('DOUBLE_QUOTED'), 'value with spaces')
            self.assertEqual(os.environ.get('SINGLE_QUOTED'), 'another value')
            self.assertEqual(os.environ.get('NO_QUOTES'), 'simple_value')
            self.assertEqual(os.environ.get('EMPTY_QUOTED'), '')
        finally:
            os.unlink(temp_env_file)


if __name__ == '__main__':
    unittest.main()