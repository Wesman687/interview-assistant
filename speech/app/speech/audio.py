import queue
import pyaudio

from app.config import RATE, CHUNK

# ✅ Global Variables
audio_queue = queue.Queue()

def audio_callback(in_data, frame_count, time_info, status):
    """Capture audio from the microphone and put it in the queue."""
    audio_queue.put(in_data)
    return None, pyaudio.paContinue

def start_audio_stream():
    """Initialize PyAudio stream."""
    audio_interface = pyaudio.PyAudio()
    stream = audio_interface.open(
        format=pyaudio.paInt16,
        channels=1,
        rate=RATE,
        input=True,
        frames_per_buffer=CHUNK,
        stream_callback=audio_callback,
    )
    return stream
