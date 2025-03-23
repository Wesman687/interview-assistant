import time
from faster_whisper import WhisperModel
from faster_whisper.audio import AudioRecorder

# Initialize Whisper model
model = WhisperModel("large-v2", device="cuda", compute_type="float16")

# Initialize Audio Recorder
recorder = AudioRecorder(sample_rate=16000)

print("🎙️ Start speaking... Press Ctrl+C to stop recording.")
recorder.start()  # Start recording

try:
    while True:
        time.sleep(1)  # Keep running until user interrupts
except KeyboardInterrupt:
    print("\n🛑 Stopping recording...")
    audio = recorder.stop()  # Stop and retrieve audio data

    print("🎧 Transcribing...")
    segments, _ = model.transcribe(audio)
    
    transcript = " ".join(segment.text for segment in segments)
    print(f"📝 Transcript: {transcript}")
