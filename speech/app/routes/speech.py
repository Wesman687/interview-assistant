import asyncio
import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.speech.transcribe import start_transcription, stop_transcription
from app.utils.websocket_manager import websocket_manager  # ✅ Import WebSocket Manager


router = APIRouter()

@router.websocket("/ws")
async def status_websocket(websocket: WebSocket):
    """Handles WebSocket connections for system status updates."""
    print("🔌 Accepting Status WebSocket connection...")
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
                print(f"🎤 Speech Action: {message_data['action']}")
                if message_data["action"] == "start":
                    try:
                        await start_transcription()
                    except Exception as e:
                        print(f"❌ Failed to start transcription: {e}")
                        await websocket_manager.broadcast_speech_status("stopped")
                    await websocket_manager.broadcast_speech_status("listening")
                elif message_data["action"] == "stop":
                    print("🛑 Stopping transcription...")
                    try:
                        await stop_transcription()
                    except Exception as e:
                        print(f"❌ Failed to stop transcription: {e}")
                    await websocket_manager.broadcast_speech_status("stopped")
                    
    except WebSocketDisconnect:
        print("❌ Status WebSocket disconnected.")
    except asyncio.CancelledError:
        print("⚠️ WebSocket task cancelled, cleaning up...")
    except Exception as e:
        print(f"❌ Unexpected WebSocket Error: {e}")
    finally:
        await websocket_manager.disconnect(websocket, "status")
