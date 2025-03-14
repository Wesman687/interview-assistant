import json
import requests
from bs4 import BeautifulSoup
from app.config import GROQ_API_KEY

async def get_follow_up_questions(transcription, ai_response):
    """Fetches follow-up questions from Groq and formats them with Tailwind CSS."""
    print(f"🔍 Fetching Follow-Up Questions for: {transcription} and AI Response: {ai_response}")

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    # ✅ Remove all HTML tags from AI response
    clean_ai_response = BeautifulSoup(ai_response, "html.parser").get_text().strip()

    # ✅ Prevent empty AI response from breaking request
    if not clean_ai_response:
        print("⚠️ Skipping follow-up request (Empty AI response).")
        return "<p class='text-gray-600'>No follow-up questions available.</p>"

    payload = {
        "model": "deepseek-r1-distill-llama-70b",  # ✅ Use correct model
        "messages": [
            {"role": "system", "content": 
                "You are an AI interview assistant. I just answered an interview question. "
                "Now, I need **smart follow-up questions** that I should ask the recruiter.\n\n"
                
                "### **Instructions:**\n"
                "- Generate **relevant follow-up questions** based on my answer.\n"
                "- Keep them **short, concise, and professional**.\n"
                "- Format the response as a **Tailwind CSS-styled HTML list**.\n"
                "- Only return the formatted HTML, no additional explanations.\n"
                "- Generate a maximum of **5 questions**.\n\n"
                
                "### **Example Response Format (Do NOT return JSON, return this format)**:\n"
                "<h2 class='text-xl font-bold text-orange-400'>Follow-Up Questions</h2>\n"
                "<ul class='list-disc pl-5 text-white-600 dark:text-gray-300'>\n"
                "  <li class='mb-1'>What are the biggest challenges the team is facing?</li>\n"
                "  <li class='mb-1'>How do you measure success in this role?</li>\n"
                "  <li class='mb-1'>What technologies are used in your stack?</li>\n"
                "</ul>"
            },
            {"role": "user", "content": 
                f"My answer: {clean_ai_response}\n\n"
                f"What are the best follow-up questions I should ask the recruiter based on my response?"}
        ]
    }

    try:
        response = requests.post("https://api.groq.com/openai/v1/chat/completions", json=payload, headers=headers)
        response_data = response.json()
        print(f"✅ Groq API Response: {response_data}")

        if response.status_code != 200:
            print(f"❌ Groq API Error {response.status_code}: {response_data}")
            return "<p class='text-red-600'>Error fetching follow-up questions.</p>"

        if "choices" in response_data and len(response_data["choices"]) > 0:
            follow_up_html = response_data["choices"][0]["message"]["content"].strip()
            return follow_up_html  # ✅ Return the properly formatted HTML response

    except Exception as e:
        print(f"❌ Exception in get_follow_up_questions: {e}")
        return "<p class='text-red-600'>Error fetching follow-up questions.</p>"

    return "<p class='text-gray-600'>No follow-up questions available.</p>"
