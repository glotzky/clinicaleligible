import os
import instructor
from groq import Groq
from pydantic import BaseModel, Field
from typing import List, Literal, Optional
from dotenv import load_dotenv

load_dotenv()

# 1. Define the Schema (The "Form")
class Criterion(BaseModel):
    """Represents a single eligibility requirement extracted from text."""
    category: Literal["Age", "Condition", "Education", "Experience", "Medication", "Other"]
    type: Literal["Inclusion", "Exclusion"]
    entity: str = Field(description="The primary subject, e.g., 'Nursing Degree', 'Diabetes'")
    operator: Optional[Literal["GREATER_THAN", "LESS_THAN", "EQUAL", "BETWEEN"]] = None
    value: Optional[str] = Field(description="The specific value or threshold required")

class StructuredCriteria(BaseModel):
    """The full collection of extracted criteria."""
    items: List[Criterion]

# 2. Initialize the Groq Client with Instructor
# Note: Groq requires 'Mode.GROQ' to handle the JSON schema correctly
client = instructor.from_groq(
    Groq(api_key=os.getenv("GROQ_API_KEY")), 
    mode=instructor.Mode.GROQ
)

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
    # Quick test
    sample = "Inclusion: Patients must be over 18. Exclusion: No history of smoking."
    result = parse_criteria(sample)
    for item in result.items:
        print(f"{item.type}: {item.entity} ({item.category})")