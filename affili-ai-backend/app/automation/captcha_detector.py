"""
Enhanced CAPTCHA Detection - Detect CAPTCHAs before and during form filling.

CRITICAL: This service ONLY detects CAPTCHAs. It does NOT solve them.
Tasks are paused for human intervention.
"""

from playwright.async_api import Page
from app.core.logging import logger
from typing import Dict, Any, Optional
import asyncio


class CaptchaDetector:
    """
    Detect various CAPTCHA types without solving them.
    """
    
    # Known CAPTCHA selectors
    CAPTCHA_SELECTORS = [
        "iframe[src*='recaptcha']",
        "iframe[src*='hcaptcha']",
        "iframe[src*='captcha']",
        ".g-recaptcha",
        ".h-captcha",
        "#captcha",
        "[class*='captcha']",
        "[id*='captcha']",
        "img[alt*='captcha' i]",
        "img[src*='captcha']"
    ]
    
    # Text patterns indicating CAPTCHA
    CAPTCHA_TEXT_PATTERNS = [
        "verify you're human",
        "prove you are human",
        "security check",
        "i'm not a robot",
        "verify you are not a robot",
        "complete the captcha"
    ]
    
    async def detect_captcha(
        self,
        page: Page,
        screenshot_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Comprehensive CAPTCHA detection.
        
        Args:
            page: Playwright page
            screenshot_path: Optional path to save screenshot if CAPTCHA found
            
        Returns:
            {
                "detected": bool,
                "type": str | None,  # "recaptcha", "hcaptcha", "image", "unknown"
                "selector": str | None,
                "screenshot_url": str | None,
                "dom_snippet": str | None
            }
        """
        logger.info("Running CAPTCHA detection...")
        
        # Method 1: Check for known CAPTCHA iframes/elements
        for selector in self.CAPTCHA_SELECTORS:
            try:
                element = page.locator(selector).first
                count = await element.count()
                
                if count > 0:
                    logger.warning(f"CAPTCHA detected via selector: {selector}")
                    
                    # Capture screenshot
                    screenshot_url = None
                    if screenshot_path:
                        await page.screenshot(path=screenshot_path, full_page=True)
                        screenshot_url = screenshot_path
                    
                    # Extract DOM snippet
                    dom_snippet = await self._extract_dom_snippet(page, selector)
                    
                    # Classify CAPTCHA type
                    captcha_type = self._classify_captcha_type(selector)
                    
                    return {
                        "detected": True,
                        "type": captcha_type,
                        "selector": selector,
                        "screenshot_url": screenshot_url,
                        "dom_snippet": dom_snippet,
                        "url": page.url
                    }
            except Exception as e:
                logger.debug(f"Selector check failed for {selector}: {e}")
                continue
        
        # Method 2: Check page text for CAPTCHA keywords
        try:
            page_text = await page.text_content("body")
            page_text_lower = page_text.lower() if page_text else ""
            
            for pattern in self.CAPTCHA_TEXT_PATTERNS:
                if pattern in page_text_lower:
                    logger.warning(f"CAPTCHA detected via text pattern: '{pattern}'")
                    
                    screenshot_url = None
                    if screenshot_path:
                        await page.screenshot(path=screenshot_path, full_page=True)
                        screenshot_url = screenshot_path
                    
                    return {
                        "detected": True,
                        "type": "text_based",
                        "selector": None,
                        "screenshot_url": screenshot_url,
                        "dom_snippet": f"Text contains: '{pattern}'",
                        "url": page.url
                    }
        except Exception as e:
            logger.error(f"Text-based CAPTCHA detection failed: {e}")
        
        # Method 3: Check for Cloudflare challenge
        try:
            title = await page.title()
            if "just a moment" in title.lower() or "challenge" in title.lower():
                logger.warning("Cloudflare challenge detected")
                
                screenshot_url = None
                if screenshot_path:
                    await page.screenshot(path=screenshot_path, full_page=True)
                    screenshot_url = screenshot_path
                
                return {
                    "detected": True,
                    "type": "cloudflare",
                    "selector": None,
                    "screenshot_url": screenshot_url,
                    "dom_snippet": f"Page title: {title}",
                    "url": page.url
                }
        except Exception as e:
            logger.debug(f"Cloudflare check failed: {e}")
        
        # No CAPTCHA detected
        logger.info("No CAPTCHA detected")
        return {
            "detected": False,
            "type": None,
            "selector": None,
            "screenshot_url": None,
            "dom_snippet": None,
            "url": page.url
        }
    
    async def detect_captcha_mid_flow(
        self,
        page: Page,
        screenshot_dir: str
    ) -> Dict[str, Any]:
        """
        Detect if a CAPTCHA appeared during form filling.
        
        Should be called periodically during automation.
        
        Args:
            page: Playwright page
            screenshot_dir: Directory to save screenshots
            
        Returns:
            Same format as detect_captcha()
        """
        import os
        import time
        
        screenshot_path = os.path.join(
            screenshot_dir,
            f"captcha_mid_flow_{int(time.time())}.png"
        )
        
        return await self.detect_captcha(page, screenshot_path)
    
    def _classify_captcha_type(self, selector: str) -> str:
        """Classify CAPTCHA type based on selector."""
        selector_lower = selector.lower()
        
        if "recaptcha" in selector_lower:
            return "recaptcha"
        elif "hcaptcha" in selector_lower:
            return "hcaptcha"
        elif "cloudflare" in selector_lower:
            return "cloudflare"
        elif "img" in selector_lower:
            return "image_captcha"
        else:
            return "unknown"
    
    async def _extract_dom_snippet(
        self,
        page: Page,
        selector: str,
        max_length: int = 500
    ) -> str:
        """Extract HTML snippet around CAPTCHA element."""
        try:
            html = await page.locator(selector).first.evaluate("el => el.outerHTML")
            
            if len(html) > max_length:
                html = html[:max_length] + "..."
            
            return html
        except Exception as e:
            logger.debug(f"Failed to extract DOM snippet: {e}")
            return f"<selector: {selector}>"


async def pause_task_for_captcha(
    task_id: str,
    captcha_info: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Pause a task when CAPTCHA is detected.
    
    This is a helper to update task status and emit events.
    
    Args:
        task_id: Task UUID
        captcha_info: CAPTCHA detection result
        
    Returns:
        {
            "status": "PAUSED_FOR_CAPTCHA",
            "captcha_type": str,
            "screenshot_url": str,
            "next_action": "HUMAN_INTERVENTION_REQUIRED"
        }
    """
    logger.warning(f"Task {task_id} paused for CAPTCHA: {captcha_info['type']}")
    
    # Update task status (would be called by task service)
    # Note: This is a placeholder - actual implementation would update DB
    
    return {
        "status": "PAUSED_FOR_CAPTCHA",
        "captcha_type": captcha_info.get("type"),
        "screenshot_url": captcha_info.get("screenshot_url"),
        "url": captcha_info.get("url"),
        "dom_snippet": captcha_info.get("dom_snippet"),
        "next_action": "HUMAN_INTERVENTION_REQUIRED",
        "task_id": task_id
    }


# Backwards-compatibility shim for legacy tests/imports
# Older code imported `detect_captcha` as a module-level function.
# We preserve that API by delegating to `CaptchaDetector.detect_captcha`.
async def detect_captcha(
    page: Page,
    screenshot_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Backwards-compatible helper to detect CAPTCHA on a page.

    This wraps `CaptchaDetector.detect_captcha` so existing tests and
    call sites that import `detect_captcha` continue to work.
    """
    detector = CaptchaDetector()
    return await detector.detect_captcha(page, screenshot_path)