import json
import datetime
from app.calls.call_utils import get_formatted_est_time
from app.utils.websocket_manager import websocket_manager

async def handle_action(intent, transcription):
    """Handle appointment booking or prayer request actions."""
    
    if intent == "APPOINTMENT":
        # ✅ Extract Date & Time (Simple Example)
        appointment_time = get_formatted_est_time()
        response = f"I have scheduled an appointment for you on {appointment_time}. If you need to change it, please call us back!"
        

        return response

    elif intent == "PRAYER_REQUEST":
        response = "Your prayer request has been received. Our church will pray for you."        

        return response
    
    elif intent == "GENERAL_INFO":
        return (
            "Hello! Thank you for calling First Church of God. "
            "Our Sunday services are at 10 AM. Bible studies are on Wednesdays at 5 PM, "
            "and Children's Camp is from 12 to 1:30 PM after service. "
            "You can reach us at (386) 325-2814 or the1stchurchofgod@gmail.com. "
            "More details are available on our website: palatka-firstchurchofgod.org."            
        )


    return "I'm not sure how to process your request. Could you clarify?"
