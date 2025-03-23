

import re
import ollama
from app.calls.ai.memory_store import retrieve_info
from app.calls.actions.action_handler import handle_action
from app.calls.call_utils import extract_final_intent  # ✅ Handles appointments/prayers

async def generate_ai_response(transcription, tone):
    """Generate an AI response that includes memory retrieval, tone awareness, and actions like appointments/prayer requests."""
    
    # ✅ Step 1: Detect Caller Tone
    print(f"🎭 Detected Caller Tone: {tone}")

    # ✅ Step 2: Retrieve Information from Memory (Church Info)
    memory_response = await retrieve_info()
    
    
    prompt = f"""
    You are an AI assistant for a church. Determine the caller's intent.  
    Possible intents:
    1. GENERAL_INFO - Asking about church services, times, location, beliefs, or events.
    2. APPOINTMENT - Wants to schedule a meeting, consultation, or event.
    3. PRAYER_REQUEST - Wants to submit a prayer request for themselves or someone else.
    4. GENERAL_QUESTION - Any other question not related to church services.
    **Only return one of the following on a single line:**
    GENERAL_INFO, APPOINTMENT, PRAYER_REQUEST, GENERAL_QUESTION

    **Caller Tone:** {tone.upper()}
    **Caller:** "{transcription}"

    **Classify the intent using only one of these labels: GENERAL_INFO, APPOINTMENT, PRAYER_REQUEST, GENERAL_QUESTION.**
    """
    
    response = ollama.chat(model="mistral:7b-instruct", messages=[{"role": "user", "content": prompt}])
    raw_intent = response['message']['content'].strip().upper()
    print(f"🤖 Detected Intent: {raw_intent}")
    intent = extract_final_intent(raw_intent)
    print(f"🎯 Classified Intent: {intent}")
    

    print(f"🎯 Detected Intent: {intent}")
    # ✅ Step 4: Handle Intent-Based Actions
    if intent == "APPOINTMENT" or intent == "PRAYER_REQUEST" or intent == "GENERAL_INFO":
        action_response = await handle_action(intent, transcription)
        return action_response  # ✅ Handle appointment/prayer requests

    # ✅ Step 5: General AI Response (Fallback)
    general_prompt = f"""
    You are a friendly AI assistant for a church.

    You are responding directly to a phone call, so speak naturally and warmly.
    Make sure to fill in actual facts such as contact number, email, and church name.

    Never say placeholders like [Phone Number] or [First Church of God].
    Instead, use these values below:

    - Church Name: First Church of God
    - Phone Number: 386-325-2814
    - Email: the1stchurchofgod@gmail.com
    - Address: 2915 St Johns Ave, Palatka, FL 32177
    - Website: https://www.palatka-firstchurchofgod.org

    **Caller Tone:** {tone.upper()}
    **Caller Message:** "{transcription}"
    **Relevant Info:** {memory_response}

    Respond clearly and concisely, as if you're speaking to someone over the phone.
    Only return the message you want to say out loud.
    """

    final_response = ollama.chat(model="mistral:7b-instruct", messages=[{"role": "user", "content": general_prompt}])
    answer = final_response['message']['content'].strip()

    print(f"🤖 AI Response: {answer}")
    return answer
