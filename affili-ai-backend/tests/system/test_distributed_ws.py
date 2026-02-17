"""
Verification test for Phase 26.3: Distributed Event Bus.
Simulates multiple instances using mocks to verify Redis Pub/Sub integration.
"""
import pytest
import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch
from app.core.websockets import ConnectionManager
from app.core.redis_bus import RedisBroadcaster

@pytest.mark.asyncio
async def test_distributed_broadcast_logic():
    """
    Verifies that ConnectionManager.broadcast publishes to Redis
     and _handle_remote_message sends to local WebSockets.
    """
    manager = ConnectionManager()
    
    # 1. Mock Local WebSockets
    ws1 = AsyncMock()
    ws2 = AsyncMock()
    tenant_id = "test-tenant-123"
    
    await manager.connect(ws1, tenant_id)
    await manager.connect(ws2, tenant_id)
    
    assert len(manager.active_connections[tenant_id]) == 2
    
    # 2. Mock Redis Broadcaster
    mock_broadcaster = AsyncMock()
    
    with patch("app.core.redis_bus.broadcaster", mock_broadcaster):
        # 3. Test Publishing
        test_message = {"event": "TASK_CREATED", "data": {"id": 1}}
        await manager.broadcast(test_message, tenant_id)
        
        # Verify it went to Redis
        mock_broadcaster.publish.assert_called_once_with(
            f"ws:tenant:{tenant_id}", 
            test_message
        )
        
        # 4. Test Receiving (Remote Event)
        # Simulate a message coming from Redis (possibly from another instance)
        remote_message = {"event": "REMOTE_EVENT", "info": "from_another_node"}
        await manager._handle_remote_message(f"ws:tenant:{tenant_id}", remote_message)
        
        # Verify local WebSockets received it
        ws1.send_json.assert_called_once_with(remote_message)
        ws2.send_json.assert_called_once_with(remote_message)

@pytest.mark.asyncio
async def test_redis_broadcaster_subscription_flow():
    """Verifies that RedisBroadcaster correctly registers callbacks and listens."""
    broadcaster = RedisBroadcaster("redis://localhost:6379/0")
    
    # Mock Redis client
    mock_redis = MagicMock()
    mock_pubsub = AsyncMock()
    mock_redis.pubsub.return_value = mock_pubsub
    
    broadcaster.redis = mock_redis
    
    # Register callback
    received_messages = []
    async def sample_callback(channel, data):
        received_messages.append((channel, data))
    
    await broadcaster.subscribe("ws:tenant:*", sample_callback)
    assert "ws:tenant:*" in broadcaster._callbacks
    
    # Simulate the listen loop receiving a message
    # In redis-py async, pubsub.listen() returns an async generator/iterator
    mock_messages = [
        {
            "type": "pmessage",
            "pattern": "ws:tenant:*",
            "channel": "ws:tenant:abc",
            "data": '{"hello": "world"}'
        }
    ]
    
    class AsyncIter:
        def __init__(self, items):
            self.items = items
        def __aiter__(self):
            return self
        async def __anext__(self):
            if not self.items:
                raise StopAsyncIteration
            return self.items.pop(0)

    # Make listen() return the async iterator
    mock_pubsub.listen = MagicMock(return_value=AsyncIter(mock_messages))
    
    # Run the loop for one iteration 
    with patch("asyncio.create_task") as mock_create_task:
        await broadcaster._listen_loop()
        
        # Verify psubscribe was called
        mock_pubsub.psubscribe.assert_called_with("ws:tenant:*")
        
        # Verify a task was created for the callback
        assert mock_create_task.called
