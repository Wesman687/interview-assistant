


from app.interview.groq.response_schema import ExtraFactsSchema, GroqResponseSchema


def parse_groq_response(response_text: str):
    """Parses the response from Groq and structures it properly."""

    try:
        sections = response_text.split("\n\n")
        preferred_response = sections[0] if len(sections) > 0 else "No response generated."
        follow_up_questions = []
        extra_facts = {"tech_stack": [], "jobs": [], "company_description": ""}

        for section in sections[1:]:
            if "Follow-Up Questions:" in section:
                follow_up_questions = [q.strip() for q in section.split("\n") if q.strip() and "-" in q]
            elif "Tech Stack:" in section:
                tech_list = section.split(":")[1].strip().split(",")  # ✅ Split correctly
                extra_facts["tech_stack"] = [tech.strip() for tech in tech_list if tech.strip()]
            elif "Jobs:" in section:
                extra_facts["jobs"] = [job.strip() for job in section.split("\n") if job.strip() and "-" in job]
            elif "Company Info:" in section:
                extra_facts["company_description"] = section.split(":")[1].strip()

        # ✅ Convert to dictionary safely
        extra_facts_dict = ExtraFactsSchema(**extra_facts).model_dump() if hasattr(ExtraFactsSchema, "model_dump") else ExtraFactsSchema(**extra_facts).dict()

        return GroqResponseSchema(
            preferred_response=preferred_response,
            follow_up_questions=follow_up_questions,
            extra_facts=extra_facts_dict
        )

    except Exception as e:
        print(f"❌ Error parsing Groq response: {e}")
        return GroqResponseSchema(
            preferred_response="Error processing response.",
            follow_up_questions=[],
            extra_facts={"tech_stack": [], "jobs": [], "company_description": ""}
        )

