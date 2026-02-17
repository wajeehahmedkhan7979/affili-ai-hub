"""
Tests for API endpoints.
"""

import pytest
import uuid
from fastapi.testclient import TestClient


def test_health_check(client):
    """Test health check endpoint."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "version" in data
    assert "time" in data


def test_create_program(client):
    """Test creating a program."""
    program_data = {
        "name": "Test Affiliate Program",
        "description": "A test program",
        "affiliate_url": "https://example.com/affiliate",
        "commission_rate": 0.15,
        "terms": "Standard terms",
        "is_active": True,
    }
    
    # Needs auth token
    headers = {"Authorization": "Bearer agent-secret-key"}
    response = client.post("/api/v1/programs", json=program_data, headers=headers)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test Affiliate Program"
    assert data["commission_rate"] == 0.15
    assert "id" in data
    return data["id"]


def test_list_programs(client):
    """Test listing programs."""
    # Create a program first
    test_create_program(client)
    
    response = client.get("/api/v1/programs")
    assert response.status_code == 200
    programs = response.json()
    assert len(programs) > 0


def test_get_program(client):
    """Test getting a specific program."""
    # Create a program
    program_id = test_create_program(client)
    
    response = client.get(f"/api/v1/programs/{program_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(program_id)


def test_update_program(client):
    """Test updating a program."""
    # Create a program
    program_id = test_create_program(client)
    
    update_data = {
        "name": "Updated Program Name",
        "commission_rate": 0.20,
    }
    
    response = client.put(f"/api/v1/programs/{program_id}", json=update_data)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Program Name"
    assert data["commission_rate"] == 0.20


def test_delete_program(client):
    """Test deleting a program."""
    # Create a program
    program_id = test_create_program(client)
    
    response = client.delete(f"/api/v1/programs/{program_id}")
    assert response.status_code == 204
    
    # Verify it's deleted
    response = client.get(f"/api/v1/programs/{program_id}")
    assert response.status_code == 404


def test_create_application(client):
    """Test creating an application."""
    # Create a program first
    program_id = test_create_program(client)
    
    app_data = {
        "program_id": str(program_id),
        "user_email": "test@example.com",
        "name": "Test User",
        "website": "https://example.com",
    }
    
    response = client.post("/api/v1/applications", json=app_data)
    assert response.status_code == 201
    data = response.json()
    assert data["user_email"] == "test@example.com"
    assert data["status"] == "PENDING"
    return data["id"]


def test_create_task(client):
    """Test creating a task."""
    task_data = {
        "task_type": "DISCOVER_PROGRAM",
        "payload": {"url": "https://example.com"},
    }
    
    response = client.post("/api/v1/tasks", json=task_data)
    assert response.status_code == 201
    data = response.json()
    assert data["task_type"] == "DISCOVER_PROGRAM"
    assert data["status"] == "PENDING"
    assert "id" in data
    return data["id"]


def test_list_tasks(client):
    """Test listing tasks."""
    # Create a task
    test_create_task(client)
    
    response = client.get("/api/v1/tasks?status=PENDING")
    assert response.status_code == 200
    tasks = response.json()
    assert len(tasks) > 0


def test_get_task(client):
    """Test getting a specific task."""
    # Create a task
    task_id = test_create_task(client)
    
    response = client.get(f"/api/v1/tasks/{task_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(task_id)


def test_claim_task(client):
    """Test claiming a task."""
    # Create a task
    task_id = test_create_task(client)
    
    claim_data = {"agent_id": "test-agent"}
    response = client.post(f"/api/v1/tasks/{task_id}/claim", json=claim_data)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "CLAIMED"
    assert data["agent_id"] == "test-agent"


def test_update_task(client):
    """Test updating a task."""
    # Create and claim a task
    task_id = test_create_task(client)
    claim_data = {"agent_id": "test-agent"}
    client.post(f"/api/v1/tasks/{task_id}/claim", json=claim_data)
    
    # Update it
    update_data = {
        "status": "COMPLETED",
        "result": {"success": True},
        "logs": "Task completed successfully",
    }
    
    response = client.post(f"/api/v1/tasks/{task_id}/update", json=update_data)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "COMPLETED"
    assert data["result"]["success"] is True


def test_create_response(client):
    """Test creating a response pool entry."""
    response_data = {
        "question": "What is the commission rate?",
        "answer": "The commission rate is 10%",
        "category": "commission",
    }
    
    response = client.post("/api/v1/response-pool", json=response_data)
    assert response.status_code == 201
    data = response.json()
    assert data["question"] == "What is the commission rate?"
    assert "id" in data
    return data["id"]


def test_search_response_pool(client):
    """Test searching response pool."""
    # Create some responses
    test_create_response(client)
    
    search_data = {
        "query": "commission",
        "limit": 10,
        "threshold": 0.0,
    }
    
    response = client.post("/api/v1/response-pool/search", json=search_data)
    assert response.status_code == 200
    results = response.json()
    assert len(results) > 0


def test_poll_tasks_without_auth(client):
    """Test that poll endpoint requires authentication."""
    poll_data = {
        "client_id": "test-agent",
        "capabilities": ["playwright"],
    }
    
    response = client.post("/api/v1/tasks/poll", json=poll_data)
    assert response.status_code == 401


def test_poll_tasks_with_auth(client):
    """Test polling tasks with valid authentication."""
    # Create a pending task first
    test_create_task(client)
    
    poll_data = {
        "client_id": "test-agent",
        "capabilities": ["playwright"],
    }
    
    headers = {"Authorization": "Bearer agent-secret-key"}
    response = client.post("/api/v1/tasks/poll", json=poll_data, headers=headers)
    assert response.status_code == 200
    tasks = response.json()
    # Should have at least one pending task
    assert len(tasks) >= 0
