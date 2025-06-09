#!/usr/bin/env python3
"""
Example script demonstrating the Automated Memory System Router

This script shows how the new automated router intelligently selects
memory systems based on request analysis.
"""

import sys
import os

from src.automated_memory_router import AutomatedMemoryRouter, MemoryRequest, Operation
from src.cab_tracker import CABTracker


def demo_routing_decisions():
    """Demonstrate various routing decisions"""
    print("🎯 Automated Memory System Router Demo")
    print("=" * 50)
    
    # Initialize router with mock CAB tracker
    cab_tracker = CABTracker("/tmp/cab_demo.md")
    router = AutomatedMemoryRouter(cab_tracker=cab_tracker, validate_config=False)
    
    # Test cases demonstrating different routing scenarios
    test_cases = [
        {
            "description": "Relationship Creation",
            "content": "Connect John Smith to the Marketing project as team lead",
            "operation": Operation.STORE
        },
        {
            "description": "Documentation Storage", 
            "content": "Create comprehensive documentation for the API endpoints",
            "operation": Operation.STORE
        },
        {
            "description": "Semantic Search",
            "content": "Find documents similar to machine learning algorithms",
            "operation": Operation.SEARCH
        },
        {
            "description": "User Profile Query",
            "content": "How is Alice connected to the DevOps team?",
            "operation": Operation.QUERY
        },
        {
            "description": "Context Retrieval",
            "content": "Remember what we discussed about the project timeline",
            "operation": Operation.RETRIEVE
        },
        {
            "description": "Comprehensive Storage",
            "content": "Store complete profile information for this user including all relationships",
            "operation": Operation.STORE
        }
    ]
    
    print("\n📊 Routing Decisions:\n")
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"{i}. {test_case['description']}")
        print(f"   Request: \"{test_case['content']}\"")
        
        # Create request
        request = MemoryRequest(
            operation=test_case['operation'],
            content=test_case['content'],
            context={'operation': test_case['operation'].value}
        )
        
        # Get routing decision
        decision = router.route(request)
        
        print(f"   📍 Primary System: {decision.primary_system.value}")
        print(f"   🎯 Confidence: {decision.confidence:.2f}")
        
        if decision.multi_system:
            secondary_names = [s.value for s in decision.secondary_systems]
            print(f"   🔗 Secondary Systems: {', '.join(secondary_names)}")
        
        if request.entities:
            entity_summary = [f"{e.name}({e.entity_type})" for e in request.entities[:3]]
            print(f"   🏷️  Entities: {', '.join(entity_summary)}")
        
        print(f"   💭 Reasoning: {decision.reasoning}")
        print()
    
    print("📈 Performance Metrics:")
    stats = router.get_routing_stats()
    for system, metrics in stats['system_performance'].items():
        print(f"   {system}: Success Rate: {metrics['success_rate']:.1%}, "
              f"Avg Response: {metrics['avg_response_time']:.0f}ms")
    
    print(f"\n✅ Router Version: {stats['router_version']}")
    print(f"📊 Recent Operations Tracked: {stats['recent_operations']}")


def demo_performance_tracking():
    """Demonstrate performance tracking and adaptation"""
    print("\n🏃‍♂️ Performance Tracking Demo")
    print("=" * 50)
    
    router = AutomatedMemoryRouter(validate_config=False)
    
    # Simulate some operations with different performance characteristics
    print("Simulating operations with different performance characteristics...\n")
    
    # Simulate Redis performing well
    for i in range(5):
        router.performance_tracker.record_operation('redis', True, 50.0 + i * 10)
    
    # Simulate Neo4j having issues
    for i in range(3):
        router.performance_tracker.record_operation('neo4j', False, 2000.0 + i * 500)
    
    # Simulate Basic Memory being slow but reliable
    for i in range(4):
        router.performance_tracker.record_operation('basic_memory', True, 300.0 + i * 50)
    
    print("Performance after simulation:")
    stats = router.get_routing_stats()
    for system, metrics in stats['system_performance'].items():
        score = router.performance_tracker.get_system_score(system)
        print(f"   {system}:")
        print(f"     Success Rate: {metrics['success_rate']:.1%}")
        print(f"     Avg Response: {metrics['avg_response_time']:.0f}ms")
        print(f"     Overall Score: {score:.2f}")
        print()
    
    # Now test how this affects routing
    print("How performance affects routing:")
    request = MemoryRequest(
        operation=Operation.QUERY,
        content="Find user relationships",  # Normally would go to Neo4j
        context={'operation': Operation.QUERY.value}
    )
    
    decision = router.route(request)
    print(f"   Query routed to: {decision.primary_system.value} (confidence: {decision.confidence:.2f})")
    print(f"   Note: Neo4j had poor performance, so routing may have been affected")


def demo_entity_extraction():
    """Demonstrate entity extraction capabilities"""
    print("\n🏷️  Entity Extraction Demo")
    print("=" * 50)
    
    router = AutomatedMemoryRouter(validate_config=False)
    
    test_content = [
        "John Smith mentioned that Project Alpha needs documentation by Friday",
        "Connect @alice to the readme.md file for the DevOps project",
        "Microsoft Corporation is working with our development team",
        "The concept of machine learning should be documented in the AI notes"
    ]
    
    for content in test_content:
        print(f"Content: \"{content}\"")
        
        request = MemoryRequest(operation=Operation.STORE, content=content)
        entities = router.entity_extractor.extract(request)
        
        if entities:
            print("   Entities found:")
            for entity in entities:
                print(f"     • {entity.name} ({entity.entity_type}, confidence: {entity.confidence:.1f})")
        else:
            print("   No entities found")
        print()


if __name__ == "__main__":
    print("🚀 Starting Automated Memory Router Demo\n")
    
    try:
        demo_routing_decisions()
        demo_performance_tracking()
        demo_entity_extraction()
        
        print("\n✨ Demo completed successfully!")
        print("The Automated Memory Router provides intelligent, performance-aware routing")
        print("without requiring manual system selection decisions.")
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)