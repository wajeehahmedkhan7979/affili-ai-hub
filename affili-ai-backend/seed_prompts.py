"""
Seed initial prompt templates for Phase 20.
"""

from sqlalchemy.orm import Session
from app.db.session import get_engine_instance
from app.db.base import Base
from app.models.prompt_template import PromptTemplate
from datetime import datetime
import uuid

def seed_prompts():
    engine = get_engine_instance()
    
    # Ensure tables exist (PromptTemplate)
    # This will also ensure metadata is registered if models are imported here
    Base.metadata.create_all(bind=engine)
    
    with Session(engine) as db:
        # Check if already exists
        exists = db.query(PromptTemplate).filter(PromptTemplate.name == "field_prediction").first()
        if exists:
            print("Prompt 'field_prediction' already exists. Skipping.")
            return

        initial_content = """You are a form-filling assistant. Given the following information, predict the best value for a form field.

**Field Label:** {field_label}
**Field Type:** {field_type}

**User Context:**
{user_data}

{rag_context}

**Decision Rules:**
1. If RAG candidates have high similarity (>0.80), strongly prefer their values (source="rag")
2. If field_type is "email", use user_context.email if available (source="heuristic")
3. If field_type is "url", use user_context.website if available (source="heuristic")
4. If field_label contains "name" or "company", use user_context.name or user_context.company (source="heuristic")
5. NEVER hallucinate or make up data
6. If confidence < 0.5, set source="rejected"

**Output Requirements:**
- Output ONLY valid JSON matching this exact schema
- No additional text before or after the JSON
- All strings must be properly escaped

**JSON Schema:**
{{
  "value": "string - predicted value or empty string if rejected",
  "confidence": number between 0.0 and 1.0,
  "source": "rag" | "heuristic" | "rejected",
  "reasoning": "string - brief explanation of decision (1-2 sentences)"
}}

Now predict the value for the field described above:
"""
        
        prompt = PromptTemplate(
            name="field_prediction",
            version=1,
            content=initial_content,
            config={"model": "gemini-1.5-flash", "temperature": 0.1},
            is_active=True
        )
        
        db.add(prompt)
        db.commit()
        print("Successfully seeded initial field_prediction prompt v1.")

if __name__ == "__main__":
    seed_prompts()
