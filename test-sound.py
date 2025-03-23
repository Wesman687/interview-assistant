from gtts import gTTS
import os

# Recruiter question
text = """At our company, we focus on frontend development with Python and TypeScript.
          Could you walk me through your experience using these technologies 
          and explain why you think your skill set is the best fit for this role?"""

# Convert text to speech
tts = gTTS(text, lang="en")
tts.save("recruiter_question.mp3")  # Save as a sound file

# Play the sound (optional)
os.system("start recruiter_question.mp3")  # Windows
# os.system("afplay recruiter_question.mp3")  # macOS
# os.system("mpg321 recruiter_question.mp3")  # Linux
