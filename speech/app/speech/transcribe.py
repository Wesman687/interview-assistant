import asyncio
import numpy as np
import webrtcvad
from faster_whisper import WhisperModel
from whisper_mic import WhisperMic
import whisper_live.transcriber as whisper_transcriber
from app.utils.websocket_manager import websocket_manager

# ✅ Initialize Whisper Live & Whisper Mic
whisper_live_transcriber = whisper_transcriber.Transcriber()
whisper_mic = WhisperMic(model="large", device="cuda")  # Use "cuda" for GPU

# ✅ Initialize VAD (Voice Activity Detection)
vad = webrtcvad.Vad(2)
buffered_transcript = ""

# ✅ STATE MANAGEMENT
STOPPED = "stopped"
IDLE = "idle"
SPEAKING = "speaking"
LISTENING = "listening"
PROCESSING = "processing"
current_state = STOPPED  # 🔥 Initial state

# ✅ Silence Counter
silence_counter = 0


async def update_state(new_state):
    """Update transcription state and broadcast status."""
    global current_state
    if current_state != new_state:
        current_state = new_state
        print(f"🔄 Transcription State: {current_state.upper()}")
        await websocket_manager.broadcast_speech_status(current_state)


async def process_transcription(transcript):
    """Process the transcription and send it to the AI model."""
    global buffered_transcript
    if transcript:
        await update_state(PROCESSING)  # 🔄 Switch to PROCESSING
        print(f"📝 Whisper Transcript: {transcript}")
        buffered_transcript += " " + transcript.strip()
        transcription_payload = {"transcription": buffered_transcript.strip()}
        await websocket_manager.broadcast_interview_message(transcription_payload)
        buffered_transcript = ""  # ✅ Clear buffer
        await update_state(LISTENING)  # 🔄 Switch to LISTENING


async def transcribe_audio(audio_chunk):
    """Transcribe incoming audio chunks using Whisper-Live."""
    global silence_counter

    if audio_chunk is None or len(audio_chunk) == 0:
        print("⚠️ Received empty audio chunk, skipping...")
        return

    is_speech = vad.is_speech(audio_chunk, whisper_mic.sampling_rate)

    if is_speech:
        silence_counter = 0  # ✅ Reset silence counter
        if current_state != SPEAKING:
            await update_state(SPEAKING)  # 🔄 Switch to SPEAKING
    else:
        silence_counter += 1
        print(f"🔇 Silence Counter: {silence_counter}")

        if silence_counter >= 50:
            print("🔕 Extended silence detected. Stopping transcription...")
            await update_state(IDLE)  # 🔄 Switch to IDLE
            return

    # ✅ Convert audio for Whisper Live
    audio_np = np.frombuffer(audio_chunk, dtype=np.int16).astype(np.float32) / 32768.0  # Normalize

    # ✅ Run Whisper-Live transcription
    segments = whisper_live_transcriber.transcribe(audio_np)
    transcript = " ".join(segment.text for segment in segments).strip()

    if transcript:
        await process_transcription(transcript)


async def start_transcription():
    """Start live transcription."""
    global current_state
    if current_state != STOPPED:
        return  # 🔄 Don't start if already running

    print("🎤 Starting Whisper Mic for real-time transcription...")
    await update_state(IDLE)  # 🔄 Switch to IDLE (waiting for speech)

    # ✅ Start Whisper Mic with `on_audio` callback
    whisper_mic.start(on_audio=transcribe_audio)


async def stop_transcription():
    """Stop live transcription."""
    global current_state
    if current_state == STOPPED:
        return  # 🔄 Already stopped

    print("🛑 Stopping Whisper Mic transcription...")
    whisper_mic.stop()
    await update_state(STOPPED)  # 🔄 Switch to STOPPED
