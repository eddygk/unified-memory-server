#!/usr/bin/env python3
"""
Example usage of AI Directives Integration for Claude Desktop
Demonstrates the unified memory system with MCP tool compliance
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from ai_directives_integration import AIDirectivesIntegration
from cab_tracker import CABTracker
import tempfile


def demonstrate_ai_directives():
    """Demonstrate AI directives compliance features"""
    print("🎯 AI Directives Integration Demo")
    print("=" * 50)
    
    # Create temporary CAB file for demo
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as temp_file:
        cab_file = temp_file.name
    
    try:
        # Initialize AI Directives Integration
        print("\n1. Initializing AI Directives Integration...")
        cab_tracker = CABTracker(cab_file)
        integration = AIDirectivesIntegration(
            cab_tracker=cab_tracker,
            enable_startup_sequence=True
        )
        
        print("✓ Integration initialized")
        
        # Execute startup sequence
        print("\n2. Executing AI Directive Startup Sequence...")
        startup_results = integration.execute_startup_sequence("DemoUser", "Claude")
        
        print(f"✓ Step 0 (CAB Tracking): {'✅' if startup_results.get('step_0_completed') else '❌'}")
        print(f"✓ Step 1 (User ID): {'✅' if startup_results.get('step_1_completed') else '❌'}")
        print(f"✓ User Profile Found: {'✅' if startup_results.get('user_profile_found') else '❌'}")
        
        # Demonstrate MCP tool routing
        print("\n3. Testing MCP Tool Routing Decision Tree...")
        
        test_tasks = [
            ("Find relationships between user and projects", "Neo4j (relationships)"),
            ("Create comprehensive documentation", "Basic Memory (documentation)"),
            ("Search for similar conversations", "Redis (semantic search)"),
            ("Store user preferences quickly", "Redis (quick memories)"),
            ("Who is the current user?", "Neo4j (user identification)")
        ]
        
        for task, expected_system in test_tasks:
            routing = integration.route_with_directives(task)
            intent = routing["mcp_decision"]["intent"]
            confidence = routing["mcp_decision"]["confidence"]
            
            print(f"  Task: '{task[:40]}...'")
            print(f"    → Intent: {intent}")
            print(f"    → Confidence: {confidence:.2f}")
            print(f"    → Expected: {expected_system}")
            print()
        
        # Demonstrate MCP tool name compliance
        print("4. Testing MCP Tool Name Compliance...")
        
        test_tools = [
            ("create_entities", "neo4j"),
            ("write_note", "basic_memory"),
            ("search_memory", "redis")
        ]
        
        for operation, system in test_tools:
            mcp_name = integration.get_mcp_tool_name(operation, system)
            is_compliant = integration.validate_mcp_compliance(mcp_name) if mcp_name else False
            
            print(f"  {operation} + {system} → {mcp_name}")
            print(f"    Compliant: {'✅' if is_compliant else '❌'}")
        
        # Show directive compliance summary
        print("\n5. AI Directive Compliance Summary")
        summary = integration.get_directive_summary()
        
        for key, value in summary.items():
            if isinstance(value, bool):
                status = "✅" if value else "❌"
                print(f"  {key.replace('_', ' ').title()}: {status}")
            elif isinstance(value, list):
                print(f"  {key.replace('_', ' ').title()}: {', '.join(value)}")
            else:
                print(f"  {key.replace('_', ' ').title()}: {value}")
        
        # Show CAB tracking file content
        print("\n6. CAB Tracking Results")
        if os.path.exists(cab_file):
            with open(cab_file, 'r') as f:
                content = f.read()
                if content.strip():
                    print("CAB suggestions logged:")
                    print("-" * 30)
                    print(content[-500:] if len(content) > 500 else content)
                else:
                    print("CAB file created but no suggestions logged yet")
        
        print("\n🎉 Demo completed successfully!")
        print(f"CAB tracking file: {cab_file}")
        
    except Exception as e:
        print(f"❌ Demo failed: {str(e)}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Clean up
        if os.path.exists(cab_file):
            print(f"\nCleaning up CAB file: {cab_file}")
            # os.unlink(cab_file)  # Comment out to keep file for inspection


def show_decision_tree():
    """Display the AI directive decision tree"""
    print("\n📋 AI Directive Decision Tree")
    print("=" * 50)
    
    decision_tree = """
├─ Does the task involve relationships/connections between entities?
│  └─ YES → Use Neo4j tools:
│      - local__neo4j-memory__create_entities
│      - local__neo4j-memory__create_relations
│      - local__neo4j-cypher__read_neo4j_cypher
│
├─ Does the task require comprehensive documentation/structured notes?
│  └─ YES → Use Basic Memory tools:
│      - local__basic-memory__write_note
│      - local__basic-memory__read_note
│      - local__basic-memory__canvas
│
└─ Does the task need conversational context/semantic search?
   └─ YES → Use Redis Memory tools:
       - local__redis-memory-server__create_long_term_memories
       - local__redis-memory-server__search_long_term_memory
       - local__redis-memory-server__hydrate_memory_prompt
"""
    
    print(decision_tree)


def show_priority_routing():
    """Display the priority-based task routing from AI directives"""
    print("\n🔄 Priority-Based Task Routing")
    print("=" * 50)
    
    priorities = [
        ("1", "User identity", "Neo4j", "local__neo4j-cypher__read_neo4j_cypher", "Redis → Basic Memory"),
        ("2", "Relationships", "Neo4j", "local__neo4j-memory__create_relations", "None"),
        ("3", "Documentation", "Basic Memory", "local__basic-memory__write_note", "Redis snippets"),
        ("4", "Context retrieval", "Redis", "local__redis-memory-server__hydrate_memory_prompt", "Search memories"),
        ("5", "Entity creation", "Neo4j", "local__neo4j-memory__create_entities", "Basic Memory note"),
        ("6", "Quick memories", "Redis", "local__redis-memory-server__create_long_term_memories", "Basic Memory note"),
    ]
    
    print(f"{'Priority':<8} {'Task Type':<15} {'Primary System':<12} {'Primary Tool':<45} {'Fallback Chain'}")
    print("-" * 120)
    
    for priority, task_type, system, tool, fallback in priorities:
        print(f"{priority:<8} {task_type:<15} {system:<12} {tool:<45} {fallback}")


if __name__ == "__main__":
    print("🤖 Claude Desktop AI Directives Demo")
    print("Unified Memory Server with MCP Tool Compliance")
    print("=" * 60)
    
    show_decision_tree()
    show_priority_routing()
    demonstrate_ai_directives()