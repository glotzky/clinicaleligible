import os
import instructor
from groq import Groq
from typing import List, Optional, Literal, Annotated
from pydantic import BaseModel, Field, field_validator, StringConstraints
from dotenv import load_dotenv

load_dotenv()

_base_client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
client = instructor.patch(_base_client)

class Criterion(BaseModel):
    category: str 
    type: Literal["Inclusion", "Exclusion"]
    entity: str = "General"
    icd10_code: Optional[str] = None 
    operator: str = "NOT_APPLICABLE"
    value: Annotated[str, StringConstraints(min_length=1)]

    @field_validator('category')
    @classmethod
    def fix_categories(cls, v: str):
        v = v.replace("Criteria", "").strip().title()
        allowed = ["Age", "Condition", "Education", "Experience", "Medication", "Laboratory", "Lifestyle", "Other"]
        
        if v in allowed:
            return v
        
        mapping = {
            "Health": "Condition",
            "Disease": "Condition",
            "Drug": "Medication",
            "Treatment": "Medication", #
            "Lab": "Laboratory",
            "Physical": "Lifestyle"
        }
        return mapping.get(v, "Other")

class StructuredCriteria(BaseModel):
    items: List[Criterion] = Field(description="A single list of all extracted criteria")

def parse_criteria(raw_text: str) -> StructuredCriteria:
    # 1. Clean the text slightly before sending it to the AI
    clean_text = raw_text.replace("¬", " ").replace("*", " ").replace("~", " ")
    safe_text = clean_text[:1200] 

    return client.chat.completions.create(
        model="llama-3.1-8b-instant",
        response_model=StructuredCriteria,
        max_retries=3,
        messages=[
            {
                "role": "system", 
                "content": (
                    "You are a medical data architect. Extract items into ONE list.\n"
                    "CRITICAL: Do not use special symbols like ¬ or ~. "
                    "If you see complex scoring, summarize it into one sentence."
                )
            },
            {"role": "user", "content": f"Extract: {safe_text}"}
        ]
    )

class ICD10Result(BaseModel):
    codes: List[str] = Field(description="List of specific ICD-10-CM codes (e.g., ['C50.9', 'C43.9'])")

def get_icd10_codes(condition_text: str) -> List[str]:
    """Specialized lookup that returns a list of medical codes."""
    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            response_model=ICD10Result,
            messages=[
                {
                    "role": "system", 
                    "content": "Professional medical coder. Extract ALL relevant ICD-10-CM codes. Output only the codes."
                },
                {"role": "user", "content": f"Conditions: {condition_text}"}
            ]
        )
        return response.codes
    except Exception as e:
        print(f"Error during ICD-10 lookup: {e}")
        return []