import json
import asyncio
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.speech.transcribe import start_transcription, stop_transcription
from app.config import INTERVIEW_WS_URL
from app.utils.websocket_manager import websocket_manager  # ✅ Import centralized WebSocket manager
import websockets

router = APIRouter()

@router.websocket("/ws")
async def speech_websocket(websocket: WebSocket):
    """Handles WebSocket connections for live speech recognition."""
    print("🔌 New Speech WebSocket connection")
    await websocket_manager.connect(websocket)

    try:
        while True:
            message = await websocket.receive_text()
            if message == "start":
                await start_transcription()
                await websocket_manager.broadcast_status("listening")
            elif message == "stop":
                await stop_transcription()
                await websocket_manager.broadcast_status("stopped")
    except WebSocketDisconnect:
        await websocket_manager.disconnect(websocket)

async def forward_to_interview_ws(message: str, retries=3):
    """Forward transcript to AI WebSocket with retry logic."""
    for attempt in range(retries):
        try:
            print(f"📤 Forwarding to Interview API: {message}")
            async with websockets.connect(INTERVIEW_WS_URL) as ws:
                await ws.send(json.dumps({"transcription": message}))
                print(f"✅ Successfully Forwarded to Interview API")
            return  # ✅ Success, exit function
        except Exception as e:
            print(f"❌ Error forwarding transcript (Attempt {attempt+1}/{retries}): {e}")
            await asyncio.sleep(2)  # ✅ Retry delay

    print(f"🚨 Failed to forward transcript after {retries} attempts.")

async def broadcast_transcription(message: str):
    """Send transcriptions to WebSocket clients & AI API."""
    await websocket_manager.broadcast(message)  # ✅ Send to all clients
    await forward_to_interview_ws(message)  # ✅ Forward to AI WebSocket
