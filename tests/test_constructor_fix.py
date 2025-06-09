"""
Tests for MemorySelector constructor parameter fix.

Verifies that config_path and validate_config are keyword-only parameters
to prevent user confusion when calling the constructor.
"""
import unittest
from unittest.mock import Mock
from src.memory_selector import MemorySelector


class TestMemorySelectorConstructorFix(unittest.TestCase):
    """Test suite for MemorySelector constructor parameter fix."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_cab_tracker = Mock()
        
    def test_keyword_only_parameters_work(self):
        """Test that keyword-only parameters work correctly."""
        # All these should work
        selector0 = MemorySelector()
        selector1 = MemorySelector(validate_config=False)
        selector2 = MemorySelector(config_path=None, validate_config=False)
        selector3 = MemorySelector(self.mock_cab_tracker, validate_config=False)
        selector4 = MemorySelector(self.mock_cab_tracker, config_path=None, validate_config=False)
        
        # Verify they were created successfully
        self.assertIsNotNone(selector0)
        self.assertIsNotNone(selector1)
        self.assertIsNotNone(selector2)
        self.assertIsNotNone(selector3)
        self.assertIsNotNone(selector4)
        
    def test_positional_arguments_fail_correctly(self):
        """Test that too many positional arguments fail with clear error."""
        # This should fail - trying to pass config_path and validate_config as positional
        with self.assertRaises(TypeError) as context:
            MemorySelector(None, None, False)
        
        # Verify the error message indicates too many positional arguments
        self.assertIn("positional arguments", str(context.exception))
        
    def test_mixed_usage_works(self):
        """Test that mixed positional/keyword usage works as expected."""
        # CAB tracker can be positional, but config_path and validate_config must be keyword
        selector = MemorySelector(self.mock_cab_tracker, validate_config=False)
        self.assertIsNotNone(selector)
        self.assertEqual(selector.cab_tracker, self.mock_cab_tracker)
        
    def test_prevents_confusion_scenario(self):
        """Test that the specific confusion scenario is prevented."""
        # The problematic case that was mentioned in the review:
        # User intends: MemorySelector(validate_config=False)
        # But accidentally writes: MemorySelector(None, False)
        # This should now fail instead of being misinterpreted
        
        with self.assertRaises(TypeError):
            # This was the confusing scenario - False would be interpreted as config_path
            MemorySelector(None, False)  # Should fail now


if __name__ == '__main__':
    unittest.main()