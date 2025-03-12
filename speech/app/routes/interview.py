import asyncio
import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.interview.ai_processing import get_clean_response
from app.utils.websocket_manager import websocket_manager  # ✅ Import centralized WebSocket manager

router = APIRouter()

@router.websocket("/ws")
async def interview_websocket(websocket: WebSocket):
    """Handles AI WebSocket connections & processes responses."""
    print("🔌 Attempting to accept Interview WebSocket connection")

    try:
        await websocket_manager.connect(websocket)
        print("✅ Interview WebSocket connection accepted")

        while True:
            try:
                print("🛑 Waiting for a message from the WebSocket...")
                
                # ✅ FORCE WebSocket to listen for a message
                message = await websocket.receive_text()
                
                # ✅ Log received message
                print(f"📥 Interview WebSocket Received RAW: {message}")

                # ✅ Ensure JSON is properly parsed
                try:
                    message_data = json.loads(message)
                    
                    # ✅ Handle possible double-encoded JSON
                    if isinstance(message_data.get("transcription"), str):
                        try:
                            print(f"🔍 Found double-encoded JSON: {message_data['transcription']}")
                            message_data = json.loads(message_data["transcription"])
                        except json.JSONDecodeError:
                            print("❌ Failed to decode double-encoded JSON")
                    
                    transcription = message_data.get("transcription", "")
                except json.JSONDecodeError:
                    print(f"❌ Failed to decode JSON: {message}")
                    transcription = message  # Fallback if JSON fails

                # ✅ Debug: Confirm transcription content
                print(f"📜 Processing Transcription: {transcription}")

                # ✅ AI Processing
                cleaned_response = get_clean_response(transcription)  # ✅ AI Call
                print(f"🤖 AI Response from Groq API: {cleaned_response}")  # ✅ Debugging

                response_payload = json.dumps({
                    "transcription": transcription,
                    "responses": {"preferred": cleaned_response or "No response available."}
                })

                print(f"📤 Sending AI Response to frontend: {response_payload}")
                await websocket.send_text(response_payload)

            except asyncio.CancelledError:
                print("⚠️ Task was cancelled. WebSocket is closing safely.")
                break  # ✅ Prevents crash

            except Exception as e:
                print(f"⚠️ Unexpected WebSocket Error: {e}")
                await websocket.close()
                break  # ✅ Exit loop on error

    except WebSocketDisconnect:
        await websocket_manager.disconnect(websocket)
        print("❌ Interview WebSocket disconnected")

    except Exception as e:
        print(f"⚠️ Unexpected WebSocket Error: {e}")
        await websocket.close()
