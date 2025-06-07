#!/usr/bin/env python3
"""
Simple test script to validate configuration management implementation
"""
import sys
import os
import tempfile
sys.path.append('src')

from memory_selector import MemorySelector
from cab_tracker import get_cab_tracker

def test_config_loading():
    """Test configuration loading from .env file"""
    print("Testing configuration loading...")
    
    # Create a temporary .env file for testing
    env_content = """
# Test configuration
REDIS_URL=redis://test:6379
REDIS_PASSWORD=test_password
NEO4J_URL=bolt://test:7687
NEO4J_USERNAME=test_user
NEO4J_PASSWORD=test_password
BASIC_MEMORY_PATH=/tmp/test_memory
CAB_MONITORING_ENABLED=true
"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
        f.write(env_content)
        temp_env_path = f.name
    
    try:
        # Initialize CAB tracker
        cab_tracker = get_cab_tracker()
        cab_tracker.initialize_session(user="test_user", primary_ai="test")
        
        # Test configuration loading
        selector = MemorySelector(cab_tracker=cab_tracker, config_path=temp_env_path)
        
        # Verify configuration was loaded correctly
        assert selector.config['redis']['url'] == 'redis://test:6379'
        assert selector.config['redis']['password'] == 'test_password'
        assert selector.config['neo4j']['url'] == 'bolt://test:7687'
        assert selector.config['neo4j']['username'] == 'test_user'
        assert selector.config['neo4j']['password'] == 'test_password'
        assert selector.config['basic_memory']['path'] == '/tmp/test_memory'
        
        print("✓ Configuration loading test passed")
        
        # Test client initialization (should create placeholder clients)
        redis_client = selector._get_redis_client()
        basic_client = selector._get_basic_memory_client()
        neo4j_client = selector._get_neo4j_client()
        
        assert redis_client is not None
        assert basic_client is not None
        assert neo4j_client is not None
        
        print("✓ Client initialization test passed")
        
        # Test existing functionality still works
        task = "Find user relationships"
        system, task_type = selector.select_memory_system(task)
        assert system is not None
        assert task_type is not None
        
        print("✓ Memory system selection test passed")
        
    finally:
        # Clean up
        os.unlink(temp_env_path)

def test_missing_config():
    """Test handling of missing configuration"""
    print("Testing missing configuration handling...")
    
    # Clear any existing environment variables that might interfere
    env_backup = {}
    env_vars_to_clear = ['REDIS_URL', 'REDIS_PASSWORD', 'NEO4J_URL', 'NEO4J_USERNAME', 'NEO4J_PASSWORD', 'BASIC_MEMORY_PATH']
    for var in env_vars_to_clear:
        if var in os.environ:
            env_backup[var] = os.environ[var]
            del os.environ[var]
    
    try:
        # Create a temporary .env file with missing essential config
        env_content = """REDIS_URL=redis://test:6379
NEO4J_URL=bolt://test:7687
NEO4J_USERNAME=test_user"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
            f.write(env_content)
            temp_env_path = f.name
        
        try:
            cab_tracker = get_cab_tracker()
            cab_tracker.initialize_session(user="test_user", primary_ai="test")
            
            # This should raise a ValueError due to missing NEO4J_PASSWORD
            try:
                selector = MemorySelector(cab_tracker=cab_tracker, config_path=temp_env_path)
                # If we get here, the test failed
                print("ERROR: Expected ValueError but none was raised")
                print("Config loaded:", selector.config)
                raise AssertionError("Expected ValueError for missing configuration")
            except ValueError as e:
                if "NEO4J_PASSWORD" in str(e):
                    print("✓ Missing configuration validation test passed")
                else:
                    raise AssertionError(f"Wrong error message: {e}")
                
        finally:
            # Clean up temp file
            os.unlink(temp_env_path)
            
    finally:
        # Restore environment variables
        for var, value in env_backup.items():
            os.environ[var] = value

def test_no_env_file():
    """Test behavior when no .env file is present"""
    print("Testing behavior with no .env file...")
    
    # Set some environment variables manually
    os.environ['REDIS_URL'] = 'redis://env:6379'
    os.environ['NEO4J_URL'] = 'bolt://env:7687'
    os.environ['NEO4J_PASSWORD'] = 'env_password'
    
    try:
        cab_tracker = get_cab_tracker()
        cab_tracker.initialize_session(user="test_user", primary_ai="test")
        
        # Should work with environment variables
        selector = MemorySelector(cab_tracker=cab_tracker)
        
        # Verify configuration from environment
        assert selector.config['redis']['url'] == 'redis://env:6379'
        assert selector.config['neo4j']['url'] == 'bolt://env:7687'
        assert selector.config['neo4j']['password'] == 'env_password'
        
        print("✓ Environment variable configuration test passed")
        
    finally:
        # Clean up environment variables
        del os.environ['REDIS_URL']
        del os.environ['NEO4J_URL']
        del os.environ['NEO4J_PASSWORD']

if __name__ == "__main__":
    print("Running configuration management tests...")
    print("=" * 50)
    
    try:
        test_config_loading()
        test_missing_config()
        test_no_env_file()
        
        print("=" * 50)
        print("All tests passed! ✓")
        
    except Exception as e:
        print(f"Test failed: {e}")
        sys.exit(1)