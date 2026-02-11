"""
Create seed test data for AFFILI-AI HUB.

Creates:
1. Test tenant
2. Test user (admin)
3. Test affiliate program
4. Test embedding data  
5. Test tasks

For end-to-end validation.
"""

import sys
import os
import uuid
from pathlib import Path
from datetime import datetime, timedelta

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

load_dotenv()

from app.models import (
    Tenant, User, UserRole, Program,
    Task, TaskType, TaskStatus, Agent,
    FormFieldEmbedding
)
from app.db.session import get_engine_instance

def create_seed_data():
    """Create test data for validation."""
    print("="*60)
    print("AFFILI-AI Seed Data Creator")
    print("="*60)
    
    try:
        engine = get_engine_instance()
        
        with Session(engine) as db:
            # Check if seed data already exists
            existing_tenant = db.query(Tenant).filter(Tenant.name == "Test Automation Tenant").first()
            
            if existing_tenant:
                print("\n⚠️  Seed data already exists!")
                print(f"   Tenant: {existing_tenant.name} ({existing_tenant.id})")
                return
            
            print("\n📝 Creating test tenant...")
            tenant = Tenant(
                id=uuid.uuid4(),
                name="Test Automation Tenant",
                slug="test-automation",
                plan="professional"
            )
            db.add(tenant)
            db.flush()
            print(f"✅ Tenant created: {tenant.id}")
            
            print("\n📝 Creating test user (admin)...")
            user = User(
                id=uuid.uuid4(),
                tenant_id=tenant.id,
                email="admin@test-automation.local",
                username="admin",
                role=UserRole.OWNER,
                hashed_password="$2b$12$test_hash_not_real"  # Placeholder
            )
            db.add(user)
            db.flush()
            print(f"✅ User created: {user.email}")
            
            print("\n📝 Creating test affiliate program...")
            program = Program(
                id=uuid.uuid4(),
                tenant_id=tenant.id,
                name="Amazon Associates",
                platform="amazon",
                url="https://affiliate-program.amazon.com",
                status="active",
                auto_discover=True
            )
            db.add(program)
            db.flush()
            print(f"✅ Program created: {program.name}")
            
            print("\n📝 Creating test agent...")
            agent = Agent(
                id=uuid.uuid4(),
                tenant_id=tenant.id,
                agent_type="APPLICATION",
                status="ACTIVE",
                last_seen=datetime.utcnow()
            )
            db.add(agent)
            db.flush()
            print(f"✅ Agent created: {agent.id}")
            
            print("\n📝 Creating test embeddings...")
            embeddings = [
                FormFieldEmbedding(
                    id=uuid.uuid4(),
                    tenant_id=tenant.id,
                    program_id=program.id,
                    field_label="Company Name",
                    field_value="Test Automation LLC",
                    embedding=[0.1] * 384,  # Dummy vector
                    success_count=5
                ),
                FormFieldEmbedding(
                    id=uuid.uuid4(),
                    tenant_id=tenant.id,
                    program_id=program.id,
                    field_label="Website URL",
                    field_value="https://test-automation.com",
                    embedding=[0.2] * 384,
                    success_count=3
                ),
            ]
            
            for emb in embeddings:
                db.add(emb)
            db.flush()
            print(f"✅ Created {len(embeddings)} test embeddings")
            
            print("\n📝 Creating test tasks...")
            tasks = [
                Task(
                    id=uuid.uuid4(),
                    tenant_id=tenant.id,
                    program_id=program.id,
                    task_type=TaskType.APPLICATION,
                    status=TaskStatus.PENDING,
                    payload={"test": True, "field": "value"}
                ),
                Task(
                    id=uuid.uuid4(),
                    tenant_id=tenant.id,
                    program_id=program.id,
                    task_type=TaskType.DISCOVERY,
                    status=TaskStatus.COMPLETED,
                    payload={"test": True},
                    completed_at=datetime.utcnow() - timedelta(hours=1)
                ),
            ]
            
            for task in tasks:
                db.add(task)
            db.flush()
            print(f"✅ Created {len(tasks)} test tasks")
            
            # Commit all
            db.commit()
            
            print("\n" + "="*60)
            print("SEED DATA CREATED SUCCESSFULLY")
            print("="*60)
            print(f"\n📊 Summary:")
            print(f"   Tenant ID: {tenant.id}")
            print(f"   User: {user.email}")
            print(f"   Program: {program.name}")
            print(f"   Agent ID: {agent.id}")
            print(f"   Embeddings: {len(embeddings)}")
            print(f"   Tasks: {len(tasks)}")
            print(f"\n💡 You can now test the system with this data!")
            
            return True
            
    except Exception as e:
        print(f"\n❌ Error creating seed data: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = create_seed_data()
    sys.exit(0 if success else 1)
