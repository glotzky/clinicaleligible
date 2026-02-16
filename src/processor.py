import os
import instructor
from groq import Groq
from pydantic import BaseModel, Field
from typing import List, Literal, Optional
from dotenv import load_dotenv

load_dotenv()

# 1. Define the Schema
class Criterion(BaseModel):
    category: Literal["Age", "Condition", "Education", "Experience", "Medication", "Other"]
    type: Literal["Inclusion", "Exclusion"]
    entity: str = Field(description="The primary subject, e.g., 'Type 2 Diabetes'")
    # --- NEW FIELD ---
    icd10_code: Optional[str] = Field(description="The matching ICD-10-CM code if it is a medical condition")
    # -----------------
    operator: Optional[Literal["GREATER_THAN", "LESS_THAN", "EQUAL", "BETWEEN"]] = None
    value: Optional[str] = Field(description="Specific threshold")

# In parse_criteria, we update the system prompt slightly:
# "Extract clinical trial eligibility. For medical conditions, resolve to the most specific ICD-10-CM code possible."

class StructuredCriteria(BaseModel):
    """The full collection of extracted criteria."""
    items: List[Criterion]

# 2. Correct Initialization
# Use from_groq directly. It handles the patching and mode automatically.
api_key = os.getenv("GROQ_API_KEY")
if not api_key:
    raise ValueError("GROQ_API_KEY not found. Check your .env file!")

client = instructor.from_groq(Groq(api_key=api_key))

def parse_criteria(raw_text: str) -> StructuredCriteria:
    """Uses Groq + Llama 3 to transform raw text into StructuredCriteria objects."""
    return client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        response_model=StructuredCriteria,
        messages=[
            {"role": "system", "content": "You are a medical data architect. Extract clinical trial eligibility into structured JSON."},
            {"role": "user", "content": f"Extract the following criteria: {raw_text}"}
        ],
    )

if __name__ == "__main__":
    sample = "Inclusion: Patients must be over 18. Exclusion: No history of smoking."
    try:
        result = parse_criteria(sample)
        for item in result.items:
            print(f"✅ [{item.type}] {item.entity} | Category: {item.category}")
    except Exception as e:
        print(f"❌ Error: {e}")