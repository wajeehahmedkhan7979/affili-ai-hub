"""
CAPTCHA detection utility for Playwright pages.

Detects common CAPTCHA services without attempting to solve them.
"""

from typing import Dict, Any
from playwright.async_api import Page


async def detect_captcha(page: Page) -> Dict[str, Any]:
    """
    Detect if the current page contains a CAPTCHA challenge.
    
    Uses multiple heuristics:
    - iframe sources containing CAPTCHA keywords
    - Visible text indicating human verification
    - Specific CAPTCHA element selectors
    
    Args:
        page: Playwright Page object
        
    Returns:
        Dict containing:
        - detected (bool): True if CAPTCHA found
        - reason (str): Detection reason
        - url (str): Current page URL
    """
    url = page.url
    detected = False
    reason = ""
    
    # Heuristic 1: Check for CAPTCHA iframes
    captcha_iframe_keywords = [
        "captcha",
        "recaptcha",
        "hcaptcha",
        "cloudflare",
        "challenge",
    ]
    
    try:
        iframes = await page.query_selector_all("iframe")
        for iframe in iframes:
            src = await iframe.get_attribute("src")
            if src:
                src_lower = src.lower()
                for keyword in captcha_iframe_keywords:
                    if keyword in src_lower:
                        detected = True
                        reason = f"CAPTCHA iframe detected: {keyword} in {src[:100]}"
                        return {"detected": detected, "reason": reason, "url": url}
    except Exception as e:
        # Continue with other checks if iframe check fails
        pass
    
    # Heuristic 2: Check for CAPTCHA-specific elements
    captcha_selectors = [
        "#g-recaptcha",  # Google reCAPTCHA
        ".g-recaptcha",
        "[data-sitekey]",  # reCAPTCHA with sitekey
        ".h-captcha",  # hCaptcha
        "#h-captcha",
        ".cf-challenge-running",  # Cloudflare challenge
        "#challenge-form",  # Generic challenge form
    ]
    
    for selector in captcha_selectors:
        try:
            element = await page.query_selector(selector)
            if element and await element.is_visible():
                detected = True
                reason = f"CAPTCHA element detected: {selector}"
                return {"detected": detected, "reason": reason, "url": url}
        except:
            continue
    
    # Heuristic 3: Check page text for CAPTCHA phrases
    captcha_phrases = [
        "verify you are human",
        "verify you're human",
        "prove you're not a robot",
        "prove you are not a robot",
        "i'm not a robot",
        "please verify",
        "complete the captcha",
        "security check",
        "checking your browser",
    ]
    
    try:
        page_text = await page.inner_text("body")
        page_text_lower = page_text.lower()
        
        for phrase in captcha_phrases:
            if phrase in page_text_lower:
                detected = True
                reason = f"CAPTCHA text detected: '{phrase}'"
                return {"detected": detected, "reason": reason, "url": url}
    except:
        pass
    
    # No CAPTCHA detected
    return {"detected": False, "reason": "", "url": url}
