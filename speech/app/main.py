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
    """Graceful shutdown for Asyncio tasks."""
    print("🛑 Initiating graceful shutdown...")

    # ✅ Close all active WebSocket connections
    await websocket_manager.close_all()

    # ✅ Cancel all pending tasks
    tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
    for task in tasks:
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            print("✅ Task successfully cancelled.")

    print("🛑 Graceful shutdown complete.")


@app.on_event("shutdown")
async def shutdown_event():
    """Triggered when FastAPI shuts down."""
    await shutdown()


def handle_exit(signal, frame):
    """Handles CTRL+C or kill signals for clean shutdown."""
    print("\n🛑 Caught exit signal, shutting down...")
    asyncio.run(shutdown())
    sys.exit(0)


# ✅ Register exit handlers for CTRL+C (SIGINT) & kill (SIGTERM)
signal.signal(signal.SIGINT, handle_exit)
signal.signal(signal.SIGTERM, handle_exit)


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