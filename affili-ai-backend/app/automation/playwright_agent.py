"""
Real Playwright-based affiliate application automation.

This module contains HARDCODED automations for specific affiliate programs.
Phase 1: Single implementation for Stripe Connect signup (proof of concept).

No abstraction, no plugins, no vision.
"""

import asyncio
import os
from datetime import datetime
from typing import Dict, Any, Optional, Tuple

from playwright.async_api import async_playwright, Page, Browser, BrowserContext


class StripeConnectAutomation:
    """Hardcoded Stripe Connect affiliate signup automation."""
    
    SIGNUP_URL = "https://stripe.com/connect/partners"
    
    # Form selectors (hardcoded for THIS program)
    EMAIL_INPUT = "input[name='email']"
    NAME_INPUT = "input[name='first_name']"  # Adjust if needed
    WEBSITE_INPUT = "input[name='website']"  # Adjust if needed
    SUBMIT_BUTTON = "button[type='submit']"
    
    async def run(
        self,
        email: str,
        name: str,
        website: str,
        traffic_source: str = "Direct",
        headless: bool = False,
        screenshot_dir: Optional[str] = None,
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Execute Stripe Connect signup automation.
        
        Args:
            email: Affiliate email address
            name: Full name
            website: Business website URL
            traffic_source: Traffic source (not used in form, metadata only)
            headless: Run browser headless (True for production)
            
        Returns:
            Tuple of (success: bool, metadata: dict)
            metadata includes:
            - screenshots: {before, after} paths
            - logs: execution log
            - error: error message if failed
        """
        logs: list[str] = []
        screenshots: Dict[str, Any] = {}
        browser: Optional[Browser] = None
        context: Optional[BrowserContext] = None
        page: Optional[Page] = None
        
        try:
            # Prepare screenshot directory
            if screenshot_dir is None:
                screenshot_dir = os.path.join("storage", "screenshots", "stripe_connect")
            os.makedirs(screenshot_dir, exist_ok=True)

            async with async_playwright() as p:
                logs.append(f"[{self._now()}] Launching Chromium browser (headless={headless})")
                browser = await p.chromium.launch(headless=headless)
                context = await browser.new_context()
                page = await context.new_page()
                
                # Set viewport to standard desktop
                await page.set_viewport_size({"width": 1280, "height": 720})
                logs.append(f"[{self._now()}] Viewport set to 1280x720")
                
                # Navigate to signup page
                logs.append(f"[{self._now()}] Navigating to {self.SIGNUP_URL}")
                await page.goto(
                    self.SIGNUP_URL,
                    wait_until="networkidle",
                    timeout=30000,
                )
                logs.append(f"[{self._now()}] Page loaded")
                
                # Take pre-fill screenshot
                screenshot_before = os.path.join(
                    screenshot_dir,
                    f"stripe_before_{datetime.utcnow().timestamp()}.png",
                )
                await page.screenshot(path=screenshot_before, full_page=True)
                screenshots["before"] = screenshot_before
                logs.append(f"[{self._now()}] Pre-fill screenshot saved: {screenshot_before}")
                
                # Fill form fields
                logs.append(f"[{self._now()}] Filling email field: {email}")
                await page.fill(self.EMAIL_INPUT, email, timeout=10000)
                
                logs.append(f"[{self._now()}] Filling name field: {name}")
                await page.fill(self.NAME_INPUT, name, timeout=10000)
                
                logs.append(f"[{self._now()}] Filling website field: {website}")
                await page.fill(self.WEBSITE_INPUT, website, timeout=10000)
                
                # Wait for form to be ready
                await page.wait_for_timeout(500)
                logs.append(f"[{self._now()}] Form fields filled, waiting 500ms")
                
                # Take screenshot before submit
                screenshot_filled = os.path.join(
                    screenshot_dir,
                    f"stripe_filled_{datetime.utcnow().timestamp()}.png",
                )
                await page.screenshot(path=screenshot_filled, full_page=True)
                logs.append(f"[{self._now()}] Post-fill screenshot saved: {screenshot_filled}")
                
                # Submit form
                logs.append(f"[{self._now()}] Clicking submit button")
                await page.click(self.SUBMIT_BUTTON, timeout=10000)
                
                # Wait for navigation or success indicator
                logs.append(f"[{self._now()}] Waiting for post-submit response (up to 10s)")
                try:
                    await asyncio.wait_for(
                        page.wait_for_url("**/confirm**", timeout=10000),
                        timeout=15
                    )
                    logs.append(f"[{self._now()}] ✅ URL changed to confirmation page")
                    success = True
                except asyncio.TimeoutError:
                    # Check for success message in DOM
                    logs.append(f"[{self._now()}] No URL change, checking for success message...")
                    try:
                        success_text = await page.query_selector(":has-text('Thank you') >> nth=0")
                        if success_text:
                            logs.append(f"[{self._now()}] ✅ Found success message in DOM")
                            success = True
                        else:
                            logs.append(f"[{self._now()}] ❌ No success indicator found")
                            success = False
                    except:
                        success = False
                
                # Take post-submit screenshot
                screenshot_after = os.path.join(
                    screenshot_dir,
                    f"stripe_after_{datetime.utcnow().timestamp()}.png",
                )
                await page.screenshot(path=screenshot_after, full_page=True)
                screenshots["after"] = screenshot_after
                logs.append(f"[{self._now()}] Post-submit screenshot saved: {screenshot_after}")
                
                # Return result
                metadata = {
                    "success": success,
                    "screenshots": screenshots,
                    "logs": "\n".join(logs),
                    "email": email,
                    "name": name,
                    "website": website,
                    "submitted_at": self._now(),
                }
                
                if success:
                    logs.append(f"[{self._now()}] ✅ AUTOMATION COMPLETED SUCCESSFULLY")
                else:
                    logs.append(f"[{self._now()}] ❌ AUTOMATION FAILED - No success indicator")
                    metadata["error"] = "Form submission failed or success not detected"
                
                return success, metadata
                
        except Exception as e:
            logs.append(f"[{self._now()}] ❌ EXCEPTION: {str(e)}")
            return False, {
                "success": False,
                "screenshots": screenshots,
                "logs": "\n".join(logs),
                "error": str(e),
            }
        finally:
            if page:
                await page.close()
            if context:
                await context.close()
            if browser:
                await browser.close()
    
    def _now(self) -> str:
        """Return current ISO timestamp."""
        return datetime.utcnow().isoformat()


async def run_apply_program_automation(
    task_payload: Dict[str, Any],
    task_id: str,
) -> Tuple[bool, Dict[str, Any]]:
    """
    Execute affiliate application automation based on program type.
    
    Task payload must contain:
    {
        "program_name": "Stripe Connect",
        "email": "affiliate@example.com",
        "name": "John Doe",
        "website": "https://example.com",
    }
    """
    program_name = task_payload.get("program_name", "").strip()
    email = task_payload.get("email", "").strip()
    name = task_payload.get("name", "").strip()
    website = task_payload.get("website", "").strip()
    
    if not all([program_name, email, name, website]):
        return False, {"error": "Missing required fields: program_name, email, name, website"}
    
    # Determine debug mode from environment
    debug_flag = os.getenv("PLAYWRIGHT_DEBUG", "0").lower()
    debug_mode = debug_flag in ("1", "true", "yes")
    headless = not debug_mode

    # Store screenshots under storage/screenshots/{task_id}/
    screenshot_dir = os.path.join("storage", "screenshots", str(task_id))

    # Phase 1: Stripe Connect only
    if program_name.lower() == "stripe connect":
        automation = StripeConnectAutomation()
        return await automation.run(
            email=email,
            name=name,
            website=website,
            headless=headless,
            screenshot_dir=screenshot_dir,
        )
    else:
        return False, {"error": f"No automation implemented for: {program_name}"}
