import asyncio
import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.speech.transcribe import start_transcription, stop_transcription
from app.utils.websocket_manager import websocket_manager  # ✅ Import WebSocket Manager
import app.config2 

router = APIRouter()

@router.websocket("/ws")
async def status_websocket(websocket: WebSocket):
    """Handles WebSocket connections for system status updates."""
    print("🔌 Accepting Status WebSocket connection...")
    global USE_WHISPER
    await websocket_manager.connect(websocket, "speech")
    print("✅ Status WebSocket connected!")

    try:
        while True:
            message = await websocket.receive_text()
            print(f"📥 Received WebSocket Message: {message}")

            # ✅ Parse message as JSON
            try:
                message_data = json.loads(message)
            except json.JSONDecodeError:
                print("❌ Invalid WebSocket message format (must be JSON).")
                continue  # Ignore invalid messages

            # ✅ Ensure required fields exist
            if "type" not in message_data or "action" not in message_data:
                print("⚠️ Missing required fields in WebSocket message.")
                continue

            # ✅ Handle speech-related actions
            if message_data["type"] == "speech":
                if message_data["action"] == "start":
                    await start_transcription()
                    await websocket_manager.broadcast_speech_status("listening")
                elif message_data["action"] == "stop":
                    await stop_transcription()
                    await websocket_manager.broadcast_speech_status("stopped")
                elif message_data["action"] == "toggleWhisper":
                    app.config2.USE_WHISPER = message_data.get("useWhisper", not app.config2.USE_WHISPER)
                    await websocket_manager.broadcast_speech_status("toggleWhisper",{ "useWhisper": app.config2.USE_WHISPER})
                elif message_data["action"] == "getWhisperStatus":
                    await websocket_manager.broadcast_speech_status("getWhisperStatus",{ "useWhisper": app.config2.USE_WHISPER})

    except WebSocketDisconnect:
        print("❌ Status WebSocket disconnected.")
    except asyncio.CancelledError:
        print("⚠️ WebSocket task cancelled, cleaning up...")
    except Exception as e:
        print(f"❌ Unexpected WebSocket Error: {e}")
    finally:
        await websocket_manager.disconnect(websocket, "status")
