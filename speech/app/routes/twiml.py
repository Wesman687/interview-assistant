

from xml.etree.ElementTree import Element, SubElement, tostring
from fastapi import APIRouter, Response

from app.config import YOUR_DOMAIN


router = APIRouter()
@router.post("/start")
async def start_call():
    response = Element("Response")

    # Step 1: Start live transcription stream
    start = SubElement(response, "Start")
    stream = SubElement(start, "Stream")
    stream.set("url", f"wss://{YOUR_DOMAIN}/twilio/ws")

    # Step 2: Greeting message
    say = SubElement(response, "Say")
    say.text = "Thank you for calling First Church of God. How may we assist you today?"

    # Step 3: Prevent immediate hangup
    SubElement(response, "Pause", length="60")

    # Step 4: Redirect to continue loop
    redirect = SubElement(response, "Redirect")
    redirect.text = f"https://{YOUR_DOMAIN}/twiml/continue"

    xml_string = tostring(response, encoding="utf-8")
    return Response(content=xml_string, media_type="application/xml")

@router.post("/hold")
async def hold_transcription():
    response = Element("Response")
    
    SubElement(response, "Pause", length="30")  # Keeps call alive quietly
    redirect = SubElement(response, "Redirect")
    redirect.text = f"https://{YOUR_DOMAIN}/twiml/hold"
    xml_string = tostring(response, encoding="utf-8")
    return Response(content=xml_string, media_type="application/xml")


@router.post("/continue")
async def continue_conversation():
    response = Element("Response")

    # Repeat listening prompt
    say = SubElement(response, "Say")
    say.text = "Let me know if you have any other questions."

    SubElement(response, "Pause", length="1")
        
    start = SubElement(response, "Start")
    stream = SubElement(start, "Stream")
    stream.set("url", f"wss://{YOUR_DOMAIN}/twilio/ws")

    SubElement(response, "Pause", length="30")
    redirect = SubElement(response, "Redirect")
    redirect.text = f"https://{YOUR_DOMAIN}/twiml/continue"

    xml_string = tostring(response, encoding="utf-8")
    return Response(content=xml_string, media_type="application/xml")
