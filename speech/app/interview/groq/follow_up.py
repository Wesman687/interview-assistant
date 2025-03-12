
import requests
from app.config import GROQ_API_KEY


def get_follow_up_questions(user_input):
    """Fetches ONLY follow-up questions from Groq."""
    print(f"🔍 Fetching Follow-Up Questions for: {user_input}")

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "deepseek-r1-distill-llama-70b",
        "messages": [
            {"role": "system", "content": 
                "You are an AI interview assistant. Your job is to generate **2-3 smart follow-up questions** "
                "related to the user's query. These should be insightful and help further the discussion."},
            {"role": "user", "content": user_input}
        ]
    }

    response = requests.post("https://api.groq.com/openai/v1/chat/completions", json=payload, headers=headers)

    if response.status_code != 200:
        return {"error": f"Groq API request failed: {response.status_code}", "details": response.text}

    data = response.json()

    if "choices" in data and len(data["choices"]) > 0:
        return data["choices"][0]["message"]["content"].split("\n")

    return {"error": "Invalid Groq API response format"}
