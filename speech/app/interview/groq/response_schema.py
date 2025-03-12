from pydantic import BaseModel
from typing import List, Optional



class ExtraFactsSchema(BaseModel):
    tech_stack: List[str] = []  # ✅ Ensure tech_stack is always a list
    jobs: List[str] = []
    company_description: str = ""
    
class GroqResponseSchema(BaseModel):
    preferred_response: str
    follow_up_questions: List[str]
    extra_facts: ExtraFactsSchema
