from fastapi import WebSocket
from typing import Dict, List
import uuid
import json

class WebSocketManager:
    def __init__(self):
        # This dictionary will hold active connections.
        # The key is the review_id, and the value is a list of WebSockets
        # connected to that review's status.
        self.active_connections: Dict[uuid.UUID, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, review_id: uuid.UUID):
        """Accepts a new WebSocket connection and adds it to the pool."""
        await websocket.accept()
        if review_id not in self.active_connections:
            self.active_connections[review_id] = []
        self.active_connections[review_id].append(websocket)

    def disconnect(self, websocket: WebSocket, review_id: uuid.UUID):
        """Removes a WebSocket connection from the pool."""
        if review_id in self.active_connections:
            self.active_connections[review_id].remove(websocket)
            if not self.active_connections[review_id]:
                del self.active_connections[review_id]

    async def broadcast_update(self, review_id: uuid.UUID, message: dict):
        """Sends a JSON message to all clients listening for a specific review."""
        if review_id in self.active_connections:
            # Create a JSON string from the dictionary
            message_json = json.dumps(message)
            # Send the message to all connected clients for this review_id
            for connection in self.active_connections.get(review_id, []):
                await connection.send_text(message_json)

# Create a single, global instance of the manager that our app can use.
manager = WebSocketManager()