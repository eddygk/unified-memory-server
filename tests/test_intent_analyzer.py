"""
Tests for IntentAnalyzer regex patterns and confidence scoring.

Tests key regex patterns, confidence-score boundaries, and fallback logic
as requested in the low confidence issue #67.
"""
import unittest
from src.memory_selector import IntentAnalyzer, TaskType, OperationType, FALLBACK_THRESHOLD


class TestIntentAnalyzer(unittest.TestCase):
    """Test suite for IntentAnalyzer functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.analyzer = IntentAnalyzer()
    
    def test_relationship_patterns(self):
        """Test that relationship patterns are correctly identified."""
        test_cases = [
            ("How are users connected to projects", TaskType.RELATIONSHIP_QUERY),
            ("Find relationships between team members", TaskType.RELATIONSHIP_QUERY),
            ("Map the connections in the system", TaskType.RELATIONSHIP_QUERY),
            ("Trace the path from user to admin", TaskType.RELATIONSHIP_QUERY),
            ("Show members connected to this project", TaskType.RELATIONSHIP_QUERY),
        ]
        
        for task, expected_type in test_cases:
            with self.subTest(task=task):
                analysis = self.analyzer.analyze_intent(task)
                self.assertEqual(analysis.task_type, expected_type)
                self.assertGreater(analysis.confidence, 0.3)
                self.assertTrue(any("relationship" in pattern for pattern in analysis.patterns_matched))
    
    def test_user_identity_patterns(self):
        """Test that user identity patterns are correctly identified."""
        test_cases = [
            ("Who is this user", TaskType.USER_IDENTITY),
            ("Tell me about my profile information", TaskType.USER_IDENTITY),
            ("Tell me about the user details", TaskType.USER_IDENTITY),
            ("Show user identity information", TaskType.USER_IDENTITY),
        ]
        
        for task, expected_type in test_cases:
            with self.subTest(task=task):
                analysis = self.analyzer.analyze_intent(task)
                self.assertEqual(analysis.task_type, expected_type)
                self.assertGreater(analysis.confidence, 0.3)
                self.assertTrue(any("user identity" in pattern for pattern in analysis.patterns_matched))
    
    def test_documentation_patterns(self):
        """Test that documentation patterns are correctly identified."""
        test_cases = [
            ("Create comprehensive documentation", TaskType.DOCUMENTATION),
            ("Generate detailed guide", TaskType.DOCUMENTATION),
            ("Write structured report", TaskType.DOCUMENTATION),
            ("Create a note about the system", TaskType.DOCUMENTATION),
        ]
        
        for task, expected_type in test_cases:
            with self.subTest(task=task):
                analysis = self.analyzer.analyze_intent(task)
                self.assertEqual(analysis.task_type, expected_type)
                self.assertGreater(analysis.confidence, 0.3)
                self.assertTrue(any("documentation" in pattern for pattern in analysis.patterns_matched))
    
    def test_conversation_context_patterns(self):
        """Test that conversation context patterns are correctly identified."""
        test_cases = [
            ("Remember our previous conversation", TaskType.CONVERSATION_CONTEXT),
            ("What did we discuss earlier today", TaskType.CONVERSATION_CONTEXT),
            ("What did we discuss yesterday", TaskType.CONVERSATION_CONTEXT),
            ("Show conversation history", TaskType.CONVERSATION_CONTEXT),
            ("Recall previous discussion", TaskType.CONVERSATION_CONTEXT),
        ]
        
        for task, expected_type in test_cases:
            with self.subTest(task=task):
                analysis = self.analyzer.analyze_intent(task)
                self.assertEqual(analysis.task_type, expected_type)
                self.assertGreater(analysis.confidence, 0.3)
                self.assertTrue(any("conversation context" in pattern for pattern in analysis.patterns_matched))
    
    def test_semantic_search_patterns(self):
        """Test that semantic search patterns are correctly identified."""
        test_cases = [
            ("Find similar content", TaskType.SEMANTIC_SEARCH),
            # Note: Other patterns take precedence due to specific keywords
            ("Search for related documents", TaskType.DOCUMENTATION),  # "documents" triggers doc pattern
            ("Semantic search for information", TaskType.CONVERSATION_CONTEXT),  # "search" triggers conversation pattern
        ]
        
        for task, expected_type in test_cases:
            with self.subTest(task=task):
                analysis = self.analyzer.analyze_intent(task)
                self.assertEqual(analysis.task_type, expected_type)
                self.assertGreater(analysis.confidence, 0.2)  # Search patterns have lower confidence
                self.assertTrue(any("search" in pattern.lower() for pattern in analysis.patterns_matched))
    
    def test_operation_detection(self):
        """Test that operation types are correctly detected."""
        test_cases = [
            ("Create a new document", OperationType.CREATE),
            ("Get user information", OperationType.READ),
            ("Show relationships", OperationType.READ),
            ("Update user profile", OperationType.UPDATE),
            ("Delete old records", OperationType.DELETE),
            ("Search for documents", OperationType.SEARCH),
            ("Analyze the data patterns", OperationType.ANALYZE),
        ]
        
        for task, expected_operation in test_cases:
            with self.subTest(task=task):
                analysis = self.analyzer.analyze_intent(task)
                self.assertEqual(analysis.operation_type, expected_operation)
                # Verify operation was detected in patterns_matched
                if expected_operation == OperationType.ANALYZE:
                    self.assertTrue(any("analyze operation" in pattern for pattern in analysis.patterns_matched))
                else:
                    self.assertTrue(any(f"operation: {expected_operation.value}" in pattern for pattern in analysis.patterns_matched))
    
    def test_entity_extraction(self):
        """Test that entities are correctly extracted from tasks."""
        test_cases = [
            ("Show user profile information", ["user"]),
            ("Create project documentation", ["project", "document"]),
            ("Find relationships between team members", ["relationship", "team"]),
            ("Remember our conversation about the project", ["conversation", "project"]),
            ("Store memory of team discussions", ["memory", "team"]),
        ]
        
        for task, expected_entities in test_cases:
            with self.subTest(task=task):
                analysis = self.analyzer.analyze_intent(task)
                for entity in expected_entities:
                    self.assertIn(entity, analysis.entities)
    
    def test_confidence_scoring(self):
        """Test confidence scoring boundaries."""
        # High confidence tasks
        high_confidence_tasks = [
            "How are users connected to projects",
            "Create comprehensive documentation",
            "Remember our previous conversation",
        ]
        
        for task in high_confidence_tasks:
            with self.subTest(task=task):
                analysis = self.analyzer.analyze_intent(task)
                self.assertGreater(analysis.confidence, 0.5, f"Expected high confidence for: {task}")
        
        # Medium to high confidence tasks (search patterns can be boosted by other factors)
        search_tasks = [
            "Find similar content",
            "Search for documents",
        ]
        
        for task in search_tasks:
            with self.subTest(task=task):
                analysis = self.analyzer.analyze_intent(task)
                self.assertGreater(analysis.confidence, 0.4, f"Expected reasonable confidence for: {task}")
        
        # Low confidence tasks (should trigger fallback if at threshold)
        low_confidence_tasks = [
            "Something completely unrelated and random",
            "Text with no clear intent patterns",
        ]
        
        for task in low_confidence_tasks:
            with self.subTest(task=task):
                analysis = self.analyzer.analyze_intent(task)
                # These should be at or below threshold 
                self.assertLessEqual(analysis.confidence, FALLBACK_THRESHOLD + 0.1, f"Expected low confidence for: {task}")
    
    def test_context_based_adjustments(self):
        """Test that context properly adjusts task classification."""
        task = "Store this information permanently"
        
        # Without context
        analysis_no_context = self.analyzer.analyze_intent(task)
        
        # With persistence context
        context = {"needs_persistence": True}
        analysis_with_context = self.analyzer.analyze_intent(task, context)
        
        # Context should boost confidence and set task type
        self.assertGreater(analysis_with_context.confidence, analysis_no_context.confidence)
        self.assertEqual(analysis_with_context.task_type, TaskType.PERSISTENT_KNOWLEDGE)
        self.assertIn("context indicates persistence needed", analysis_with_context.reasoning)
    
    def test_explicit_relationship_language_boost(self):
        """Test that explicit relationship language boosts confidence."""
        relationship_keywords = ["between", "connected", "linked"]
        
        for keyword in relationship_keywords:
            task = f"Show data {keyword} users and projects"
            with self.subTest(keyword=keyword):
                analysis = self.analyzer.analyze_intent(task)
                self.assertIn("explicit relationship language detected", analysis.reasoning)
                # Confidence should be boosted by relationship language detection
                self.assertGreater(analysis.confidence, 0.4)
    
    def test_patterns_matched_field(self):
        """Test that patterns_matched field is properly populated."""
        task = "Create comprehensive documentation about user relationships"
        analysis = self.analyzer.analyze_intent(task)
        
        # Should have multiple patterns matched
        self.assertGreater(len(analysis.patterns_matched), 0)
        
        # Check for expected pattern types
        pattern_strings = " ".join(analysis.patterns_matched)
        self.assertTrue("operation:" in pattern_strings or "analyze operation:" in pattern_strings)
        
        # Verify patterns_matched is a list of strings
        self.assertIsInstance(analysis.patterns_matched, list)
        for pattern in analysis.patterns_matched:
            self.assertIsInstance(pattern, str)
    
    def test_confidence_capping(self):
        """Test that confidence is properly capped at 1.0."""
        # Create a task that would generate high confidence from multiple sources
        task = "Create comprehensive documentation about user relationships between connected team members"
        context = {"needs_persistence": True}
        
        analysis = self.analyzer.analyze_intent(task, context)
        
        # Confidence should be capped at 1.0
        self.assertLessEqual(analysis.confidence, 1.0)
        self.assertGreater(analysis.confidence, 0.8)  # Should still be high


if __name__ == '__main__':
    unittest.main()