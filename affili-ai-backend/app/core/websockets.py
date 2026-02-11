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
        # Map tenant_id -> list of WebSockets
        self.active_connections: Dict[str, List[WebSocket]] = defaultdict(list)

    async def connect(self, websocket: WebSocket, tenant_id: str):
        """Account task to accept connection and store it."""
        await websocket.accept()
        self.active_connections[tenant_id].append(websocket)
        logger.info(f"WebSocket connected: tenant_id={tenant_id}")
        
    def disconnect(self, websocket: WebSocket, tenant_id: str):
        """Remove connection from pool."""
        if tenant_id in self.active_connections:
            if websocket in self.active_connections[tenant_id]:
                self.active_connections[tenant_id].remove(websocket)
                logger.info(f"WebSocket disconnected: tenant_id={tenant_id}")
            
            # Cleanup key if empty
            if not self.active_connections[tenant_id]:
                del self.active_connections[tenant_id]

    async def broadcast(self, message: Dict[str, Any], tenant_id: str):
        """
        Broadcast message to all connections for a specific tenant.
        
        Args:
            message: JSON-serializable dictionary
            tenant_id: Target tenant
        """
        if tenant_id not in self.active_connections:
            return

        # Copy list to avoid modification during iteration issues
        connections = self.active_connections[tenant_id][:]
        
        for connection in connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.warning(
                    "Failed to send WebSocket message",
                    extra={
                        "error": str(e),
                        "tenant_id": tenant_id
                    }
                )
                # Cleanup dead connection
                self.disconnect(connection, tenant_id)

    async def broadcast_system_wide(self, message: Dict[str, Any]):
        """
        Broadcast to ALL connected clients (System Admins only).
        Use sparingly.
        """
        for tenant_id in list(self.active_connections.keys()):
            await self.broadcast(message, tenant_id)


# Global instance
manager = ConnectionManager()
