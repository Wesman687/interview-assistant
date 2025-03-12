import asyncio
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.utils.websocket_manager import websocket_manager  # ✅ Import the manager

router = APIRouter()

@router.websocket("/ws")
async def speech_status_endpoint(websocket: WebSocket):
    """Handles WebSocket connections for live status updates."""
    print("🔌 New Speech Status WebSocket connection")
    await websocket_manager.connect(websocket)

    try:
        while True:
            await asyncio.sleep(1)  # ✅ Keeps WebSocket alive
    except WebSocketDisconnect:
        await websocket_manager.disconnect(websocket)

async def broadcast_status(status: str):
    """Send live status updates to all connected clients."""
    await websocket_manager.broadcast(f'{{"status": "{status}"}}')
    print(f"📡 Sent status update: {status}")
