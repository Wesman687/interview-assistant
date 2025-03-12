
import json
import re
from app.interview.groq.preferred_response import get_preferred_response  # ✅ Groq API Call

async def get_clean_response(transcription: str) -> str:
    """Fetch and clean AI response for a given transcription."""
    try:
        print(f"🚀 Fetching AI response for: {transcription}")

        preferred_response = get_preferred_response(transcription)  # ✅ AI Call
        print(f"✅ Raw AI Response: {preferred_response}")

        if isinstance(preferred_response, dict):
            print(f"⚠️ Fixing dict issue in AI response: {preferred_response}")
            preferred_response = json.dumps(preferred_response)  # ✅ Convert to string

        cleaned_response = clean_ai_response(preferred_response)
        print(f"✅ Cleaned AI Response: {cleaned_response}")

        return cleaned_response

    except Exception as e:
        print(f"❌ ERROR in get_clean_response: {e}")
        return "AI processing failed."

def clean_ai_response(response: str) -> str:
    """Remove <think> tags and return only the formatted response."""
    
    # ✅ Remove <think> tags
    response = re.sub(r"<think>.*?</think>", "", response, flags=re.DOTALL)

    # ✅ Trim extra spaces
    response = response.strip()

    # ✅ Find the first <h2> tag and keep everything after it
    match = re.search(r"<h2.*?>", response)
    if match:
        response = response[match.start():]  # ✅ Slice response from <h2> onwards

    return response
