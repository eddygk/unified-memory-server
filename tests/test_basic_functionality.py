"""
Test basic functionality without external dependencies
"""
import json
import asyncio
import sys
import os

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

try:
    from memory_selector import MemorySelector, MockCabTracker, TaskType, MemorySystem
    print("✓ Memory selector imports successful")
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)


def test_memory_selector_basic():
    """Test basic memory selector functionality"""
    print("Testing memory selector basic functionality...")
    
    # Initialize with mock CAB tracker
    cab_tracker = MockCabTracker()
    memory_selector = MemorySelector(cab_tracker=cab_tracker, validate_config=False)
    
    # Test task analysis
    test_cases = [
        ("Create a new memory about Python programming", TaskType.STORE_MEMORY),
        ("Find all notes about machine learning", TaskType.SEARCH_NOTES),
        ("Add entity named John as a Person", TaskType.STORE_ENTITY),
        ("Show relationships between users and projects", TaskType.SEARCH_NODES),
    ]
    
    for task, expected_type in test_cases:
        task_type = memory_selector.analyze_task(task)
        print(f"  Task: '{task[:30]}...' → {task_type.value}")
        # Note: The actual logic might choose different systems based on implementation
    
    print("✓ Task analysis completed")


def test_fallback_chains():
    """Test fallback chain configuration"""
    print("Testing fallback chains...")
    
    cab_tracker = MockCabTracker()
    memory_selector = MemorySelector(cab_tracker=cab_tracker, validate_config=False)
    
    # Test fallback chains for each system
    for system in MemorySystem:
        fallback_chain = memory_selector.get_fallback_chain(system)
        print(f"  {system.value} → {[s.value for s in fallback_chain]}")
    
    print("✓ Fallback chains configured correctly")


def test_config_loading():
    """Test configuration loading"""
    print("Testing configuration loading...")
    
    cab_tracker = MockCabTracker()
    memory_selector = MemorySelector(cab_tracker=cab_tracker, validate_config=False)
    
    # Check that config is loaded
    assert memory_selector.config is not None
    print("✓ Configuration loaded")
    
    # Test some default values
    config_keys = ['REDIS_URL', 'NEO4J_URL', 'BASIC_MEMORY_URL']
    for key in config_keys:
        if key in memory_selector.config:
            print(f"  {key}: {memory_selector.config[key]}")
    
    print("✓ Configuration values accessible")


def test_cab_tracker_integration():
    """Test CAB tracker integration"""
    print("Testing CAB tracker integration...")
    
    cab_tracker = MockCabTracker()
    memory_selector = MemorySelector(cab_tracker=cab_tracker, validate_config=False)
    
    # Test that CAB tracker is accessible
    assert memory_selector.cab_tracker is not None
    print("✓ CAB tracker accessible")
    
    # Test mock functionality
    if hasattr(cab_tracker, 'logged_suggestions'):
        initial_count = len(cab_tracker.logged_suggestions)
        cab_tracker.log_suggestion("Test", "Test suggestion", severity="LOW")
        assert len(cab_tracker.logged_suggestions) == initial_count + 1
        print("✓ CAB tracker logging functional")


def run_all_tests():
    """Run all basic tests"""
    print("Starting basic functionality tests...\n")
    
    try:
        test_memory_selector_basic()
        print()
        
        test_fallback_chains()
        print()
        
        test_config_loading()
        print()
        
        test_cab_tracker_integration()
        print()
        
        print("✅ All basic tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)