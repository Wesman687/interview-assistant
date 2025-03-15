import asyncio
import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.speech.transcribe import start_transcription, stop_transcription
from app.utils.websocket_manager import websocket_manager  # ✅ Import WebSocket Manager
import websockets

router = APIRouter()

USE_WHISPER = False  # Default to Google STT

@router.post("/toggle-transcription")
async def toggle_transcription(engine: str):
    """Toggle between Google STT and Whisper AI."""
    global USE_WHISPER

    if engine.lower() == "whisper":
        USE_WHISPER = True
    else:
        USE_WHISPER = False


    return {"message": f"Switched to {'Whisper' if USE_WHISPER else 'Google STT'}"}


@router.websocket("/ws")
async def speech_websocket(websocket: WebSocket):
    """Handles WebSocket connections for live speech recognition."""
    print("🔌 Accepting Speech WebSocket connection...")
    await websocket_manager.connect(websocket)
    print("✅ Speech WebSocket connected!")

    try:
        while True:
            try:
                message = await websocket.receive_text()
                print(f"📥 Received WebSocket Message: {message}")

                # ✅ Handle start/stop commands safely
                if message.strip().lower() == "start":
                    await start_transcription()
                    await websocket_manager.broadcast_status("listening")
                elif message.strip().lower() == "stop":
                    await stop_transcription()
                    await websocket_manager.broadcast_status("stopped")

            except json.JSONDecodeError:
                print("❌ Error: Received malformed JSON, ignoring...")

            except asyncio.CancelledError:
                print("⚠️ WebSocket task was cancelled.")
                break  # ✅ Prevents crash on cancellation

    except WebSocketDisconnect:
        print("❌ Speech WebSocket disconnected (Client closed connection).")

    except Exception as e:
        print(f"⚠️ Unexpected WebSocket Error: {e}")

    finally:
        try:
            await websocket_manager.disconnect(websocket)
        except RuntimeError:
            print("⚠️ WebSocket was already closed, skipping cleanup.")

        print("🔴 WebSocket Cleanup Complete.")
