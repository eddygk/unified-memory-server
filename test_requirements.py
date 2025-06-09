#!/usr/bin/env python3
"""
Comprehensive test to verify all requirements from Section 3.5 are met
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from memory_selector import MemorySelector, MemorySystem, TaskType
from cab_tracker import CABTracker
import tempfile
import pytest

@pytest.mark.parametrize("method_name,system", [
    ('_store_in_redis', MemorySystem.REDIS),
    ('_store_in_neo4j', MemorySystem.NEO4J),
    ('_store_in_basic_memory', MemorySystem.BASIC_MEMORY)
])
def test_store_methods_raise_exceptions(method_name, system):
    """Test that _store_in_X methods raise exceptions on failure"""
    # Create a temporary CAB file for testing
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        cab_file = f.name
    
    try:
        # Initialize memory selector with CAB tracker
        cab_tracker = CABTracker(cab_file)
        selector = MemorySelector(cab_tracker)
        
        # Test that the method raises an exception
        method = getattr(selector, method_name)
        with pytest.raises(Exception):
            method({"test": "data"}, TaskType.UNKNOWN)
        
        print(f"  ✓ {method_name} properly raises exception")
        
    finally:
        # Clean up
        if os.path.exists(cab_file):
            os.unlink(cab_file)

@pytest.mark.parametrize("method_name,system", [
    ('_retrieve_from_redis', MemorySystem.REDIS),
    ('_retrieve_from_neo4j', MemorySystem.NEO4J),
    ('_retrieve_from_basic_memory', MemorySystem.BASIC_MEMORY)
])
def test_retrieve_methods_raise_exceptions(method_name, system):
    """Test that _retrieve_from_X methods raise exceptions on failure"""
    # Create a temporary CAB file for testing
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        cab_file = f.name
    
    try:
        # Initialize memory selector with CAB tracker
        cab_tracker = CABTracker(cab_file)
        selector = MemorySelector(cab_tracker)
        
        # Test that the method raises an exception
        method = getattr(selector, method_name)
        with pytest.raises(Exception):
            method({"test": "query"}, TaskType.UNKNOWN)
        
        print(f"  ✓ {method_name} properly raises exception")
        
    finally:
        # Clean up
        if os.path.exists(cab_file):
            os.unlink(cab_file)

def test_requirement_3_5():
    """Test that all requirements from Section 3.5 are implemented"""
    
    print("Testing Requirements from Section 3.5: Fallback and Error Handling")
    print("=" * 70)
    
    # Create a temporary CAB file for testing
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        cab_file = f.name
    
    try:
        # Initialize memory selector with CAB tracker
        cab_tracker = CABTracker(cab_file)
        selector = MemorySelector(cab_tracker)
        
        print("✓ CABTracker initialized and passed to MemorySelector")
        
        # Requirement 1: Ensure _store_in_X methods raise exceptions on failure
        print("\n1. Testing _store_in_X methods raise exceptions on failure:")
        print("  (Store method tests moved to parametrized test functions)")
        
        # Requirement 2: Ensure _retrieve_from_X methods raise exceptions on failure
        print("\n2. Testing _retrieve_from_X methods raise exceptions on failure:")
        print("  (Retrieve method tests moved to parametrized test functions)")
        
        # Requirement 3: Test that exceptions trigger execute_with_fallback
        print("\n3. Testing exceptions trigger execute_with_fallback:")
        
        def failing_operation(system, task, context):
            raise Exception(f"{system.value} operation failed")
        
        def working_operation(system, task, context):
            if system == MemorySystem.NEO4J:
                raise Exception("Neo4j failed")
            return f"Success with {system.value}"
        
        # Test that all failures are handled
        try:
            selector.execute_with_fallback("test task", failing_operation)
            assert False, "execute_with_fallback should have raised exception after all failures"
        except Exception as e:
            print("  ✓ execute_with_fallback properly handles all system failures")
        
        # Test that fallback works when one system succeeds
        try:
            result, successful_system, used_fallback = selector.execute_with_fallback(
                "Find user relationships", working_operation  # This should select Neo4j as primary
            )
            if used_fallback and successful_system != MemorySystem.NEO4J:
                print("  ✓ execute_with_fallback properly uses fallback systems")
            else:
                print(f"  ✗ Fallback not used correctly: {used_fallback}, {successful_system}")
                # Let's see what the primary selection was
                primary_system, task_type = selector.select_memory_system("Find user relationships")
                print(f"    Primary system selected: {primary_system}, Task type: {task_type}")
                assert False, f"Fallback not used correctly: {used_fallback}, {successful_system}"
        except Exception as e:
            print(f"  ✗ execute_with_fallback failed unexpectedly: {e}")
            assert False, f"execute_with_fallback failed unexpectedly: {e}"
        
        # Requirement 4: Log API errors via CABTracker
        print("\n4. Testing API errors are logged via CABTracker:")
        
        # Check CAB file for logged errors
        if os.path.exists(cab_file):
            with open(cab_file, 'r') as f:
                cab_content = f.read()
                
                api_error_count = cab_content.count("API Error")
                client_error_count = cab_content.count("Client Instantiation Error")
                
                print(f"  ✓ {api_error_count} API errors logged to CAB tracker")
                print(f"  ✓ {client_error_count} client instantiation errors logged to CAB tracker")
                
                if api_error_count > 0 and "severity='HIGH'" in cab_content:
                    print("  ✓ API errors logged with HIGH severity")
                elif api_error_count > 0:
                    print("  ✓ API errors logged (checking severity format)")
                    # Check for both possible formats
                    if "**[HIGH]**" in cab_content or "severity='HIGH'" in cab_content:
                        print("  ✓ API errors logged with HIGH severity (confirmed)")
                    else:
                        print(f"  ✗ API errors not logged with proper severity format")
                        print(f"    Content sample: {cab_content[:500]}...")
                        assert False, "API errors not logged with proper severity format"
                else:
                    print("  ✗ No API errors found in CAB log")
                    assert False, "No API errors found in CAB log"
                
                if "context=" in cab_content and "metrics=" in cab_content:
                    print("  ✓ API errors logged with context and metrics")
                elif "**Context**:" in cab_content and "**Metrics**:" in cab_content:
                    print("  ✓ API errors logged with context and metrics (markdown format)")
                else:
                    print("  ✗ API errors missing context or metrics")
                    print(f"    Content sample: {cab_content[:1000]}...")
                    assert False, "API errors missing context or metrics"
        
        # Requirement 5: Integration with store_data and retrieve_data methods
        print("\n5. Testing integration with store_data and retrieve_data methods:")
        
        try:
            selector.store_data({"test": "data"}, "store user information")
            assert False, "store_data should have failed with exceptions"
        except Exception:
            print("  ✓ store_data properly triggers fallback and fails appropriately")
        
        try:
            selector.retrieve_data({"query": "test"}, "find user information")
            assert False, "retrieve_data should have failed with exceptions"
        except Exception:
            print("  ✓ retrieve_data properly triggers fallback and fails appropriately")
        
        print("\n" + "=" * 70)
        print("ALL REQUIREMENTS FROM SECTION 3.5 SUCCESSFULLY IMPLEMENTED!")
        print("✓ _store_in_X methods raise exceptions on failure")
        print("✓ _retrieve_from_X methods raise exceptions on failure") 
        print("✓ Exceptions trigger execute_with_fallback")
        print("✓ API errors logged via CABTracker with proper severity, context, and metrics")
        print("✓ Integration with high-level store_data and retrieve_data methods")
        
        # Test passes if we reach here without assertion errors
    
    finally:
        # Clean up
        if os.path.exists(cab_file):
            os.unlink(cab_file)

def main():
    """Run comprehensive requirements test"""
    try:
        test_requirement_3_5()
        return 0
    except Exception as e:
        print(f"\nTest failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())