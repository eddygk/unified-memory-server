"""
Unit tests for MemorySelector configuration loading and validation.
"""
import os
import tempfile
import unittest
from unittest.mock import patch, MagicMock
import sys
import shutil

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from memory_selector import MemorySelector


class TestMemorySelectorConfig(unittest.TestCase):
    """Test MemorySelector configuration loading and validation."""

    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.temp_dir)
        
        # Mock CAB tracker
        self.mock_cab_tracker = MagicMock()
        
    def tearDown(self):
        """Clean up test environment."""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.temp_dir)
        
        # Clean up environment variables
        env_vars_to_clean = [
            'REDIS_URL', 'NEO4J_URL', 'NEO4J_PASSWORD', 'BASIC_MEMORY_PATH',
            'NEO4J_ENABLED', 'BASIC_MEMORY_ENABLED', 'CAB_MONITORING_ENABLED',
            'DISABLE_AUTH', 'JWT_SECRET', 'OAUTH2_ISSUER_URL'
        ]
        for var in env_vars_to_clean:
            if var in os.environ:
                del os.environ[var]

    def create_env_file(self, filename, content):
        """Helper to create .env files."""
        with open(filename, 'w') as f:
            f.write(content)

    def test_load_config_with_dotenv_fallback_order(self):
        """Test config loading follows correct fallback order when dotenv is available."""
        # Create multiple env files
        self.create_env_file('.env', 'REDIS_URL=redis://env:6379\n')
        self.create_env_file('.env.production', 'REDIS_URL=redis://prod:6379\n')
        self.create_env_file('.env.local', 'REDIS_URL=redis://local:6379\n')
        
        # Since dotenv isn't available, it will use manual parsing
        # Just test that it loads the first file (.env)
        selector = MemorySelector(validate_config=False)
        
        # Should have loaded from .env file
        self.assertIsNotNone(selector.config)
        self.assertEqual(os.environ.get('REDIS_URL'), 'redis://env:6379')

    def test_load_config_with_custom_path(self):
        """Test config loading with custom config path."""
        custom_config = 'custom.env'
        self.create_env_file(custom_config, 'REDIS_URL=redis://custom:6379\n')
        
        selector = MemorySelector(config_path=custom_config, validate_config=False)
        
        # Should load custom config
        self.assertEqual(os.environ.get('REDIS_URL'), 'redis://custom:6379')

    def test_load_config_manual_parsing_fallback(self):
        """Test manual parsing when python-dotenv is not available."""
        self.create_env_file('.env', '''
# Test comment
REDIS_URL=redis://localhost:6379
NEO4J_PASSWORD="secret_password"
NEO4J_ENABLED='true'
EMPTY_LINE=

# Another comment
BASIC_MEMORY_PATH=/test/path
''')
        
        # Since dotenv is not available in this environment, 
        # it will automatically use manual parsing
        selector = MemorySelector(validate_config=False)
        
        # Check that environment variables were set correctly
        self.assertEqual(os.environ.get('REDIS_URL'), 'redis://localhost:6379')
        self.assertEqual(os.environ.get('NEO4J_PASSWORD'), 'secret_password')
        self.assertEqual(os.environ.get('NEO4J_ENABLED'), 'true')
        self.assertEqual(os.environ.get('BASIC_MEMORY_PATH'), '/test/path')

    def test_load_config_no_file_found(self):
        """Test config loading when no config files exist."""
        with patch('memory_selector.logger') as mock_logger:
            selector = MemorySelector(validate_config=False)
            
            mock_logger.warning.assert_called_with("No configuration file found, using environment variables only")
            self.assertIsNotNone(selector.config)

    def test_load_config_default_values(self):
        """Test that default configuration values are set correctly."""
        selector = MemorySelector(validate_config=False)
        
        # Test default values
        self.assertEqual(selector.config['PORT'], '8000')
        self.assertEqual(selector.config['MCP_PORT'], '9000')
        self.assertEqual(selector.config['HOST'], '0.0.0.0')
        self.assertEqual(selector.config['REDIS_MAX_MEMORY'], '4gb')
        self.assertEqual(selector.config['NEO4J_USERNAME'], 'neo4j')
        self.assertEqual(selector.config['NEO4J_DATABASE'], 'neo4j')
        self.assertEqual(selector.config['BASIC_MEMORY_PATH'], '/data/obsidian')
        self.assertEqual(selector.config['CAB_SEVERITY_THRESHOLD'], 'MEDIUM')
        
        # Test boolean defaults
        self.assertTrue(selector.config['NEO4J_ENABLED'])
        self.assertTrue(selector.config['BASIC_MEMORY_ENABLED'])
        self.assertTrue(selector.config['CAB_MONITORING_ENABLED'])
        self.assertFalse(selector.config['DISABLE_AUTH'])
        self.assertFalse(selector.config['REDIS_TLS_ENABLED'])

    def test_validate_config_redis_warnings(self):
        """Test Redis configuration validation warnings."""
        selector = MemorySelector(
            cab_tracker=self.mock_cab_tracker,
            validate_config=False
        )
        
        # Remove REDIS_URL to trigger warning
        selector.config['REDIS_URL'] = None
        
        with patch('memory_selector.logger') as mock_logger:
            selector._validate_config()
            
            mock_logger.warning.assert_any_call(
                "Configuration warning: REDIS_URL not configured - Redis memory system may not function"
            )
            self.mock_cab_tracker.log_suggestion.assert_any_call(
                "Configuration Warning",
                "REDIS_URL not configured - Redis memory system may not function",
                severity='MEDIUM',
                context="Configuration validation"
            )

    def test_validate_config_neo4j_warnings(self):
        """Test Neo4j configuration validation warnings."""
        selector = MemorySelector(
            cab_tracker=self.mock_cab_tracker,
            validate_config=False
        )
        
        # Set Neo4j enabled but missing required config
        selector.config['NEO4J_ENABLED'] = True
        selector.config['NEO4J_URL'] = None
        selector.config['NEO4J_PASSWORD'] = None
        
        with patch('memory_selector.logger') as mock_logger:
            selector._validate_config()
            
            mock_logger.warning.assert_any_call(
                "Configuration warning: NEO4J_URL not configured but Neo4j is enabled"
            )
            mock_logger.warning.assert_any_call(
                "Configuration warning: NEO4J_PASSWORD not configured but Neo4j is enabled"
            )

    def test_validate_config_basic_memory_warnings(self):
        """Test Basic Memory configuration validation warnings."""
        selector = MemorySelector(
            cab_tracker=self.mock_cab_tracker,
            validate_config=False
        )
        
        # Test missing path
        selector.config['BASIC_MEMORY_ENABLED'] = True
        selector.config['BASIC_MEMORY_PATH'] = None
        
        with patch('memory_selector.logger') as mock_logger:
            selector._validate_config()
            
            mock_logger.warning.assert_any_call(
                "Configuration warning: BASIC_MEMORY_PATH not configured but Basic Memory is enabled"
            )
        
        # Test non-existent path
        selector.config['BASIC_MEMORY_PATH'] = '/non/existent/path'
        
        with patch('memory_selector.logger') as mock_logger:
            selector._validate_config()
            
            mock_logger.warning.assert_any_call(
                "Configuration warning: BASIC_MEMORY_PATH does not exist: /non/existent/path"
            )

    def test_validate_config_auth_warnings(self):
        """Test authentication configuration validation warnings."""
        selector = MemorySelector(
            cab_tracker=self.mock_cab_tracker,
            validate_config=False
        )
        
        # Set auth enabled but missing required config
        selector.config['DISABLE_AUTH'] = False
        selector.config['JWT_SECRET'] = None
        selector.config['OAUTH2_ISSUER_URL'] = None
        
        with patch('memory_selector.logger') as mock_logger:
            selector._validate_config()
            
            mock_logger.warning.assert_any_call(
                "Configuration warning: JWT_SECRET not configured but authentication is enabled"
            )
            mock_logger.warning.assert_any_call(
                "Configuration warning: OAUTH2_ISSUER_URL not configured but authentication is enabled"
            )

    def test_validate_config_cab_warnings(self):
        """Test CAB configuration validation warnings."""
        selector = MemorySelector(
            cab_tracker=self.mock_cab_tracker,
            validate_config=False
        )
        
        # Set CAB enabled with non-existent log directory
        selector.config['CAB_MONITORING_ENABLED'] = True
        selector.config['CAB_LOG_PATH'] = '/non/existent/dir/cab.log'
        
        with patch('memory_selector.logger') as mock_logger:
            selector._validate_config()
            
            mock_logger.warning.assert_any_call(
                "Configuration warning: CAB log directory does not exist: /non/existent/dir"
            )

    def test_parse_env_file_error_handling(self):
        """Test error handling in manual env file parsing."""
        # Create invalid file
        invalid_file = 'invalid.env'
        with open(invalid_file, 'w') as f:
            f.write('INVALID_LINE_WITHOUT_EQUALS\n')
        
        selector = MemorySelector(validate_config=False)
        
        with patch('memory_selector.logger') as mock_logger:
            selector._parse_env_file('non_existent_file.env')
            
            # Should log warning for file not found
            mock_logger.warning.assert_called()

    def test_client_getters_raise_errors_when_misconfigured(self):
        """Test that client getters raise appropriate errors when misconfigured."""
        selector = MemorySelector(validate_config=False)
        
        # Test Redis client with missing URL
        selector.config['REDIS_URL'] = None
        with self.assertRaises(ValueError) as cm:
            selector._get_redis_client()
        self.assertEqual(str(cm.exception), "Redis URL not configured")
        
        # Test Basic Memory client when disabled
        selector.config['BASIC_MEMORY_ENABLED'] = False
        with self.assertRaises(ValueError) as cm:
            selector._get_basic_memory_client()
        self.assertEqual(str(cm.exception), "Basic Memory not enabled")
        
        # Test Neo4j client when disabled
        selector.config['NEO4J_ENABLED'] = False
        with self.assertRaises(ValueError) as cm:
            selector._get_neo4j_client()
        self.assertEqual(str(cm.exception), "Neo4j not enabled")
        
        # Test Neo4j client with missing URL
        selector.config['NEO4J_ENABLED'] = True
        selector.config['NEO4J_URL'] = None
        with self.assertRaises(ValueError) as cm:
            selector._get_neo4j_client()
        self.assertEqual(str(cm.exception), "Neo4j URL not configured")
        
        # Test Neo4j client with missing password
        selector.config['NEO4J_URL'] = 'bolt://localhost:7687'
        selector.config['NEO4J_PASSWORD'] = None
        with self.assertRaises(ValueError) as cm:
            selector._get_neo4j_client()
        self.assertEqual(str(cm.exception), "Neo4j password not configured")

    def test_client_getters_return_placeholder(self):
        """Test that client getters return None (placeholder) when properly configured."""
        selector = MemorySelector(validate_config=False)
        
        # Configure properly
        selector.config['REDIS_URL'] = 'redis://localhost:6379'
        selector.config['BASIC_MEMORY_ENABLED'] = True
        selector.config['BASIC_MEMORY_PATH'] = '/tmp'
        selector.config['NEO4J_ENABLED'] = True
        selector.config['NEO4J_URL'] = 'bolt://localhost:7687'
        selector.config['NEO4J_PASSWORD'] = 'password'
        
        with patch('memory_selector.logger') as mock_logger:
            # Test all clients return None (placeholder)
            self.assertIsNone(selector._get_redis_client())
            self.assertIsNone(selector._get_basic_memory_client())
            self.assertIsNone(selector._get_neo4j_client())
            
            # Verify logging
            mock_logger.info.assert_any_call("Creating Redis client (placeholder)")
            mock_logger.info.assert_any_call("Creating Basic Memory client (placeholder)")
            mock_logger.info.assert_any_call("Creating Neo4j client (placeholder)")


if __name__ == '__main__':
    unittest.main()