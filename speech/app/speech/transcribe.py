import asyncio
import collections
import os
import queue
import numpy as np
import pyaudio
import threading
from google.cloud import speech
import webrtcvad
import whisper
from app.interview.ai_processing import process_ai_response
from app.utils.websocket_manager import websocket_manager
from app.speech.stream_config import streaming_config
from app.routes.speech import USE_WHISPER

# ✅ Google Cloud Speech-to-Text
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "service-account.json"
whisper_model = whisper.load_model("large", device="cuda")  # ✅ Forces GPU usage
vad = webrtcvad.Vad(3)

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
processing_state = False


# ✅ VAD Parameters
CHUNK_DURATION_MS = 30  
CHUNK_SIZE = int(RATE * CHUNK_DURATION_MS / 1000)  # Convert ms to samples
NUM_PADDING_CHUNKS = int(1500 / CHUNK_DURATION_MS)  # 1.5 seconds of silence detection


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
        
async def transcribe_whisper():
    """Transcribes audio using Whisper AI with VAD to detect sentence boundaries."""
    print("🎙️ Using Whisper AI with VAD...")
    global buffered_transcript

    ring_buffer = collections.deque(maxlen=NUM_PADDING_CHUNKS)
    triggered = False
    voiced_frames = []
    
    while running:
        try:
            audio_chunk = audio_queue.get(timeout=2)

            # ✅ Speech Start Detection
            if not triggered:
                ring_buffer.append(audio_chunk)
                num_voiced = sum(vad.is_speech(frame, RATE) for frame in ring_buffer)
                if num_voiced > 0.8 * len(ring_buffer):  # If 80% of recent frames contain speech
                    print("🎤 Speech detected! Starting transcription...")
                    await websocket_manager.broadcast_status("speaking")
                    triggered = True
                    voiced_frames.extend(ring_buffer)
                    ring_buffer.clear()

            # ✅ Speech End Detection
            else:
                voiced_frames.append(audio_chunk)
                ring_buffer.append(audio_chunk)
                num_unvoiced = len(ring_buffer) - sum(vad.is_speech(frame, RATE) for frame in ring_buffer)

                if num_unvoiced > 0.90 * len(ring_buffer):  # If 90% of recent frames are silent
                    print("🔕 Silence detected. Ending transcription...")

                    # ✅ Convert collected voiced frames into a single numpy array
                    final_audio = np.concatenate([np.frombuffer(frame, dtype=np.int16) for frame in voiced_frames])
                    final_audio = final_audio.astype(np.float32) / 32768.0  # Normalize audio for Whisper
                    processing_state = True
                    # ✅ Transcribe with Whisper (Pass raw audio data)
                    result = whisper_model.transcribe(final_audio, fp16=True)  
                    transcript = result["text"].strip()

                    if transcript:
                        print(f"📝 Whisper: {transcript}")
                        buffered_transcript += " " + transcript.strip()

                        transcription_payload = {"transcription": buffered_transcript.strip()}
                        await processing_transcription(transcription_payload)

                        buffered_transcript = ""  # ✅ Reset transcript

                    # ✅ Reset VAD state
                    triggered = False
                    voiced_frames = []
                    ring_buffer.clear()

        except queue.Empty:
            break
        except Exception as e:
            print(f"❌ Whisper Transcription Error: {e}")

async def transcribe_google():
    global client
    global buffered_transcript, silence_timer
    print("🎙️ Listening for speech...")
    while running:
        responses = await asyncio.to_thread(client.streaming_recognize, streaming_config, audio_generator())

        try:
            for response in responses:
                for result in response.results:
                    transcript = result.alternatives[0].transcript.strip()
                    speaker = result.speaker_tag if hasattr(result, "speaker_tag") else None
                    speaker_label = "Recruiter" if speaker == 1 else "Me"

                    if not transcript:
                        continue  # ✅ Skip empty results
                    await websocket_manager.broadcast_status("speaking")
                    if result.is_final:  # ✅ Only send complete sentences
                        print(f"📝 Finalized: {transcript}")
                        # ✅ Store full sentence
                        buffered_transcript += " " + transcript.strip()  # ✅ Append instead of overwriting
                        processing_state = True
                        formatted_transcript = f"{speaker_label}: {transcript}"

                        print(f"🎙️ {formatted_transcript}")  # ✅ Debugging output

                        # ✅ Send filtered transcript to WebSocket
                        transcription_payload = {
                            "transcription": formatted_transcript,
                        }
                        await processing_transcription(transcription_payload)
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
            
async def processing_transcription(transcription_payload):
    """Process the transcription and send it to the AI model."""
    try:        
        await websocket_manager.broadcast_message(transcription_payload)
        print(f"📡 Sent Immediate Transcription: {transcription_payload}")                    
        await websocket_manager.broadcast_status("listening")
        # ✅ Run AI processing asynchronously
        print("🚀 Creating AI Processing Task...")
        task = asyncio.create_task(process_ai_response(buffered_transcript.strip()))
        await asyncio.sleep(0)
        print(f"✅ AI Processing Task Created: {task}")
        processing_state = False
    except Exception as e:
        print(f"❌ Error in processing_transcription: {e}")


async def notify_silence():
    """Enter Idle Mode after 5 seconds of silence."""
    global running, idle

    await asyncio.sleep(7)  # ✅ If silence persists, enter idle mode

    if running:
        print("🔕 No speech detected. Entering Idle Mode...")
        idle = True  # ✅ Set Idle Mode ON
        await websocket_manager.broadcast_status("idle")
        await stop_transcription()  # ✅ Stop Google Streaming


async def start_transcription():
    """Start transcription only if not already running."""
    global running, idle, client

    if running or processing_state:
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
    if USE_WHISPER:
        asyncio.create_task(transcribe_whisper())
    else:
        asyncio.create_task(transcribe_google())

        
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

