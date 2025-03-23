
from datetime import datetime, timedelta
import re
from zoneinfo import ZoneInfo
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import pyttsx3

analyzer = SentimentIntensityAnalyzer()

async def analyze_tone(text):
    """Analyze sentiment of caller's message."""
    sentiment = analyzer.polarity_scores(text)
    compound_score = sentiment["compound"]  # Overall sentiment score (-1 to 1)
    
    if compound_score >= 0.5:
        return "positive"
    elif compound_score <= -0.3:
        return "negative"
    else:
        return "neutral"
    
async def text_to_speech(text, filename="response.mp3"):
    """Convert AI-generated response to speech and save as an MP3 file."""
    engine = pyttsx3.init()
    engine.save_to_file(text, filename)
    engine.runAndWait()
    return filename

async def clean_deepseek_response(response_text):
    """Remove the <think> section and other unnecessary artifacts from DeepSeek responses."""
    response_text = re.sub(r"<think>.*?</think>", "", response_text, flags=re.DOTALL)  # ✅ Remove DeepSeek "thinking"
    return response_text.strip()


def extract_final_intent(raw_response: str) -> str:
    # Look for final answer label or clearly formatted intent
    for line in reversed(raw_response.strip().splitlines()):
        for label in ["GENERAL_INFO", "APPOINTMENT", "PRAYER_REQUEST", "GENERAL_QUESTION"]:
            if label in line.upper():
                return label
    return "GENERAL_QUESTION"  # Default fallback

def get_formatted_est_time():
    # Get current time + 1 day in Eastern Time
    appointment_time = datetime.now(ZoneInfo("America/New_York")) + timedelta(days=1)
    return appointment_time.strftime("%A, %B %d at %I:%M %p EST")