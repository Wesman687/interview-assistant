import asyncio
import os
import signal
import sys
from fastapi import FastAPI
from app.utils.websocket_manager import websocket_manager
import uvicorn
from fastapi.middleware.cors import CORSMiddleware
from app.routes.speech import router as speech_router
from app.routes.interview import router as interview_router
from app.routes.twilio import router as twilio_router
from app.routes.twiml import router as twiml_router
from app.utils.event_loop import EVENT_LOOP

app = FastAPI(title="Live Transcribe & Interview Assistant")

# ✅ Ensure `app.state` exists
if not hasattr(app, "state"):
    print("❌ app.state does not exist! Creating it now...")
    app.state = type("State", (), {})()  # ✅ Creates an attribute-based state object


if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(twiml_router, prefix="/twiml")
app.include_router(twilio_router, prefix="/twilio")
app.include_router(speech_router, prefix="/speech")    
app.include_router(interview_router, prefix="/interview")

# ✅ Include API routes

@app.get("/")
async def root():
    return {"message": "Live Transcriber is running!"}
@app.on_event("startup")
async def startup_event():
    global EVENT_LOOP
    """✅ Store FastAPI's event loop globally."""
    EVENT_LOOP = asyncio.get_running_loop()  # 🔥 Save loop globally
    print("✅ FastAPI event loop stored globally.")

async def shutdown():
    """Gracefully shutdown WebSocket connections and services."""
    print("🛑 Broadcasting shutdown message...")
    await websocket_manager.broadcast('{"type": "shutdown", "status": "shutdown"}', "speech")
    await asyncio.sleep(3)  # 🕒 Allow clients to close
    await websocket_manager.close_all()
    print("✅ Server shut down successfully.")

    # 🔥 Kill all Uvicorn processes to prevent stuck processes
    os.system("taskkill /IM python.exe /F")  # 🔴 Force close all Python instances (Windows only)

    sys.exit(0)

def start_server():
    """Run Uvicorn server."""
    print("🚀 Starting FastAPI Server...")
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=False)

if __name__ == "__main__":
    EVENT_LOOP.run_forever()
    
    # ✅ Handle shutdown with signal handlers
    for sig in (signal.SIGINT, signal.SIGTERM):
        EVENT_LOOP.add_signal_handler(sig, lambda: asyncio.create_task(shutdown()))

    try:
        start_server()
    except KeyboardInterrupt:
        print("🛑 Server manually stopped.")
        EVENT_LOOP.run_until_complete(shutdown())
