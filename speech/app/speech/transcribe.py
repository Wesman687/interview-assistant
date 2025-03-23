
import asyncio
import sounddevice as sd
from lt_app.transcriber import transcribe_audio
from lt_app.audio import toggle_recording, mic_callback, system_callback
import lt_app.config as config
from app.interview.ai_processing import process_ai_response
from app.utils.websocket_manager import websocket_manager  # ✅ Keep WebSocket integration


# ✅ STATE MANAGEMENT
STOPPED = "stopped"
IDLE = "idle"
SPEAKING = "speaking"
LISTENING = "listening"
PROCESSING = "processing"
RUNNING = "running"
current_state = STOPPED  # 🔥 Initial state
running = False
config.MODEL_SIZE = "large-v3"
config.DEVICE = "cuda"
# ✅ Silence Counter
silence_counter = 0
mic_stream = None
system_stream = None
hasStarted = None


async def update_state(new_state):
    """Update transcription state and broadcast status."""
    global current_state
    if current_state != new_state:
        current_state = new_state
        print(f"🔄 Transcription State: {current_state.upper()}")
        await websocket_manager.broadcast_speech_status(current_state)

async def speaking_state_callback(source, is_speaking):
    """Handle the speaking state changes."""
    state = "Speaking" if is_speaking else "Silent"
    print(f"🔔 {source.capitalize()} is now {state}")
    if is_speaking:
        await update_state(SPEAKING)
    else:
        await update_state(LISTENING)

async def process_transcription(transcript, source):
    """Process the transcription and send it to the AI model."""
    global buffered_transcript
    print(f"🔤 Processing transcription from {source}: {transcript}")
    if transcript:
        await update_state(PROCESSING)  # 🔄 Switch to PROCESSING
        print(f"📝 Transcript: {transcript}")
        speaker = "Me" if source == "mic" else "Recruiter"
        transcription_payload = {"transcription": f"{speaker}: {transcript}"}
        await websocket_manager.broadcast_interview_message(transcription_payload)
        if speaker != "Me":
            await process_ai_response(transcript)
        await update_state(LISTENING)  # 🔄 Switch to LISTENING
        
async def initialize_transcription():
    """Initialize the transcription process."""
    global mic_stream, system_stream, hasStarted

    loop = asyncio.get_event_loop()

    # ✅ Set up audio streams using `live-transcribe`
    if mic_stream is None:
        try:
            mic_stream = sd.InputStream(
                samplerate=config.SAMPLE_RATE,
                channels=config.CHANNELS,
                callback=lambda *args: mic_callback(
                    *args,
                    speaking_callback=lambda src, state: asyncio.run_coroutine_threadsafe(
                        speaking_state_callback(src, state), loop
                    ),
                ),
                dtype="int16",
                device=1,
            )
            mic_stream.start()
        except Exception as e:
            print(f"❌ Error starting mic stream: {e}")

    if system_stream is None:
        try:
            system_stream = sd.InputStream(
                samplerate=config.SAMPLE_RATE,
                channels=config.CHANNELS,
                callback=lambda *args: system_callback(
                    *args,
                    speaking_callback=lambda src, state: asyncio.run_coroutine_threadsafe(
                        speaking_state_callback(src, state), loop
                    ),
                ),
                dtype="int16",
                device=3,
            )
            system_stream.start()
        except Exception as e:
            print(f"❌ Error starting system stream: {e}")

    if hasStarted is None:
        print("starting transcribe")
        hasStarted = True
        await transcribe_audio(callback=process_transcription)



async def start_transcription():
    """Start live-transcribe audio processing in a background task."""
    global mic_stream, system_stream, running, hasStarted
    if running:
        print("⚠️ Transcription is already running!")
        return
    toggle_recording()  # ✅ Start recording
    await update_state("listening")
    running = True

    if not mic_stream or not system_stream:
        asyncio.create_task(initialize_transcription())  # ✅ Run in the background

    print("✅ Transcription is running!")
    


async def stop_transcription():
    """Stop the audio stream and transcription."""
    global running
    print("🛑 Stopping transcription...")
    if not running:
        print("⚠️ Transcription is not running!")
        return
    running = False

    toggle_recording()  # ✅ Stop transcription
    print("🛑 Transcription stopped.")
    await update_state("stopped")  # ✅ Notify WebSocket