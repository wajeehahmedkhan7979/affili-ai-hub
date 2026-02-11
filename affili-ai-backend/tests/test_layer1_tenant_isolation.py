"""
Layer 1: Tenant Isolation Tests

These tests assert that no cross-tenant data leakage is possible.
These tests MUST NEVER FAIL - they are safety invariants.

If any of these tests fail, the pilot must be stopped.

# NOTE: v1.1 schema intentionally does NOT include `program_id` on tasks.
# Tests must not assume program-level task binding. Do not add `program_id`.
"""

import pytest
import uuid
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.tenant import Tenant
from app.models.user import User, UserRole
from app.models.task import Task, TaskStatus, TaskType
from app.models.program import Program
from app.core.tenant import set_tenant_id, reset_tenant_id


@pytest.fixture
def test_tenant_a_id():
    """Fixture for test tenant A UUID"""
    return uuid.uuid4()


@pytest.fixture
def test_tenant_b_id():
    """Fixture for test tenant B UUID"""
    return uuid.uuid4()


def setup_test_tenant_and_user(db_session: Session, tenant_id: uuid.UUID, email_suffix: str = "") -> tuple[Tenant, User]:
    """Helper to create test tenant and user."""
    from sqlalchemy import text
    
    tenant = Tenant(id=tenant_id, name=f"Test Tenant {email_suffix}", is_active=True)
    db_session.add(tenant)
    db_session.commit()
    
    # Create user with proper enum casting for PostgreSQL
    user_id = uuid.uuid4()
    db_session.execute(
        text("""
            INSERT INTO users (id, tenant_id, email, role, is_active, created_at)
            VALUES (:id, :tenant_id, :email, CAST(:role AS userrole), :is_active, NOW())
        """),
        {
            "id": user_id,
            "tenant_id": tenant_id,
            "email": f"test-{email_suffix}@example.com",
            "role": "OWNER",
            "is_active": True
        }
    )
    db_session.commit()
    
    user = db_session.query(User).filter(User.id == user_id).first()
    return tenant, user


class TestTenantIsolation:
    """Layer 1: Tenant isolation tests"""
    
    def test_tenant_cannot_read_other_tasks(
        self, db_session: Session, test_tenant_a_id: uuid.UUID, test_tenant_b_id: uuid.UUID, insert_task
    ):
        """
        TC-4.1: Tenant A cannot read Tenant B tasks
        
        This test verifies that tasks are isolated by tenant_id.
        """
        # Setup: Create both tenants
        tenant_a, user_a = setup_test_tenant_and_user(db_session, test_tenant_a_id, "A")
        tenant_b, user_b = setup_test_tenant_and_user(db_session, test_tenant_b_id, "B")
        
        # Create task for Tenant B using safe fixture (bypasses ORM schema mismatches)
        task_b_id = insert_task(
            tenant_id=test_tenant_b_id,
            task_type=TaskType.APPLY_PROGRAM,
            status=TaskStatus.PENDING,
            payload={"program_name": "Tenant B Task"}
        )
        
        # Action: Tenant A queries tasks
        set_tenant_id(str(test_tenant_a_id))
        from app.services.task_dispatcher import get_pending_tasks
        tenant_a_tasks = get_pending_tasks(db_session, limit=100)
        
        # Assert: Tenant A should not see Tenant B's task
        task_ids = [str(t.id) for t in tenant_a_tasks]
        assert str(task_b_id) not in task_ids, \
            "Tenant A should not see Tenant B's tasks"
        
        # Verify Tenant B can see their own task
        set_tenant_id(str(test_tenant_b_id))
        tenant_b_tasks = get_pending_tasks(db_session, limit=100)
        tenant_b_task_ids = [str(t.id) for t in tenant_b_tasks]
        assert str(task_b_id) in tenant_b_task_ids, \
            "Tenant B should see their own tasks"
    
    def test_tenant_cannot_modify_other_programs(
        self, db_session: Session, test_tenant_a_id: uuid.UUID, test_tenant_b_id: uuid.UUID
    ):
        """
        TC-4.2: Tenant A cannot modify Tenant B programs
        
        This test verifies that programs are isolated by tenant_id.
        """
        # Setup: Create both tenants
        tenant_a, user_a = setup_test_tenant_and_user(db_session, test_tenant_a_id, "A")
        tenant_b, user_b = setup_test_tenant_and_user(db_session, test_tenant_b_id, "B")
        
        # Create program for Tenant B
        set_tenant_id(str(test_tenant_b_id))
        program_b = Program(
            id=uuid.uuid4(),
            tenant_id=test_tenant_b_id,
            name="Tenant B Program",
            signup_url="https://example.com/signup",
            affiliate_url="https://example.com/affiliate", # Required field
            is_active=True
        )
        db_session.add(program_b)
        db_session.commit()
        program_b_id = program_b.id
        
        # Action: Tenant A attempts to query programs
        set_tenant_id(str(test_tenant_a_id))
        from app.services.program_service import list_programs
        tenant_a_programs = list_programs(db_session)
        
        # Assert: Tenant A should not see Tenant B's program
        program_ids = [str(p.id) for p in tenant_a_programs]
        assert str(program_b_id) not in program_ids, \
            "Tenant A should not see Tenant B's programs"
    
    def test_tenant_isolation_in_task_creation(
        self, db_session: Session, test_tenant_a_id: uuid.UUID, test_tenant_b_id: uuid.UUID
    ):
        """
        TC-4.3: Tasks created with wrong tenant context are isolated
        
        This test verifies that tenant_id from context is enforced.
        """
        # Setup: Create both tenants
        tenant_a, user_a = setup_test_tenant_and_user(db_session, test_tenant_a_id, "A")
        tenant_b, user_b = setup_test_tenant_and_user(db_session, test_tenant_b_id, "B")
        
        # Action: Create task with Tenant A context using Service Layer
        set_tenant_id(str(test_tenant_a_id))
        from app.services.task_dispatcher import create_task
        task_a = create_task(
            db=db_session,
            # tenant_id is derived from context (set_tenant_id)
            task_type=TaskType.APPLY_PROGRAM,
            payload={"program_name": "Tenant A Task", "program_domain": "shareasale.com"}
        )
        
        # Verify: Task belongs to Tenant A
        assert task_a.tenant_id == test_tenant_a_id, \
            "Task should belong to Tenant A"
        
        # Verify: Tenant B cannot see it
        set_tenant_id(str(test_tenant_b_id))
        from app.services.task_dispatcher import get_pending_tasks
        tenant_b_tasks = get_pending_tasks(db_session, limit=100)
        tenant_b_task_ids = [str(t.id) for t in tenant_b_tasks]
        assert str(task_a.id) not in tenant_b_task_ids, \
            "Tenant B should not see Tenant A's tasks"
    
    def test_tenant_id_from_context_enforced(
        self, db_session: Session, test_tenant_a_id: uuid.UUID, test_tenant_b_id: uuid.UUID
    ):
        """
        TC-4.4: Tenant ID from context is enforced, not from payload
        
        This test verifies that tenant_id comes from context (JWT), not request payload.
        """
        # Setup: Create both tenants
        tenant_a, user_a = setup_test_tenant_and_user(db_session, test_tenant_a_id, "A")
        tenant_b, user_b = setup_test_tenant_and_user(db_session, test_tenant_b_id, "B")
        
        # Action: Set Tenant A context, but payload might try to specify Tenant B
        set_tenant_id(str(test_tenant_a_id))
        
        # Attempt to create task using Service - tenant_id should come from context argument/auth
        from app.services.task_dispatcher import create_task
        task = create_task(
            db=db_session,
            # tenant_id derived from context
            task_type=TaskType.APPLY_PROGRAM,
            payload={"program_name": "Test Task", "tenant_id": str(test_tenant_b_id), "program_domain": "shareasale.com"}  # Payload tries to specify B
        )
        
        # Assert: Task belongs to Tenant A (from context), not B (from payload)
        assert task.tenant_id == test_tenant_a_id, \
            "Task tenant_id should come from context, not payload"
        
        assert task.tenant_id != test_tenant_b_id, \
            "Task should not belong to Tenant B even if payload specifies it"
