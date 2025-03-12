import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.interview.ai_processing import get_preferred_response, clean_ai_response
from app.utils.websocket_manager import websocket_manager  # ✅ Import centralized WebSocket manager

router = APIRouter()

@router.websocket("/ws")
async def interview_websocket(websocket: WebSocket):
    """Handles AI WebSocket connections & sends responses."""
    print("🔌 Attempting to accept WebSocket connection")
    
    try:
        await websocket_manager.connect(websocket)
        print("✅ WebSocket connection accepted")

        while True:
            message = await websocket.receive_text()
            print(f"📥 Received transcription: {message}")

            preferred_response = get_preferred_response(message)
            cleaned_response = clean_ai_response(preferred_response)

            response_payload = json.dumps({
                "transcription": message,
                "responses": {"preferred": cleaned_response or "No response available."}
            })

            print(f"📤 Sending AI Response: {response_payload}")

            await websocket.send_text(response_payload)
            await websocket_manager.broadcast(response_payload)

    except WebSocketDisconnect:
        await websocket_manager.disconnect(websocket)
        print("❌ Interview WebSocket disconnected")

    except Exception as e:
        print(f"⚠️ Unexpected WebSocket Error: {e}")
        await websocket.close()
