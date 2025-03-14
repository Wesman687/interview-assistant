import asyncio
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.utils.websocket_manager import websocket_manager  # ✅ Import the manager

router = APIRouter()

@router.websocket("/ws")
async def speech_status_endpoint(websocket: WebSocket):
    """Handles WebSocket connections for live status updates."""
    print("🔌 Accepting Speech Status WebSocket connection...")
    await websocket_manager.connect(websocket)
    print("✅ Speech Status WebSocket connected!")

    try:
        while True:
            try:
                # ✅ Wait for incoming messages (keeps WebSocket alive)
                message = await websocket.receive_text()
                print(f"📥 Received Status WebSocket Message: {message}")

                # ✅ Echo the message back (optional for debugging)
                await websocket.send_text(f"✅ Status received: {message}")

            except asyncio.CancelledError:
                print("⚠️ WebSocket task was cancelled.")
                break  # ✅ Prevents crash on cancellation

            except WebSocketDisconnect:
                print("❌ WebSocket disconnected (Client closed connection).")
                break

            except Exception as e:
                print(f"⚠️ Unexpected WebSocket Error: {e}")
                break  # ✅ Exit loop on error

    finally:
        try:
            await websocket_manager.disconnect(websocket)
        except RuntimeError:
            print("⚠️ WebSocket was already closed, skipping cleanup.")

        print("🔴 WebSocket Cleanup Complete.")

async def broadcast_status(status: str):
    """Send live status updates to all connected clients."""
    message = f'{{"status": "{status}"}}'
    await websocket_manager.broadcast(message)
    print(f"📡 Sent status update: {message}")
