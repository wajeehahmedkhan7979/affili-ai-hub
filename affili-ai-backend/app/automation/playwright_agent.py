"""
Universal Playwright-based affiliate application automation.

This module provides a unified automation entry point that uses 
IntelligentFormFiller (RAG + LLM) to handle any affiliate program
without hardcoded selectors.
"""

import asyncio
import os
from datetime import datetime
from typing import Dict, Any, Optional, Tuple
import uuid

from playwright.async_api import async_playwright, Page, Browser, BrowserContext

from app.automation.base_automation import BaseAffiliateAutomation
from app.automation.intelligent_form_filler import fill_form_with_predictions
from app.db.session import SessionLocal
from app.core.logging import logger


class UniversalAffiliateAutomation(BaseAffiliateAutomation):
    """
    Universal affiliate signup automation using RAG-based intelligence.
    
    Replaces hardcoded program-specific classes.
    """
    
    def __init__(self, program_name: str, signup_url: str):
        self._program_name = program_name
        self._signup_url = signup_url
        
    @property
    def PROGRAM_NAME(self) -> str:
        return self._program_name
    
    @property
    def SIGNUP_URL(self) -> str:
        return self._signup_url
    
    async def run(
        self,
        tenant_id: uuid.UUID,
        user_profile: Dict[str, Any],
        program_id: Optional[uuid.UUID] = None,
        task_id: Optional[uuid.UUID] = None,
        headless: bool = True,
        screenshot_dir: Optional[str] = None,
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Execute universal automation using IntelligentFormFiller.
        """
        logs: list[str] = []
        screenshots: Dict[str, Any] = {}
        browser: Optional[Browser] = None
        context: Optional[BrowserContext] = None
        page: Optional[Page] = None
        
        # Load db session
        db = SessionLocal()
        
        try:
            # Prepare screenshot directory
            screenshot_dir = self._prepare_screenshot_dir(screenshot_dir, str(task_id) if task_id else None)

            async with async_playwright() as p:
                logs.append(f"[{self._now()}] Launching browser (headless={headless})")
                
                # Configure proxy if available
                proxy_url = os.getenv("PROXY_URL")
                launch_options = {"headless": headless}
                if proxy_url:
                    launch_options["proxy"] = {"server": proxy_url}
                    logs.append(f"[{self._now()}] Using proxy configuration")
                
                browser = await p.chromium.launch(**launch_options)
                context = await browser.new_context()
                page = await context.new_page()
                
                # Set viewport
                await page.set_viewport_size({"width": 1280, "height": 720})
                
                # Navigate to signup page
                logs.append(f"[{self._now()}] Navigating to {self.SIGNUP_URL}")
                await page.goto(self.SIGNUP_URL, wait_until="networkidle", timeout=60000)
                logs.append(f"[{self._now()}] Page loaded")
                
                # Check for CAPTCHA
                captcha_check = await self._check_for_captcha(page)
                if captcha_check["detected"]:
                    logs.append(f"[{self._now()}] PAUSED: CAPTCHA detected - {captcha_check['reason']}")
                    screenshot_captcha = os.path.join(screenshot_dir, "captcha.png")
                    await page.screenshot(path=screenshot_captcha, full_page=True)
                    return (False, {
                        "error": "CAPTCHA_DETECTED",
                        "logs": "\n".join(logs),
                        "screenshots": {"captcha": screenshot_captcha},
                        "captcha_url": captcha_check["url"],
                        "captcha_reason": captcha_check["reason"],
                    })
                
                # Take pre-fill screenshot
                screenshot_before = os.path.join(screenshot_dir, "before.png")
                await page.screenshot(path=screenshot_before, full_page=True)
                screenshots["before"] = screenshot_before
                
                # Run Intelligent Form Filler
                logs.append(f"[{self._now()}] Starting Intelligent Form Filler (RAG + LLM)")
                fill_result = await fill_form_with_predictions(
                    page=page,
                    db=db,
                    tenant_id=tenant_id,
                    user_profile=user_profile,
                    program_id=program_id,
                    confidence_threshold=0.6  # Approved threshold
                )
                
                logs.append(f"[{self._now()}] Form fill complete: {fill_result['filled']}/{fill_result['total_fields']} fields")
                
                # Check if we have enough confidence to proceed
                if fill_result['filled'] == 0 and fill_result['total_fields'] > 0:
                    logs.append(f"[{self._now()}] PAUSED: Zero fields filled with high confidence")
                    screenshot_low_conf = os.path.join(screenshot_dir, "low_confidence.png")
                    await page.screenshot(path=screenshot_low_conf, full_page=True)
                    return (False, {
                        "error": "PAUSED_LOW_CONFIDENCE",
                        "logs": "\n".join(logs),
                        "screenshots": {"paused": screenshot_low_conf},
                        "fill_stats": fill_result['stats']
                    })

                # Take post-fill screenshot
                screenshot_filled = os.path.join(screenshot_dir, "filled.png")
                await page.screenshot(path=screenshot_filled, full_page=True)
                screenshots["filled"] = screenshot_filled
                
                # User Review/Submit Logic
                # In this universal mode, we try to detect the submit button automatically
                logs.append(f"[{self._now()}] Attempting to identify and click submit button")
                
                # Try to find submit button by type or text
                selectors = [
                    "button[type='submit']", 
                    "input[type='submit']",
                    "button:has-text('Apply')",
                    "button:has-text('Join')",
                    "button:has-text('Submit')",
                    "button:has-text('Sign up')"
                ]
                
                submit_button = None
                for selector in selectors:
                    try:
                        el = await page.query_selector(selector)
                        if el and await el.is_visible():
                            submit_button = selector
                            break
                    except:
                        continue
                
                if submit_button:
                    logs.append(f"[{self._now()}] Found submit button: {submit_button}")
                    await page.click(submit_button)
                    await page.wait_for_timeout(5000) # Wait for processing
                else:
                    logs.append(f"[{self._now()}] ⚠️ Could not identify submit button automatically")
                
                # Final screenshot
                screenshot_after = os.path.join(screenshot_dir, "after.png")
                await page.screenshot(path=screenshot_after, full_page=True)
                screenshots["after"] = screenshot_after
                
                return True, {
                    "success": True,
                    "screenshots": screenshots,
                    "logs": "\n".join(logs),
                    "fill_stats": fill_result['stats'],
                    "submitted_at": self._now()
                }
                
        except Exception as e:
            logger.error(f"Universal automation failed: {e}")
            logs.append(f"[{self._now()}] ❌ EXCEPTION: {str(e)}")
            return False, {
                "success": False,
                "screenshots": screenshots,
                "logs": "\n".join(logs),
                "error": str(e),
            }
        finally:
            db.close()
            if page: await page.close()
            if context: await context.close()
            if browser: await browser.close()


async def run_apply_program_automation(
    task_payload: Dict[str, Any],
    task_id: str,
) -> Tuple[bool, Dict[str, Any]]:
    """
    Execute affiliate application automation using Universal Intelligent Agent.
    """
    program_name = task_payload.get("program_name", "Unknown Program")
    signup_url = task_payload.get("signup_url") or task_payload.get("website_url")
    
    # Fallback URLs for known names if not provided in payload
    if not signup_url:
        KNOWN_URLS = {
            "stripe connect": "https://stripe.com/connect/partners",
            "amazon associates": "https://affiliate-program.amazon.com/",
            "clickbank": "https://www.clickbank.com/affiliates/",
        }
        signup_url = KNOWN_URLS.get(program_name.lower())

    if not signup_url:
        return False, {"error": f"Missing signup_url for program: {program_name}"}

    tenant_id_str = task_payload.get("tenant_id")
    if not tenant_id_str:
        return False, {"error": "Missing tenant_id in task payload"}
    
    tenant_id = uuid.UUID(tenant_id_str)
    user_profile = task_payload.get("user_profile", {})
    program_id = task_payload.get("program_id")
    if program_id:
        program_id = uuid.UUID(program_id)

    # Determine execution mode
    debug_mode = os.getenv("PLAYWRIGHT_DEBUG", "0").lower() in ("1", "true")
    headless = not debug_mode

    # Run Universal Automation
    automation = UniversalAffiliateAutomation(program_name, signup_url)
    return await automation.run(
        tenant_id=tenant_id,
        user_profile=user_profile,
        program_id=program_id,
        task_id=uuid.UUID(task_id),
        headless=headless
    )
