import asyncio
import collections
import os
import queue
import struct
import time
import numpy as np
import pyaudio
import threading
from google.cloud import speech
import webrtcvad
from faster_whisper import WhisperModel
import app.config2
from app.interview.ai_processing import process_ai_response
from app.utils.websocket_manager import websocket_manager

# ✅ Google Cloud Speech-to-Text
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "service-account.json"
whisper_model = WhisperModel("large", device="cuda", compute_type="float16")
vad = webrtcvad.Vad(2)
industry_terms = [
    "cloud computing", "microservices", "Kubernetes", "Docker", "DevOps",
    "CI/CD", "machine learning", "neural network", "REST API", "Agile"
]
business_terms = [
    "stakeholder", "return on investment", "client requirements", 
    "project timeline", "team collaboration", "budget", "Agile methodology"
]

# 2. Define common technical and behavioral interview questions
technical_questions = [
    "Can you explain the Model-View-Controller architecture?",
    "How does the event loop work in Node.js?",
    "What are the differences between REST and GraphQL?",
    "How would you optimize a database query?",
    "Describe a challenging bug you encountered.",
    "What is the difference between unit and integration testing?",
    "Explain the concept of 'state' in React.",
    "How do you handle asynchronous operations in JavaScript?",
    "What is the purpose of a Docker container?",
    "How would you deploy a web application to AWS?"
    "Can you tell me your experience using python?",
    "Can you explain how you manage states in React?",
    "How do you handle errors in JavaScript?",
    "What is the difference between SQL and NoSQL databases?",
    "How do you ensure the security of a web application?",
    "What is the purpose of a RESTful API?",
    "How do you ensure your code is scalable and maintainable?",
    "What is the difference between Git and GitHub?",
    "How do you stay updated with the latest technologies?",
    "What is your experience with cloud computing services?",
    "Can you explain the difference between Agile and Waterfall methodologies?",
    "How do you approach debugging and troubleshooting in your projects?",
    "What is your experience with CI/CD pipelines?",
    "How do you handle version control in your projects?",
    "What is your experience with microservices architecture?",
    "Can you explain the concept of 'dependency injection'?",
    "How do you handle performance optimization in web applications?",
    "What is your experience with cloud computing services?",
    "Can you explain the difference between Agile and Waterfall methodologies?",
    "How do you approach debugging and troubleshooting in your projects?",
    "What is your experience with CI/CD pipelines?",
    "How do you handle version control in your projects?",
    "What is your experience with microservices architecture?",
    "Can you explain the concept of 'dependency injection'?",
    "How do you handle performance optimization in web applications?",
]
algorithmic_questions = [
    "Can you implement a binary search algorithm?",
    "What is the time complexity of quicksort?",
    "Can you explain the difference between breadth-first search and depth-first search?",
    "How would you reverse a linked list?",
    "What are the advantages of using a hash table over an array?",
    "How would you detect a cycle in a linked list?",
    "Can you implement a LRU cache?",
    "What is memoization and how does it differ from tabulation?",
    "Can you implement the Fibonacci sequence using dynamic programming?",
    "How would you solve the knapsack problem?",
    "Explain the longest increasing subsequence problem.",
    "Can you optimize a search function for a large dataset?",
    "How would you handle a large number of concurrent API requests?",
    "How do you handle memory leaks in JavaScript applications?"
]

behavioral_questions = [
    "Tell me about a time you resolved a team conflict.",
    "Describe a situation where you missed a deadline.",
    "How do you handle multiple priorities under pressure?",
    "Give an example of showing leadership in a project.",
    "How do you respond to constructive criticism?"
]

# 3. Include keywords from the provided resume (programming languages, frameworks, etc.)
resume_keywords = [
    "React", "Node.js", "Express", "Django", "GraphQL", "PostgreSQL",
    "MongoDB", "AWS", "Docker", "Kubernetes", "Python", "JavaScript", "TypeScript", "CI/CD", "Agile",
    "Vue.js", "Angular", "REST API", "Bootstrap", "TailwindCSS", "C#", ".NET", "ASP.NET Core", "SQL Server",
    "MySQL", "Firebase", "Azure", "GCP", "Java", "Spring Boot", "Ruby on Rails", "Laravel", "Symfony",
    "React Native", "Android", "Java", "Kotlin", "HTML5", "CSS3", "jQuery", "Blazor", "Webpack", "Babel",
    "Responsive Design", "PHP", "Flask", "Redis", "Firebase", "AWS", "S3", "EC2", "Lambda", "CI/CD Pipelines",
    "microservices", "machine learning", "neural network", "DevOps", "cloud computing", "NEXT.js", "Nuxt.js"
]

# Combine all custom phrases and assign a strong boost for recognition
custom_phrases = (
    industry_terms 
    + business_terms 
    + technical_questions 
    + behavioral_questions 
    + resume_keywords 
    + algorithmic_questions
)
speech_context = speech.SpeechContext(phrases=custom_phrases, boost=5.0)

# 4. Configure speaker diarization for exactly 2 speakers (Recruiter and Me)
diarization_config = speech.SpeakerDiarizationConfig(
    enable_speaker_diarization=True,
    min_speaker_count=2,
    max_speaker_count=2
)

recognition_config = speech.RecognitionConfig(
    language_code="en-US",
    encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
    sample_rate_hertz=16000,  # ✅ Match your microphone input
    enable_automatic_punctuation=True,
    diarization_config=diarization_config,
    speech_contexts=[speech_context],
    use_enhanced=True,        # enable enhanced model for higher accuracy
)

streaming_config = speech.StreamingRecognitionConfig(
    config=recognition_config,
    interim_results=True  # ✅ Test with partial results first
)


# ✅ Audio Handling
RATE = 16000
CHUNK = int(RATE / 10)
audio_queue = queue.Queue()
buffered_transcript = ""
lock = threading.Lock()
connected_clients = set()  # ✅ WebSocket Clients
running = False  # ✅ Track if recognition is running
idle = False  # ✅ Track if we are in Idle Mode
processing_state = False
silence_counter = 0


# ✅ VAD Parameters

CHUNK_DURATION_MS = 20  # 🔥 Set this to 20ms (can be 10ms, 20ms, or 30ms)
CHUNK_SIZE = int(RATE * (CHUNK_DURATION_MS / 1000)) 
NUM_PADDING_CHUNKS = int(1500 / CHUNK_DURATION_MS)  # 1.5 seconds of silence detection


# ✅ Detect Silence Timer (10s threshold)
silence_timer = None

def is_silent(audio_chunk, threshold=1000):  # 🔥 Lower threshold to catch actual silence
    """Check if an audio chunk is silent."""
    audio_data = np.frombuffer(audio_chunk, dtype=np.int16)
    return np.mean(np.abs(audio_data)) < threshold  # ✅ Check overall energy, not just max volume


def audio_callback(in_data, frame_count, time_info, status):
    """Capture audio from the microphone and wake up from idle if needed."""
    global idle, running

    if not running:
        return None, pyaudio.paAbort

    if idle:
        print("🎤 Voice detected! Exiting Idle Mode and restarting transcription...")
        idle = False
        from app.main import EVENT_LOOP
        loop = EVENT_LOOP
        try:
            asyncio.run_coroutine_threadsafe(websocket_manager.broadcast_speech_status("speaking"), loop)
            future = asyncio.run_coroutine_threadsafe(start_transcription(), loop)
            future.result()
        except Exception as e:
            print(f"❌ Error scheduling transcription: {e}")

    # ✅ Ensure valid chunk sizes before adding to the queue
    valid_sizes = [320, 640, 960]  # ✅ Expected sizes at 16kHz
    if in_data and isinstance(in_data, bytes):
        if len(in_data) in valid_sizes:
            audio_queue.put(in_data)  # ✅ Correct frame size
        else:
            print(f"⚠️ Adjusting oversized frame: Received {len(in_data)} bytes")
            split_frames = [in_data[i:i + 320] for i in range(0, len(in_data), 320)]
            for frame in split_frames:
                if len(frame) in valid_sizes:
                    audio_queue.put(frame)
    else:
        print(f"⚠️ Skipping invalid audio chunk: {type(in_data)}, Length: {len(in_data) if in_data else 0}")

    return None, pyaudio.paContinue


def audio_generator():
    """Continuously fetch audio from the queue and send it to speech API."""
    while running:
        try:
            data = audio_queue.get(timeout=2)  # ✅ Use timeout to avoid deadlock
            if data is None:
                print("⏳ Audio queue empty, entering idle mode...")
                continue  # ✅ Instead of stopping, keep waiting
            print(f"🎤 Streaming {len(data)} bytes of audio")
            valid_sizes = [160, 320, 480]  # Corresponding to 10ms, 20ms, 30ms at 16kHz
            if len(data) not in valid_sizes and app.config2.USE_WHISPER:
                print(f"⚠️ Dropping oversized frame ({len(data)} bytes). Expected {valid_sizes}")
                continue
            yield speech.StreamingRecognizeRequest(audio_content=data)
        except queue.Empty:
            print("⏳ Audio queue empty, stopping generator...")
            break  # ✅ Prevents iterating on an empty queue
        
async def transcribe_whisper():
    """Transcribes audio using Whisper AI with VAD to detect sentence boundaries."""
    print("🎙️ Using Whisper AI with VAD...")
    global buffered_transcript, processing_state, idle, silence_counter

    # ✅ Ensure we have a valid event loop
    from app.main import EVENT_LOOP  
    loop = EVENT_LOOP

    if loop is None:
        print("❌ EVENT_LOOP is missing! Waiting...")
        for _ in range(5):
            await asyncio.sleep(0.5)
            from app.main import EVENT_LOOP  
            if EVENT_LOOP:
                loop = EVENT_LOOP
                print("✅ Found EVENT_LOOP, proceeding with Whisper.")
                break
        else:
            print("❌ Timed out waiting for EVENT_LOOP. Skipping Whisper transcription.")
            return

    ring_buffer = collections.deque(maxlen=NUM_PADDING_CHUNKS)
    triggered = False
    voiced_frames = []    

    while running:
        try:
            
            # ✅ Ensure `audio_chunk` is valid
            audio_chunk = audio_queue.get(timeout=2)
            if audio_chunk is None or len(audio_chunk) == 0:
                print("⚠️ Received NoneType or empty audio chunk, skipping...")
                continue  # ✅ Skip empty frames safely

            if len(audio_chunk) not in [CHUNK_SIZE * 2]:
                print(f"⚠️ Invalid frame length: {len(audio_chunk)} bytes, skipping...")
                continue

            # ✅ Ensure frame is actually bytes
            if not isinstance(audio_chunk, bytes):
                print(f"⚠️ Invalid frame type: {type(audio_chunk)}, expected bytes. Skipping...")
                continue

            is_speech = vad.is_speech(audio_chunk, RATE)
            if is_speech:
                voiced_frames.append(audio_chunk)
            else:
                silence_counter += 1  # 🔥 Count silent frames
                print(f"🔇 Silence Counter: {silence_counter}")
                
            if silence_counter >= 50:
                await asyncio.sleep(0.5)
                print("🔕 Extended silence detected. Finalizing transcription...")
                
                if len(voiced_frames) > 0:
                    print("📜 Processing final transcription before stopping...")
                    final_audio = np.concatenate(
                        [np.frombuffer(frame, dtype=np.int16) for frame in voiced_frames]
                    )
                    final_audio = final_audio.astype(np.float32) / 32768.0  # ✅ Normalize

                    segments, info = whisper_model.transcribe(final_audio)
                    transcript = " ".join(segment.text for segment in segments).strip()

                    if transcript:
                        print(f"📝 Final Whisper Transcript: {transcript}")
                        await websocket_manager.broadcast_speech_status("listening")
                        transcription_payload = {"transcription": transcript}
                        await websocket_manager.broadcast_interview_message(transcription_payload)
                        transcript = ""

            if not triggered:
                ring_buffer.append(audio_chunk)
                num_voiced = sum(vad.is_speech(frame, RATE) for frame in ring_buffer)
                if num_voiced > 0.8 * len(ring_buffer):  # ✅ 80% speech threshold
                    print("🎤 Speech detected! Starting transcription...")
                    await websocket_manager.broadcast_speech_status("speaking")
                    triggered = True
                    voiced_frames.extend(ring_buffer)
                    ring_buffer.clear()

            else:
                ring_buffer.append(audio_chunk)
                num_unvoiced = len(ring_buffer) - sum(vad.is_speech(frame, RATE) for frame in ring_buffer)

                if num_unvoiced > 0.95 * len(ring_buffer):  # ✅ 90% silence threshold
                    print("🔕 Silence detected. Ending transcription...")

                    if len(voiced_frames) > 0:
                        final_audio = np.concatenate(
                            [np.frombuffer(frame, dtype=np.int16) for frame in voiced_frames]
                        )
                        final_audio = final_audio.astype(np.float32) / 32768.0  # ✅ Normalize

                        print(f"🎧 Whisper Processing Audio - Shape: {final_audio.shape}")

                        # ✅ Use correct event loop for Whisper transcription
                        segments, info = await loop.run_in_executor(
                            None, whisper_model.transcribe, final_audio
                        )

                        transcript = " ".join(segment.text for segment in segments).strip()
                        if transcript:
                            print(f"📝 Whisper: {transcript}")
                            buffered_transcript += " " + transcript.strip()
                            processing_state = True
                            transcription_payload = {"transcription": buffered_transcript.strip()}
                            await websocket_manager.broadcast_speech_status("listening")
                            await processing_transcription(transcription_payload)
                            transcript = ""
                            

                    triggered = False
                    voiced_frames = []
                    ring_buffer.clear()

        except queue.Empty:
            print("⏳ No audio received, stopping Whisper transcription...")
            idle = True
            await websocket_manager.broadcast_speech_status("idle")
            break
        except Exception as e:
            print(f"❌ Whisper Processing Error: {e}")




async def transcribe_google():
    print("🎙️ Using Google Speech-to-Text...")
    global client
    global buffered_transcript, silence_timer, processing_state
    while running:
        try:
            await asyncio.sleep(1) 
            responses = await asyncio.to_thread(client.streaming_recognize, streaming_config, audio_generator())
        except Exception as e:
            print(f"❌ Error in Google Speech API: {e}")
            raise

        try:
            for response in responses:
                for result in response.results:
                    transcript = result.alternatives[0].transcript.strip()
                    speaker = result.speaker_tag if hasattr(result, "speaker_tag") else None
                    speaker_label = "Recruiter" if speaker == 1 else "Me"

                    if not transcript:
                        continue  # ✅ Skip empty results
                    await websocket_manager.broadcast_speech_status("speaking")
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
    global processing_state, buffered_transcript
    try:
        processing_state = True        
        await websocket_manager.broadcast_interview_message(transcription_payload)
        print(f"📡 Sent Immediate Transcription: {transcription_payload}")                    
        await websocket_manager.broadcast_speech_status("listening")
        # ✅ Run AI processing asynchronously
        # print("🚀 Creating AI Processing Task...")
        # task = asyncio.create_task(process_ai_response(buffered_transcript.strip()))
        # await asyncio.sleep(0)
        # print(f"✅ AI Processing Task Created: {task}")
        processing_state = False
        buffered_transcript = ""
    except Exception as e:
        print(f"❌ Error in processing_transcription: {e}")


async def notify_silence():
    """Enter Idle Mode after 5 seconds of silence."""
    global running, idle

    await asyncio.sleep(6)  # ✅ If silence persists, enter idle mode

    if running:
        print("🔕 No speech detected. Entering Idle Mode...")
        idle = True  # ✅ Set Idle Mode ON
        await websocket_manager.broadcast_speech_status("idle")
        await stop_transcription()  # ✅ Stop Google Streaming


async def start_transcription():
    """Start transcription only if not already running."""
    global running, idle, client, processing_state, USE_WHISPER, EVENT_LOOP

    if running or processing_state:
        return
    running = True
    
    if idle:
        print("🎤 Restarting transcription after silence...")
        idle = False
        await websocket_manager.broadcast_speech_status("listening")

        if app.config2.USE_WHISPER:
            asyncio.run_coroutine_threadsafe(transcribe_whisper(), loop)
    idle = False  # ✅ Exit Idle Mode
    
    await asyncio.sleep(1)
    
    from app.main import EVENT_LOOP  
    loop = EVENT_LOOP

    if loop is None:
        print("❌ EVENT_LOOP is missing! Waiting...")
        for _ in range(5):
            await asyncio.sleep(0.5)
            from app.main import EVENT_LOOP
            if EVENT_LOOP:
                loop = EVENT_LOOP
                print("✅ Found EVENT_LOOP, proceeding.")
                break
        else:
            print("❌ Timed out waiting for EVENT_LOOP. Skipping transcription.")
            return

    print("🎤 Starting fresh speech recognition...")
    
    # ✅ Always create a fresh SpeechClient on start
    client = speech.SpeechClient()

    await websocket_manager.broadcast_speech_status("listening")
    
    audio_interface = pyaudio.PyAudio()
    stream = audio_interface.open(
        format=pyaudio.paInt16,
        channels=1,
        rate=RATE,
        input=True,
        frames_per_buffer=CHUNK_SIZE,  # ✅ Ensure this matches CHUNK_SIZE (320 bytes)
        stream_callback=audio_callback,
    )
    print(f"Use Whisper: {app.config2.USE_WHISPER}")
    if app.config2.USE_WHISPER:
        if loop.is_running():
            asyncio.run_coroutine_threadsafe(transcribe_whisper(), loop)
        else:
            await transcribe_whisper()
    else:
        asyncio.run_coroutine_threadsafe(transcribe_google(), loop)

    print("✅ Fresh speech recognition started")





async def stop_transcription():
    """Stop the audio stream and recognition completely."""
    global running, audio_queue

    if not running:
        return
    running = False  # ✅ Stop further streaming
    
    # ✅ Fully clear the audio queue to remove old data
    with audio_queue.mutex:
        audio_queue.queue.clear()

    # ✅ Properly end the generator
    audio_queue.put(None)  # 🔥 Sends a signal to stop `audio_generator()`

    # ✅ Reset Google SpeechClient (for safety)
    global client
    client = None

    print("🛑 Speech recognition fully stopped.")
    await websocket_manager.broadcast_speech_status("stopped")
