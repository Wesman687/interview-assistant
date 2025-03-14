import httpx
from app.config import GROQ_API_KEY
from app.interview.cleaning import clean_ai_response

async def fetch_company_info(company: str) -> dict:
    """Fetches a brief company overview formatted with Tailwind CSS."""
    
    # ✅ AI Processing Setup
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "deepseek-r1-distill-llama-70b",
        "messages": [
            {"role": "system", "content": 
                "You are an AI assistant. A user is preparing for a job interview."
                "Provide **brief company details** for quick reference, formatted using Tailwind CSS."
                "Include any relevant recent news. Keep it concise."
                "\n\n"
                "### **Required Information:**\n"
                "- **Industry**\n"
                "- **Company Size**\n"
                "- **Key Products/Services**\n\n"
                
                "### **Tailwind CSS Formatting:**\n"
                "- **Use `<h2 class='text-xl font-bold text-blue-700'>` for the Company Name.**\n"
                "- **Use `<h3 class='text-lg font-semibold text-gray-800 mt-4'>` for each section header.**\n"
                "- **Use `<p class='text-gray-600 leading-relaxed'>` for descriptions.**\n"
                "- **Use `<ul class='list-disc pl-5 text-gray-600'>` and `<li class='mb-1'>` for bullet points.**\n"
                "- **Ensure a professional layout with clear structure.**\n\n"
                
                "### **Example Response:**\n"
                "<h2 class='text-xl font-bold text-blue-700'>Tesla, Inc.</h2>\n"
                "<h3 class='text-lg font-semibold text-gray-800 mt-4'>Industry</h3>\n"
                "<p class='text-gray-600 leading-relaxed'>Automotive and Clean Energy</p>\n"
                "<h3 class='text-lg font-semibold text-gray-800 mt-4'>Company Size</h3>\n"
                "<p class='text-gray-600 leading-relaxed'>100,000+ employees</p>\n"
                "<h3 class='text-lg font-semibold text-gray-800 mt-4'>Key Products & Services</h3>\n"
                "<ul class='list-disc pl-5 text-gray-600'>\n"
                "<li class='mb-1'>Electric Vehicles</li>\n"
                "<li class='mb-1'>Solar Energy Solutions</li>\n"
                "<li class='mb-1'>Battery Storage Systems</li>\n"
                "</ul>"
            },
            {"role": "user", "content": f"Give me a quick overview of {company}."}
        ]
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                json=payload,
                headers=headers
            )
            response.raise_for_status()  # ✅ Raise an error for bad responses (4xx, 5xx)
    except httpx.RequestError as e:
        print(f"❌ Network Error: {e}")
        return {"error": "Network request failed"}

    data = response.json()

    # ✅ Check if "choices" exist
    if "choices" not in data or not data["choices"]:
        return {"error": "No valid response from AI"}

    # ✅ Extract AI-generated message
    raw_content = data["choices"][0]["message"]["content"].strip()

    # ✅ Clean response
    cleaned_content = clean_ai_response(raw_content)

    return {"company_info": cleaned_content}
