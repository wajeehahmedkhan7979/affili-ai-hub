"""
Redis Pub/Sub Broadcaster.
Phase 26.3: Distributed Event Bus

Provides a unified interface for publishing and subscribing to events
across multiple backend instances using Redis.
"""
import asyncio
import json
import logging
from typing import Any, Callable, Dict, Optional
import redis.asyncio as redis
from app.core.config import settings

logger = logging.getLogger(__name__)

class RedisBroadcaster:
    def __init__(self, redis_url: str):
        self.redis_url = redis_url
        self.redis: Optional[redis.Redis] = None
        self.pubsub: Optional[redis.client.PubSub] = None
        self._listen_task: Optional[asyncio.Task] = None
        self._callbacks: Dict[str, Callable] = {}

    async def connect(self):
        """Initialize Redis connection."""
        if not self.redis:
            self.redis = redis.from_url(self.redis_url, decode_responses=True)
            logger.info("Connected to Redis Event Bus")

    async def disconnect(self):
        """Close Redis connection and cleanup."""
        if self._listen_task:
            self._listen_task.cancel()
            try:
                await self._listen_task
            except asyncio.CancelledError:
                pass
        
        if self.redis:
            await self.redis.close()
            self.redis = None
            logger.info("Disconnected from Redis Event Bus")

    async def publish(self, channel: str, message: Dict[str, Any]):
        """Publish a message to a specific Redis channel."""
        if not self.redis:
            await self.connect()
        
        try:
            await self.redis.publish(channel, json.dumps(message))
        except Exception as e:
            logger.error(f"Failed to publish to Redis channel {channel}: {e}")

    async def subscribe(self, channel_pattern: str, callback: Callable[[str, Dict[str, Any]], Any]):
        """
        Subscribe to a channel pattern and register a callback.
        
        Note: This only registers the callback locally. 
        `start_listening` must be called to actually process messages.
        """
        self._callbacks[channel_pattern] = callback
        logger.debug(f"Registered callback for Redis pattern: {channel_pattern}")

    async def start_listening(self):
        """Start the background task to listen for Redis messages."""
        if not self.redis:
            await self.connect()
            
        if self._listen_task and not self._listen_task.done():
            return

        self._listen_task = asyncio.create_task(self._listen_loop())
        logger.info("Redis Event Bus listener started")

    async def _listen_loop(self):
        """Background loop to poll Redis for messages and trigger callbacks."""
        self.pubsub = self.redis.pubsub()
        
        # Subscribe to all patterns we have callbacks for
        for pattern in self._callbacks.keys():
            await self.pubsub.psubscribe(pattern)
            
        try:
            async for message in self.pubsub.listen():
                if message["type"] == "pmessage":
                    channel = message["channel"]
                    pattern = message["pattern"]
                    data_str = message["data"]
                    
                    try:
                        data = json.loads(data_str)
                        callback = self._callbacks.get(pattern)
                        if callback:
                            # Run callback as a background task to not block the loop
                            asyncio.create_task(callback(channel, data))
                    except json.JSONDecodeError:
                        logger.warning(f"Received invalid JSON on Redis channel {channel}: {data_str}")
                    except Exception as e:
                        logger.error(f"Error in Redis listener callback: {e}")
                        
        except asyncio.CancelledError:
            logger.info("Redis listener loop cancelled")
        except Exception as e:
            logger.error(f"Redis listener loop error: {e}")
            # Optional: Implement reconnection logic here if needed
        finally:
            if self.pubsub:
                await self.pubsub.close()

# Global instance
broadcaster = RedisBroadcaster(settings.REDIS_URL)
