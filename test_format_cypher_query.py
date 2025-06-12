#!/usr/bin/env python3
"""
Test script for the format_cypher_query helper function.

This script validates that the helper function correctly applies textwrap.dedent() and strip()
to format Cypher queries consistently.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from memory_selector import format_cypher_query


def test_format_cypher_query_basic():
    """Test basic functionality of format_cypher_query"""
    query = """
    MATCH (n:User)
    RETURN n
    """
    
    expected = "MATCH (n:User)\nRETURN n"
    result = format_cypher_query(query)
    
    assert result == expected, f"Expected '{expected}', got '{result}'"
    print("✓ Basic formatting test passed")


def test_format_cypher_query_with_indentation():
    """Test format_cypher_query with various indentation levels"""
    query = """
        MATCH (source {name: $source_name})
        MATCH (target {name: $target_name})
        CREATE (source)-[r:RELATED_TO]->(target)
        RETURN r
        """
    
    expected = "MATCH (source {name: $source_name})\nMATCH (target {name: $target_name})\nCREATE (source)-[r:RELATED_TO]->(target)\nRETURN r"
    result = format_cypher_query(query)
    
    assert result == expected, f"Expected '{expected}', got '{result}'"
    print("✓ Indentation formatting test passed")


def test_format_cypher_query_f_string():
    """Test format_cypher_query with f-string content (simulating actual usage)"""
    relation_type = "WORKS_ON"
    query = f"""
    MATCH (source)-[r:{relation_type}]->(target)
    WHERE source.name = $source_name
    RETURN source, r, target
    """
    
    expected = "MATCH (source)-[r:WORKS_ON]->(target)\nWHERE source.name = $source_name\nRETURN source, r, target"
    result = format_cypher_query(query)
    
    assert result == expected, f"Expected '{expected}', got '{result}'"
    print("✓ F-string formatting test passed")


def test_format_cypher_query_edge_cases():
    """Test format_cypher_query with edge cases"""
    # Empty string
    assert format_cypher_query("") == "", "Empty string should return empty string"
    
    # String with only whitespace
    assert format_cypher_query("   \n  \t  ") == "", "Whitespace-only string should return empty string"
    
    # String with no leading/trailing whitespace
    query = "MATCH (n) RETURN n"
    assert format_cypher_query(query) == query, "No-whitespace string should return unchanged"
    
    print("✓ Edge cases test passed")


def main():
    """Run all tests"""
    print("Testing format_cypher_query helper function...")
    
    try:
        test_format_cypher_query_basic()
        test_format_cypher_query_with_indentation()
        test_format_cypher_query_f_string()
        test_format_cypher_query_edge_cases()
        
        print("\n✅ All tests passed! The format_cypher_query function works correctly.")
        return True
        
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        return False
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)