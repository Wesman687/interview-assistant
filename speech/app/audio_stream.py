import pyaudio
import queue
import threading
import websockets
import asyncio
import json
import sounddevice as sd
import numpy as np
from google.cloud import speech
import google.auth

# Google Cloud Speech-to-Text setup
client = speech.SpeechClient()
config = speech.RecognitionConfig(
    encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
    sample_rate_hertz=16000,
    language_code="en-US",
    enable_automatic_punctuation=True,
)
streaming_config = speech.StreamingRecognitionConfig(
    config=config, interim_results=True
)

# Queue for real-time audio streaming
audio_queue = queue.Queue()

# FastAPI WebSocket URL
FASTAPI_WS_URL = "ws://your-fastapi-server.com/ws/audio"

# Capture audio callback
def audio_callback(indata, frames, time, status):
    if status:
        print(f"Error: {status}", flush=True)
    audio_queue.put(indata.copy())

# Convert audio and send to Google STT
def process_audio():
    requests = (speech.StreamingRecognizeRequest(audio_content=chunk.tobytes())
                for chunk in iter(audio_queue.get, None))
    
    responses = client.streaming_recognize(streaming_config, requests)
    
    for response in responses:
        for result in response.results:
            if result.is_final:
                text = result.alternatives[0].transcript
                print(f"Transcript: {text}")
                asyncio.run(send_to_fastapi(text))

# Send transcript to FastAPI WebSocket
async def send_to_fastapi(text):
    async with websockets.connect(FASTAPI_WS_URL) as websocket:
        await websocket.send(json.dumps({"text": text}))

# Start real-time audio capture
def start_audio_stream():
    with sd.InputStream(callback=audio_callback, channels=1, samplerate=16000, dtype="int16"):
        process_audio()

# Run in a separate thread
threading.Thread(target=start_audio_stream, daemon=True).start()

print("🎤 Listening for audio...")
while True:
    pass  # Keep script running
