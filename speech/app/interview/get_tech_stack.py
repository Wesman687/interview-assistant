
import httpx

from app.config import GROQ_API_KEY, RESUME_TEXT
from app.interview.cleaning import clean_ai_response


async def fetch_tech_stack(jobInfo: str) -> dict:
    """Fetches a brief company overview formatted with Tailwind CSS."""
    
    # ✅ AI Processing Setup
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
    "model": "deepseek-r1-distill-llama-70b",
    "messages": [
        {
            "role": "system",
            "content": (
                "You are an AI assistant helping a user prepare for a job interview. "
                "Your task is to analyze the given job details and extract the **Tech Stack** used in the job. "
                "Then, compare it to the user's resume and highlight relevant past projects or experience that align with the tech stack. "
                "Format the response in **Tailwind CSS HTML** for display in a web application."
                
                "\n\n"
                "### **Instructions:**\n"
                "- Extract **technologies** (programming languages, frameworks, databases, tools) mentioned in the job details.\n"
                "- Briefly explain each technology's purpose in the job.\n"
                "- Compare the extracted tech stack to the user's resume.\n"
                "- List relevant past projects and explain how they align with the job.\n"
                "- Format the output in HTML with **Tailwind CSS** styling.\n\n"
                
                "### **Tailwind CSS Formatting:**\n"
                "- **Use `<h2 class='text-xl font-bold text-blue-700'>` for 'Tech Stack for [Company Name]'.**\n"
                "- **Use `<h3 class='text-lg font-semibold text-gray-800 mt-4'>` for 'Technologies Used'.**\n"
                "- **Use `<ul class='list-disc pl-5 text-gray-600 dark:text-gray-300'>` for listing technologies.**\n"
                "- **Use `<p class='text-gray-600 leading-relaxed'>` for descriptions.**\n"
                "- **Use `<h3 class='text-lg font-semibold text-gray-800 mt-4'>` for 'Relevant Experience'.**\n"
                "- **Use `<ul class='list-disc pl-5 text-gray-600 dark:text-gray-300'>` for listing relevant projects.**\n"
                "- Ensure a **structured, professional, and easy-to-read layout**.\n\n"

                "### **Example Response:**\n"
                "<h2 class='text-xl font-bold text-blue-700'>Tech Stack for Google</h2>\n"
                "<h3 class='text-lg font-semibold text-gray-800 mt-4'>Technologies Used</h3>\n"
                "<ul class='list-disc pl-5 text-gray-600 dark:text-gray-300'>\n"
                "<li class='mb-1'><strong>Python</strong> - Used for backend development and AI models.</li>\n"
                "<li class='mb-1'><strong>React.js</strong> - Frontend framework for user interfaces.</li>\n"
                "<li class='mb-1'><strong>BigQuery</strong> - Google’s data warehouse for large-scale analytics.</li>\n"
                "</ul>\n\n"
                
                "<h3 class='text-lg font-semibold text-gray-800 mt-4'>Relevant Experience</h3>\n"
                "<ul class='list-disc pl-5 text-gray-600 dark:text-gray-300'>\n"
                "<li class='mb-1'><strong>Built an AI-powered chatbot using Python and TensorFlow</strong> - Related to Google's AI projects.</li>\n"
                "<li class='mb-1'><strong>Developed a React-based dashboard</strong> - Similar frontend stack as Google's UI systems.</li>\n"
                "<li class='mb-1'><strong>Worked with SQL-based analytics tools</strong> - Relevant to BigQuery usage.</li>\n"
                "</ul>"
            )
        },
        {
            "role": "user",
            "content": f"Here is my Resume Info:\n{RESUME_TEXT}\n\nHere is the job information:\n{jobInfo}.\n\nExtract the tech stack and compare it to my experience."
        }
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
    print("Got response from json")

    # ✅ Check if "choices" exist
    if "choices" not in data or not data["choices"]:
        return {"error": "No valid response from AI"}

    # ✅ Extract AI-generated message
    raw_content = data["choices"][0]["message"]["content"].strip()
    # ✅ Clean response
    cleaned_content = clean_ai_response(raw_content)

    return {"tech_stack": cleaned_content}
