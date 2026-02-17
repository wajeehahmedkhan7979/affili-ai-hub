"""
WebSocket Connection Manager.
Phase 14: UX & Operator Experience v2

Manages active WebSocket connections and broadcasts events.
Supports tenant-scoped broadcasting to ensure data isolation.
"""
from typing import List, Dict, Any
from collections import defaultdict
from fastapi import WebSocket
import logging
import json

logger = logging.getLogger(__name__)


class ConnectionManager:
    def __init__(self):
        # Map tenant_id -> list of WebSockets (local to this instance)
        self.active_connections: Dict[str, List[WebSocket]] = defaultdict(list)

    async def connect(self, websocket: WebSocket, tenant_id: str):
        """Accept connection and store it locally."""
        await websocket.accept()
        self.active_connections[tenant_id].append(websocket)
        logger.info(f"WebSocket connected: tenant_id={tenant_id}")
        
    def disconnect(self, websocket: WebSocket, tenant_id: str):
        """Remove connection from local pool."""
        if tenant_id in self.active_connections:
            if websocket in self.active_connections[tenant_id]:
                self.active_connections[tenant_id].remove(websocket)
                logger.debug(f"WebSocket disconnected: tenant_id={tenant_id}")
            
            # Cleanup key if empty
            if not self.active_connections[tenant_id]:
                del self.active_connections[tenant_id]

    async def broadcast(self, message: Dict[str, Any], tenant_id: str):
        """
        Broadcast message to all instances via Redis.
        Local clients will be handled by the Redis subscription listener.
        """
        from app.core.redis_bus import broadcaster
        channel = f"ws:tenant:{tenant_id}"
        await broadcaster.publish(channel, message)
        logger.debug(f"Published message to Redis channel: {channel}")

    async def _handle_remote_message(self, channel: str, message: Dict[str, Any]):
        """
        Callback for Redis subscription events.
        Pushes messages from Redis to local WebSocket connections.
        """
        # Channel format: "ws:tenant:{tenant_id}"
        try:
            tenant_id = channel.split(":")[-1]
            if tenant_id in self.active_connections:
                # Send to all local connections for this tenant
                connections = self.active_connections[tenant_id][:]
                for connection in connections:
                    try:
                        await connection.send_json(message)
                    except Exception as e:
                        logger.warning(f"Failed to send local WS message: {e}")
                        self.disconnect(connection, tenant_id)
        except Exception as e:
            logger.error(f"Error in remote message handler: {e}")

    async def broadcast_system_wide(self, message: Dict[str, Any]):
        """Broadcast to ALL instances and ALL tenants via Redis."""
        from app.core.redis_bus import broadcaster
        # Using a special pattern for system-wide broadcasts
        await broadcaster.publish("ws:system:all", message)


# Global instance
manager = ConnectionManager()
