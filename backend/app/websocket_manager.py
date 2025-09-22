from fastapi import WebSocket
from typing import Dict, List, Set
import uuid
import json
import asyncio
from arq.connections import ArqRedis

from .redis_manager import get_redis_pool

WEBSOCKET_PUBLISH_CHANNEL = "ws_broadcast"

class WebSocketManager:
    def __init__(self):
        # We now have THREE pools of connections
        self.review_connections: Dict[uuid.UUID, Set[WebSocket]] = {}
        self.user_connections: Dict[uuid.UUID, Set[WebSocket]] = {}
        self.global_connections: Set[WebSocket] = set() # For all users
        
        self.redis: ArqRedis = None
        self.listener_task = None

    async def startup(self):
        """Initializes the manager and starts the Redis listener."""
        self.redis = await get_redis_pool()
        self.listener_task = asyncio.create_task(self._redis_listener())
        print("Scalable WebSocket Manager started.")

    async def shutdown(self):
        if self.listener_task:
            self.listener_task.cancel()
        print("WebSocket Manager shut down.")

    async def connect(self, websocket: WebSocket, user_id: uuid.UUID, review_id: uuid.UUID):
        """Accepts a connection and adds it to all relevant pools."""
        await websocket.accept()
        self.review_connections.setdefault(review_id, set()).add(websocket)
        self.user_connections.setdefault(user_id, set()).add(websocket)
        self.global_connections.add(websocket)

    def disconnect(self, websocket: WebSocket, user_id: uuid.UUID, review_id: uuid.UUID):
        """Removes a connection from all pools."""
        if review_id in self.review_connections:
            self.review_connections[review_id].remove(websocket)
            if not self.review_connections[review_id]:
                del self.review_connections[review_id]

        if user_id in self.user_connections:
            self.user_connections[user_id].remove(websocket)
            if not self.user_connections[user_id]:
                del self.user_connections[user_id]
        
        self.global_connections.discard(websocket)

    async def broadcast_to_review(self, review_id: uuid.UUID, message: dict):
        """Publishes a job progress update."""
        payload = {"type": "review_update", "review_id": str(review_id), "message": message}
        await self.redis.publish(WEBSOCKET_PUBLISH_CHANNEL, json.dumps(payload))

    async def broadcast_to_user(self, user_id: uuid.UUID, message: dict):
        """Publishes a user-specific notification."""
        payload = {"type": "user_notification", "user_id": str(user_id), "message": message}
        await self.redis.publish(WEBSOCKET_PUBLISH_CHANNEL, json.dumps(payload))
        
    async def broadcast_to_all(self, message: dict):
        """Publishes a system-wide message to all servers."""
        payload = {"type": "system_broadcast", "message": message}
        await self.redis.publish(WEBSOCKET_PUBLISH_CHANNEL, json.dumps(payload))

    async def _broadcast_locally(self, connections: Set[WebSocket], message_json: str):
        """Sends a message to a set of locally connected clients."""
        # Use asyncio.gather for concurrent sending
        await asyncio.gather(*[conn.send_text(message_json) for conn in connections], return_exceptions=True)

    async def _redis_listener(self):
        """Listens to Redis and routes messages to the correct local clients."""
        pubsub = self.redis.pubsub()
        await pubsub.subscribe(WEBSOCKET_PUBLISH_CHANNEL)
        
        while True:
            try:
                message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
                if not message: continue

                data = json.loads(message["data"])
                message_type = data.get("type")
                message_json = json.dumps(data["message"])

                if message_type == "review_update":
                    review_id = uuid.UUID(data["review_id"])
                    await self._broadcast_locally(self.review_connections.get(review_id, set()), message_json)
                elif message_type == "user_notification":
                    user_id = uuid.UUID(data["user_id"])
                    await self._broadcast_locally(self.user_connections.get(user_id, set()), message_json)
                elif message_type == "system_broadcast":
                    await self._broadcast_locally(self.global_connections, message_json)
                    
            except (asyncio.CancelledError, ConnectionError):
                break
            except Exception as e:
                print(f"Error in Redis listener: {e}")
                await asyncio.sleep(1)

manager = WebSocketManager()
