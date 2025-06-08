"""
Tests for MemorySelector configuration functionality
"""
import unittest
import tempfile
import os
from unittest.mock import patch, MagicMock, call
import sys
import logging

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from memory_selector import MemorySelector
from cab_tracker import CABTracker


class TestMemorySelectorConfig(unittest.TestCase):
    """Test MemorySelector configuration loading and validation"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.mock_cab_tracker = MagicMock(spec=CABTracker)
        
    def tearDown(self):
        """Clean up after tests"""
        # Clean up any environment variables that might have been set
        env_vars_to_clean = [
            'TEST_KEY', 'MALFORMED_TEST', 'REDIS_URL', 'NEO4J_URL',
            'NEO4J_PASSWORD', 'BASIC_MEMORY_PATH', 'JWT_SECRET', 'OAUTH2_ISSUER_URL'
        ]
        for var in env_vars_to_clean:
            if var in os.environ:
                del os.environ[var]
    
    @patch('memory_selector.logger')
    def test_parse_env_file_malformed_lines_logs_warning(self, mock_logger):
        """Test that parsing .env file with malformed lines logs warnings"""
        # Create a temporary .env file with malformed content
        env_content = """
# This is a comment
VALID_KEY=valid_value
malformed_line_without_equals
ANOTHER_VALID=another_value
invalid line with spaces
KEY_WITH_QUOTES="quoted value"
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as temp_file:
            temp_file.write(env_content)
            temp_file.flush()
            
            try:
                # Create MemorySelector instance and call _parse_env_file
                selector = MemorySelector(validate_config=False)
                selector._parse_env_file(temp_file.name)
                
                # Verify that logger.warning was called for malformed entries
                warning_calls = [call for call in mock_logger.warning.call_args_list 
                               if 'Malformed line' in str(call)]
                
                # Should have 2 malformed lines: 'malformed_line_without_equals' and 'invalid line with spaces'
                self.assertEqual(len(warning_calls), 2)
                
                # Check that the warning messages contain the expected content
                warning_messages = [str(call) for call in warning_calls]
                self.assertTrue(any('malformed_line_without_equals' in msg for msg in warning_messages))
                self.assertTrue(any('invalid line with spaces' in msg for msg in warning_messages))
                
            finally:
                # Clean up temporary file
                os.unlink(temp_file.name)
    
    @patch('memory_selector.logger')
    def test_parse_env_file_valid_lines_no_warning(self, mock_logger):
        """Test that parsing .env file with only valid lines doesn't log malformed warnings"""
        # Create a temporary .env file with only valid content
        env_content = """
# This is a comment
VALID_KEY=valid_value
ANOTHER_VALID=another_value
KEY_WITH_QUOTES="quoted value"
KEY_WITH_SINGLE_QUOTES='single quoted'

# Another comment
EMPTY_VALUE=
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as temp_file:
            temp_file.write(env_content)
            temp_file.flush()
            
            try:
                # Create MemorySelector instance and call _parse_env_file
                selector = MemorySelector(validate_config=False)
                selector._parse_env_file(temp_file.name)
                
                # Verify that logger.warning was NOT called for malformed entries
                warning_calls = [call for call in mock_logger.warning.call_args_list 
                               if 'Malformed line' in str(call)]
                
                # Should have 0 malformed line warnings
                self.assertEqual(len(warning_calls), 0)
                
            finally:
                # Clean up temporary file
                os.unlink(temp_file.name)
    
    def test_config_validation_with_cab_tracker_logging(self):
        """Test that config validation logs to CAB tracker when available"""
        # Create a MemorySelector with a mock CAB tracker but no valid config
        with patch.dict(os.environ, {}, clear=True):
            selector = MemorySelector(
                cab_tracker=self.mock_cab_tracker, 
                validate_config=True
            )
            
            # Verify that CAB tracker log_suggestion was called for config warnings
            self.mock_cab_tracker.log_suggestion.assert_called()
            
            # Check that at least one call was for Configuration Warning
            suggestion_calls = self.mock_cab_tracker.log_suggestion.call_args_list
            config_warning_calls = [
                call for call in suggestion_calls 
                if call[0][0] == "Configuration Warning"
            ]
            self.assertGreater(len(config_warning_calls), 0)
    
    @patch('memory_selector.logger')
    def test_config_validation_logger_warnings(self, mock_logger):
        """Test that config validation logs warnings when essential config is missing"""
        # Create a MemorySelector with minimal environment
        with patch.dict(os.environ, {}, clear=True):
            selector = MemorySelector(validate_config=True)
            
            # Verify that logger.warning was called for configuration warnings
            warning_calls = [call for call in mock_logger.warning.call_args_list 
                           if 'Configuration warning' in str(call)]
            
            # Should have multiple configuration warnings
            self.assertGreater(len(warning_calls), 0)
            
            # Check for specific warnings we expect
            warning_messages = [str(call) for call in warning_calls]
            self.assertTrue(any('REDIS_URL not configured' in msg for msg in warning_messages))


if __name__ == '__main__':
    unittest.main()