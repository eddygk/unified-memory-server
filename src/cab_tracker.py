"""
CAB (Continuous Adaptive Baseline) Tracking System
Monitors system performance and logs suggestions for improvements
"""
import os
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Any
import logging

logger = logging.getLogger(__name__)


class CABTracker:
    """Tracks system performance and logs improvement suggestions"""
    
    def __init__(self, cab_file_path: str = None):
        self.cab_file_path = Path(cab_file_path or os.path.expanduser("~/projects/cab_suggestions.md"))
        self.session_id = self._generate_session_id()
        self.initialized = False
        
    def _generate_session_id(self) -> str:
        """Generate unique session identifier"""
        return f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    def initialize_session(self, user: str = "Unknown", primary_ai: str = "Claude") -> None:
        """Initialize CAB tracking session"""
        self.cab_file_path.parent.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Create or append to CAB file
        with open(self.cab_file_path, 'a') as f:
            f.write(f"\n\n## CAB Session - {timestamp}\n")
            f.write(f"Session ID: {self.session_id}\n")
            f.write(f"User: {user}\n")
            f.write(f"Primary AI: {primary_ai}\n")
            f.write("### Suggested Improvements:\n\n")
        
        self.initialized = True
        logger.info(f"CAB tracking session initialized: {self.session_id}")
    
    def log_suggestion(
        self,
        suggestion_type: str,
        description: str,
        severity: str = 'MEDIUM',
        context: Optional[str] = None,
        metrics: Optional[Dict[str, Any]] = None
    ) -> None:
        """Log CAB suggestion in real-time"""
        if not self.initialized:
            self.initialize_session()
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Format suggestion entry
        suggestion_entry = f"**[{severity}]** {suggestion_type} (at {timestamp})\n"
        suggestion_entry += f"- **Description**: {description}\n"
        
        if context:
            suggestion_entry += f"- **Context**: {context}\n"
        
        if metrics:
            suggestion_entry += f"- **Metrics**: {json.dumps(metrics, indent=2)}\n"
        
        suggestion_entry += "\n"
        
        # Write to CAB file
        with open(self.cab_file_path, 'a') as f:
            f.write(suggestion_entry)
        
        logger.info(f"CAB suggestion logged: {suggestion_type} - {description}")
    
    def log_memory_operation(
        self,
        operation: str,
        system: str,
        success: bool,
        duration_ms: float,
        fallback_used: bool = False
    ) -> None:
        """Log memory system operation metrics"""
        if not success and not fallback_used:
            self.log_suggestion(
                "Memory System Failure",
                f"{system} failed during {operation} operation",
                severity='HIGH',
                context=f"Operation took {duration_ms}ms before failing",
                metrics={"duration_ms": duration_ms, "system": system}
            )
        elif duration_ms > 1000:  # More than 1 second
            self.log_suggestion(
                "Performance Issue",
                f"Slow {operation} operation in {system}",
                severity='MEDIUM',
                context=f"Consider optimizing query or adding indexes",
                metrics={"duration_ms": duration_ms, "system": system}
            )
    
    def log_data_inconsistency(
        self,
        entity: str,
        systems: list,
        inconsistency_type: str
    ) -> None:
        """Log data inconsistency between systems"""
        self.log_suggestion(
            "Data Inconsistency",
            f"{inconsistency_type} for entity '{entity}' across systems",
            severity='HIGH',
            context=f"Systems involved: {', '.join(systems)}. Implement sync mechanism.",
            metrics={"entity": entity, "systems": systems}
        )
    
    def log_missing_implementation(
        self,
        feature: str,
        impact: str
    ) -> None:
        """Log missing implementation"""
        self.log_suggestion(
            "Missing Implementation",
            f"{feature} not implemented",
            severity='MEDIUM',
            context=f"Impact: {impact}"
        )
    
    def get_session_summary(self) -> Dict[str, Any]:
        """Get summary of current session suggestions"""
        if not self.cab_file_path.exists():
            return {"session_id": self.session_id, "suggestions": [], "total": 0}
        
        # Parse suggestions from file
        suggestions = []
        with open(self.cab_file_path, 'r') as f:
            content = f.read()
            # Simple parsing - in production would use proper parser
            lines = content.split('\n')
            for line in lines:
                if line.startswith('**['):
                    suggestions.append(line)
        
        return {
            "session_id": self.session_id,
            "suggestions": suggestions,
            "total": len(suggestions)
        }


# Singleton instance
_cab_tracker = None


def get_cab_tracker() -> CABTracker:
    """Get singleton CAB tracker instance"""
    global _cab_tracker
    if _cab_tracker is None:
        _cab_tracker = CABTracker()
    return _cab_tracker
