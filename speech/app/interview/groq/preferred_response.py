
import requests

from app.config import GROQ_API_KEY, RESUME_TEXT


def get_preferred_response(user_input):
    """Fetches ONLY the preferred response from Groq."""
    print(f"🔍 Fetching Preferred Response for: {user_input}")

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "deepseek-r1-distill-llama-70b",
        "messages": [
            {"role": "system", "content": 
                "You are an AI interview assistant, and I am currently on an interview call with a recruiter. "
                "I need you to analyze my resume data and generate the **best structured response** to the question.\n\n" 
                "Clearly Mark out the thinking portion with <Think>...</Think> tags.\n\n"              
                
                "### **My Resume Data:**\n"
                f"{RESUME_TEXT}\n\n"

                "### **Response Formatting Instructions (Tailwind CSS Ready)**:\n"
                "- Use `<h2 class='text-xl font-bold text-blue-700'>` for section headers.\n"
                "- Use `<h3 class='text-lg font-semibold text-gray-800 mt-4'>` for sub-section headers.\n"
                "- Use `<p class='text-gray-600 leading-relaxed'>` for paragraphs.\n"
                "- Use `<ul class='list-disc pl-5 text-gray-600'>` with `<li class='mb-1'>` for bullet points.\n"
                "- Use `<strong class='font-bold'>` to highlight key terms.\n"
                "- Ensure proper spacing between elements using Tailwind margins (`mt-3`, `mb-4`, etc.).\n"
                "- Keep responses **concise and professional**, Make it readable as if you were answering this to a recruiter.\n"
                "💡 Do a good job, we really need this high-paying job! \n\n"
            },
            {"role": "user", "content": user_input}
        ]
    }

    try:
        response = requests.post("https://api.groq.com/openai/v1/chat/completions", json=payload, headers=headers)
    except TypeError as e:
        print(f"❌ JSON Serialization Error: {e}")
        return {"error": "Payload contains non-serializable data."}

    if response.status_code != 200:
        return {"error": f"Groq API request failed: {response.status_code}", "details": response.text}

    data = response.json()

    if "choices" in data and len(data["choices"]) > 0:
        raw_response = data["choices"][0]["message"]["content"]

        # ✅ Remove "<think>...</think>" section (if present)
        if "<think>" in raw_response and "</think>" in raw_response:
            raw_response = raw_response.split("</think>")[-1].strip()

        return raw_response

    return {"error": "Invalid Groq API response format"}

async def get_follow_up_questions(transcription, ai_response):
    """Fetches follow-up questions from Groq based on both the transcription and AI response."""
    print(f"🔍 Fetching Follow-Up Questions for: {transcription} and AI Response: {ai_response}")

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "deepseek-r1-distill-llama-70b",
        "messages": [
            {"role": "system", "content": 
                "You are an AI interview assistant. I just answered an interview question. "
                "Now, I need **smart follow-up questions** that I should ask the recruiter.\n\n"
                
                "### **Instructions:**\n"
                "- Generate **relevant follow-up questions** based on my answer.\n"
                "- Keep them **short, concise, and professional**.\n"
                "- Only return **questions**—no explanations.\n"
                "- Format the response as a **JSON list of follow-up questions**.\n"
                "- Generate a maximum of **5 questions**.\n\n"
                
                "### **Example Response Format:**\n"
                '["What are the biggest challenges the team is facing?", "How do you measure success in this role?", "What technologies are used in your stack?"]'
            },
            {"role": "user", "content": 
                f"My answer: {ai_response}\n\n"
                f"What are the best follow-up questions I should ask the recruiter based on my response?"}
        ]
    }


    try:
        response = requests.post("https://api.groq.com/openai/v1/chat/completions", json=payload, headers=headers)
    except TypeError as e:
        print(f"❌ JSON Serialization Error: {e}")
        return ["Error fetching follow-up questions."]

    if response.status_code != 200:
        return [f"Groq API request failed: {response.status_code}", response.text]

    data = response.json()

    if "choices" in data and len(data["choices"]) > 0:
        try:
            follow_up_list = eval(data["choices"][0]["message"]["content"])  # ✅ Convert JSON string to Python list
            return follow_up_list
        except Exception as e:
            print(f"❌ Error parsing follow-up response: {e}")
            return ["Error parsing follow-up questions."]
    
    return ["No follow-up questions available."]