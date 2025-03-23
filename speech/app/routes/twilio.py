
import asyncio
import json
from xml.etree.ElementTree import Element, SubElement, tostring
from fastapi import APIRouter, Request, Response, WebSocket, WebSocketDisconnect
from app.calls.call_transcribe import  pause_transcription, start_call_transcription
from app.config import YOUR_DOMAIN
from app.utils.websocket_manager import websocket_manager  # ✅ Use existing WebSocketManager

router = APIRouter()

@router.websocket("/ws")
async def twilio_websocket(websocket: WebSocket):
    """Handles Twilio's live audio WebSocket stream."""
    print("🔌 Accepting Twilio WebSocket connection...")
    try:
        await websocket_manager.connect(websocket, "twilio")
        print("✅ Twilio WebSocket successfully connected!")

    except Exception as e:
        print(f"❌ WebSocket Connection Failed: {e}")
    print("🔌 Twilio WebSocket connected!")

    call_sid = None  # Call ID
    caller_number = None  # Phone number
    active_calls = {}  # 🔥 Store caller info by stream ID
      # ✅ Start transcription process

    try:
        while True:
            data = await websocket.receive_text()
            parsed_data = json.loads(data)
            await websocket.send_text(json.dumps({"event": "keepalive"})) 
            # ✅ Handle Call Start Event
            if parsed_data["event"] == "start":
                call_sid = parsed_data["start"]["callSid"]
                caller_number = parsed_data["start"].get("phoneNumber", "Unknown")
                websocket_manager.call_sid = call_sid

                # 🔥 Store caller info
                active_calls[call_sid] = {"caller": caller_number}
                print(f"📞 Incoming call from: {caller_number} (SID: {call_sid})")

                # ✅ Notify WebSocket clients

            # ✅ Handle Incoming Audio Data
            elif parsed_data["event"] == "media":
                audio_payload = parsed_data["media"]["payload"]

                # 🔥 Process the audio
                asyncio.create_task(start_call_transcription(audio_payload))

            # ✅ Handle Call End
            elif parsed_data["event"] == "stop":
                print(f"🛑 Call ended: {caller_number} (SID: {call_sid})")

                if call_sid in active_calls:
                    del active_calls[call_sid]  # Cleanup
    except WebSocketDisconnect:
        print("❌ Twilio WebSocket disconnected.")
        await pause_transcription()
    except Exception as e:
        print(f"⚠️ Error in Twilio WebSocket: {e}")
        await pause_transcription()


