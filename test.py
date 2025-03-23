import asyncio
import os
import websockets
import json
import base64
import numpy as np
import sounddevice as sd
import soundfile as sf
from pydub import AudioSegment

async def simulate_twilio_audio():
    """Simulates sending a test audio file to Twilio WebSocket."""
    uri = "wss://4cb333b9cd528f3c83fa12cf728a0a73.loophole.site/twilio/ws"  # 🔥 Change to your Loophole URL

    async with websockets.connect(uri) as websocket:
        print("🔌 Connected to Twilio WebSocket!")

        start_payload = {
            "event": "start",
            "start": {
                "callSid": "TEST-CALL",
                "phoneNumber": "+1234567890"
            }
        }
        await websocket.send(json.dumps(start_payload))
        print("📞 Simulated Call Started.")

        # ✅ Load and resample WAV file to 16kHz
        audio_path = "C:/Code/live-interview/test.wav"
        audio = AudioSegment.from_wav(audio_path).set_frame_rate(16000).set_channels(1)

        # ✅ Convert to raw PCM bytes
        audio_data = np.array(audio.get_array_of_samples(), dtype=np.int16).tobytes()
        encoded_audio = base64.b64encode(audio_data).decode("utf-8")

        # ✅ Send as Media Event
        media_payload = {
            "event": "media",
            "media": {
                "payload": encoded_audio
            }
        }
        await websocket.send(json.dumps(media_payload))
        print("🎙️ Real Audio Sent.")
        
        await asyncio.sleep(20)
        # ✅ Stop Event
        stop_payload = {"event": "stop"}
        await websocket.send(json.dumps(stop_payload))
        print("🛑 Simulated Call Ended.")

# ✅ Run Test
asyncio.run(simulate_twilio_audio())