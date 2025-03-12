@echo off
cd /d C:\Code\live-interview\speech
uvicorn live-transcribe:app --host 0.0.0.0 --port 8000 --reload
