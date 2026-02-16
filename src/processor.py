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
    icd10_code: Optional[str] = Field(description="Matching ICD-10-CM code for medical conditions")
    operator: Optional[Literal["GREATER_THAN", "LESS_THAN", "EQUAL", "BETWEEN"]] = None
    value: Optional[str] = Field(description="The original text value (e.g., '18-65 years')")
    
    min_age: Optional[int] = Field(None, description="Minimum age bound as an integer. Use 0 if none.")
    max_age: Optional[int] = Field(None, description="Maximum age bound as an integer. Use 120 if none.")

class StructuredCriteria(BaseModel):
    """The full collection of extracted criteria."""
    items: List[Criterion]

# 2. Correct Initialization
api_key = os.getenv("GROQ_API_KEY")
if not api_key:
    raise ValueError("GROQ_API_KEY not found. Check your .env file!")

client = instructor.from_groq(Groq(api_key=api_key))

def parse_criteria(raw_text: str) -> StructuredCriteria:
    """Uses Groq + Llama 3 to transform raw text into StructuredCriteria objects."""
    
    system_instruction = (
        "You are a medical data architect. Extract clinical trial eligibility into structured JSON.\n"
        "RULES:\n"
        "1. For medical conditions, resolve to the most specific ICD-10-CM code possible.\n"
        "2. For 'Age' category, always extract numeric bounds into min_age and max_age.\n"
        "   - If '18 years or older': min_age=18, max_age=120.\n"
        "   - If 'Up to 65': min_age=0, max_age=65.\n"
        "   - If '18 to 65': min_age=18, max_age=65."
    )

    return client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        response_model=StructuredCriteria,
        messages=[
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": f"Extract the following criteria: {raw_text}"}
        ],
    )

if __name__ == "__main__":
    sample = "Inclusion: Patients 18 to 75 years old. Exclusion: Type 2 Diabetes (E11)."
    try:
        result = parse_criteria(sample)
        for item in result.items:
            print(f"✅ [{item.type}] {item.entity} | Age Range: {item.min_age}-{item.max_age}")
    except Exception as e:
        print(f"❌ Error: {e}")