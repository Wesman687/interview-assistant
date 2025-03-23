

import asyncio
from app.utils.twilio_client import inject_twi_response_with_stream, inject_twi_say_only
from app.utils.websocket_manager import websocket_manager
from app.calls.ai.deepseek_response import generate_ai_response
from app.calls.call_utils import analyze_tone, clean_deepseek_response

async def process_call(transcript, source):
    """Process the received Twilio audio and transcribe it."""
    if not transcript:
        print("⚠️ No transcript received.")
        return
    print("🔊 Processing Twilio call...")
    print(f"🎤 Twilio Transcript: {transcript}")
    tone = await analyze_tone(transcript)
    print(f"🎭 Caller Tone: {tone}")
    response = await generate_ai_response(transcript, tone)
    final_response = await clean_deepseek_response(response)
    print(f"🧠 AI Response: {final_response}")     
    inject_twi_response_with_stream(websocket_manager.call_sid, final_response)
