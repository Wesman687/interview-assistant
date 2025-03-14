import asyncio
import multiprocessing
from app.utils.websocket_manager import websocket_manager
from fastapi import FastAPI
import uvicorn
from app.routes.interview import router as interview_router
from app.routes.status import router as status_router
from app.routes.speech import router as speech_router
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Live Transcribe & Interview Assistant")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # ✅ Allow all origins
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],  # ✅ WebSockets use GET
    allow_headers=["*"],
)
# ✅ Include API routes
app.include_router(interview_router, prefix="/interview")
app.include_router(status_router, prefix="/status")
app.include_router(speech_router, prefix="/speech")
import asyncio
import signal
import sys
from fastapi import FastAPI
import uvicorn
from app.routes.speech import router as speech_router
from app.routes.interview import router as interview_router
from app.routes.status import router as status_router
from fastapi.middleware.cors import CORSMiddleware
from app.utils.websocket_manager import websocket_manager

app = FastAPI(title="Live Transcribe & Interview Assistant")
# taskkill /F /IM uvicorn.exe




app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ Include API routes
app.include_router(speech_router, prefix="/speech")
app.include_router(interview_router, prefix="/interview")
app.include_router(status_router, prefix="/status")



@app.get("/")
async def root():
    return {"message": "Live Transcriber is running!"}


async def shutdown():
    """Gracefully shutdown the WebSocket manager and other async processes."""
    await websocket_manager.close_all()
    print("✅ Server shut down successfully.")


def run():
    """Run Uvicorn with Windows-safe multiprocessing."""
    print("🚀 Starting FastAPI Server...")
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)


if __name__ == "__main__":
    multiprocessing.freeze_support()  # ✅ Fix for Windows multiprocessing issues
    try:
        run()
    except KeyboardInterrupt:
        print("🛑 Server manually stopped.")
        asyncio.run(shutdown())










def run():
    """Run Uvicorn with Windows-safe multiprocessing."""
    if __name__ == "__main__":
        multiprocessing.freeze_support()  # ✅ Prevents Windows multiprocessing issues
        try:
            print("🚀 Starting FastAPI Server...")
            uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
        except KeyboardInterrupt:
            print("🛑 Server manually stopped.")
            asyncio.run(shutdown())


if __name__ == "__main__":
    run()