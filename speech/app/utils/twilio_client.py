# app/utils/twilio_client.py
import asyncio
from textwrap import dedent
from twilio.rest import Client
from dotenv import load_dotenv
import os
from app.utils.websocket_manager import websocket_manager

# ✅ Load variables from .env
load_dotenv()

# ✅ Now access them
account_sid = os.getenv("TWILIO_ACCOUNT_SID")
auth_token = os.getenv("TWILIO_AUTH_TOKEN")
YOUR_DOMAIN = os.getenv("YOUR_DOMAIN")
call_sid = None
twilio_client = Client(account_sid, auth_token)


def inject_twi_response_with_stream(call_sid: str, response_text: str, redirect_path="/twiml/continue"):
    twiml = dedent(f"""
    <Response>
        <Say>{response_text}</Say>
        <Stop>
            <Stream name="live-transcription" />
        </Stop>
        <Pause length="1" />
        <Redirect>https://{YOUR_DOMAIN}{redirect_path}</Redirect>
    </Response>
    """)
    twilio_client.calls(call_sid).update(twiml=twiml)
    
async def inject_twi_say_only(call_sid: str, response_text: str):
    """Immediately speak a message while holding the call open."""
    print("Say only response")
    twiml = dedent(f"""
    <Response>
        <Say>{response_text}</Say>
        <Pause length="1" />
        <Redirect>https://{YOUR_DOMAIN}/twiml/hold</Redirect>
    </Response>
    """)
    twilio_client.calls(call_sid).update(twiml=twiml)