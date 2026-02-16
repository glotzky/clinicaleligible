import os
import instructor
from openai import OpenAI
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

# 2. Initialize the Patched Client
# Instructor transforms the OpenAI client to support 'response_model'
client = instructor.from_openai(OpenAI(api_key=os.getenv("OPENAI_API_KEY")))

def parse_criteria(raw_text: str) -> StructuredCriteria:
    """Uses LLM to transform raw text into StructuredCriteria objects."""
    return client.chat.completions.create(
        model="gpt-4o",  # Or "gpt-4o-mini" for faster/cheaper testing
        response_model=StructuredCriteria,
        messages=[
            {"role": "system", "content": "You are a medical data architect. Extract clinical trial eligibility into structured JSON."},
            {"role": "user", "content": f"Extract the following criteria: {raw_text}"}
        ],
    )

if __name__ == "__main__":
    # Test with a small snippet
    sample_text = "Inclusion: Adults 18-65. Must have a Master's degree in Nursing. Exclusion: History of heart failure."
    structured_data = parse_criteria(sample_text)
    
    for item in structured_data.items:
        print(f"[{item.type}] {item.category}: {item.entity} | Value: {item.value}")