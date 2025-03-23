       
import asyncio

from app.calls.process_call import process_call
from lt_app.transcriber import transcribe_audio
from lt_app.audio import digital_stream, toggle_recording
import lt_app.config as config

paused = False
running = False


async def setup_config():
    config.WHITELIST_WORDS = [
        "Sunday Service", "Evening Worship", "Bible Study", "Prayer Meeting",
        "Baptism", "Communion", "Eucharist", "Confirmation",
        "Wedding", "Funeral", "Memorial Service",
        "Youth Group", "Choir Practice", "Outreach", "Missionary", "Fellowship",
        "Pastor", "Reverend", "Deacon", "Elder", "Minister",
        "Sanctuary", "Fellowship Hall", "Nursery",
        "Christmas Eve Service", "Easter Vigil", "Revival", "Retreat",
        "God Bless", "Peace Be With You", "Amen", "Hallelujah"
    ]

    config.EXAMPLE_FIXES = [
        # Misheard Words
        ("What time is the Sunday circus?", "What time is the Sunday service?"),
        ("Is there a Bible sturdy tonight?", "Is there a Bible study tonight?"),

        # Homophones and Similar-Sounding Words
        ("I want to speak with the pasture.", "I want to speak with the pastor."),
        ("What time is the child champ?", "When time is the children's camp?"),

        # Phrases and Idioms
        ("Can I get a copy of the salmon notes?", "Can I get a copy of the sermon notes?"),
        ("Do you offer missionary services?", "Do you offer missionary services?"),

        # Technical Terms
        ("Is there a fee for the retreat?", "Is there a fee for the retreat?"),
        ("How do I join the congregation?", "How do I join the congregation?"),
        
        #Common Phrases
        ("What is your service times or hours?"),
        ("How can I get involved in the church?"),
        ("What is the process for baptism?"),
        ("How do I sign up for the youth group?"),
        ("How can I volunteer for outreach programs?"),
        ("What is the role of an member in the church?"),
        ("Where is the church located?"),
        ("Can you tell me more about the church's youth program?")
        
    ]

  # ✅ Track if transcription is active
async def initialize_call_transcription():
    """Start the transcription process only once."""
    await setup_config()
    print("🎤 Starting call transcription...")
    # ✅ Run `transcribe_audio()` only if it's not already running
    await transcribe_audio(callback=process_call)


async def start_call_transcription(audio_data):
    """Start live-transcribe audio processing in a background task."""
    global running, paused
    if not running:
        toggle_recording()  
        asyncio.create_task(initialize_call_transcription())  # ✅ Run in background
        running = True
    if paused:
        paused = False
        toggle_recording()
        print("▶️ Resuming transcription...")
        
    asyncio.create_task(digital_stream(audio_data))  

async def pause_transcription():
    """Stop transcription and cleanup resources."""
    global paused
    if paused:
        print("⚠️ Transcription is not paused!")
        return
    paused = True
    toggle_recording()
    print("🛑 Stopping call transcription...")
    
async def resume_transcription():
    """Resume transcription if paused."""
    global paused
    if not paused:
        print("⚠️ Transcription is not paused!")
        return
    paused = False
    toggle_recording()
    print("▶️ Resuming call transcription...")

