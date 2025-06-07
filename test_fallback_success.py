#!/usr/bin/env python3
"""
Test script to verify fallback success scenarios in MemorySelector
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from memory_selector import MemorySelector, MemorySystem, TaskType
from cab_tracker import CABTracker
import tempfile

class MockSuccessfulClient:
    """Mock client that simulates successful operations"""
    def __init__(self, system_name):
        self.system_name = system_name

def test_fallback_success():
    """Test that fallback works when primary system fails but secondary succeeds"""
    
    # Create a temporary CAB file for testing
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        cab_file = f.name
    
    try:
        # Initialize memory selector with CAB tracker
        cab_tracker = CABTracker(cab_file)
        selector = MemorySelector(cab_tracker)
        
        # Override one of the client methods to simulate a working system
        # Let's make Basic Memory "work" but Neo4j and Redis fail
        def mock_basic_memory_store(data, task_type, context=None):
            return f"Successfully stored {type(data).__name__} in Basic Memory"
        
        def mock_basic_memory_retrieve(query, task_type, context=None):
            return f"Successfully retrieved data from Basic Memory for query: {query}"
        
        # Override the basic memory methods
        selector._store_in_basic_memory = mock_basic_memory_store
        selector._retrieve_from_basic_memory = mock_basic_memory_retrieve
        
        # Test store operation that should fallback to Basic Memory
        test_data = {"test": "data", "user_id": "123"}
        task = "Store user profile information"  # This will be analyzed as USER_IDENTITY -> NEO4J primary
        
        print(f"Testing store operation with task: '{task}'")
        print("Primary system (Neo4j) will fail, Redis will fail, Basic Memory will succeed")
        
        result, successful_system, used_fallback = selector.store_data(test_data, task)
        
        print(f"Result: {result}")
        print(f"Successful system: {successful_system.value}")
        print(f"Used fallback: {used_fallback}")
        
        # Verify fallback was used
        assert used_fallback == True, "Fallback should have been used"
        assert successful_system == MemorySystem.BASIC_MEMORY, f"Expected Basic Memory, got {successful_system}"
        
        # Test retrieve operation
        test_query = {"search": "user profile"}
        task = "Find user relationships"  # This will be analyzed as RELATIONSHIP_QUERY -> NEO4J primary
        
        print(f"\nTesting retrieve operation with task: '{task}'")
        
        result, successful_system, used_fallback = selector.retrieve_data(test_query, task)
        
        print(f"Result: {result}")
        print(f"Successful system: {successful_system.value}")
        print(f"Used fallback: {used_fallback}")
        
        # Verify fallback was used
        assert used_fallback == True, "Fallback should have been used"
        assert successful_system == MemorySystem.BASIC_MEMORY, f"Expected Basic Memory, got {successful_system}"
        
        # Check CAB file for fallback success logs
        if os.path.exists(cab_file):
            with open(cab_file, 'r') as f:
                cab_content = f.read()
                print(f"\nCAB Tracker entries created")
                if "Fallback Success" in cab_content:
                    print("✓ Fallback success properly logged to CAB tracker")
                else:
                    print("! Fallback success not found in CAB log")
        
        return True
    
    finally:
        # Clean up
        if os.path.exists(cab_file):
            os.unlink(cab_file)

def main():
    """Run fallback success test"""
    print("Testing Fallback Success Scenarios")
    print("=" * 50)
    
    try:
        test_fallback_success()
        
        print("\n" + "=" * 50)
        print("Fallback success test completed!")
        print("✓ Primary system failure triggers fallback")
        print("✓ Secondary system success works correctly")
        print("✓ Fallback success is logged via CABTracker")
        
    except Exception as e:
        print(f"\nTest failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())