"""
Webhook service for event dispatching and secure delivery.
"""
import hmac
import hashlib
import json
import httpx
import uuid
import asyncio
from datetime import datetime
from sqlalchemy.orm import Session
from typing import Any, Dict, List

from app.models.webhook import WebhookConfig, WebhookDelivery

async def deliver_webhook(
    db_factory, # Function to get a new session
    config_id: uuid.UUID,
    event_type: str,
    payload: Dict[str, Any]
):
    """Deliver a webhook payload with HMAC signature."""
    db = db_factory()
    config = db.query(WebhookConfig).filter(WebhookConfig.id == config_id).first()
    if not config or not config.is_active:
        db.close()
        return

    # Prepare payload
    body = {
        "event": event_type,
        "timestamp": datetime.utcnow().isoformat(),
        "payload": payload
    }
    body_str = json.dumps(body)
    
    # Sign payload
    signature = hmac.new(
        config.secret.encode(),
        body_str.encode(),
        hashlib.sha256
    ).hexdigest()
    
    headers = {
        "Content-Type": "application/json",
        "X-Webhook-Signature": signature,
        "X-Webhook-Event": event_type
    }
    
    delivery = WebhookDelivery(
        id=uuid.uuid4(),
        tenant_id=config.tenant_id,
        config_id=config.id,
        event_type=event_type,
        payload=body,
        attempt_count=1
    )
    db.add(delivery)
    db.flush()
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(config.url, content=body_str, headers=headers)
            delivery.status_code = resp.status_code
            delivery.response_body = resp.text[:1000]
            delivery.success = (200 <= resp.status_code < 300)
    except Exception as e:
        delivery.response_body = str(e)
        delivery.success = False
        
    db.commit()
    db.close()

def trigger_webhook_event(
    db: Session,
    tenant_id: uuid.UUID,
    event_type: str,
    payload: Dict[str, Any]
):
    """Find matching webhook configs and trigger delivery in background."""
    configs = db.query(WebhookConfig).filter(
        WebhookConfig.tenant_id == tenant_id,
        WebhookConfig.is_active == True
    ).all()
    
    # Filter by event type
    matching_configs = []
    for c in configs:
        if event_type in c.event_types or "*" in c.event_types:
            matching_configs.append(c.id)
            
    if not matching_configs:
        return
        
    # We need a way to get a db session in the background
    from app.db.session import SessionLocal
    
    for cid in matching_configs:
        # Fire and forget
        asyncio.create_task(deliver_webhook(SessionLocal, cid, event_type, payload))
