"""
Test data propagation functionality in MemorySelector.

Tests the new propagate_data and _propagate_to_X methods added to MemorySelector
as per issue requirements and Section 3.4 of the implementation plan.
"""
import os
import tempfile
import unittest
from unittest.mock import Mock, patch, call
from src.memory_selector import MemorySelector, MemorySystem
from src.cab_tracker import CABTracker


class TestMemorySelectorPropagation(unittest.TestCase):
    """Test suite for MemorySelector data propagation functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_cab_tracker = Mock()
        
        # Create minimal config to avoid validation errors
        self.test_config = {
            'REDIS_URL': 'redis://localhost:6379',
            'NEO4J_ENABLED': 'true',
            'NEO4J_MCP_MEMORY_URL': 'http://neo4j:8001',
            'NEO4J_MCP_CYPHER_URL': 'http://neo4j:8002',
            'BASIC_MEMORY_ENABLED': 'true',
            'BASIC_MEMORY_URL': 'http://basic-memory:8080'
        }
        
    def tearDown(self):
        """Clean up after tests."""
        # Clean up environment variables
        env_vars_to_clean = [
            'REDIS_URL', 'NEO4J_URL', 'NEO4J_PASSWORD', 'BASIC_MEMORY_URL',
            'NEO4J_ENABLED', 'BASIC_MEMORY_ENABLED'
        ]
        for var in env_vars_to_clean:
            if var in os.environ:
                del os.environ[var]

    def test_propagate_data_user_profile(self):
        """Test propagation of user profile data to multiple systems."""
        with patch.dict(os.environ, self.test_config):
            selector = MemorySelector(self.mock_cab_tracker, validate_config=False)
            
            # Mock the individual _store_in_X methods to avoid actual network calls
            with patch.object(selector, '_store_in_redis') as mock_redis, \
                 patch.object(selector, '_store_in_neo4j') as mock_neo4j, \
                 patch.object(selector, '_store_in_basic_memory') as mock_basic:
                
                mock_redis.return_value = {"status": "stored", "system": "redis"}
                mock_neo4j.return_value = {"status": "stored", "system": "neo4j"}
                mock_basic.return_value = {"status": "stored", "system": "basic_memory"}
                
                user_data = {
                    "user_id": "user_123",
                    "name": "John Doe",
                    "email": "john@example.com",
                    "preferences": {"theme": "dark"}
                }
                
                result = selector.propagate_data(
                    data=user_data,
                    source_system=MemorySystem.REDIS,
                    data_type="user_profile",
                    entity_id="user_123"
                )
                
                # Verify propagation to Neo4j and Basic Memory (excluding source Redis)
                self.assertIn("neo4j", result)
                self.assertIn("basic_memory", result)
                self.assertNotIn("redis", result)  # Source system should be excluded
                
                # Verify successful status
                self.assertEqual(result["neo4j"]["status"], "success")
                self.assertEqual(result["basic_memory"]["status"], "success")
                
                # Verify _store_in_X methods were called with enhanced data
                mock_neo4j.assert_called_once()
                mock_basic.assert_called_once()
                mock_redis.assert_not_called()  # Source system excluded

    def test_propagate_data_relationship(self):
        """Test propagation of relationship data primarily to Neo4j."""
        with patch.dict(os.environ, self.test_config):
            selector = MemorySelector(self.mock_cab_tracker, validate_config=False)
            
            with patch.object(selector, '_store_in_redis') as mock_redis, \
                 patch.object(selector, '_store_in_neo4j') as mock_neo4j:
                
                mock_redis.return_value = {"status": "stored", "system": "redis"}
                mock_neo4j.return_value = {"status": "stored", "system": "neo4j"}
                
                relationship_data = {
                    "source": "user_123",
                    "target": "project_456",
                    "relation_type": "WORKS_ON",
                    "properties": {"role": "developer", "since": "2024-01-01"}
                }
                
                result = selector.propagate_data(
                    data=relationship_data,
                    source_system=MemorySystem.NEO4J,
                    data_type="relationship",
                    entity_id="rel_123"
                )
                
                # For relationship data from Neo4j, should propagate to Redis
                self.assertIn("redis", result)
                self.assertEqual(result["redis"]["status"], "success")
                
                # Verify Redis was called
                mock_redis.assert_called_once()
                mock_neo4j.assert_not_called()  # Source system excluded

    def test_propagate_data_conversation_context(self):
        """Test propagation of conversation context (Redis only)."""
        with patch.dict(os.environ, self.test_config):
            selector = MemorySelector(self.mock_cab_tracker, validate_config=False)
            
            conversation_data = {
                "session_id": "session_123",
                "messages": ["Hello", "How are you?"],
                "context": {"user_id": "user_123"}
            }
            
            result = selector.propagate_data(
                data=conversation_data,
                source_system=MemorySystem.BASIC_MEMORY,
                data_type="conversation_context",
                entity_id="session_123"
            )
            
            # Conversation context should only go to Redis
            self.assertIn("redis", result)
            self.assertEqual(len(result), 1)  # Only one target system

    def test_propagate_data_with_system_failure(self):
        """Test propagation handling when one system fails."""
        with patch.dict(os.environ, self.test_config):
            selector = MemorySelector(self.mock_cab_tracker, validate_config=False)
            
            with patch.object(selector, '_store_in_redis') as mock_redis, \
                 patch.object(selector, '_store_in_neo4j') as mock_neo4j:
                
                mock_redis.return_value = {"status": "stored", "system": "redis"}
                mock_neo4j.side_effect = Exception("Neo4j connection failed")
                
                user_data = {
                    "user_id": "user_123",
                    "name": "John Doe"
                }
                
                result = selector.propagate_data(
                    data=user_data,
                    source_system=MemorySystem.BASIC_MEMORY,
                    data_type="user_profile",
                    entity_id="user_123"
                )
                
                # Verify partial success
                self.assertEqual(result["redis"]["status"], "success")
                self.assertEqual(result["neo4j"]["status"], "error")
                self.assertIn("Neo4j connection failed", result["neo4j"]["error"])
                
                # Verify error was logged to CAB tracker
                error_calls = [call for call in self.mock_cab_tracker.log_suggestion.call_args_list 
                              if call[0][0] == "Propagation Error"]
                self.assertGreater(len(error_calls), 0)

    def test_propagate_to_redis_metadata_enhancement(self):
        """Test that _propagate_to_redis enhances data with metadata."""
        with patch.dict(os.environ, self.test_config):
            selector = MemorySelector(self.mock_cab_tracker, validate_config=False)
            
            with patch.object(selector, '_store_in_redis') as mock_store:
                mock_store.return_value = {"status": "stored"}
                
                test_data = {"key": "value"}
                
                selector._propagate_to_redis(
                    data=test_data,
                    data_type="user_profile",
                    entity_id="user_123",
                    task="test_task",
                    context=None
                )
                
                # Verify enhanced data was passed to _store_in_redis
                call_args = mock_store.call_args[0][0]  # First argument (data)
                self.assertIn("_propagation_metadata", call_args)
                self.assertEqual(call_args["_propagation_metadata"]["entity_id"], "user_123")
                self.assertEqual(call_args["_propagation_metadata"]["data_type"], "user_profile")

    def test_propagate_to_neo4j_relationship_structure(self):
        """Test that _propagate_to_neo4j properly structures relationship data."""
        with patch.dict(os.environ, self.test_config):
            selector = MemorySelector(self.mock_cab_tracker, validate_config=False)
            
            with patch.object(selector, '_store_in_neo4j') as mock_store:
                mock_store.return_value = {"status": "stored"}
                
                relationship_data = {
                    "source": "user_123",
                    "target": "project_456",
                    "relation_type": "WORKS_ON",
                    "properties": {"role": "developer"}
                }
                
                selector._propagate_to_neo4j(
                    data=relationship_data,
                    data_type="relationship",
                    entity_id="rel_123",
                    task="test_task",
                    context=None
                )
                
                # Verify relationship structure was created
                call_args = mock_store.call_args[0][0]  # First argument (data)
                self.assertIn("relations", call_args)
                self.assertEqual(len(call_args["relations"]), 1)
                self.assertEqual(call_args["relations"][0]["source"], "user_123")
                self.assertEqual(call_args["relations"][0]["target"], "project_456")
                
                # Verify propagation metadata fields are correctly populated
                self.assertIn("_propagation_metadata", call_args)
                metadata = call_args["_propagation_metadata"]
                self._assert_propagation_metadata(
                    metadata,
                    expected_entity_id="rel_123",
                    expected_data_type="relationship",
                    expected_task="test_task"
                )

    def test_propagate_to_basic_memory_content_formatting(self):
        """Test that _propagate_to_basic_memory properly formats content."""
        with patch.dict(os.environ, self.test_config):
            selector = MemorySelector(self.mock_cab_tracker, validate_config=False)
            
            with patch.object(selector, '_store_in_basic_memory') as mock_store:
                mock_store.return_value = {"status": "stored"}
                
                test_data = {"key": "value", "description": "test data"}
                
                selector._propagate_to_basic_memory(
                    data=test_data,
                    data_type="documentation",
                    entity_id="doc_123",
                    task="test_task",
                    context=None
                )
                
                # Verify content and title were added
                call_args = mock_store.call_args[0][0]  # First argument (data)
                self.assertIn("content", call_args)
                self.assertIn("title", call_args)
                self.assertIn("Documentation - doc_123", call_args["title"])
                
                # Verify propagation metadata fields are correctly populated
                self.assertIn("_propagation_metadata", call_args)
                self._assert_propagation_metadata(
                    call_args["_propagation_metadata"],
                    expected_entity_id="doc_123",
                    expected_data_type="documentation",
                    expected_task="test_task",
                    expected_propagated_at=None
                )

    def test_get_propagation_targets_filtering(self):
        """Test that _get_propagation_targets properly filters based on system availability."""
        # Test with limited system availability
        limited_config = {
            'REDIS_URL': 'redis://localhost:6379',
            'NEO4J_ENABLED': 'false',  # Neo4j disabled
            'BASIC_MEMORY_ENABLED': 'true',
            'BASIC_MEMORY_URL': 'http://basic-memory:8080'
        }
        
        with patch.dict(os.environ, limited_config):
            selector = MemorySelector(self.mock_cab_tracker, validate_config=False)
            
            targets = selector._get_propagation_targets(MemorySystem.REDIS, "user_profile")
            
            # Should only include Basic Memory (Neo4j disabled, Redis is source)
            self.assertIn(MemorySystem.BASIC_MEMORY, targets)
            self.assertNotIn(MemorySystem.NEO4J, targets)
            self.assertNotIn(MemorySystem.REDIS, targets)  # Source system excluded

    def test_enrich_with_propagation_metadata_basic_functionality(self):
        """Test that _enrich_with_propagation_metadata correctly merges data and adds metadata."""
        with patch.dict(os.environ, self.test_config):
            selector = MemorySelector(self.mock_cab_tracker, validate_config=False)
            
            # Test basic functionality with typical data
            input_data = {
                "user_id": "user_123",
                "name": "John Doe",
                "email": "john@example.com"
            }
            
            result = selector._enrich_with_propagation_metadata(
                data=input_data,
                data_type="user_profile",
                entity_id="user_123",
                task="test_task"
            )
            
            # Verify original data is preserved
            self.assertEqual(result["user_id"], "user_123")
            self.assertEqual(result["name"], "John Doe")
            self.assertEqual(result["email"], "john@example.com")
            
            # Verify metadata is added
            self.assertIn("_propagation_metadata", result)
            metadata = result["_propagation_metadata"]
            self.assertEqual(metadata["entity_id"], "user_123")
            self.assertEqual(metadata["data_type"], "user_profile")
            self.assertEqual(metadata["propagation_task"], "test_task")
            self.assertIsNone(metadata["propagated_at"])  # No timestamp in input data

    def test_enrich_with_propagation_metadata_with_timestamp(self):
        """Test that _enrich_with_propagation_metadata preserves existing timestamp."""
        with patch.dict(os.environ, self.test_config):
            selector = MemorySelector(self.mock_cab_tracker, validate_config=False)
            
            # Test with data that contains a timestamp
            input_data = {
                "user_id": "user_456",
                "timestamp": "2024-01-15T10:30:00Z",
                "activity": "login"
            }
            
            result = selector._enrich_with_propagation_metadata(
                data=input_data,
                data_type="activity_log",
                entity_id="activity_789",
                task="activity_tracking"
            )
            
            # Verify timestamp is preserved in metadata
            self.assertEqual(result["_propagation_metadata"]["propagated_at"], "2024-01-15T10:30:00Z")
            self.assertEqual(result["_propagation_metadata"]["entity_id"], "activity_789")
            self.assertEqual(result["_propagation_metadata"]["data_type"], "activity_log")

    def test_enrich_with_propagation_metadata_none_entity_id(self):
        """Test that _enrich_with_propagation_metadata handles None entity_id correctly."""
        with patch.dict(os.environ, self.test_config):
            selector = MemorySelector(self.mock_cab_tracker, validate_config=False)
            
            # Test with None entity_id (which is Optional[str])
            input_data = {"global_setting": "value"}
            
            result = selector._enrich_with_propagation_metadata(
                data=input_data,
                data_type="global_config",
                entity_id=None,
                task="config_sync"
            )
            
            # Verify None entity_id is handled correctly
            self.assertIsNone(result["_propagation_metadata"]["entity_id"])
            self.assertEqual(result["_propagation_metadata"]["data_type"], "global_config")
            self.assertEqual(result["_propagation_metadata"]["propagation_task"], "config_sync")

    def test_enrich_with_propagation_metadata_empty_data(self):
        """Test that _enrich_with_propagation_metadata works with empty input data."""
        with patch.dict(os.environ, self.test_config):
            selector = MemorySelector(self.mock_cab_tracker, validate_config=False)
            
            # Test with empty dictionary
            input_data = {}
            
            result = selector._enrich_with_propagation_metadata(
                data=input_data,
                data_type="empty_test",
                entity_id="test_001",
                task="empty_data_test"
            )
            
            # Should only contain metadata
            self.assertEqual(len(result), 1)
            self.assertIn("_propagation_metadata", result)
            metadata = result["_propagation_metadata"]
            self.assertEqual(metadata["entity_id"], "test_001")
            self.assertEqual(metadata["data_type"], "empty_test")
            self.assertIsNone(metadata["propagated_at"])  # No timestamp in empty data

    def test_cab_tracker_logging_integration(self):
        """Test that propagation operations are properly logged to CAB tracker."""
        with patch.dict(os.environ, self.test_config):
            selector = MemorySelector(self.mock_cab_tracker, validate_config=False)
            
            with patch.object(selector, '_store_in_redis') as mock_redis, \
                 patch.object(selector, '_store_in_neo4j') as mock_neo4j:
                
                mock_redis.return_value = {"status": "stored"}
                mock_neo4j.return_value = {"status": "stored"}
                
                selector.propagate_data(
                    data={"test": "data"},
                    source_system=MemorySystem.BASIC_MEMORY,
                    data_type="user_profile",
                    entity_id="user_123"
                )
                
                # Verify logging calls were made
                start_calls = [call for call in self.mock_cab_tracker.log_suggestion.call_args_list 
                              if call[0][0] == "Data Propagation Started"]
                summary_calls = [call for call in self.mock_cab_tracker.log_suggestion.call_args_list 
                               if call[0][0] == "Data Propagation Summary"]
                
                self.assertGreater(len(start_calls), 0, "Propagation start should be logged")
                self.assertGreater(len(summary_calls), 0, "Propagation summary should be logged")


if __name__ == '__main__':
    unittest.main()