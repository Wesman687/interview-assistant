import asyncio
import os
import queue
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
running = False  # ✅ Track if recognition is running
idle = False  # ✅ Track if we are in Idle Mode


# ✅ Detect Silence Timer (10s threshold)
silence_timer = None

def audio_callback(in_data, frame_count, time_info, status):
    """Capture audio from the microphone and wake up from idle if needed."""
    global idle, running

    if idle:  # ✅ If we are in idle mode, wake up and restart transcription
        print("🎤 Voice detected! Exiting Idle Mode and restarting transcription...")
        idle = False  # ✅ Disable Idle Mode
        asyncio.run(start_transcription())  # ✅ Restart transcription

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
                await websocket_manager.broadcast_status("speaking")
                if result.is_final:  # ✅ Only send complete sentences
                    print(f"📝 Finalized: {transcript}")
                    await websocket_manager.broadcast_status("listening")
                    # ✅ Store full sentence
                    buffered_transcript += " " + transcript  

                    # ✅ Step 1: Send Transcription Immediately
                    transcription_payload = {
                        "transcription": buffered_transcript.strip(),
                        "responses": {}  # Empty responses at first
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

    except Exception as e:
        print(f"❌ Error in speech recognition: {e}")


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
    running = False

    await websocket_manager.broadcast_status("stopped")
    
    # ✅ Fully clear the audio queue to remove old data
    with audio_queue.mutex:
        audio_queue.queue.clear()

    # ✅ Reset Google SpeechClient (for safety)
    global client
    client = None

    print("🛑 Speech recognition fully stopped.")

