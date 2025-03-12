import asyncio
import os
import queue
import pyaudio
import threading
import json
from google.cloud import speech
from app.interview.ai_processing import get_clean_response
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
    global client
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
                    
                    # ✅ Store full sentence
                    buffered_transcript += " " + transcript  

                    # ✅ Step 1: Send Transcription Immediately
                    transcription_payload = {
                        "transcription": buffered_transcript.strip(),
                        "responses": {}  # Empty responses at first
                    }
                    await websocket_manager.broadcast_message(transcription_payload)
                    print(f"📡 Sent Immediate Transcription: {transcription_payload}")

                    # ✅ Step 2: Process AI Response Separately
                    async def process_ai_response(transcription_text):
                        try:
                            print(f"⏳ Processing AI Response for: {transcription_text}")

                            # ✅ Log BEFORE calling AI processing
                            print("🚀 Calling get_clean_response()...")

                            cleaned_response = await get_clean_response(transcription_text)  # ✅ AI Call
                            
                            # ✅ Log AFTER AI processing
                            print(f"✅ AI Processing Complete: {cleaned_response}")

                            response_payload = {
                                "transcription": transcription_text,
                                "responses": {"preferred": cleaned_response or "No response available."}
                            }

                            await websocket_manager.broadcast_message(response_payload)
                            print(f"📡 Sent AI Response: {response_payload}")

                        except Exception as e:
                            print(f"❌ ERROR in process_ai_response: {e}")

                        finally:
                            print("🛑 AI Processing Task Finished.")

                    # ✅ Run AI processing asynchronously
                    print("🚀 Creating AI Processing Task...")
                    task = asyncio.create_task(process_ai_response(buffered_transcript.strip()))
                    await asyncio.sleep(0)
                    print(f"✅ AI Processing Task Created: {task}")

                    # ✅ Reset transcript after sending
                    buffered_transcript = ""

                else:
                    print(f"📝 Interim: {transcript}")  # ✅ Debugging interim results

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
    print("🎤 Starting speech recognition...")
    global running
    if running:
        return
    running = True
    await websocket_manager.broadcast_status("listening")
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

    await websocket_manager.broadcast_status("stopped")
    audio_queue.put(None)
    print("🛑 Speech recognition stopped")
