import asyncio

# ✅ Create a global event loop once
EVENT_LOOP = asyncio.new_event_loop()
asyncio.set_event_loop(EVENT_LOOP)