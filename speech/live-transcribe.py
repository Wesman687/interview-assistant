import asyncio
import os
import queue
import pyaudio
import threading
import json
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from google.cloud import speech

# ✅ Set Google Cloud credentials
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.path.join(os.path.dirname(__file__), "service-account.json")

# ✅ FastAPI Server
app = FastAPI()

# ✅ Audio recording parameters
RATE = 16000
CHUNK = int(RATE / 10)  # 100ms

# ✅ Google Speech-to-Text client
client = speech.SpeechClient()
streaming_config = speech.StreamingRecognitionConfig(
    config=speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=RATE,
        language_code="en-US",
    ),
    interim_results=True,
)

# ✅ Global Variables
audio_queue = queue.Queue()
buffered_transcript = ""
lock = threading.Lock()
running = False  # ✅ Track if recognition is running
connected_clients = set()  # ✅ WebSocket Clients

# ✅ Detect Silence Timer (10s threshold)
silence_timer = None


def audio_callback(in_data, frame_count, time_info, status):
    """Capture audio from the microphone and put it in the queue."""
    audio_queue.put(in_data)
    return None, pyaudio.paContinue


def audio_generator():
    """Continuously fetch audio from the queue and send it to Google API."""
    while running:
        data = audio_queue.get()
        if data is None:
            break
        yield speech.StreamingRecognizeRequest(audio_content=data)


async def recognize_speech():
    """Process speech recognition and send transcriptions via WebSocket."""
    global buffered_transcript, silence_timer
    print("🎙️ Listening for speech...")

    responses = client.streaming_recognize(streaming_config, audio_generator())

    try:
        for response in responses:
            for result in response.results:
                transcript = result.alternatives[0].transcript.strip()

                if not transcript:
                    continue  # Skip empty results

                # ✅ Restart Silence Timer
                if silence_timer:
                    silence_timer.cancel()

                # ✅ Notify WebSocket clients
                await broadcast_message(json.dumps({"transcription": transcript}))

                # ✅ Detect if speech has ended (10 sec timeout)
                silence_timer = asyncio.create_task(notify_silence())

    except Exception as e:
        print(f"❌ Error in speech recognition: {e}")


async def notify_silence():
    """Notify the frontend after 10s of silence."""
    await asyncio.sleep(10)
    await broadcast_message(json.dumps({"transcription": "No speech detected, stopping listener."}))
    stop_transcription()


async def broadcast_message(message):
    """Send messages to all WebSocket clients."""
    for client in connected_clients:
        try:
            await client.send_text(message)
        except:
            connected_clients.remove(client)


def start_transcription():
    """Start audio stream and recognition."""
    print("🎤 Starting speech recognition...")
    global running
    if running:
        return
    running = True

    audio_interface = pyaudio.PyAudio()
    stream = audio_interface.open(
        format=pyaudio.paInt16,
        channels=1,
        rate=RATE,
        input=True,
        frames_per_buffer=CHUNK,
        stream_callback=audio_callback,
    )

    threading.Thread(target=asyncio.run, args=(recognize_speech(),), daemon=True).start()
    print("✅ Speech recognition started")


def stop_transcription():
    """Stop the audio stream and recognition."""
    global running
    if not running:
        return
    running = False
    audio_queue.put(None)
    print("🛑 Speech recognition stopped")


connected_clients = set()

@app.websocket("/speech-status")
async def speech_status_endpoint(websocket: WebSocket):
    """WebSocket to send live speech recognition status to frontend."""
    await websocket.accept()
    connected_clients.add(websocket)
    print("🔌 WebSocket Connected for Speech Status")

    try:
        while True:
            await asyncio.sleep(1)  # Keep connection alive
    except WebSocketDisconnect:
        connected_clients.remove(websocket)
        print("❌ WebSocket Disconnected")

def broadcast_status(status):
    """Send live status updates to all connected clients."""
    async def send():
        for client in connected_clients:
            try:
                await client.send_json({"status": status})
            except:
                pass  # Ignore disconnected clients

    asyncio.create_task(send())
    
@app.websocket("/speech/ws")
async def websocket_endpoint(websocket: WebSocket):
    """Handles WebSocket connections for the frontend."""
    await websocket.accept()
    connected_clients.add(websocket)
    print("🔌 New Speech WebSocket connection")

    try:
        while True:
            message = await websocket.receive_text()
            if message == "start":
                print("🎤 Starting transcription...")
                start_transcription()
            elif message == "stop":
                print("🛑 Stopping transcription...")
                stop_transcription()
    except WebSocketDisconnect:
        connected_clients.remove(websocket)
        print("❌ WebSocket client disconnected")


