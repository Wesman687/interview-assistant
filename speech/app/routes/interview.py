import asyncio
import json
from fastapi import APIRouter, HTTPException, Query, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from app.config import GROQ_API_KEY
from app.interview.cleaning import get_clean_response
from app.interview.get_company import fetch_company_info
from app.interview.get_tech_stack import fetch_tech_stack
from app.utils.websocket_manager import websocket_manager  # ✅ Import centralized WebSocket manager

router = APIRouter()

@router.websocket("/ws")
async def interview_websocket(websocket: WebSocket):
    """Handles AI WebSocket connections & only broadcasts responses."""
    print("🔌 Accepting WebSocket connection...")
    await websocket_manager.connect(websocket)
    print("✅ WebSocket connected!")

    try:
        while True:
            await asyncio.sleep(30)  # ✅ Keep connection alive

    except WebSocketDisconnect:
        print("❌ WebSocket disconnected (Client likely closed connection).")

    except Exception as e:
        print(f"⚠️ Unexpected WebSocket Error: {e}")

    finally:
        try:
            await websocket_manager.disconnect(websocket)
        except RuntimeError:
            print("⚠️ WebSocket was already closed, skipping cleanup.")



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

        if "error" in response:
            return JSONResponse(content={"error": response["error"]}, status_code=500)

        return JSONResponse(content=response, status_code=200)  # ✅ Ensure proper JSON response

    except Exception as e:
        return JSONResponse(content={"error": f"Error fetching tech stack: {str(e)}"}, status_code=500)