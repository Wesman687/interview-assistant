
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

def clean_ai_response(content: str) -> str:
    """Cleans AI-generated responses by removing unwanted tags and trimming extra spaces."""
    if not content or not isinstance(content, str):
        return "Error: Invalid response format"
    # ✅ Remove <think>...</think> blocks
    content = re.sub(r"<think>.*?</think>", "", content, flags=re.DOTALL)

    # ✅ Trim leading/trailing whitespace
    content = content.strip()

    # ✅ Optional: Keep only HTML from first <h2> or <p> tag onwards (ensures proper structure)
    match = re.search(r"<(h2|p|ul|ol|div|section).*?>", content)
    if match:
        content = content[match.start():]  # ✅ Slice response from first valid HTML tag onwards

    return content