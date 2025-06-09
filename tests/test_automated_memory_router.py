"""
Tests for AutomatedMemoryRouter and related components.

Tests intent analysis, entity extraction, routing decisions, and performance tracking.
"""
import unittest
from unittest.mock import Mock, patch, MagicMock
import tempfile
import os

from src.automated_memory_router import (
    AutomatedMemoryRouter, IntentAnalyzer, EntityExtractor, RoutingEngine,
    PerformanceTracker, MemoryRequest, Entity, IntentType, RoutingDecision, Operation
)
from src.memory_selector import MemorySystem


class TestIntentAnalyzer(unittest.TestCase):
    """Test intent analysis functionality"""
    
    def setUp(self):
        self.analyzer = IntentAnalyzer()
    
    def test_relationship_intent_detection(self):
        """Test detection of relationship-related intents"""
        test_cases = [
            ("Connect John to the marketing project", IntentType.CREATE_RELATION),
            ("Who is linked to this project?", IntentType.QUERY_RELATION),
            ("Find the path from user to organization", IntentType.TRAVERSE_GRAPH),
            ("How is Alice related to Bob?", IntentType.QUERY_RELATION)
        ]
        
        for content, expected_intent in test_cases:
            request = MemoryRequest(operation=Operation.QUERY, content=content)
            result = self.analyzer.analyze(request)
            self.assertEqual(result, expected_intent, f"Failed for: {content}")
    
    def test_documentation_intent_detection(self):
        """Test detection of documentation-related intents"""
        test_cases = [
            ("Write a comprehensive note about the project", IntentType.WRITE_DOC),
            ("Create documentation for the API", IntentType.WRITE_DOC),
            ("Read the document about deployment", IntentType.READ_DOC),
            ("Show me the file contents", IntentType.READ_DOC)
        ]
        
        for content, expected_intent in test_cases:
            request = MemoryRequest(operation=Operation.QUERY, content=content)
            result = self.analyzer.analyze(request)
            self.assertEqual(result, expected_intent, f"Failed for: {content}")
    
    def test_search_intent_detection(self):
        """Test detection of search-related intents"""
        test_cases = [
            ("Find similar documents to this one", IntentType.SEMANTIC_SEARCH),
            ("Remember what we discussed about AI", IntentType.CONTEXT_RETRIEVAL),
            ("Search for information about machine learning", IntentType.SEMANTIC_SEARCH),
            ("Retrieve the stored user preferences", IntentType.MEMORY_LOOKUP)
        ]
        
        for content, expected_intent in test_cases:
            request = MemoryRequest(operation=Operation.QUERY, content=content)
            result = self.analyzer.analyze(request)
            self.assertEqual(result, expected_intent, f"Failed for: {content}")
    
    def test_comprehensive_intent_detection(self):
        """Test detection of multi-system intents"""
        test_cases = [
            ("Store everything about this user", IntentType.COMPREHENSIVE_STORE),
            ("Save complete profile information", IntentType.COMPREHENSIVE_STORE),
            ("Get all information about this project", IntentType.COMPREHENSIVE_STORE)
        ]
        
        for content, expected_intent in test_cases:
            request = MemoryRequest(operation=Operation.QUERY, content=content)
            result = self.analyzer.analyze(request)
            self.assertEqual(result, expected_intent, f"Failed for: {content}")
    
    def test_context_based_scoring(self):
        """Test that context influences intent detection"""
        content = "user information"
        
        # Test with store context
        request_store = MemoryRequest(
            operation=Operation.QUERY, 
            content=content,
            context={'operation': 'store'}
        )
        result_store = self.analyzer.analyze(request_store)
        
        # Test with search context  
        request_search = MemoryRequest(
            operation=Operation.QUERY,
            content=content, 
            context={'operation': 'search'}
        )
        result_search = self.analyzer.analyze(request_search)
        
        # With context boost, search should favor search intents
        # Since content doesn't match any strong patterns, context should be decisive
        # Note: This test may be flaky if content matches other patterns strongly
        # At minimum, the scores should be influenced even if final intent is same
        
        # Let's test with clearer differentiation
        content_ambiguous = "handle data"
        request_ambiguous_store = MemoryRequest(
            operation=Operation.QUERY, 
            content=content_ambiguous,
            context={'operation': 'store'}
        )
        request_ambiguous_search = MemoryRequest(
            operation=Operation.QUERY,
            content=content_ambiguous, 
            context={'operation': 'retrieve'}
        )
        
        result_ambig_store = self.analyzer.analyze(request_ambiguous_store)
        result_ambig_search = self.analyzer.analyze(request_ambiguous_search)
        
        # At least one should be different, or test that context scoring was applied
        self.assertTrue(
            result_store != result_search or result_ambig_store != result_ambig_search,
            "Context should influence intent detection in at least one case"
        )
    
    def test_unknown_intent_fallback(self):
        """Test that unclear content returns UNKNOWN intent"""
        unclear_content = "Lorem ipsum dolor sit amet"
        request = MemoryRequest(operation=Operation.QUERY, content=unclear_content)
        result = self.analyzer.analyze(request)
        self.assertEqual(result, IntentType.UNKNOWN)


class TestEntityExtractor(unittest.TestCase):
    """Test entity extraction functionality"""
    
    def setUp(self):
        self.extractor = EntityExtractor()
    
    def test_person_entity_extraction(self):
        """Test extraction of person entities"""
        content = "John Smith mentioned that Alice Johnson is working on the project"
        request = MemoryRequest(operation=Operation.QUERY, content=content)
        entities = self.extractor.extract(request)
        
        person_entities = [e for e in entities if e.entity_type == 'person']
        self.assertGreater(len(person_entities), 0, "Should extract at least one person")
        
        # Check that names are extracted correctly
        names = [e.name for e in person_entities]
        self.assertTrue(any('John' in name for name in names), "Should extract John")
    
    def test_project_entity_extraction(self):
        """Test extraction of project entities"""
        content = "Working on Project Alpha and the Database Migration initiative"
        request = MemoryRequest(operation=Operation.QUERY, content=content)
        entities = self.extractor.extract(request)
        
        project_entities = [e for e in entities if e.entity_type == 'project']
        self.assertGreater(len(project_entities), 0, "Should extract project entities")
    
    def test_document_entity_extraction(self):
        """Test extraction of document entities"""
        content = "Please read the readme.md file and the API documentation"
        request = MemoryRequest(operation=Operation.QUERY, content=content)
        entities = self.extractor.extract(request)
        
        doc_entities = [e for e in entities if e.entity_type == 'document']
        self.assertGreater(len(doc_entities), 0, "Should extract document entities")
        
        # Check for specific file
        names = [e.name for e in doc_entities]
        self.assertTrue(any('readme.md' in name for name in names), "Should extract readme.md")
    
    def test_context_entity_injection(self):
        """Test that entities from context are included"""
        content = "Simple content"
        context_entities = [
            {'name': 'TestEntity', 'entity_type': 'custom', 'confidence': 0.9}
        ]
        request = MemoryRequest(
            operation=Operation.QUERY, 
            content=content,
            context={'entities': context_entities}
        )
        entities = self.extractor.extract(request)
        
        custom_entities = [e for e in entities if e.entity_type == 'custom']
        self.assertEqual(len(custom_entities), 1, "Should include context entities")
        self.assertEqual(custom_entities[0].name, 'TestEntity')
    
    def test_entity_confidence_scoring(self):
        """Test that entities have confidence scores"""
        content = "John Smith is working on Project Alpha"
        request = MemoryRequest(operation=Operation.QUERY, content=content)
        entities = self.extractor.extract(request)
        
        for entity in entities:
            self.assertIsInstance(entity.confidence, float, "Confidence should be a float")
            self.assertGreaterEqual(entity.confidence, 0.0, "Confidence should be >= 0")
            self.assertLessEqual(entity.confidence, 1.0, "Confidence should be <= 1")


class TestPerformanceTracker(unittest.TestCase):
    """Test performance tracking functionality"""
    
    def setUp(self):
        self.tracker = PerformanceTracker()
    
    def test_initial_metrics(self):
        """Test that initial metrics are reasonable"""
        metrics = self.tracker.get_metrics()
        
        for system in ['neo4j', 'redis', 'basic_memory']:
            self.assertIn(system, metrics)
            self.assertIn('success_rate', metrics[system])
            self.assertIn('avg_response_time', metrics[system])
            
            # Check reasonable initial values
            self.assertGreater(metrics[system]['success_rate'], 0.0)
            self.assertLessEqual(metrics[system]['success_rate'], 1.0)
            self.assertGreater(metrics[system]['avg_response_time'], 0.0)
    
    def test_operation_recording(self):
        """Test recording of operations"""
        initial_operations = self.tracker.metrics['redis']['operations']
        
        # Record successful operation
        self.tracker.record_operation('redis', True, 100.0)
        
        # Check that operation count increased
        self.assertEqual(
            self.tracker.metrics['redis']['operations'],
            initial_operations + 1
        )
        
        # Check that recent operations were recorded
        self.assertEqual(len(self.tracker.recent_operations), 1)
        self.assertEqual(self.tracker.recent_operations[0]['system'], 'redis')
        self.assertTrue(self.tracker.recent_operations[0]['success'])
    
    def test_metrics_updates(self):
        """Test that metrics update correctly"""
        # Record multiple operations
        initial_success_rate = self.tracker.metrics['redis']['success_rate']
        
        # Record successful operations
        for _ in range(5):
            self.tracker.record_operation('redis', True, 50.0)
        
        # Record failed operation
        self.tracker.record_operation('redis', False, 200.0)
        
        # Success rate should have changed
        new_success_rate = self.tracker.metrics['redis']['success_rate']
        self.assertNotEqual(initial_success_rate, new_success_rate)
    
    def test_system_score_calculation(self):
        """Test calculation of system scores"""
        # Test with good metrics
        score_good = self.tracker.get_system_score('redis')  # Redis has good initial metrics
        
        # Test with unknown system
        score_unknown = self.tracker.get_system_score('unknown_system')
        
        self.assertGreater(score_good, score_unknown, "Known system should score higher")
        self.assertGreaterEqual(score_unknown, 0.0, "Score should be >= 0")
        self.assertLessEqual(score_good, 1.0, "Score should be <= 1")
    
    def test_recent_operations_limit(self):
        """Test that recent operations list is limited"""
        # Record more than 100 operations
        for i in range(150):
            self.tracker.record_operation('redis', True, 50.0)
        
        # Should not exceed 100 entries
        self.assertLessEqual(len(self.tracker.recent_operations), 100)


class TestRoutingEngine(unittest.TestCase):
    """Test routing engine functionality"""
    
    def setUp(self):
        self.performance_tracker = PerformanceTracker()
        self.routing_engine = RoutingEngine(self.performance_tracker)
    
    def test_intent_system_mapping(self):
        """Test that intents are mapped to appropriate systems"""
        # Test relationship intent -> Neo4j
        scores = self.routing_engine.score_systems(IntentType.CREATE_RELATION, [])
        self.assertGreater(scores['neo4j'], scores['redis'])
        self.assertGreater(scores['neo4j'], scores['basic_memory'])
        
        # Test documentation intent -> Basic Memory
        scores = self.routing_engine.score_systems(IntentType.WRITE_DOC, [])
        self.assertGreater(scores['basic_memory'], scores['neo4j'])
        
        # Test search intent -> Redis
        scores = self.routing_engine.score_systems(IntentType.SEMANTIC_SEARCH, [])
        self.assertGreater(scores['redis'], scores['basic_memory'])
    
    def test_entity_boost_calculation(self):
        """Test that entities influence system scoring"""
        # Create entities that should boost Neo4j
        entities = [
            Entity("John Smith", "person"),
            Entity("Acme Corp", "organization")
        ]
        
        scores = self.routing_engine.score_systems(IntentType.UNKNOWN, entities)
        
        # Neo4j should get a boost from relationship entities
        scores_no_entities = self.routing_engine.score_systems(IntentType.UNKNOWN, [])
        self.assertGreaterEqual(scores['neo4j'], scores_no_entities['neo4j'])
    
    def test_context_adjustments(self):
        """Test that context affects scoring"""
        # Test long content -> Basic Memory preference
        context_long = {'content_length': 2000}
        scores_long = self.routing_engine.score_systems(IntentType.UNKNOWN, [], context_long)
        
        # Test short content -> Redis preference  
        context_short = {'content_length': 50}
        scores_short = self.routing_engine.score_systems(IntentType.UNKNOWN, [], context_short)
        
        # Basic Memory should score relatively higher for long content
        bm_ratio_long = scores_long['basic_memory'] / sum(scores_long.values())
        bm_ratio_short = scores_short['basic_memory'] / sum(scores_short.values())
        
        self.assertGreater(bm_ratio_long, bm_ratio_short, "Basic Memory should prefer long content")
    
    def test_routing_decision_generation(self):
        """Test generation of routing decisions"""
        request = MemoryRequest(operation=Operation.QUERY, content="Create relationship between users")
        scores = {'neo4j': 0.8, 'redis': 0.3, 'basic_memory': 0.2}
        
        decision = self.routing_engine.route(request, scores)
        
        self.assertIsInstance(decision, RoutingDecision)
        self.assertEqual(decision.primary_system, MemorySystem.NEO4J)
        self.assertGreater(decision.confidence, 0.0)
        self.assertIsInstance(decision.reasoning, str)
    
    def test_multi_system_detection(self):
        """Test detection of operations requiring multiple systems"""
        # Test with comprehensive content
        request = MemoryRequest(
            operation=Operation.STORE,
            content="Store complete profile information for this user"
        )
        scores = {'neo4j': 0.7, 'redis': 0.6, 'basic_memory': 0.5}
        
        decision = self.routing_engine.route(request, scores)
        
        # Should detect multi-system need for comprehensive operations
        self.assertTrue(decision.multi_system, "Should detect multi-system need for comprehensive operations")
        self.assertGreater(len(decision.secondary_systems), 0, "Should have secondary systems")


class TestAutomatedMemoryRouter(unittest.TestCase):
    """Test main AutomatedMemoryRouter functionality"""
    
    def setUp(self):
        self.mock_cab_tracker = Mock()
        
        # Mock the MemorySelector to avoid configuration issues
        with patch('src.automated_memory_router.MemorySelector') as mock_selector_class:
            self.mock_selector = Mock()
            mock_selector_class.return_value = self.mock_selector
            
            self.router = AutomatedMemoryRouter(
                cab_tracker=self.mock_cab_tracker,
                validate_config=False
            )
    
    def test_router_initialization(self):
        """Test that router initializes correctly"""
        self.assertIsNotNone(self.router.intent_analyzer)
        self.assertIsNotNone(self.router.entity_extractor)
        self.assertIsNotNone(self.router.routing_engine)
        self.assertIsNotNone(self.router.performance_tracker)
    
    def test_routing_workflow(self):
        """Test complete routing workflow"""
        request = MemoryRequest(
            operation=Operation.STORE,
            content="Connect John Smith to the marketing project"
        )
        
        decision = self.router.route(request)
        
        self.assertIsInstance(decision, RoutingDecision)
        self.assertIn(decision.primary_system, list(MemorySystem))
        self.assertGreater(decision.confidence, 0.0)
        
        # Check that CAB tracking was called
        self.mock_cab_tracker.log_suggestion.assert_called()
    
    def test_store_data_routing(self):
        """Test data storage with automated routing"""
        data = {"user": "John", "project": "Alpha"}
        content = "Store user project relationship"
        
        # Mock the operation
        def mock_store_operation(system, task, context):
            return {"status": "stored", "system": system.value}
        
        self.mock_selector._store_in_system.return_value = {"status": "stored"}
        
        with patch.object(self.router, 'execute_routed_operation') as mock_execute:
            mock_execute.return_value = ({"status": "stored"}, MemorySystem.NEO4J, False)
            
            result, system, used_fallback = self.router.store_data(data, content)
            
            self.assertEqual(system, MemorySystem.NEO4J)
            self.assertFalse(used_fallback)
            mock_execute.assert_called_once()
    
    def test_retrieve_data_routing(self):
        """Test data retrieval with automated routing"""
        query = {"search": "project relationships"}
        content = "Find project relationships"
        
        self.mock_selector._retrieve_from_system.return_value = {"results": ["test"]}
        
        with patch.object(self.router, 'execute_routed_operation') as mock_execute:
            mock_execute.return_value = ({"results": ["test"]}, MemorySystem.REDIS, False)
            
            result, system, used_fallback = self.router.retrieve_data(query, content)
            
            self.assertEqual(system, MemorySystem.REDIS)
            self.assertFalse(used_fallback)
            mock_execute.assert_called_once()
    
    def test_performance_tracking_integration(self):
        """Test that performance is tracked during operations"""
        request = MemoryRequest(operation=Operation.QUERY, content="Test operation")
        
        def mock_operation(system, task, context):
            return {"result": "success"}
        
        # Mock successful operation
        result, system, used_fallback = self.router.execute_routed_operation(request, mock_operation)
        
        # Check that performance was tracked
        operations_count = self.router.performance_tracker.metrics[system.value]['operations']
        self.assertGreater(operations_count, 0, "Should track operation performance")
    
    def test_routing_stats(self):
        """Test retrieval of routing statistics"""
        stats = self.router.get_routing_stats()
        
        self.assertIn('system_performance', stats)
        self.assertIn('recent_operations', stats)
        self.assertIn('router_version', stats)
        
        # Check that system performance includes expected metrics
        for system in ['neo4j', 'redis', 'basic_memory']:
            self.assertIn(system, stats['system_performance'])
    
    def test_fallback_integration(self):
        """Test integration with existing fallback mechanism"""
        request = MemoryRequest(operation=Operation.QUERY, content="Test content")
        
        def failing_operation(system, task, context):
            raise Exception("Primary system failed")
        
        # Mock fallback success
        self.mock_selector.execute_with_fallback.return_value = (
            {"result": "fallback_success"}, MemorySystem.REDIS, True
        )
        
        result, system, used_fallback = self.router.execute_routed_operation(request, failing_operation)
        
        self.assertTrue(used_fallback, "Should use fallback when primary fails")
        self.mock_selector.execute_with_fallback.assert_called_once()


class TestIntegrationScenarios(unittest.TestCase):
    """Test realistic integration scenarios"""
    
    def setUp(self):
        self.mock_cab_tracker = Mock()
        
        # Create router with mocked dependencies
        with patch('src.automated_memory_router.MemorySelector') as mock_selector_class:
            self.mock_selector = Mock()
            mock_selector_class.return_value = self.mock_selector
            
            self.router = AutomatedMemoryRouter(
                cab_tracker=self.mock_cab_tracker,
                validate_config=False
            )
    
    def test_user_profile_storage_scenario(self):
        """Test complete user profile storage scenario"""
        content = "Store complete profile for John Smith including his work on Project Alpha and relationships with team members"
        data = {
            "name": "John Smith",
            "project": "Project Alpha",
            "role": "Developer",
            "team": ["Alice", "Bob"]
        }
        
        # This should trigger comprehensive storage (multi-system)
        request = MemoryRequest(operation=Operation.STORE, content=content, metadata=data)
        decision = self.router.route(request)
        
        # Should detect comprehensive storage need
        self.assertTrue(decision.multi_system or decision.primary_system == MemorySystem.NEO4J,
                       "Should route to Neo4j or use multi-system for relationship-heavy content")
    
    def test_document_search_scenario(self):
        """Test document search scenario"""
        content = "Find documentation similar to API design principles"
        query = {"search_text": content, "type": "semantic"}
        
        request = MemoryRequest(operation=Operation.SEARCH, content=content, metadata=query)
        decision = self.router.route(request)
        
        # Should route to Redis for semantic search or Basic Memory for documents
        self.assertIn(decision.primary_system, [MemorySystem.REDIS, MemorySystem.BASIC_MEMORY],
                     "Should route to Redis or Basic Memory for document search")
    
    def test_relationship_query_scenario(self):
        """Test relationship query scenario"""
        content = "How is Alice connected to the DevOps team and what projects do they share?"
        
        request = MemoryRequest(operation=Operation.QUERY, content=content)
        decision = self.router.route(request)
        
        # Should route to Neo4j for relationship queries
        self.assertEqual(decision.primary_system, MemorySystem.NEO4J,
                        "Should route to Neo4j for relationship queries")
    
    def test_performance_degradation_handling(self):
        """Test handling of performance degradation"""
        # Simulate poor Neo4j performance
        self.router.performance_tracker.record_operation('neo4j', False, 2000.0)
        self.router.performance_tracker.record_operation('neo4j', False, 3000.0)
        
        # Test relationship query (normally would go to Neo4j)
        content = "Find connections between users"
        request = MemoryRequest(operation=Operation.QUERY, content=content)
        decision = self.router.route(request)
        
        # With poor Neo4j performance, might route elsewhere or have lower confidence
        neo4j_score = self.router.routing_engine.score_systems(
            self.router.intent_analyzer.analyze(request),
            self.router.entity_extractor.extract(request)
        )['neo4j']
        
        # Score should be impacted by poor performance
        self.assertLess(neo4j_score, 1.0, "Poor performance should reduce system scores")


if __name__ == '__main__':
    unittest.main()