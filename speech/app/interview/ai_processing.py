from app.interview.cleaning import get_clean_response
from app.interview.groq.preferred_response import get_follow_up_questions
from app.utils.websocket_manager import websocket_manager


async def process_ai_response(transcription_text):
    try:
        print(f"⏳ Processing AI Response for: {transcription_text}")

        # ✅ Log BEFORE calling AI processing
        print("🚀 Calling get_clean_response()...")

        cleaned_response = await get_clean_response(transcription_text)  # ✅ AI Call
        
        # ✅ Log AFTER AI processing
        print(f"✅ AI Processing Complete: {cleaned_response}")

        response_payload = {
            "transcription": transcription_text,
            "responses": {"preferred": cleaned_response or "No response available."}
        }

        await websocket_manager.broadcast_message(response_payload)
        print(f"📡 Sent AI Response: {response_payload}")
        
         # ✅ Step 2: Fetch Follow-Up Questions
        print("🚀 Fetching follow-up questions...")
        follow_up_questions = await get_follow_up_questions(transcription_text, cleaned_response)  # ✅ Fetch
        print(f"✅ Follow-Up Questions Received: {follow_up_questions}")

        cleaned_response = await get_clean_response(follow_up_questions)
        # ✅ Step 3: Broadcast Follow-Up Questions
        full_response_payload = {
            "transcription": transcription_text,
            "responses": {
                "preferred": cleaned_response or "No response available.",
                "followUp": follow_up_questions or ["No follow-up questions available."]
            }
        }
        await websocket_manager.broadcast_message(full_response_payload)
        print(f"📡 Sent Full AI Response (with Follow-Ups): {full_response_payload}")

    except Exception as e:
        print(f"❌ ERROR in process_ai_response: {e}")

    finally:
        print("🛑 AI Processing Task Finished.")
