import asyncio
import os
import queue
import pyaudio
import threading
import json
from google.cloud import speech
from app.utils.websocket_manager import websocket_manager

# ✅ Google Cloud Speech-to-Text
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "service-account.json"

client = speech.SpeechClient()
streaming_config = speech.StreamingRecognitionConfig(
    config=speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=16000,
        language_code="en-US",
        enable_automatic_punctuation=True,
        enable_word_time_offsets=True,
        model="phone_call",
        use_enhanced=True
    ),
    interim_results=True,
)

# ✅ Audio Handling
RATE = 16000
CHUNK = int(RATE / 5)
audio_queue = queue.Queue()
running = False
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
    """Process speech recognition and send transcriptions."""
    global running, silence_timer
    print("🎙️ Listening for speech...")

    responses = client.streaming_recognize(streaming_config, audio_generator())

    try:
        for response in responses:
            for result in response.results:
                transcript = result.alternatives[0].transcript.strip()

                if not transcript:
                    continue

                await websocket_manager.broadcast_status("speaking")

                if result.is_final:
                    print(f"📝 Finalized: {transcript}")
                    await websocket_manager.broadcast_message(transcript)
                else:
                    print(f"📝 Interim: {transcript}")

                # ✅ Restart Silence Timer
                if silence_timer:
                    silence_timer.cancel()
                silence_timer = asyncio.create_task(notify_silence())

    except Exception as e:
        print(f"❌ Error in speech recognition: {e}")

async def notify_silence():
    """Notify frontend after 5s of silence."""
    await asyncio.sleep(5)
    if running:
        await websocket_manager.broadcast_status("silent")
        await websocket_manager.broadcast_message("No speech detected.")
        await stop_transcription()

async def start_transcription():
    """Start audio stream and recognition."""
    global running
    if running:
        return
    running = True

    await websocket_manager.broadcast_status("listening")
    asyncio.create_task(recognize_speech())
    print("✅ Speech recognition started")

async def stop_transcription():
    """Stop the audio stream and recognition."""
    global running
    if not running:
        return
    running = False

    await websocket_manager.broadcast_status("stopped")
    audio_queue.put(None)
    print("🛑 Speech recognition stopped")
