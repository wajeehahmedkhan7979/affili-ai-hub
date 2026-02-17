"""
Adaptive confidence threshold service.

Dynamically adjusts confidence thresholds based on:
- Program success rate
- CAPTCHA frequency
- Failure patterns

Ensures safe, controlled autonomy scaling.
"""

from sqlalchemy.orm import Session  
from sqlalchemy import func
from app.core.time import utcnow
from app.models.task import Task, TaskStatus
from app.models.agent import Agent
from app.models.metrics import TaskMetrics
from app.core.logging import logger
from typing import Dict, Any
from datetime import datetime, timedelta
import uuid


class AdaptiveThreshold:
    """
    Calculate adaptive confidence thresholds.
    
    Base threshold = 0.7
    Adjustments based on program reliability + risk factors.
    """
    
    BASE_THRESHOLD = 0.7
    MIN_THRESHOLD = 0.5
    MAX_THRESHOLD = 0.95
    
    def calculate_threshold(
        self,
        db: Session,
        tenant_id: uuid.UUID,
        program_id: Optional[uuid.UUID],
        task_type: str
    ) -> Dict[str, Any]:
        """
        Calculate adaptive threshold for this program/task.
        
        Returns:
            {
                "effective_threshold": float,
                "base_threshold": float,
                "adjustments": {
                    "success_rate_bonus": float,
                    "captcha_penalty": float,
                    "failure_penalty": float
                },
                "reasoning": str
            }
        """
        adjustments = {
            "success_rate_bonus": 0.0,
            "captcha_penalty": 0.0,
            "failure_penalty": 0.0
        }
        
        # Calculate program success rate (last 30 days)
        success_rate = self._get_program_success_rate(
            db, tenant_id, program_id, days=30
        )
        
        # Success rate bonus: -0.1 if >90% success, 0 otherwise
        if success_rate > 0.9:
            adjustments["success_rate_bonus"] = -0.05
        elif success_rate < 0.5:
            adjustments["failure_penalty"] = +0.1
        
        # CAPTCHA frequency penalty
        captcha_frequency = self._get_captcha_frequency(
            db, tenant_id, program_id, days=30
        )
        
        if captcha_frequency > 0.2:  # >20% of tasks hit CAPTCHA
            adjustments["captcha_penalty"] = +0.1
        
        # Calculate effective threshold
        effective = self.BASE_THRESHOLD + sum(adjustments.values())
        
        # Clamp to safe range
        effective = max(self.MIN_THRESHOLD, min(self.MAX_THRESHOLD, effective))
        
        reasoning = self._build_reasoning(success_rate, captcha_frequency, adjustments, effective)
        
        logger.info(f"Adaptive threshold for {task_type}: {effective:.2f} (base: {self.BASE_THRESHOLD})")
        
        return {
            "effective_threshold": round(effective, 2),
            "base_threshold": self.BASE_THRESHOLD,
            "adjustments": adjustments,
            "success_rate": round(success_rate, 3),
            "captcha_frequency": round(captcha_frequency, 3),
            "reasoning": reasoning
        }
    
    def _get_program_success_rate(
        self,
        db: Session,
        tenant_id: uuid.UUID,
        program_id: Optional[uuid.UUID],
        days: int
    ) -> float:
        """Calculate program success rate."""
        since = utcnow() - timedelta(days=days)
        
        query = db.query(TaskMetrics).filter(
            TaskMetrics.tenant_id == tenant_id,
            TaskMetrics.completed_at >= since
        )
        
        if program_id:
            # Filter by program (via task payload - approximation)
            # In production, would have explicit program_id column
            pass
        
        total = query.count()
        
        if total == 0:
            return 0.5  # Neutral for new programs
        
        successful = query.filter(
            TaskMetrics.status == TaskStatus.COMPLETED
        ).count()
        
        return successful / total
    
    def _get_captcha_frequency(
        self,
        db: Session,
        tenant_id: uuid.UUID,
        program_id: Optional[uuid.UUID],
        days: int
    ) -> float:
        """Calculate CAPTCHA encounter frequency."""
        since = utcnow() - timedelta(days=days)
        
        query = db.query(Task).filter(
            Task.tenant_id == tenant_id,
            Task.created_at >= since
        )
        
        total = query.count()
        
        if total == 0:
            return 0.0
        
        captcha_count = query.filter(
            Task.status == TaskStatus.PAUSED_FOR_CAPTCHA
        ).count()
        
        return captcha_count / total
    
    def _build_reasoning(
        self,
        success_rate: float,
        captcha_frequency: float,
        adjustments: Dict[str, float],
        effective: float
    ) -> str:
        """Build human-readable reasoning."""
        reasons = []
        
        if success_rate > 0.9:
            reasons.append(f"High success rate ({success_rate:.1%}) → lower threshold")
        elif success_rate < 0.5:
            reasons.append(f"Low success rate ({success_rate:.1%}) → raise threshold")
        
        if captcha_frequency > 0.2:
            reasons.append(f"High CAPTCHA rate ({captcha_frequency:.1%}) → raise threshold")
        
        if not reasons:
            reasons.append("Normal operating conditions")
        
        return f"Effective threshold {effective:.2f}: " + ", ".join(reasons)


# Singleton
adaptive_threshold = AdaptiveThreshold()