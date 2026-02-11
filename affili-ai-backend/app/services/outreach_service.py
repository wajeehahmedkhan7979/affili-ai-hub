"""
Outreach service for merchant affiliate partnership automation.

Uses LLM (Gemini) to generate personalized outreach emails.
"""

import google.generativeai as genai
from app.core.config import get_settings
from app.core.logging import logger
from app.models.outreach_log import OutreachLog, OutreachStatus
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional
import uuid
from datetime import datetime

settings = get_settings()


def generate_outreach_email(
    merchant_name: str,
    merchant_url: str,
    user_profile: Dict[str, Any],
    temperature: float = 0.7
) -> Dict[str, Any]:
    """
    Generate personalized affiliate outreach email using Gemini.
    
    Args:
        merchant_name: Target merchant name
        merchant_url: Merchant website
        user_profile: Sender profile (name, website, niche, etc.)
        temperature: LLM temperature (0.7 for creative writing)
        
    Returns:
        {
            "subject": str,
            "body": str,
            "personalization_score": float
        }
    """
    logger.info(f"Generating outreach email for: {merchant_name}")
    
    if not hasattr(genai, 'configure'):
        logger.warning("Gemini not configured")
        return {
            "subject": f"Partnership Opportunity: {merchant_name}",
            "body": f"Dear {merchant_name} team,\n\nI would like to discuss a potential affiliate partnership...",
            "personalization_score": 0.0
        }
    
    prompt = f"""
Write a professional affiliate partnership outreach email.

**Merchant:** {merchant_name}
**Merchant Website:** {merchant_url}

**Sender Profile:**
- Name: {user_profile.get('name', 'Unknown')}
- Website: {user_profile.get('website', '')}
- Niche: {user_profile.get('niche', 'General Marketing')}
- Audience: {user_profile.get('audience_size', 'established audience')}

**Requirements:**
- Professional and friendly tone
- 3-4 paragraphs maximum
- Personalized to the merchant (mention their brand/products)
- Highlight mutual benefits
- Clear call-to-action
- Include sender's credentials
- NO generic templates or fluff
- NO fake statistics

**Structure:**
1. Brief introduction
2. Why you're interested in their program (specific)
3. What you can offer (audience, reach, content quality)
4. Next steps / CTA

Output the email in this JSON format:
{{
  "subject": "compelling subject line (max 60 chars)",
  "body": "full email body as plain text",
  "personalization_score": 0.0-1.0
}}
"""
    
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(
            prompt,
            generation_config=genai.GenerationConfig(
                temperature=temperature,
                response_mime_type="application/json"
            )
        )
        
        import json
        result = json.loads(response.text)
        
        logger.info(f"Generated outreach email: personalization={result.get('personalization_score', 0)}")
        return result
        
    except Exception as e:
        logger.error(f"Failed to generate outreach email: {e}")
        return {
            "subject": f"Affiliate Partnership Inquiry - {merchant_name}",
            "body": f"Dear {merchant_name} Team,\n\nI hope this message finds you well...",
            "personalization_score": 0.0
        }


def log_outreach_attempt(
    db: Session,
    tenant_id: uuid.UUID,
    merchant_name: str,
    merchant_url: str,
    merchant_email: Optional[str],
    generated_email: str,
    email_subject: str,
    sent_via: str = "email",
    metadata: Optional[Dict[str, Any]] = None
) -> OutreachLog:
    """
    Log an outreach attempt to the database.
    
    Args:
        db: Database session
        tenant_id: Tenant UUID
        merchant_name: Merchant name
        merchant_url: Merchant website
        merchant_email: Merchant contact email (if available)
        generated_email: Full email body
        email_subject: Email subject line
        sent_via: Delivery method (email, contact_form, etc.)
        metadata: Additional context
        
    Returns:
        Created OutreachLog instance
    """
    log = OutreachLog(
        tenant_id=tenant_id,
        merchant_name=merchant_name,
        merchant_url=merchant_url,
        merchant_email=merchant_email,
        generated_email=generated_email,
        email_subject=email_subject,
        sent_via=sent_via,
        metadata=metadata or {}
    )
    
    db.add(log)
    db.commit()
    db.refresh(log)
    
    logger.info(f"Logged outreach attempt: {log.id} for {merchant_name}")
    return log


def update_outreach_response(
    db: Session,
    outreach_id: uuid.UUID,
    status: OutreachStatus,
    response_text: Optional[str] = None
) -> Optional[OutreachLog]:
    """
    Update an outreach log with response information.
    
    Args:
        db: Database session
        outreach_id: Outreach log UUID
        status: Response status
        response_text: Optional response content
        
    Returns:
        Updated OutreachLog or None if not found
    """
    log = db.query(OutreachLog).filter(OutreachLog.id == outreach_id).first()
    
    if not log:
        logger.warning(f"Outreach log not found: {outreach_id}")
        return None
    
    log.response_status = status
    log.response_text = response_text
    log.response_received_at = datetime.utcnow()
    
    db.commit()
    db.refresh(log)
    
    logger.info(f"Updated outreach {outreach_id}: status={status}")
    return log
