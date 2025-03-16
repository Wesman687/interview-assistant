import asyncio
import json
from fastapi import WebSocket, WebSocketDisconnect

class WebSocketManager:
    """Manages separate WebSocket connections for different message types."""

    def __init__(self):
        self.connections = {
            "interview": set(),
            "speech": set(),
        }

    async def connect(self, websocket: WebSocket, connection_type: str):
        """Accepts a WebSocket connection and adds it to the correct pool."""
        await websocket.accept()
        if connection_type in self.connections:
            self.connections[connection_type].add(websocket)
            print(f"🔌 {connection_type.upper()} WebSocket connected! Total: {len(self.connections[connection_type])}")

    async def disconnect(self, websocket: WebSocket, connection_type: str):
        """Removes a WebSocket connection from the correct pool."""
        if connection_type in self.connections and websocket in self.connections[connection_type]:
            self.connections[connection_type].discard(websocket)
            print(f"❌ {connection_type.upper()} WebSocket disconnected. Remaining: {len(self.connections[connection_type])}")

    async def broadcast(self, message: str, connection_type: str):
        """Broadcasts a message to all WebSockets of a specific type."""
        print(f"📡 Broadcasting to {connection_type.upper()} WebSockets: {message}")

        disconnected_clients = set()

        for client in list(self.connections.get(connection_type, [])):
            try:
                await client.send_text(message)
            except WebSocketDisconnect:
                print(f"❌ WebSocket {client} disconnected.")
                disconnected_clients.add(client)
            except Exception as e:
                print(f"⚠️ Error sending to {connection_type} WebSocket: {e}")
                disconnected_clients.add(client)

        for client in disconnected_clients:
            self.connections[connection_type].discard(client)

        print(f"✅ Finished broadcasting to {len(self.connections[connection_type])} active {connection_type} WebSockets.")

    async def close_all(self):
        """Force-close all WebSocket connections on shutdown."""
        print("🔌 Closing all WebSockets...")

        for connection_type, clients in self.connections.items():
            for client in list(clients):
                try:
                    await client.close(code=1000)
                except Exception as e:
                    print(f"⚠️ Error closing {connection_type} WebSocket: {e}")

            clients.clear()
            print(f"✅ All {connection_type.upper()} WebSockets closed.")
    async def broadcast_speech_status(self, status: str, data: dict = None):
        """Send system status updates to connected clients."""
        message = {"type": "speech", "status": status}
        if data:
            message.update(data)  # ✅ Merge additional data

        json_message = json.dumps(message)
        await websocket_manager.broadcast(json_message, "speech")
        print(f"📡 Sent system status update: {message}")
        
    async def broadcast_interview_message(self, payload: dict):
        """Send live interview updates to connected clients."""
        payload["type"] = "interview"

        json_message = json.dumps(payload)  # ✅ Serialize message
        await websocket_manager.broadcast(json_message, "interview")
        print(f"📡 Sent interview update: {payload}")
        


# ✅ Create a single instance to be shared across routes
websocket_manager = WebSocketManager()
