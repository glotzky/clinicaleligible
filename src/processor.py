import os
from typing import List, Optional, Literal
from pydantic import BaseModel, Field
import instructor
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

# --- 1. Schema Definition ---
class Criterion(BaseModel):
    category: Literal["Age", "Condition", "Education", "Experience", "Medication", "Laboratory", "Lifestyle", "Other"]
    type: Literal["Inclusion", "Exclusion"]
    entity: str = Field(description="The specific medical entity, e.g., 'HbA1c' or 'Left Ventricular Function'")
    icd10_code: Optional[str] = Field(None, description="Granular ICD-10 code (e.g., C50.911 instead of just C50)")
    
    # We add NOT_APPLICABLE and handle common LLM hallucinations here
    operator: Optional[Literal["GREATER_THAN", "LESS_THAN", "EQUAL", "BETWEEN", "NOT_APPLICABLE"]] = Field(
        "NOT_APPLICABLE", 
        description="The mathematical relationship for the value"
    )
    
    value: Optional[str] = Field(description="The original text or threshold (e.g., '> 5.0')")
    min_age: Optional[int] = Field(None, description="Numeric minimum age in years")
    max_age: Optional[int] = Field(None, description="Numeric maximum age in years")

class StructuredCriteria(BaseModel):
    items: List[Criterion]

# --- 2. AI Client Setup ---
client = instructor.patch(Groq(api_key=os.environ.get("GROQ_API_KEY")))

def parse_criteria(raw_text: str) -> StructuredCriteria:
    """
    Parses raw eligibility text into a structured list of criteria items.
    Uses Llama-3.1-8b with strict schema enforcement via the 'instructor' library.
    """
    
    system_instruction = (
        "You are a Clinical Trial Data Specialist. Your task is to extract eligibility criteria into structured JSON.\n\n"
        "STRICT ADHERENCE REQUIRED:\n"
        "1. CATEGORIES: Only use: Age, Condition, Education, Experience, Medication, Laboratory, Lifestyle, Other.\n"
        "   - Map 'Pregnancy' to 'Lifestyle'.\n"
        "   - Map 'Informed Consent' to 'Other'.\n"
        "2. OPERATORS: Use ONLY 'GREATER_THAN', 'LESS_THAN', 'EQUAL', 'BETWEEN', or 'NOT_APPLICABLE'.\n"
        "   - NEVER use 'EXCLUSION' as an operator name.\n"
        "3. ICD-10 CODES: Provide the most granular code possible (e.g., 'C50.911'). If no specific disease is mentioned, use null.\n"
        "4. AGE: For 'Age' category, extract min_age and max_age as integers. If it says '18 years and older', min_age=18, max_age=120.\n"
        "5. ENTITY: Keep this short (1-3 words). Example: 'Type 2 Diabetes', 'Prior Chemotherapy'."
    )

    # We use the 8B model as it's faster and cheaper on tokens for the Free Tier
    return client.chat.completions.create(
        model="llama-3.1-8b-instant",
        response_model=StructuredCriteria,
        max_retries=3, # Instructor will automatically re-prompt the LLM if it fails validation
        messages=[
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": f"Extract structured criteria from this text: \n\n{raw_text}"}
        ],
        temperature=0.1, # Lower temperature = more consistent/predictable output
    )