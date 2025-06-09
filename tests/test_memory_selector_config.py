"""
Tests for MemorySelector configuration functionality
"""
import os
import tempfile
import unittest
from unittest.mock import patch, MagicMock
import sys

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from memory_selector import MemorySelector


class TestMemorySelectorConfig(unittest.TestCase):
    """Test suite for MemorySelector configuration loading and validation"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.test_config = {
            'redis_url': 'redis://localhost:6379',
            'neo4j_url': 'bolt://localhost:7687',
            'neo4j_username': 'neo4j',
            'neo4j_password': 'password',
            'basic_memory_url': 'http://localhost:8080',
            'basic_memory_path': '/tmp/basic_memory'
        }
        
    def create_temp_config_file(self, config_data):
        """Create a temporary configuration file"""
        temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.env')
        for key, value in config_data.items():
            temp_file.write(f"{key.upper()}={value}\n")
        temp_file.close()
        return temp_file.name
    
    def test_init_with_default_parameters(self):
        """Test MemorySelector initialization with default parameters"""
        selector = MemorySelector()
        self.assertIsNotNone(selector)
        self.assertIsNone(selector.cab_tracker)
        self.assertIsInstance(selector.config, dict)
    
    def test_init_with_cab_tracker(self):
        """Test MemorySelector initialization with CAB tracker"""
        mock_tracker = MagicMock()
        selector = MemorySelector(cab_tracker=mock_tracker)
        self.assertEqual(selector.cab_tracker, mock_tracker)
    
    def test_load_config_from_file(self):
        """Test loading configuration from specified file"""
        temp_file = self.create_temp_config_file(self.test_config)
        try:
            selector = MemorySelector(config_path=temp_file)
            
            # Check that config was loaded
            self.assertEqual(selector.config['REDIS_URL'], 'redis://localhost:6379')
            self.assertEqual(selector.config['NEO4J_URL'], 'bolt://localhost:7687')
            self.assertEqual(selector.config['NEO4J_USERNAME'], 'neo4j')
            self.assertEqual(selector.config['NEO4J_PASSWORD'], 'password')
            
        finally:
            os.unlink(temp_file)
    
    def test_load_config_file_not_found(self):
        """Test behavior when specified config file doesn't exist"""
        with patch('memory_selector.logger') as mock_logger:
            selector = MemorySelector(config_path='/nonexistent/path.env')
            
            # Should log a warning
            mock_logger.warning.assert_called()
            warning_calls = [call for call in mock_logger.warning.call_args_list 
                           if 'Config file not found' in str(call) or 'No configuration file found' in str(call)]
            self.assertTrue(len(warning_calls) > 0)
    
    def test_load_config_fallback_paths(self):
        """Test configuration loading from fallback paths"""
        # Create a temporary file in current directory as .env
        with tempfile.NamedTemporaryFile(mode='w', delete=False, 
                                       suffix='.env', dir='.') as temp_file:
            temp_file.write("REDIS_URL=redis://fallback:6379\n")
            temp_file.write("NEO4J_URL=bolt://fallback:7687\n")
        
        try:
            # Rename to .env for fallback test
            fallback_path = '.env'
            os.rename(temp_file.name, fallback_path)
            
            selector = MemorySelector()
            
            # Should load from fallback .env file
            self.assertEqual(selector.config.get('REDIS_URL'), 'redis://fallback:6379')
            self.assertEqual(selector.config.get('NEO4J_URL'), 'bolt://fallback:7687')
            
        finally:
            if os.path.exists(fallback_path):
                os.unlink(fallback_path)
    
    @patch.dict(os.environ, {
        'REDIS_URL': 'redis://env:6379',
        'NEO4J_URL': 'bolt://env:7687',
        'NEO4J_USERNAME': 'env_user',
        'NEO4J_PASSWORD': 'env_pass'
    })
    def test_load_config_from_environment(self):
        """Test loading configuration from environment variables"""
        selector = MemorySelector()
        
        # Should load from environment
        self.assertEqual(selector.config['REDIS_URL'], 'redis://env:6379')
        self.assertEqual(selector.config['NEO4J_URL'], 'bolt://env:7687')
        self.assertEqual(selector.config['NEO4J_USERNAME'], 'env_user')
        self.assertEqual(selector.config['NEO4J_PASSWORD'], 'env_pass')
    
    def test_parse_env_file_valid_format(self):
        """Test parsing valid .env file format"""
        temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False)
        temp_file.write("# This is a comment\n")
        temp_file.write("REDIS_URL=redis://localhost:6379\n")
        temp_file.write("NEO4J_USERNAME=\"test_user\"\n")
        temp_file.write("NEO4J_PASSWORD='test_pass'\n")
        temp_file.write("\n")  # Empty line
        temp_file.write("BASIC_MEMORY_PATH=/tmp/memory\n")
        temp_file.close()
        
        try:
            selector = MemorySelector()
            selector._parse_env_file(temp_file.name)
            
            # Check that environment variables were set
            self.assertEqual(os.environ.get('REDIS_URL'), 'redis://localhost:6379')
            self.assertEqual(os.environ.get('NEO4J_USERNAME'), 'test_user')
            self.assertEqual(os.environ.get('NEO4J_PASSWORD'), 'test_pass')
            self.assertEqual(os.environ.get('BASIC_MEMORY_PATH'), '/tmp/memory')
            
        finally:
            os.unlink(temp_file.name)
            # Clean up environment variables
            for key in ['REDIS_URL', 'NEO4J_USERNAME', 'NEO4J_PASSWORD', 'BASIC_MEMORY_PATH']:
                if key in os.environ:
                    del os.environ[key]
    
    def test_parse_env_file_invalid_lines(self):
        """Test parsing .env file with invalid lines"""
        temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False)
        temp_file.write("VALID_KEY=valid_value\n")
        temp_file.write("INVALID_LINE_NO_EQUALS\n")
        temp_file.write("ANOTHER_VALID=another_value\n")
        temp_file.close()
        
        try:
            with patch('memory_selector.logger') as mock_logger:
                selector = MemorySelector()
                selector._parse_env_file(temp_file.name)
                
                # Should have set valid entries
                self.assertEqual(os.environ.get('VALID_KEY'), 'valid_value')
                self.assertEqual(os.environ.get('ANOTHER_VALID'), 'another_value')
                
                # Should have logged warning for malformed line
                mock_logger.warning.assert_called()
                
                # Use assert_any_call with a custom matcher for more specific assertion
                class ContainsMalformedLineWarning:
                    def __eq__(self, other):
                        return ('INVALID_LINE_NO_EQUALS' in str(other) and 
                                'Malformed line' in str(other) and 
                                'Expected KEY=VALUE format' in str(other))
                    def __repr__(self):
                        return '<ContainsMalformedLineWarning>'
                
                mock_logger.warning.assert_any_call(ContainsMalformedLineWarning())
                
        finally:
            os.unlink(temp_file.name)
            # Clean up environment variables
            for key in ['VALID_KEY', 'ANOTHER_VALID']:
                if key in os.environ:
                    del os.environ[key]
    
    def test_validate_config_complete(self):
        """Test configuration validation with complete config"""
        temp_file = self.create_temp_config_file(self.test_config)
        try:
            with patch('memory_selector.logger') as mock_logger:
                selector = MemorySelector(config_path=temp_file)
                
                # Should still have some warnings for paths and directories that don't exist
                # but no "not configured" warnings
                warning_calls = [call for call in mock_logger.warning.call_args_list 
                               if 'not configured' in str(call)]
                # With a complete config, we should have fewer "not configured" warnings
                self.assertTrue(len(warning_calls) <= 2)  # Allow for auth-related warnings
                
        finally:
            os.unlink(temp_file)
    
    def test_validate_config_missing_redis(self):
        """Test configuration validation with missing Redis config"""
        incomplete_config = {k: v for k, v in self.test_config.items() 
                           if not k.startswith('redis')}
        temp_file = self.create_temp_config_file(incomplete_config)
        
        try:
            # Ensure REDIS_URL is not in environment
            original_redis_url = os.environ.get('REDIS_URL')
            if 'REDIS_URL' in os.environ:
                del os.environ['REDIS_URL']
                
            with patch('memory_selector.logger') as mock_logger:
                selector = MemorySelector(config_path=temp_file)
                
                # Should log warning about Redis
                warning_calls = [call for call in mock_logger.warning.call_args_list 
                               if 'REDIS_URL not configured' in str(call)]
                self.assertTrue(len(warning_calls) > 0)
                
        finally:
            # Restore environment
            if original_redis_url is not None:
                os.environ['REDIS_URL'] = original_redis_url
            os.unlink(temp_file)
    
    def test_validate_config_missing_neo4j_credentials(self):
        """Test configuration validation with missing Neo4j credentials"""
        incomplete_config = {k: v for k, v in self.test_config.items() 
                           if k not in ['neo4j_username', 'neo4j_password']}
        temp_file = self.create_temp_config_file(incomplete_config)
        
        try:
            # Ensure NEO4J_PASSWORD is not in environment
            original_neo4j_password = os.environ.get('NEO4J_PASSWORD')
            if 'NEO4J_PASSWORD' in os.environ:
                del os.environ['NEO4J_PASSWORD']
                
            with patch('memory_selector.logger') as mock_logger:
                selector = MemorySelector(config_path=temp_file)
                
                # Should log warning about Neo4j credentials
                warning_calls = [call for call in mock_logger.warning.call_args_list 
                               if 'NEO4J_PASSWORD not configured' in str(call)]
                self.assertTrue(len(warning_calls) > 0)
                
        finally:
            # Restore environment
            if original_neo4j_password is not None:
                os.environ['NEO4J_PASSWORD'] = original_neo4j_password
            os.unlink(temp_file)
    
    def test_validate_config_disabled(self):
        """Test that validation can be disabled"""
        incomplete_config = {'redis_url': 'redis://localhost:6379'}  # Very incomplete
        temp_file = self.create_temp_config_file(incomplete_config)
        
        try:
            with patch('memory_selector.logger') as mock_logger:
                selector = MemorySelector(config_path=temp_file, validate_config=False)
                
                # Should not log validation warnings when disabled
                warning_calls = [call for call in mock_logger.warning.call_args_list 
                               if 'not configured' in str(call)]
                self.assertEqual(len(warning_calls), 0)
                
        finally:
            os.unlink(temp_file)
    
    def test_client_getters(self):
        """Test client getter methods"""
        # Disable neo4j and basic memory to test None return
        with patch.dict(os.environ, {
            'BASIC_MEMORY_ENABLED': 'false',
            'NEO4J_ENABLED': 'false'
        }, clear=False):
            selector = MemorySelector(validate_config=False)
            
            # Test that _get_redis_client returns None when REDIS_URL not configured
            redis_client = selector._get_redis_client()
            self.assertIsNone(redis_client)
            
            # Test that _get_basic_memory_client returns None when disabled
            basic_client = selector._get_basic_memory_client()
            self.assertIsNone(basic_client)
            
            # Test that _get_neo4j_client returns None when disabled
            neo4j_client = selector._get_neo4j_client()
            self.assertIsNone(neo4j_client)
    
    def test_config_error_logging_to_cab(self):
        """Test that configuration errors are logged to CAB tracker"""
        mock_tracker = MagicMock()
        
        # Test with invalid config file
        with patch('memory_selector.logger'):
            selector = MemorySelector(
                cab_tracker=mock_tracker, 
                config_path='/invalid/path.env'
            )
            
            # CAB tracker should be called for configuration warnings
            # With no valid config path, validation should trigger warnings
            # which should be logged to CAB tracker
            self.assertTrue(mock_tracker.log_suggestion.called, "Expected log_suggestion to be called for configuration warnings")
    
    def test_validation_warnings_to_cab(self):
        """Test that validation warnings are logged to CAB tracker"""
        mock_tracker = MagicMock()
        
        # Create config with missing Redis
        incomplete_config = {k: v for k, v in self.test_config.items() 
                           if not k.startswith('redis')}
        temp_file = self.create_temp_config_file(incomplete_config)
        
        try:
            selector = MemorySelector(
                cab_tracker=mock_tracker,
                config_path=temp_file
            )
            
            # Should have called log_suggestion for missing Redis config
            mock_tracker.log_suggestion.assert_called()
            
            # Verify that the call was made with appropriate parameters
            calls = mock_tracker.log_suggestion.call_args_list
            config_warning_calls = [call for call in calls 
                                  if len(call[0]) > 0 and 'Configuration Warning' in call[0][0]]
            self.assertTrue(len(config_warning_calls) > 0)
            
        finally:
            os.unlink(temp_file)


if __name__ == '__main__':
    unittest.main()
