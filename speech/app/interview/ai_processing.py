
import re
from app.interview.groq.preferred_response import get_preferred_response  # ✅ Groq API Call

def get_clean_response(transcription: str) -> str:
    """Fetch and clean AI response for a given transcription."""
    preferred_response = get_preferred_response(transcription)  # ✅ AI Call

    return clean_ai_response(preferred_response)

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
