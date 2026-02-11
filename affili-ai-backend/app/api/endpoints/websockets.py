"""
WebSocket Endpoints.
Phase 14: UX & Operator Experience v2

Exposes /ws/{tenant_id} endpoint for real-time updates.
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException, status
from typing import Optional
import logging

from app.core.websockets import manager
from app.core.tenant import get_tenant_id
# Note: In a real app, we would validate the token in the WebSocket handshake
# For this phase, we'll assume the client connects to their assigned tenant path
# and we'll implement token validation in a future hardening step if needed.

router = APIRouter()
logger = logging.getLogger(__name__)

@router.websocket("/ws/{tenant_id}")
async def websocket_endpoint(websocket: WebSocket, tenant_id: str):
    """
    WebSocket endpoint for real-time task updates.
    
    Clients should connect to /ws/{their_tenant_id}.
    Server will push: TASK_CREATED, TASK_UPDATED, TASK_COMPLETED events.
    """
    # Validate auth token from query param ?token=...
    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    try:
        from app.core.security import decode_access_token
        # Verify token and extract tenant_id
        payload = decode_access_token(token)
        token_tenant_id = payload.get("tenant_id")
        
        # Enforce Tenant Boundary: Token tenant must match requested path tenant
        if str(token_tenant_id) != tenant_id:
             logger.warning(f"WebSocket tenant mismatch: token={token_tenant_id}, path={tenant_id}")
             await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
             return
             
    except Exception as e:
        logger.warning(f"WebSocket auth failed: {e}")
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return
    # For now, we trust the path param matches the user's tenant (internal app)
    
    await manager.connect(websocket, tenant_id)
    
    try:
        while True:
            # Keep the connection alive and listen for client messages (if any)
            # Currently we use this channel as Push-Only from server, 
            # but we need to await receive to detect disconnects.
            data = await websocket.receive_text()
            
            # Optional: Handle ping/pong or client commands
            if data == "ping":
                await websocket.send_text("pong")
                
    except WebSocketDisconnect:
        manager.disconnect(websocket, tenant_id)
    except Exception as e:
        logger.error(f"WebSocket error for tenant {tenant_id}: {e}")
        manager.disconnect(websocket, tenant_id)
