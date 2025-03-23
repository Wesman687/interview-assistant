import base64
import io
from PIL import Image 
import httpx
import pytesseract
from app.config import GROQ_API_KEY
from app.interview.cleaning import clean_ai_response
from app.utils.websocket_manager import websocket_manager

def extract_text_from_image(image_base64: str) -> str:
    """Decode base64 image and extract text using Tesseract OCR."""

    # Remove base64 header if present (e.g., "data:image/png;base64,...")
    if "," in image_base64:
        image_base64 = image_base64.split(",")[1]

    try:
        # Decode base64 string and open as a PIL image
        image_data = base64.b64decode(image_base64)
        image = Image.open(io.BytesIO(image_data))

        # OCR using Tesseract
        extracted_text = pytesseract.image_to_string(image)
        return extracted_text.strip()

    except Exception as e:
        print(f"❌ Error processing image: {e}")
        return ""

async def evaluate_code_with_deepseek(code_text: str) -> dict:
    """Sends extracted code to DeepSeek API for evaluation."""
    payload = {
        "model": "deepseek-r1-distill-llama-70b",
        "messages": [
            {"role": "system", "content": "Evaluate this code and provide feedback. Format the response in HTML with Tailwind CSS classes so it can be rendered safely via dangerouslySetInnerHTML"},
            {"role": "user", "content": "Make it short and concise, enough to fit into half a screen."},
            {"role": "user", "content": code_text}
        ]
    }
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }


    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                json=payload,
                headers=headers
            )
            response.raise_for_status()  # ✅ Raise an error for bad responses (4xx, 5xx)
    except httpx.RequestError as e:
        print(f"❌ Network Error: {e}")
        return {"error": "Network request failed"}

    data = response.json()

    # ✅ Check if "choices" exist
    if "choices" not in data or not data["choices"]:
        return {"error": "No valid response from AI"}

    # ✅ Extract AI-generated message
    raw_content = data["choices"][0]["message"]["content"].strip()

    # ✅ Clean response
    followup_response = clean_ai_response(raw_content)
        # ✅ Step 3: Broadcast Follow-Up Questions
    full_response_payload = {
        "responses": {
            "followUp": followup_response or ["No follow-up questions available."]
        }
    }
    await websocket_manager.broadcast_interview_message(full_response_payload)
    print(f"📡 Sent Full AI Response (with Follow-Ups): {full_response_payload}")
    return {"code_info": followup_response}