
import asyncio
import io
import os
from PIL import Image 
import imghdr
from fastapi import APIRouter, File, HTTPException, Query, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import pytesseract
from app.config import GROQ_API_KEY
from app.interview.cleaning import clean_ai_response
from app.interview.get_code import evaluate_code_with_deepseek, extract_text_from_image
from app.interview.get_company import fetch_company_info
from app.interview.get_tech_stack import fetch_tech_stack
from app.utils.websocket_manager import websocket_manager  # ✅ Import centralized WebSocket manager
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
router = APIRouter()

@router.websocket("/ws")
async def interview_websocket(websocket: WebSocket):
    """Handles WebSocket connections for interview responses."""
    print("🔌 Accepting Interview WebSocket connection...")
    await websocket_manager.connect(websocket, "interview")
    print("✅ Interview WebSocket connected!")

    try:
        while True:
            message = await websocket.receive_text()
            print(f"📥 Interview WebSocket Received: {message}")

            # ✅ Process interview-specific messages
            await websocket_manager.broadcast(message, "interview")

    except WebSocketDisconnect:
        print("❌ Status WebSocket disconnected.")
    except asyncio.CancelledError:
        print("⚠️ WebSocket task cancelled, cleaning up...")
    except Exception as e:
        print(f"❌ Unexpected WebSocket Error: {e}")
    finally:
        await websocket_manager.disconnect(websocket, "status")
        
@router.post("/ss")
async def get_ss(file: UploadFile = File(...)):
    """ Accepts an image file, extracts code, and evaluates it with DeepSeek. """

    try:
        # ✅ Read the file content into memory
        image_bytes = await file.read()
        print(f"🧪 Received file: {file.filename}, Content-Type: {file.content_type}")
        print(f"🧪 First 20 bytes: {image_bytes[:20]}")
        print(f"🧪 Detected format: {imghdr.what(None, h=image_bytes)}")
        # ✅ Open the image using PIL from bytes
        image = Image.open(io.BytesIO(image_bytes))

        # ✅ OCR the image
        text = pytesseract.image_to_string(image).strip()

    except Exception as e:
        print(f"❌ Error processing image: {e}")
        return {"error": "Failed to process image"}

    if not text:
        return {"error": "No readable text found in the image"}

    # 🧠 Evaluate code with DeepSeek
    prompt = await evaluate_code_with_deepseek(text)

    return {
        "filename": file.filename,
        "extracted_text": text,
        "deepseek_response": prompt
    }


@router.get("/company-info")
async def get_company_info(company: str = Query(..., title="Company Name")):
    """Fetches quick company details from DeepSeek R1."""
    print(f"🔍 Fetching company info for: {company}")
    try:
        response = await fetch_company_info(company)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching company info: {str(e)}")

class TechStackRequest(BaseModel):
    jobInfo: str

@router.post("/tech-stack")
async def get_tech_stack(request: TechStackRequest):
    """Fetches tech stack details and returns it as JSON."""
    try:
        print(f"🔍 Fetching Tech Stack Data for: {request.jobInfo}")
        response = await fetch_tech_stack(request.jobInfo)
        print(f"✅ Tech Stack Data Fetched Successfully!")
        if "error" in response:
            return JSONResponse(content={"error": response["error"]}, status_code=500)
        print("✅ Tech Stack Data Fetched Successfully!")

        return JSONResponse(content=response, status_code=200)  # ✅ Ensure proper JSON response

    except Exception as e:
        return JSONResponse(content={"error": f"Error fetching tech stack: {str(e)}"}, status_code=500)
    