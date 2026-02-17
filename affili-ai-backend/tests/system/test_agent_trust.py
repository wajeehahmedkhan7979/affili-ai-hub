import pytest
import base64
import time
import uuid
from cryptography.hazmat.primitives.asymmetric import ed25519
from sqlalchemy.orm import Session
from fastapi.testclient import TestClient
from app.models.task import Task, TaskType, TaskStatus
from app.models.agent import Agent

def generate_key_pair():
    private_key = ed25519.Ed25519PrivateKey.generate()
    public_key = private_key.public_key()
    
    public_bytes = public_key.public_bytes_raw()
    public_b64 = base64.b64encode(public_bytes).decode("utf-8")
    
    return private_key, public_b64

def sign_message(private_key, message: str):
    signature = private_key.sign(message.encode("utf-8"))
    return base64.b64encode(signature).decode("utf-8")

def test_agent_identity_pinning(client: TestClient, db_session: Session, agent_headers: dict):
    """Verify that an agent pins their public key on first claim."""
    # 1. Create a task
    from app.services.task_dispatcher import create_task
    task = create_task(db_session, TaskType.DISCOVER_PROGRAM.value)
    
    # 2. First claim with public key
    _, pub_key_1 = generate_key_pair()
    agent_id = "test-agent-1"
    
    resp = client.post(
        f"/api/v1/tasks/{task.id}/claim",
        headers=agent_headers,
        json={"agent_id": agent_id, "public_key": pub_key_1}
    )
    assert resp.status_code == 200
    
    # Verify pinned in DB
    agent = db_session.query(Agent).filter(Agent.id == agent_id).first()
    assert agent.pinned_public_key == pub_key_1
    
    # 3. Attempt to claim another task with DIFFERENT public key
    task_2 = create_task(db_session, TaskType.DISCOVER_PROGRAM.value)
    _, pub_key_2 = generate_key_pair()
    
    resp = client.post(
        f"/api/v1/tasks/{task_2.id}/claim",
        headers=agent_headers,
        json={"agent_id": agent_id, "public_key": pub_key_2}
    )
    assert resp.status_code == 409  # Conflict/Mismatch
    assert "identity mismatch" in resp.json()["detail"]

def test_agent_signature_verification(client: TestClient, db_session: Session, agent_headers: dict):
    """Verify that signed updates work and unsigned/invalid fail."""
    priv_key, pub_key = generate_key_pair()
    agent_id = "trusted-agent"
    
    # 1. Create and claim task (pins the key)
    from app.services.task_dispatcher import create_task
    task = create_task(db_session, TaskType.DISCOVER_PROGRAM.value)
    client.post(f"/api/v1/tasks/{task.id}/claim", headers=agent_headers, 
                json={"agent_id": agent_id, "public_key": pub_key})
    
    # 2. Update status WITHOUT signature (should fail)
    resp = client.post(f"/api/v1/tasks/{task.id}/update", headers=agent_headers,
                       json={"status": "RUNNING"})
    assert resp.status_code == 401
    
    # 3. Update status WITH valid signature
    timestamp = str(int(time.time()))
    message = f"{task.id}:{timestamp}"
    signature = sign_message(priv_key, message)
    
    headers = {**agent_headers, "X-Agent-Signature": signature, "X-Agent-Timestamp": timestamp}
    resp = client.post(f"/api/v1/tasks/{task.id}/update", headers=headers,
                       json={"status": "RUNNING"})
    assert resp.status_code == 200
    
    # 4. Update status with INVALID signature
    bad_signature = base64.b64encode(b"invalid_sig").decode("utf-8")
    headers["X-Agent-Signature"] = bad_signature
    resp = client.post(f"/api/v1/tasks/{task.id}/update", headers=headers,
                       json={"status": "COMPLETED"})
    assert resp.status_code == 401

def test_agent_replay_protection(client: TestClient, db_session: Session, agent_headers: dict):
    """Verify that old signatures are rejected."""
    priv_key, pub_key = generate_key_pair()
    agent_id = "replay-agent"
    
    from app.services.task_dispatcher import create_task
    task = create_task(db_session, TaskType.DISCOVER_PROGRAM.value)
    client.post(f"/api/v1/tasks/{task.id}/claim", headers=agent_headers, 
                json={"agent_id": agent_id, "public_key": pub_key})
    
    # Use an old timestamp (10 mins ago)
    old_timestamp = str(int(time.time()) - 600)
    message = f"{task.id}:{old_timestamp}"
    signature = sign_message(priv_key, message)
    
    headers = {**agent_headers, "X-Agent-Signature": signature, "X-Agent-Timestamp": old_timestamp}
    resp = client.post(f"/api/v1/tasks/{task.id}/update", headers=headers,
                       json={"status": "RUNNING"})
    assert resp.status_code == 401
    assert "expired" in resp.json()["detail"].lower()
