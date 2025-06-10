"""
Test to verify that client variables are properly defined before use
This test addresses GitHub issue #93
"""
import os
import sys
import tempfile
import unittest
from unittest.mock import MagicMock, patch

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from memory_selector import MemorySelector
from cab_tracker import CABTracker


class TestClientVariableUsage(unittest.TestCase):
    """Test suite to verify client variables are properly defined before use"""

    def setUp(self):
        """Set up test environment"""
        # Create a temporary CAB file
        self.cab_file = tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False)
        self.cab_file.close()
        
        # Initialize CAB tracker and selector
        self.cab_tracker = CABTracker(self.cab_file.name)
        self.selector = MemorySelector(cab_tracker=self.cab_tracker, validate_config=False)

    def tearDown(self):
        """Clean up test environment"""
        if os.path.exists(self.cab_file.name):
            os.unlink(self.cab_file.name)

    def test_redis_client_variable_defined_before_use(self):
        """Test that Redis client variable is properly defined before use"""
        # Mock the _get_redis_client method to return a mock client
        mock_client = MagicMock()
        # Also mock the config to include Redis URL
        test_config = self.selector.config.copy()
        test_config['REDIS_URL'] = 'redis://localhost:6379'
        
        with patch.object(self.selector, '_get_redis_client', return_value=mock_client), \
             patch.object(self.selector, 'config', test_config):
            try:
                # This should not raise NameError for undefined 'client'
                self.selector._store_in_redis({"test": "data"}, "test task")
            except NameError as e:
                # Ensure the exception is specifically about the 'client' variable
                if "client" in str(e).lower() and "not defined" in str(e).lower():
                    self.fail(f"Client variable not defined: {e}")

    def test_basic_memory_client_variable_defined_before_use(self):
        """Test that Basic Memory client variable is properly defined before use"""
        # Mock the _get_basic_memory_client method to return a mock client
        mock_client = MagicMock()
        with patch.object(self.selector, '_get_basic_memory_client', return_value=mock_client):
            try:
                # This should not raise NameError for undefined 'client'
                self.selector._store_in_basic_memory({"test": "data"}, "test task")
            except Exception as e:
                # Should not be a NameError about undefined 'client'
                self.assertNotIsInstance(e, NameError)
                if "client" in str(e).lower() and "not defined" in str(e).lower():
                    self.fail(f"Client variable not defined: {e}")

    def test_neo4j_client_variable_defined_before_use(self):
        """Test that Neo4j client variable is properly defined before use"""
        # Mock the _ensure_neo4j_client method to return a mock client
        mock_client = MagicMock()
        with patch.object(self.selector, '_ensure_neo4j_client', return_value=mock_client):
            try:
                # This should not raise NameError for undefined 'client'
                self.selector._store_in_neo4j({"test": "data"}, "test task")
            except Exception as e:
                # Should not be a NameError about undefined 'client'
                self.assertNotIsInstance(e, NameError)
                if "client" in str(e).lower() and "not defined" in str(e).lower():
                    self.fail(f"Client variable not defined: {e}")

    def test_redis_retrieval_client_variable_defined_before_use(self):
        """Test that Redis client variable is properly defined before use in retrieval"""
        # Mock the _get_redis_client method to return a mock client
        mock_client = MagicMock()
        with patch.object(self.selector, '_get_redis_client', return_value=mock_client):
            try:
                # This should not raise NameError for undefined 'client'
                self.selector._retrieve_from_redis({"test": "query"}, "test task")
            except Exception as e:
                # Should not be a NameError about undefined 'client'
                self.assertNotIsInstance(e, NameError)
                if "client" in str(e).lower() and "not defined" in str(e).lower():
                    self.fail(f"Client variable not defined: {e}")

    def test_basic_memory_retrieval_client_variable_defined_before_use(self):
        """Test that Basic Memory client variable is properly defined before use in retrieval"""
        # Mock the _get_basic_memory_client method to return a mock client
        mock_client = MagicMock()
        with patch.object(self.selector, '_get_basic_memory_client', return_value=mock_client):
            try:
                # This should not raise NameError for undefined 'client'
                self.selector._retrieve_from_basic_memory({"test": "query"}, "test task")
            except Exception as e:
                # Should not be a NameError about undefined 'client'
                self.assertNotIsInstance(e, NameError)
                if "client" in str(e).lower() and "not defined" in str(e).lower():
                    self.fail(f"Client variable not defined: {e}")

    def test_neo4j_retrieval_client_variable_defined_before_use(self):
        """Test that Neo4j client variable is properly defined before use in retrieval"""
        # Mock the _ensure_neo4j_client method to return a mock client
        mock_client = MagicMock()
        with patch.object(self.selector, '_ensure_neo4j_client', return_value=mock_client):
            try:
                # This should not raise NameError for undefined 'client'
                self.selector._retrieve_from_neo4j({"test": "query"}, "test task")
            except Exception as e:
                # Should not be a NameError about undefined 'client'
                self.assertNotIsInstance(e, NameError)
                if "client" in str(e).lower() and "not defined" in str(e).lower():
                    self.fail(f"Client variable not defined: {e}")

    def test_no_undefined_client_variables_in_codebase(self):
        """Test that no client variables are used without being defined"""
        # This is a static analysis test - read the source code and look for patterns
        memory_selector_path = os.path.join(
            os.path.dirname(__file__), '..', 'src', 'memory_selector.py'
        )
        
        with open(memory_selector_path, 'r') as f:
            content = f.read()
        
        lines = content.split('\n')
        
        # Build a map of method boundaries
        method_starts = {}
        current_method = None
        for i, line in enumerate(lines, 1):
            if line.strip().startswith('def '):
                current_method = i
                method_starts[i] = current_method
            elif current_method:
                method_starts[i] = current_method
        
        client_usage_lines = []
        
        for i, line in enumerate(lines, 1):
            # Look for lines that use 'client.' but don't define client
            if 'client.' in line and '=' not in line and not line.strip().startswith('#'):
                # Check if this line is using client without defining it
                client_usage_lines.append((i, line.strip()))
        
        # For each client usage, verify it's preceded by a client assignment within the same method
        for line_num, line_content in client_usage_lines:
            # Find the method this line belongs to
            method_start = method_starts.get(line_num)
            if not method_start:
                continue  # Skip if not in a method
            
            # Look backwards from this line to the method start to find client assignment
            found_assignment = False
            for j in range(line_num - 1, method_start - 1, -1):
                if j <= 0 or j >= len(lines):
                    continue
                prev_line = lines[j - 1]
                if 'client =' in prev_line and ('_get_' in prev_line or '_ensure_' in prev_line):
                    found_assignment = True
                    break
            
            if not found_assignment:
                self.fail(
                    f"Line {line_num}: '{line_content}' uses client without proper assignment within method starting at line {method_start}. "
                    f"This indicates the original issue from GitHub #93 may still exist."
                )


if __name__ == '__main__':
    unittest.main()