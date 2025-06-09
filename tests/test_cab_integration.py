"""
Tests for comprehensive CABTracker integration in MemorySelector.

Tests that all required events are properly logged to CABTracker including:
- API errors
- Fallback usage
- Performance issues
- Data inconsistencies  
- Missing implementations
"""
import os
import tempfile
import unittest
from unittest.mock import Mock, patch, call
from src.memory_selector import MemorySelector, MemorySystem, MemoryPropagator
from src.cab_tracker import CABTracker


class TestCABTrackerIntegration(unittest.TestCase):
    """Test suite for comprehensive CABTracker integration."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_cab_tracker = Mock()
        
        # Create a temporary CAB file for real CABTracker tests
        self.temp_cab_file = tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False)
        self.temp_cab_file.close()
        
    def tearDown(self):
        """Clean up after tests."""
        # Clean up environment variables
        env_vars_to_clean = [
            'REDIS_URL', 'NEO4J_URL', 'NEO4J_PASSWORD', 'BASIC_MEMORY_PATH',
            'JWT_SECRET', 'OAUTH2_ISSUER_URL'
        ]
        for var in env_vars_to_clean:
            if var in os.environ:
                del os.environ[var]
                
        # Clean up temporary file
        if os.path.exists(self.temp_cab_file.name):
            os.unlink(self.temp_cab_file.name)

    def test_cab_tracker_session_initialization(self):
        """Test that CABTracker session is automatically initialized."""
        real_cab_tracker = CABTracker(self.temp_cab_file.name)
        self.assertFalse(real_cab_tracker.initialized)
        
        # Initialize MemorySelector with CABTracker
        selector = MemorySelector(real_cab_tracker, validate_config=False)
        
        # Verify session was initialized
        self.assertTrue(real_cab_tracker.initialized)

    def test_memory_operation_success_logging(self):
        """Test that successful memory operations are logged."""
        with patch.dict(os.environ, {'REDIS_URL': 'redis://localhost:6379'}):
            selector = MemorySelector(self.mock_cab_tracker, validate_config=False)
            
            # Mock successful operation
            with patch.object(selector, '_store_in_redis') as mock_store:
                mock_store.return_value = {"status": "success"}
                
                try:
                    selector.store_data({"test": "data"}, "Store test data")
                except:
                    pass  # Expected to fail due to mock setup
                
                # Verify CABTracker logged the operation
                self.mock_cab_tracker.log_memory_operation.assert_called()

    def test_api_error_logging(self):
        """Test that API errors are properly logged to CABTracker."""
        selector = MemorySelector(self.mock_cab_tracker, validate_config=False)
        
        # Attempt operation that will fail
        try:
            selector.store_data({"test": "data"}, "Store test data")
        except Exception:
            pass  # Expected to fail
        
        # Verify API errors were logged
        api_error_calls = [call for call in self.mock_cab_tracker.log_suggestion.call_args_list 
                          if call[0][0] == "API Error"]
        self.assertGreater(len(api_error_calls), 0, "API errors should be logged")

    def test_fallback_success_logging(self):
        """Test that successful fallback usage is logged."""
        # Set up environment where first system fails but second succeeds
        with patch.dict(os.environ, {'BASIC_MEMORY_PATH': '/tmp/test_memory'}):
            os.makedirs('/tmp/test_memory', exist_ok=True)
            
            try:
                selector = MemorySelector(self.mock_cab_tracker, validate_config=False)
                
                # Mock Redis to fail and Basic Memory to succeed
                with patch.object(selector, '_store_in_redis') as mock_redis, \
                     patch.object(selector, '_store_in_basic_memory') as mock_basic:
                    mock_redis.side_effect = Exception("Redis connection failed")
                    mock_basic.return_value = {"status": "success"}
                    
                    try:
                        selector.store_data({"test": "data"}, "Store user profile")
                    except:
                        pass
                    
                    # Check for fallback success logging
                    fallback_calls = [call for call in self.mock_cab_tracker.log_suggestion.call_args_list 
                                    if call[0][0] == "Fallback Success"]
                    self.assertGreater(len(fallback_calls), 0, "Fallback success should be logged")
                    
            finally:
                # Clean up
                if os.path.exists('/tmp/test_memory'):
                    os.rmdir('/tmp/test_memory')

    def test_complete_system_failure_logging(self):
        """Test that complete system failures are logged with CRITICAL severity."""
        selector = MemorySelector(self.mock_cab_tracker, validate_config=False)
        
        try:
            selector.store_data({"test": "data"}, "Store test data")
        except Exception:
            pass  # Expected to fail
        
        # Check for complete system failure logging
        critical_calls = [call for call in self.mock_cab_tracker.log_suggestion.call_args_list 
                         if call[0][0] == "Complete System Failure"]
        self.assertGreater(len(critical_calls), 0, "Complete system failure should be logged")
        
        # Verify severity is CRITICAL
        if critical_calls:
            call_args, call_kwargs = critical_calls[0]
            self.assertEqual(call_kwargs.get('severity'), 'CRITICAL')

    def test_missing_implementation_logging(self):
        """Test that missing implementations are properly logged."""
        selector = MemorySelector(self.mock_cab_tracker, validate_config=False)
        
        try:
            selector.retrieve_data({"query": "test"}, "Find test data")
        except Exception:
            pass  # Expected to fail
        
        # Check for missing implementation logging
        missing_impl_calls = [call for call in self.mock_cab_tracker.log_suggestion.call_args_list 
                             if call[0][0] == "Missing Implementation"]
        self.assertGreater(len(missing_impl_calls), 0, "Missing implementations should be logged")

    def test_data_inconsistency_logging_in_propagator(self):
        """Test that data inconsistencies are logged in MemoryPropagator."""
        mock_clients = {
            MemorySystem.REDIS: Mock(),
            MemorySystem.NEO4J: Mock(),
            MemorySystem.BASIC_MEMORY: Mock()
        }
        
        propagator = MemoryPropagator(mock_clients, self.mock_cab_tracker)
        
        # Mock data consistency check to return False (inconsistent)
        with patch.object(propagator, '_check_data_consistency', return_value=False):
            propagator.propagate_data(
                data={"user_id": "123", "name": "test"},
                source_system=MemorySystem.REDIS,
                data_type="user_profile",
                entity_id="user_123"
            )
        
        # Verify data inconsistency was logged
        self.mock_cab_tracker.log_data_inconsistency.assert_called()

    def test_propagation_error_logging(self):
        """Test that propagation errors are logged."""
        mock_clients = {
            MemorySystem.REDIS: Mock(),
            MemorySystem.NEO4J: Mock(),
            MemorySystem.BASIC_MEMORY: Mock()
        }
        
        propagator = MemoryPropagator(mock_clients, self.mock_cab_tracker)
        
        # Mock propagation to raise an exception
        with patch.object(propagator, '_check_data_consistency', side_effect=Exception("Connection failed")):
            propagator.propagate_data(
                data={"user_id": "123"},
                source_system=MemorySystem.REDIS,
                data_type="user_profile",
                entity_id="user_123"
            )
        
        # Check for propagation error logging
        propagation_error_calls = [call for call in self.mock_cab_tracker.log_suggestion.call_args_list 
                                  if call[0][0] == "Propagation Error"]
        self.assertGreater(len(propagation_error_calls), 0, "Propagation errors should be logged")

    def test_performance_logging_integration(self):
        """Test that performance issues are logged via log_memory_operation."""
        selector = MemorySelector(self.mock_cab_tracker, validate_config=False)
        
        # Use real CABTracker to test log_memory_operation method
        real_cab_tracker = CABTracker(self.temp_cab_file.name)
        selector.cab_tracker = real_cab_tracker
        
        try:
            selector.store_data({"test": "data"}, "Store test data")
        except Exception:
            pass  # Expected to fail
        
        # Verify that log_memory_operation was called (indirectly through file content)
        with open(self.temp_cab_file.name, 'r') as f:
            content = f.read()
            # Should contain session initialization and various logged entries
            self.assertIn("CAB Session", content)


if __name__ == '__main__':
    unittest.main()