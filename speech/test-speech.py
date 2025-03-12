import os
from google.cloud import speech
GOOGLE_CREDENTIALS_PATH = "C:/Code/live-interview/speech/service-account.json"
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = GOOGLE_CREDENTIALS_PATH

client = speech.SpeechClient()
print(client)
