"""
LLM service for field value prediction using Gemini 3 Flash.

Provides structured, explainable field predictions with strict JSON output.
Integrates with RAG service for context-aware recommendations.
"""

import google.generativeai as genai
from app.core.config import get_settings
from app.core.logging import logger
from typing import Dict, Any, List, Optional
import json
import time
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from app.services.prompt_service import prompt_service
from app.db.session import Session

settings = get_settings()

# Configure Gemini API
try:
    genai.configure(api_key=settings.GEMINI_API_KEY)
    GEMINI_AVAILABLE = True
except Exception as e:
    logger.warning(f"Gemini API key not configured: {e}")
    GEMINI_AVAILABLE = False


def predict_field_value(
    field_label: str,
    field_type: str,
    rag_candidates: List[Dict[str, Any]],
    user_context: Dict[str, Any],
    temperature: float = 0.1,
    tenant_id: Optional[Any] = None,
    task_id: Optional[Any] = None,
    current_task_llm_calls: int = 0,
    db: Optional[Any] = None
) -> Dict[str, Any]:
    """
    Use LLM (Gemini 3 Flash) to predict a field value with strict JSON output.
    
    CRITICAL: This function enforces cost governance before making LLM calls.
    
    Args:
        field_label: The form field label (e.g., "Company Name")
        field_type: Field type (text, email, url, etc.)
        rag_candidates: List of similar fields from RAG search
        user_context: User profile data (name, email, website, etc.)
        temperature: LLM temperature (0-1, lower = more deterministic)
        tenant_id: Tenant UUID for quota enforcement
        task_id: Task UUID for per-task limits
        current_task_llm_calls: Number of LLM calls made in current task
        db: Database session for quota checks
        
    Returns:
        {
            "value": str,               # Predicted value
            "confidence": float (0-1),  # Confidence score
            "source": str,              # "rag" | "heuristic" | "rejected"
            "reasoning": str,           # Explanation of the decision
            "prompt_version_id": str | None,
            "latency_ms": int | None
        }
    """
    start_time = time.time()
    
    # Internal function to handle the actual LLM call with retries
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((Exception)), # Broad for now, can be refined
        reraise=True
    )
    def _call_gemini_with_retry(model_name: str, prompt_text: str, temp: float):
        model = genai.GenerativeModel(model_name)
        return model.generate_content(
            prompt_text,
            generation_config=genai.GenerationConfig(
                temperature=temp,
                response_mime_type="application/json"
            )
        )

    if not GEMINI_AVAILABLE:
        logger.warning("Gemini not configured, returning rejected prediction")
        return {
            "value": "",
            "confidence": 0.0,
            "source": "rejected",
            "reasoning": "LLM service not configured",
            "prompt_version_id": None,
            "latency_ms": 0
        }
    
    # GOVERNANCE: Check LLM quota before calling API
    if tenant_id and db:
        from app.services.cost_governance import check_llm_allowed
        
        governance_check = check_llm_allowed(
            db=db,
            tenant_id=tenant_id,
            task_id=task_id,
            current_task_calls=current_task_llm_calls
        )
        
        if not governance_check["allowed"]:
            logger.warning(f"LLM quota check failed: {governance_check['reason']}")
            return {
                "value": "",
                "confidence": 0.0,
                "source": "rejected",
                "reasoning": f"LLM quota exceeded: {governance_check['reason']}",
                "prompt_version_id": None,
                "latency_ms": 0
            }
    
    # Fetch prompt from Database if possible
    prompt_version_id = None
    model_name = 'gemini-1.5-flash'
    prompt_content = None
    
    if db:
        active_prompt = prompt_service.get_active_prompt(db, "field_prediction")
        if active_prompt:
            prompt_version_id = active_prompt.id
            prompt_content = active_prompt.content
            if active_prompt.config and "model" in active_prompt.config:
                model_name = active_prompt.config["model"]
            if active_prompt.config and "temperature" in active_prompt.config:
                temperature = active_prompt.config["temperature"]

    # Build prompt using template or fallback
    if prompt_content:
        # Simple string formatting for now, can move to Jinja2 if needed
        # We need to be careful about keys. Let's assume the template uses {key}
        try:
            rag_context = _format_rag_context(rag_candidates)
            user_data = json.dumps(user_context, indent=2)
            prompt = prompt_content.format(
                field_label=field_label,
                field_type=field_type,
                rag_context=rag_context,
                user_data=user_data
            )
        except Exception as e:
            logger.error(f"Failed to format versioned prompt: {e}. Falling back to default.")
            prompt = _build_prediction_prompt(field_label, field_type, rag_candidates, user_context)
    else:
        prompt = _build_prediction_prompt(field_label, field_type, rag_candidates, user_context)
    
    try:
        # Generate prediction with retry and fallback
        try:
            response = _call_gemini_with_retry(model_name, prompt, temperature)
        except Exception as e:
            logger.warning(f"Gemini call failed after retries: {e}. Attempting fallback model...")
            # FALLBACK logic
            if model_name != 'gemini-1.5-flash':
                 response = _call_gemini_with_retry('gemini-1.5-flash', prompt, temperature)
            else:
                 raise e
        
        latency_ms = int((time.time() - start_time) * 1000)
        
        # Parse JSON response
        result = json.loads(response.text)
        
        # Validate schema
        _validate_prediction_schema(result)
        
        # Inject metadata
        result["prompt_version_id"] = str(prompt_version_id) if prompt_version_id else None
        result["latency_ms"] = latency_ms
        
        # GOVERNANCE: Record LLM usage
        if tenant_id and db:
            from app.services.cost_governance import cost_governance
            # Estimate tokens
            estimated_tokens = (len(prompt) + len(response.text)) // 4
            estimated_cost = estimated_tokens * 0.0000001
            
            cost_governance.record_llm_call(
                db=db,
                tenant_id=tenant_id,
                task_id=task_id,
                tokens_used=estimated_tokens,
                cost_usd=estimated_cost,
                model=model_name,
                operation="field_prediction",
                prompt_version_id=prompt_version_id,
                confidence=result.get("confidence"),
                latency_ms=latency_ms
            )
        
        logger.info(f"LLM prediction for '{field_label}': confidence={result['confidence']}, source={result['source']}")
        return result
        
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse LLM JSON response: {e}")
        return {
            "value": "",
            "confidence": 0.0,
            "source": "rejected",
            "reasoning": f"LLM response parsing error: {str(e)}",
            "prompt_version_id": str(prompt_version_id) if prompt_version_id else None,
            "latency_ms": int((time.time() - start_time) * 1000)
        }
    except Exception as e:
        logger.error(f"LLM prediction failed: {e}")
        return {
            "value": "",
            "confidence": 0.0,
            "source": "rejected",
            "reasoning": f"LLM error: {str(e)}",
            "prompt_version_id": str(prompt_version_id) if prompt_version_id else None,
            "latency_ms": int((time.time() - start_time) * 1000)
        }


def _format_rag_context(rag_candidates: List[Dict[str, Any]]) -> str:
    """Format RAG candidates for the prompt."""
    if not rag_candidates:
        return "**No RAG candidates found** (first time seeing this field)\n\n"
        
    context = "**RAG Candidates from past successful submissions:**\n"
    for idx, candidate in enumerate(rag_candidates[:3], 1):
        context += f"{idx}. Label: '{candidate['field_label']}'\n"
        context += f"   Value: '{candidate['successful_value']}'\n"
        context += f"   Similarity: {candidate['similarity']:.2f}\n"
        context += f"   Success count: {candidate['success_count']}\n\n"
    return context


def _build_prediction_prompt(
    field_label: str,
    field_type: str,
    rag_candidates: List[Dict[str, Any]],
    user_context: Dict[str, Any]
) -> str:
    """Build the prediction prompt for Gemini."""
    
    # Format RAG candidates
    rag_context = ""
    if rag_candidates:
        rag_context = "**RAG Candidates from past successful submissions:**\n"
        for idx, candidate in enumerate(rag_candidates[:3], 1):
            rag_context += f"{idx}. Label: '{candidate['field_label']}'\n"
            rag_context += f"   Value: '{candidate['successful_value']}'\n"
            rag_context += f"   Similarity: {candidate['similarity']:.2f}\n"
            rag_context += f"   Success count: {candidate['success_count']}\n\n"
    else:
        rag_context = "**No RAG candidates found** (first time seeing this field)\n\n"
    
    # Format user context
    user_data = json.dumps(user_context, indent=2)
    
    prompt = f"""You are a form-filling assistant. Given the following information, predict the best value for a form field.

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

**Example outputs:**

High confidence RAG match:
{{
  "value": "Acme Corporation",
  "confidence": 0.92,
  "source": "rag",
  "reasoning": "RAG candidate has 0.95 similarity and 12 successful uses."
}}

Heuristic match:
{{
  "value": "contact@example.com",
  "confidence": 0.85,
  "source": "heuristic",
  "reasoning": "Field type is email, using user's email from profile."
}}

Rejected (low confidence):
{{
  "value": "",
  "confidence": 0.0,
  "source": "rejected",
  "reasoning": "No RAG matches and no applicable heuristic for this field."
}}

Now predict the value for the field described above:
"""
    
    return prompt


def _validate_prediction_schema(result: Dict[str, Any]) -> None:
    """Validate that LLM response matches expected schema."""
    required_fields = ["value", "confidence", "source", "reasoning"]
    
    for field in required_fields:
        if field not in result:
            raise ValueError(f"Missing required field: {field}")
    
    # Validate types
    if not isinstance(result["value"], str):
        raise ValueError("'value' must be a string")
    
    if not isinstance(result["confidence"], (int, float)):
        raise ValueError("'confidence' must be a number")
    
    if result["confidence"] < 0.0 or result["confidence"] > 1.0:
        raise ValueError("'confidence' must be between 0.0 and 1.0")
    
    valid_sources = ["rag", "heuristic", "rejected"]
    if result["source"] not in valid_sources:
        raise ValueError(f"'source' must be one of: {valid_sources}")
    
    if not isinstance(result["reasoning"], str):
        raise ValueError("'reasoning' must be a string")


def batch_predict(
    fields: List[Dict[str, Any]],
    user_context: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """
    Predict values for multiple fields in a batch.
    
    Args:
        fields: List of dicts with keys: field_label, field_type, rag_candidates
        user_context: User profile data
        
    Returns:
        List of prediction results
    """
    predictions = []
    
    for field in fields:
        try:
            prediction = predict_field_value(
                field_label=field["field_label"],
                field_type=field["field_type"],
                rag_candidates=field.get("rag_candidates", []),
                user_context=user_context
            )
            predictions.append({
                "field_label": field["field_label"],
                **prediction
            })
        except Exception as e:
            logger.error(f"Failed to predict field '{field.get('field_label')}': {e}")
            predictions.append({
                "field_label": field.get("field_label", "unknown"),
                "value": "",
                "confidence": 0.0,
                "source": "rejected",
                "reasoning": f"Prediction error: {str(e)}"
            })
    
    return predictions
