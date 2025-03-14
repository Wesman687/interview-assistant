import asyncio
import os
import queue
import numpy as np
import pyaudio
import threading
from google.cloud import speech
from app.interview.ai_processing import process_ai_response
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
        model="latest_long",  # ⬅️ Switch to a model that handles longer speech
        use_enhanced=True,
        speech_contexts=[speech.SpeechContext(phrases=["tell me about your experience"])]  # ⬅️ Helps prevent truncation
    ),
    interim_results=True,  # ✅ Ensures continuous updates
    single_utterance=False,  # ✅ Allow longer speech instead of finalizing too early
)
# ✅ Audio Handling
RATE = 16000
CHUNK = int(RATE / 10)
audio_queue = queue.Queue()
buffered_transcript = ""
lock = threading.Lock()
running = False  # ✅ Track if recognition is running
connected_clients = set()  # ✅ WebSocket Clients
running = False  # ✅ Track if recognition is running
idle = False  # ✅ Track if we are in Idle Mode


# ✅ Detect Silence Timer (10s threshold)
silence_timer = None

def is_silent(audio_chunk, threshold=500):
    """Check if an audio chunk is silent."""
    audio_data = np.frombuffer(audio_chunk, dtype=np.int16)
    return np.max(np.abs(audio_data)) < threshold  # ✅ Ignore low-volume sounds

def audio_callback(in_data, frame_count, time_info, status):
    """Capture audio from the microphone and wake up from idle if needed."""
    global idle, running
    if not running:
        return None, pyaudio.paAbort

    if idle:  
        print("🎤 Voice detected! Exiting Idle Mode and restarting transcription...")
        idle = False  
        asyncio.ensure_future(start_transcription()) 

    if not is_silent(in_data):  # ✅ Only queue non-silent audio
        audio_queue.put(in_data)

    return None, pyaudio.paContinue

def audio_generator():
    """Continuously fetch audio from the queue and send it to Google API."""
    while running:
        try:
            data = audio_queue.get(timeout=2)  # ✅ Use timeout to avoid deadlock
            if data is None:
                print("⏳ Audio queue empty, entering idle mode...")
                continue  # ✅ Instead of stopping, keep waiting
            print(f"🎤 Streaming {len(data)} bytes of audio")
            yield speech.StreamingRecognizeRequest(audio_content=data)
        except queue.Empty:
            print("⏳ Audio queue empty, stopping generator...")
            break  # ✅ Prevents iterating on an empty queue

async def recognize_speech():
    global client
    global buffered_transcript, silence_timer
    print("🎙️ Listening for speech...")
    while running:
        responses = await asyncio.to_thread(client.streaming_recognize, streaming_config, audio_generator())

        try:
            for response in responses:
                for result in response.results:
                    transcript = result.alternatives[0].transcript.strip()

                    if not transcript:
                        continue  # ✅ Skip empty results
                    await websocket_manager.broadcast_status("speaking")
                    if result.is_final:  # ✅ Only send complete sentences
                        print(f"📝 Finalized: {transcript}")
                        await websocket_manager.broadcast_status("listening")
                        # ✅ Store full sentence
                        buffered_transcript += " " + transcript  

                        # ✅ Step 1: Send Transcription Immediately
                        transcription_payload = {
                            "transcription": buffered_transcript.strip(),
                        }
                        await websocket_manager.broadcast_message(transcription_payload)
                        print(f"📡 Sent Immediate Transcription: {transcription_payload}")                    

                        # ✅ Run AI processing asynchronously
                        print("🚀 Creating AI Processing Task...")
                        task = asyncio.create_task(process_ai_response(buffered_transcript.strip()))
                        await asyncio.sleep(0)
                        print(f"✅ AI Processing Task Created: {task}")

                        # ✅ Reset transcript after sending
                        buffered_transcript = ""

                        # ✅ Refresh Google SpeechClient after every finalized sentence
                        print("🔄 Refreshing Google SpeechClient to prevent lag...")
                        client = speech.SpeechClient()  # ✅ Throw away the old client and start fresh

                    else:
                        print(f"📝 Interim: {transcript}")  # ✅ Debugging interim results

                    if silence_timer:
                        silence_timer.cancel()
                    silence_timer = asyncio.create_task(notify_silence())

        except queue.Empty:
            print("🔕 No more audio in queue, stopping generator...")
        except Exception as e:
            print(f"❌ Error in speech recognition: {e}")

async def notify_silence():
    """Enter Idle Mode after 5 seconds of silence."""
    global running, idle

    await asyncio.sleep(5)  # ✅ If silence persists, enter idle mode

    if running:
        print("🔕 No speech detected. Entering Idle Mode...")
        idle = True  # ✅ Set Idle Mode ON
        await websocket_manager.broadcast_status("idle")
        await stop_transcription()  # ✅ Stop Google Streaming


async def start_transcription():
    """Start transcription only if not already running."""
    global running, idle, client

    if running:
        return
    running = True
    idle = False  # ✅ Exit Idle Mode

    print("🎤 Starting fresh speech recognition...")
    
    # ✅ Always create a fresh SpeechClient on start
    client = speech.SpeechClient()

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
    print("✅ Fresh speech recognition started")





async def stop_transcription():
    """Stop the audio stream and recognition completely."""
    global running, audio_queue

    if not running:
        return
    running = False  # ✅ Stop further streaming

    await websocket_manager.broadcast_status("stopped")
    
    # ✅ Fully clear the audio queue to remove old data
    with audio_queue.mutex:
        audio_queue.queue.clear()

    # ✅ Properly end the generator
    audio_queue.put(None)  # 🔥 Sends a signal to stop `audio_generator()`

    # ✅ Reset Google SpeechClient (for safety)
    global client
    client = None

    print("🛑 Speech recognition fully stopped.")

