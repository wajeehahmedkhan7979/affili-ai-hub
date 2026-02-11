"""
Enhanced Playwright automation with RAG + LLM field prediction.

This module provides intelligent form field filling using:
- DOM extraction to discover form fields
- RAG similarity search for historical matches
- LLM prediction with confidence scoring
- Fallback to deterministic heuristics
"""

from playwright.async_api import async_playwright, Page, Browser
from app.services.field_predictor import predict_form_field, predict_multiple_fields, get_prediction_stats
from app.services.embedding_service import store_field_embedding
from app.core.logging import logger
from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional, Tuple
import uuid
import asyncio
import json


async def extract_form_fields(page: Page) -> List[Dict[str, Any]]:
    """
    Extract all form fields from the current page using Playwright.
    
    Returns list of fields with structure:
    [
        {
            "selector": str,  # CSS selector
            "label": str,     # Field label text
            "type": str,      # input type (text, email, etc.)
            "placeholder": str,
            "required": bool
        }
    ]
    """
    logger.info("Extracting form fields from page")
    
    # JavaScript to extract form fields
    js_extractor = """
    () => {
        const fields = [];
        const inputs = document.querySelectorAll('input, textarea, select');
        
        inputs.forEach((input, index) => {
            // Skip hidden inputs, buttons, submit
            if (input.type === 'hidden' || input.type === 'submit' || input.type === 'button') {
                return;
            }
            
            // Find associated label
            let label = '';
            if (input.id) {
                const labelEl = document.querySelector(`label[for="${input.id}"]`);
                if (labelEl) label = labelEl.textContent.trim();
            }
            if (!label) {
                // Try parent label
                const parentLabel = input.closest('label');
                if (parentLabel) label = parentLabel.textContent.trim().replace(input.value || '', '').trim();
            }
            if (!label) {
                // Try aria-label
                label = input.getAttribute('aria-label') || input.getAttribute('placeholder') || input.name || `field_${index}`;
            }
            
            // Generate unique selector
            let selector = '';
            if (input.id) {
                selector = `#${input.id}`;
            } else if (input.name) {
                selector = `[name="${input.name}"]`;
            } else {
                selector = `${input.tagName.toLowerCase()}:nth-of-type(${Array.from(input.parentElement.children).indexOf(input) + 1})`;
            }
            
            fields.push({
                selector: selector,
                label: label,
                type: input.type || input.tagName.toLowerCase(),
                placeholder: input.placeholder || '',
                required: input.required || false,
                name: input.name || ''
            });
        });
        
        return fields;
    }
    """
    
    try:
        fields = await page.evaluate(js_extractor)
        logger.info(f"Extracted {len(fields)} form fields")
        return fields
    except Exception as e:
        logger.error(f"Failed to extract form fields: {e}")
        return []


async def fill_form_with_predictions(
    page: Page,
    db: Session,
    tenant_id: uuid.UUID,
    user_profile: Dict[str, Any],
    program_id: Optional[uuid.UUID] = None,
    confidence_threshold: float = 0.7
) -> Dict[str, Any]:
    """
    Fill form fields using RAG + LLM predictions.
    
    Flow:
    1. Extract all form fields from page
    2. Batch predict values using RAG + LLM
    3. Fill fields with high-confidence predictions
    4. Return summary of filled vs. skipped fields
    
    Args:
        page: Playwright page object
        db: Database session
        tenant_id: Tenant UUID
        user_profile: User context (name, email, website, etc.)
        program_id: Optional program UUID for more targeted predictions
        confidence_threshold: Minimum confidence to auto-fill (0.7 = 70%)
        
    Returns:
        {
            "total_fields": int,
            "filled": int,
            "skipped": int,
            "predictions": Dict[str, Dict],
            "stats": Dict
        }
    """
    logger.info(f"Starting intelligent form fill for tenant {tenant_id}")
    
    # Step 1: Extract form fields
    fields = await extract_form_fields(page)
    
    if not fields:
        logger.warning("No form fields found on page")
        return {
            "total_fields": 0,
            "filled": 0,
            "skipped": 0,
            "predictions": {},
            "stats": {}
        }
    
    # Step 2: Batch predict values
    predictions = predict_multiple_fields(
        db=db,
        tenant_id=tenant_id,
        fields=[{"field_label": f["label"], "field_type": f["type"]} for f in fields],
        user_profile=user_profile,
        program_id=program_id
    )
    
    # Step 3: Fill fields with high-confidence predictions
    filled_count = 0
    skipped_count = 0
    
    for field in fields:
        label = field["label"]
        selector = field["selector"]
        
        prediction = predictions.get(label)
        
        if not prediction or prediction["value"] is None:
            logger.info(f"Skipping field '{label}': no prediction")
            skipped_count += 1
            continue
        
        if prediction["confidence"] < confidence_threshold:
            logger.info(f"Skipping field '{label}': confidence {prediction['confidence']} below threshold")
            skipped_count += 1
            continue
        
        # Fill the field
        try:
            await page.fill(selector, str(prediction["value"]))
            filled_count += 1
            logger.info(f"Filled field '{label}' with value (confidence: {prediction['confidence']})")
        except Exception as e:
            logger.error(f"Failed to fill field '{label}': {e}")
            skipped_count += 1
    
    # Step 4: Generate stats
    stats = get_prediction_stats(predictions)
    
    logger.info(f"Form fill complete: {filled_count}/{len(fields)} fields filled")
    
    return {
        "total_fields": len(fields),
        "filled": filled_count,
        "skipped": skipped_count,
        "predictions": predictions,
        "stats": stats
    }


async def store_successful_form_submission(
    db: Session,
    tenant_id: uuid.UUID,
    program_id: Optional[uuid.UUID],
    filled_fields: Dict[str, str]
):
    """
    Store successful form field submissions to build RAG knowledge base.
    
    Should be called after a successful automation to learn from the submission.
    
    Args:
        db: Database session
        tenant_id: Tenant UUID
        program_id: Program UUID
        filled_fields: Dict of field_label -> value that was successfully submitted
    """
    logger.info(f"Storing {len(filled_fields)} successful field submissions")
    
    for label, value in filled_fields.items():
        try:
            store_field_embedding(
                db=db,
                tenant_id=tenant_id,
                program_id=program_id,
                field_label=label,
                field_type="text",  # Could be improved by tracking actual type
                successful_value=value,
                form_context={"source": "playwright_automation"}
            )
        except Exception as e:
            logger.error(f"Failed to store field '{label}': {e}")
    
    logger.info("Successfully stored form submission data")
