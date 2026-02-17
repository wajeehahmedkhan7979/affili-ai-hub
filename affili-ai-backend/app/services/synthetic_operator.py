"""
Synthetic Operator Service.
Phase 26.4: Continuous Production Certification

Simulates a real user lifecycle to ensure core system surfaces are healthy.
"""
import asyncio
import logging
import time
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.models.metrics import SyntheticAudit
from app.models.tenant import Tenant
from app.models.user import User, UserRole
from app.services.auth_service import get_password_hash, create_access_token
from app.core.time import utcnow
from app.db.uuid_type import UUID

logger = logging.getLogger(__name__)

class SyntheticOperator:
    """
    Executes end-to-end certification runs in the background.
    Targets a dedicated 'Synthetic' tenant to avoid polluting real data.
    """
    
    SYNTHETIC_EMAIL = "synthetic_op@example.com"
    SYNTHETIC_TENANT = "Synthetic Certification Tenant"
    
    def __init__(self):
        self._is_running = False

    async def run_certification(self, db: Optional[Session] = None):
        """High-level runner for the certification cycle."""
        start_time = time.perf_counter()
        results = {
            "auth": "PENDING",
            "task_flow": "PENDING",
            "broadcasting": "PENDING",
            "errors": []
        }
        
        # Use provided session or create new one
        created_locally = False
        if db is None:
            db = SessionLocal()
            created_locally = True
            
        try:
            # 1. Setup / Connect Synthetic User
            user = await self._ensure_synthetic_user(db)
            if not user:
                results["auth"] = "FAILED"
                return self._store_result(db, "DOWN", results, start_time)
            
            results["auth"] = "UP"
            
            # 2. Check Task Flow
            task_healthy = await self._check_task_flow(db, user)
            results["task_flow"] = "UP" if task_healthy else "DOWN"
            
            # 3. Check Broadcasting (Redis Path)
            broadcasting_healthy = await self._check_broadcasting()
            results["broadcasting"] = "UP" if broadcasting_healthy else "DOWN"
            
            # Final Status
            status = "UP"
            if any(v == "DOWN" for k, v in results.items() if k != "errors"):
                status = "DOWN"
            elif any(v == "FAILED" for v in results.values()):
                 status = "DOWN"
            
            self._store_result(db, status, results, start_time)
            logger.info(f"Synthetic Operator cycle complete: {status}")
            
        except Exception as e:
            logger.error(f"Synthetic Operator error: {e}")
            results["errors"].append(str(e))
            self._store_result(db, "DOWN", results, start_time)
        finally:
            if created_locally:
                db.close()

    async def _ensure_synthetic_user(self, db: Session) -> Optional[User]:
        """Ensure the synthetic tenant and user exist."""
        try:
            user = db.query(User).filter(User.email == self.SYNTHETIC_EMAIL).first()
            if not user:
                # Create tenant
                tenant = Tenant(name=self.SYNTHETIC_TENANT)
                db.add(tenant)
                db.flush()
                
                # Create user
                user = User(
                    email=self.SYNTHETIC_EMAIL,
                    hashed_password=get_password_hash("CertSecure123!"),
                    tenant_id=tenant.id,
                    role=UserRole.OWNER,
                    is_active=True
                )
                db.add(user)
                db.commit()
                db.refresh(user)
                logger.info("Created Synthetic Certification User")
            return user
        except Exception as e:
            logger.error(f"Failed to ensure synthetic user: {e}")
            return None

    async def _check_task_flow(self, db: Session, user: User) -> bool:
        """Verifies task creation and basic lifecycle."""
        from app.models.task import Task, TaskStatus, TaskType
        try:
            # Create a dummy task
            task = Task(
                tenant_id=user.tenant_id,
                task_type="SYNTHETIC_CHECK",
                payload={"check": "alive"},
                status=TaskStatus.PENDING
            )
            db.add(task)
            db.commit()
            db.refresh(task)
            
            # Simulate claim
            task.status = TaskStatus.RUNNING
            task.agent_id = "synthetic-agent"
            db.commit()
            
            # Simulate complete
            task.status = TaskStatus.COMPLETED
            task.result = {"status": "ok"}
            db.commit()
            
            return True
        except Exception as e:
            logger.error(f"Task flow check failed: {e}")
            return False

    async def _check_broadcasting(self) -> bool:
        """Verifies Redis connectivity."""
        from app.core.redis_bus import broadcaster
        try:
            # Simple ping/test
            if not broadcaster.redis:
                await broadcaster.connect()
            
            await broadcaster.publish("ws:system:synthetic", {"ping": True})
            return True
        except Exception as e:
            logger.error(f"Broadcasting check failed: {e}")
            return False

    def _store_result(self, db: Session, status: str, results: Dict[str, Any], start_perf: float):
        """Persist results to the database."""
        duration_ms = int((time.perf_counter() - start_perf) * 1000)
        audit = SyntheticAudit(
            status=status,
            results=results,
            duration_ms=duration_ms
        )
        db.add(audit)
        db.commit()

# Global Instance
synthetic_op = SyntheticOperator()
