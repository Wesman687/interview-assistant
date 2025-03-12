import asyncio
import json
from fastapi import WebSocket

class WebSocketManager:
    """Manages connected WebSocket clients and broadcasting messages."""
    
    def __init__(self):
        self.connected_clients = set()

    async def connect(self, websocket: WebSocket):
        """Accepts a WebSocket connection and adds it to the list."""
        await websocket.accept()
        self.connected_clients.add(websocket)
        print(f"🔌 New WebSocket connection. Total: {len(self.connected_clients)}")

    async def disconnect(self, websocket: WebSocket):
        """Removes a WebSocket connection."""
        self.connected_clients.discard(websocket)
        print(f"❌ WebSocket disconnected. Remaining: {len(self.connected_clients)}")

    async def broadcast(self, message: str):
        """Broadcasts a message to all connected WebSockets."""
        disconnected_clients = set()

        for client in self.connected_clients.copy():
            try:
                await client.send_text(message)
            except Exception:
                disconnected_clients.add(client)

        # ✅ Remove disconnected clients
        for client in disconnected_clients:
            self.connected_clients.remove(client)

        print(f"📡 Broadcasted message to {len(self.connected_clients)} clients.")
        
    async def close_all(self):
        """Force-close all WebSocket connections on shutdown."""
        print("🔌 Closing all WebSockets...")
        for client in list(self.connected_clients):
            try:
                await client.close(code=1000)
            except Exception as e:
                print(f"⚠️ Error closing WebSocket: {e}")
        self.connected_clients.clear()
        print("✅ All WebSockets closed.")

        
    async def broadcast_status(self, status: str):
        """Send live status updates to all clients."""
        await self.broadcast(json.dumps({"status": status}))
        
    async def broadcast_message(self, transcription: str):
        """Broadcasts transcriptions to all connected WebSockets."""
        message = json.dumps({"transcription": transcription})
        await self.broadcast(message)
        print(f"📡 Sent transcription: {transcription}")

websocket_manager = WebSocketManager()
