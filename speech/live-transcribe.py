import asyncio
import os
import queue
import pyaudio
import threading
import json
import websockets
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from google.cloud import speech
import uvicorn

# ✅ Set Google Cloud credentials
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.path.join(os.path.dirname(__file__), "service-account.json")

# ✅ FastAPI Server
app = FastAPI()

# ✅ Audio recording parameters
RATE = 16000
CHUNK = int(RATE / 5)  # 100ms
INTERVIEW_WS_URL = "ws://127.0.0.1:5000/interview/ws" 

# ✅ Google Speech-to-Text client
client = speech.SpeechClient()
streaming_config = speech.StreamingRecognitionConfig(
    config=speech.RecognitionConfig(
    encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
    sample_rate_hertz=RATE,
    language_code="en-US",
    enable_automatic_punctuation=True,  # ✅ Adds punctuation for better readability
    enable_word_time_offsets=True,  # ✅ Helps detect pauses in speech
    model="phone_call",  # ✅ Uses Google's improved model
    use_enhanced=True  # ✅ Enables enhanced speech recognition
),interim_results=True,)


# ✅ Global Variables
audio_queue = queue.Queue()
buffered_transcript = ""
lock = threading.Lock()
running = False  # ✅ Track if recognition is running
connected_clients = set()  # ✅ WebSocket Clients

# ✅ Detect Silence Timer (10s threshold)
silence_timer = None


async def shutdown():
    """Graceful shutdown for Asyncio tasks."""
    tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
    for task in tasks:
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            print("✅ Task successfully cancelled.")

    print("🛑 Graceful shutdown complete.")


if __name__ == "__main__":
    try:
        print("🚀 Starting FastAPI Speech WebSocket Server...")
        uvicorn.run(app, host="0.0.0.0", port=8000)
    except KeyboardInterrupt:
        print("🛑 Server manually stopped.")
        asyncio.run(shutdown())
        




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
    global buffered_transcript, silence_timer
    print("🎙️ Listening for speech...")

    responses = client.streaming_recognize(streaming_config, audio_generator())

    try:
        for response in responses:
            for result in response.results:
                transcript = result.alternatives[0].transcript.strip()

                if not transcript:
                    continue  # ✅ Skip empty results

                if result.is_final:  # ✅ Only send complete sentences
                    print(f"📝 Finalized: {transcript}")
                    buffered_transcript += " " + transcript  # ✅ Store full sentence
                    await broadcast_message(json.dumps({"transcription": buffered_transcript.strip()}))
                    buffered_transcript = ""  # ✅ Reset transcript after sending
                else:
                    print(f"📝 Interim: {transcript}")  # ✅ Debugging interim results

                if silence_timer:
                    silence_timer.cancel()
                silence_timer = asyncio.create_task(notify_silence())

    except Exception as e:
        print(f"❌ Error in speech recognition: {e}")



        
async def broadcast_status(status):
    """Send live status updates to all connected clients."""
    async def send():
        for client in connected_clients:
            print(f"📡 Sending status update to client {status}")
            try:
                await client.send_json({"status": status})
            except:
                pass  # Ignore disconnected clients

    asyncio.create_task(send())



async def notify_silence():
    """Notify the frontend after 2s of silence."""
    await asyncio.sleep(5)

    if connected_clients:
        await broadcast_status("silent")  # ✅ Make sure it's awaited
        await broadcast_message(json.dumps({"transcription": "No speech detected."}))

    stop_transcription()

async def broadcast_message(message):
    """Send messages to all WebSocket clients and forward to Interview WebSocket."""
    disconnected_clients = []  # Track disconnected clients

    for client in connected_clients.copy():
        try:
            await client.send_text(message)
        except:
            disconnected_clients.append(client)  # Mark client for removal

    # ✅ Remove disconnected clients after iteration
    for client in disconnected_clients:
        connected_clients.remove(client)

    # ✅ Forward transcript to the Interview WebSocket (AI Processing)
    await forward_to_interview_ws(message)


async def forward_to_interview_ws(message):
    """Ensure the transcript gets forwarded to the Interview Assistant WebSocket."""
    try:
        print(f"📤 Forwarding to Interview API: {message}")
        async with websockets.connect(INTERVIEW_WS_URL) as ws:
            await ws.send(message)
            print(f"📤 Successfully Forwarded to Interview API: {message}")
    except Exception as e:
        print(f"❌ Error forwarding transcript: {e}")
        await asyncio.sleep(2)  # Retry delay
        await forward_to_interview_ws(message)  # ✅ Retry on failure

async def start_transcription():
    """Start audio stream and recognition."""
    print("🎤 Starting speech recognition...")
    global running
    if running:
        return
    running = True
    await broadcast_status("listening")
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


async def stop_transcription():
    """Stop the audio stream and recognition."""
    global running
    if not running:
        return
    running = False
    await broadcast_status("stopped")
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
                await start_transcription()
            elif message == "stop":
                await stop_transcription()
    except WebSocketDisconnect:
        print("❌ WebSocket client disconnected")
    except Exception as e:
        print(f"⚠️ Unexpected WebSocket error: {e}")
    finally:
        connected_clients.discard(websocket)  # ✅ Use discard to avoid KeyError




