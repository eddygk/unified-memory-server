"""
Startup Sequence Handler for AI Directives
Implements the multi-system user identification and CAB initialization sequence
for universal AI assistant integration
"""
import logging
import os
from typing import Dict, Optional, Any, Tuple
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)


class StartupSequenceHandler:
    """
    Handles the AI directive startup sequence:
    
    Step 0: Initialize CAB Tracking
    - Create CAB suggestions file at specified location
    - Log session initialization in Redis Memory
    - Track all system improvements and issues

    Step 1: Multi-System User Identification
    1. Primary: Neo4j natural language query for user profile
    2. Fallback 1: Redis Memory search in "user_profile" namespace
    3. Fallback 2: Basic Memory search for "user identity" notes
    4. Action: Sync user data across all systems if found in only one
    """
    
    def __init__(self, memory_selector, cab_tracker, mcp_router):
        """
        Initialize startup sequence handler
        
        Args:
            memory_selector: MemorySelector instance for system operations
            cab_tracker: CABTracker instance for logging
            mcp_router: MCPToolRouter instance for tool routing
        """
        self.memory_selector = memory_selector
        self.cab_tracker = cab_tracker
        self.mcp_router = mcp_router
        self.startup_completed = False
        self.user_profile_data = None
        
    def execute_startup_sequence(self, user: str = "Unknown", primary_ai: str = "Assistant") -> Dict[str, Any]:
        """
        Execute the complete startup sequence as defined in AI directives
        
        Returns:
            Dict containing startup results and user profile data
        """
        startup_results = {
            "step_0_completed": False,
            "step_1_completed": False,
            "user_profile_found": False,
            "user_profile_source": None,
            "sync_performed": False,
            "errors": [],
            "user_data": None
        }
        
        try:
            # Step 0: Initialize CAB Tracking
            startup_results["step_0_completed"] = self._execute_step_0(user, primary_ai)
            
            # Step 1: Multi-System User Identification
            user_profile_result = self._execute_step_1(user)
            startup_results.update(user_profile_result)
            startup_results["step_1_completed"] = True
            
            self.startup_completed = True
            
            if self.cab_tracker:
                self.cab_tracker.log_suggestion(
                    "Startup Sequence Complete",
                    f"AI directive startup sequence completed successfully for user: {user}",
                    severity='LOW',
                    context=f"Primary AI: {primary_ai}",
                    metrics=startup_results
                )
                
        except Exception as e:
            error_msg = f"Startup sequence failed: {str(e)}"
            startup_results["errors"].append(error_msg)
            logger.error(error_msg)
            
            if self.cab_tracker:
                self.cab_tracker.log_suggestion(
                    "Startup Sequence Failure",
                    error_msg,
                    severity='HIGH',
                    context="AI directive startup sequence",
                    metrics={"error": str(e)}
                )
        
        return startup_results
    
    def _execute_step_0(self, user: str, primary_ai: str) -> bool:
        """
        Step 0: Initialize CAB Tracking
        - Create CAB suggestions file at specified location
        - Log session initialization in Redis Memory
        - Track all system improvements and issues
        """
        try:
            # Initialize CAB tracking with session
            if not self.cab_tracker.initialized:
                self.cab_tracker.initialize_session(user, primary_ai)
            
            # Log session initialization in Redis Memory if available
            self._log_session_in_redis(user, primary_ai)
            
            logger.info(f"Step 0 completed: CAB tracking initialized for {user}")
            return True
            
        except Exception as e:
            logger.error(f"Step 0 failed: {str(e)}")
            return False
    
    def _execute_step_1(self, user: str) -> Dict[str, Any]:
        """
        Step 1: Multi-System User Identification
        1. Primary: Neo4j natural language query for user profile
        2. Fallback 1: Redis Memory search in "user_profile" namespace
        3. Fallback 2: Basic Memory search for "user identity" notes
        4. Action: Sync user data across all systems if found in only one
        """
        result = {
            "user_profile_found": False,
            "user_profile_source": None,
            "sync_performed": False,
            "user_data": None,
            "systems_checked": []
        }
        
        # 1. Primary: Neo4j natural language query for user profile
        neo4j_data = self._search_user_in_neo4j(user)
        result["systems_checked"].append("neo4j")
        
        if neo4j_data:
            result["user_profile_found"] = True
            result["user_profile_source"] = "neo4j"
            result["user_data"] = neo4j_data
            self.user_profile_data = neo4j_data
            logger.info("User profile found in Neo4j (primary system)")
            return result
        
        # 2. Fallback 1: Redis Memory search in "user_profile" namespace
        redis_data = self._search_user_in_redis(user)
        result["systems_checked"].append("redis")
        
        if redis_data:
            result["user_profile_found"] = True
            result["user_profile_source"] = "redis"
            result["user_data"] = redis_data
            self.user_profile_data = redis_data
            
            # Sync to other systems since found in only one
            sync_success = self._sync_user_data_across_systems(redis_data, source="redis")
            result["sync_performed"] = sync_success
            
            logger.info("User profile found in Redis (fallback 1), syncing to other systems")
            return result
        
        # 3. Fallback 2: Basic Memory search for "user identity" notes
        basic_data = self._search_user_in_basic_memory(user)
        result["systems_checked"].append("basic_memory")
        
        if basic_data:
            result["user_profile_found"] = True
            result["user_profile_source"] = "basic_memory"
            result["user_data"] = basic_data
            self.user_profile_data = basic_data
            
            # Sync to other systems since found in only one
            sync_success = self._sync_user_data_across_systems(basic_data, source="basic_memory")
            result["sync_performed"] = sync_success
            
            logger.info("User profile found in Basic Memory (fallback 2), syncing to other systems")
            return result
        
        # No user profile found in any system
        logger.warning(f"No user profile found for {user} in any system")
        
        if self.cab_tracker:
            self.cab_tracker.log_suggestion(
                "User Profile Not Found",
                f"No user profile found for {user} in any memory system during startup",
                severity='MEDIUM',
                context="Multi-system user identification",
                metrics={"systems_checked": result["systems_checked"]}
            )
        
        return result
    
    def _search_user_in_neo4j(self, user: str) -> Optional[Dict[str, Any]]:
        """Search for user profile in Neo4j using natural language query"""
        try:
            # Use Neo4j cypher query for user profile search
            query = f"""
            MATCH (u:User {{name: '{user}'}})
            OPTIONAL MATCH (u)-[r]->(p:Profile)
            RETURN u, collect(p) as profiles, collect(r) as relations
            """
            
            # This would use the actual neo4j client - placeholder for now
            # In real implementation, would call the MCP tool:
            # local__neo4j-cypher__read_neo4j_cypher
            
            # Placeholder result - in real implementation would parse actual Neo4j response
            return None  # No user found
            
        except Exception as e:
            logger.error(f"Error searching user in Neo4j: {str(e)}")
            if self.cab_tracker:
                self.cab_tracker.log_suggestion(
                    "Neo4j User Search Error",
                    f"Failed to search for user {user} in Neo4j: {str(e)}",
                    severity='MEDIUM',
                    context="User identification startup sequence"
                )
            return None
    
    def _search_user_in_redis(self, user: str) -> Optional[Dict[str, Any]]:
        """Search for user profile in Redis Memory in user_profile namespace"""
        try:
            # Use Redis Memory search in user_profile namespace
            # This would use the MCP tool: local__redis-memory-server__search_long_term_memory
            
            search_payload = {
                "text": f"user profile {user}",
                "namespace": {"eq": "user_profile"},
                "limit": 10
            }
            
            # Placeholder result - in real implementation would call actual Redis search
            return None  # No user found
            
        except Exception as e:
            logger.error(f"Error searching user in Redis: {str(e)}")
            if self.cab_tracker:
                self.cab_tracker.log_suggestion(
                    "Redis User Search Error",
                    f"Failed to search for user {user} in Redis: {str(e)}",
                    severity='MEDIUM',
                    context="User identification startup sequence"
                )
            return None
    
    def _search_user_in_basic_memory(self, user: str) -> Optional[Dict[str, Any]]:
        """Search for user identity notes in Basic Memory"""
        try:
            # Use Basic Memory search for user identity notes
            # This would use the MCP tool: local__basic-memory__search_notes
            
            search_query = f"user identity {user}"
            
            # Placeholder result - in real implementation would call actual Basic Memory search
            return None  # No user found
            
        except Exception as e:
            logger.error(f"Error searching user in Basic Memory: {str(e)}")
            if self.cab_tracker:
                self.cab_tracker.log_suggestion(
                    "Basic Memory User Search Error",
                    f"Failed to search for user {user} in Basic Memory: {str(e)}",
                    severity='MEDIUM',
                    context="User identification startup sequence"
                )
            return None
    
    def _sync_user_data_across_systems(self, user_data: Dict[str, Any], source: str) -> bool:
        """
        Sync user data across all systems when found in only one
        Implements the cross-system integration rules for optimal data consistency
        """
        try:
            sync_success = True
            
            # Sync to systems that don't have the data
            if source != "neo4j":
                neo4j_sync = self._sync_user_to_neo4j(user_data)
                sync_success = sync_success and neo4j_sync
            
            if source != "redis":
                redis_sync = self._sync_user_to_redis(user_data)
                sync_success = sync_success and redis_sync
            
            if source != "basic_memory":
                basic_sync = self._sync_user_to_basic_memory(user_data)
                sync_success = sync_success and basic_sync
            
            if sync_success and self.cab_tracker:
                self.cab_tracker.log_suggestion(
                    "User Data Sync Success",
                    f"Successfully synced user data from {source} to all other systems",
                    severity='LOW',
                    context="Cross-system user data synchronization",
                    metrics={"source_system": source}
                )
            
            return sync_success
            
        except Exception as e:
            logger.error(f"Error syncing user data: {str(e)}")
            if self.cab_tracker:
                self.cab_tracker.log_suggestion(
                    "User Data Sync Error",
                    f"Failed to sync user data from {source}: {str(e)}",
                    severity='HIGH',
                    context="Cross-system user data synchronization"
                )
            return False
    
    def _sync_user_to_neo4j(self, user_data: Dict[str, Any]) -> bool:
        """Sync user data to Neo4j system"""
        try:
            # Would use: local__neo4j-memory__create_entities
            # and local__neo4j-memory__add_observations
            logger.info("Syncing user data to Neo4j (placeholder)")
            return True  # Placeholder
        except Exception as e:
            logger.error(f"Failed to sync user to Neo4j: {str(e)}")
            return False
    
    def _sync_user_to_redis(self, user_data: Dict[str, Any]) -> bool:
        """Sync user data to Redis system"""
        try:
            # Would use: local__redis-memory-server__create_long_term_memories
            logger.info("Syncing user data to Redis (placeholder)")
            return True  # Placeholder
        except Exception as e:
            logger.error(f"Failed to sync user to Redis: {str(e)}")
            return False
    
    def _sync_user_to_basic_memory(self, user_data: Dict[str, Any]) -> bool:
        """Sync user data to Basic Memory system"""
        try:
            # Would use: local__basic-memory__write_note
            logger.info("Syncing user data to Basic Memory (placeholder)")
            return True  # Placeholder
        except Exception as e:
            logger.error(f"Failed to sync user to Basic Memory: {str(e)}")
            return False
    
    def _log_session_in_redis(self, user: str, primary_ai: str) -> None:
        """Log session initialization in Redis Memory"""
        try:
            # Would use: local__redis-memory-server__create_long_term_memories
            session_data = {
                "text": f"Session initialized for user {user} with primary AI {primary_ai}",
                "namespace": "session_tracking",
                "topics": ["session", "startup", "initialization"],
                "session_id": self.cab_tracker.session_id if self.cab_tracker else None
            }
            
            logger.info(f"Session logged in Redis for {user} (placeholder)")
            
        except Exception as e:
            logger.error(f"Failed to log session in Redis: {str(e)}")
    
    def get_user_profile(self) -> Optional[Dict[str, Any]]:
        """Get the user profile data found during startup"""
        return self.user_profile_data
    
    def is_startup_completed(self) -> bool:
        """Check if startup sequence has been completed"""
        return self.startup_completed
    
    def force_user_identification(self, user: str) -> Dict[str, Any]:
        """
        Force user identification process outside of startup
        Useful for re-running user identification after startup
        """
        logger.info(f"Forcing user identification for {user}")
        return self._execute_step_1(user)