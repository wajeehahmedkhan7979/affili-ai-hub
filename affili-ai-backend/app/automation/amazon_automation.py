"""
Amazon Associates affiliate program automation.

Hardcoded automation for Amazon Associates signup process.
"""

import asyncio
import os
from datetime import datetime
from typing import Dict, Any, Optional, Tuple

from playwright.async_api import async_playwright, Page, Browser, BrowserContext

from app.automation.base_automation import BaseAffiliateAutomation


class AmazonAssociatesAutomation(BaseAffiliateAutomation):
    """Hardcoded Amazon Associates affiliate signup automation."""
    
    PROGRAM_NAME = "Amazon Associates"
    SIGNUP_URL = "https://affiliate-program.amazon.com/signup"
    
    # Form selectors (hardcoded for Amazon Associates)
    EMAIL_INPUT = "input[name='email']"
    PASSWORD_INPUT = "input[name='password']"
    NAME_INPUT = "input[name='name']"
    WEBSITE_INPUT = "input[name='websiteUrl']"
    SUBMIT_BUTTON = "input[type='submit'], button[type='submit']"
    
    async def run(
        self,
        email: str,
        name: str,
        website: str,
        headless: bool = False,
        screenshot_dir: Optional[str] = None,
        **kwargs
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Execute Amazon Associates signup automation.
        
        Args:
            email: Affiliate email address
            name: Full name
            website: Business website URL
            headless: Run browser headless (True for production)
            screenshot_dir: Directory to save screenshots
            
        Returns:
            Tuple of (success: bool, metadata: dict)
        """
        logs: list[str] = []
        screenshots: Dict[str, Any] = {}
        browser: Optional[Browser] = None
        context: Optional[BrowserContext] = None
        page: Optional[Page] = None
        
        try:
            # Prepare screenshot directory
            screenshot_dir = self._prepare_screenshot_dir(screenshot_dir)

            async with async_playwright() as p:
                logs.append(f"[{self._now()}] Launching Chromium browser (headless={headless})")
                browser = await p.chromium.launch(headless=headless)
                context = await browser.new_context()
                page = await context.new_page()
                
                # Set viewport
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
                    f"amazon_before_{datetime.utcnow().timestamp()}.png",
                )
                await page.screenshot(path=screenshot_before, full_page=True)
                screenshots["before"] = screenshot_before
                logs.append(f"[{self._now()}] Pre-fill screenshot saved")
                
                # Fill form fields
                logs.append(f"[{self._now()}] Filling email field: {email}")
                await page.fill(self.EMAIL_INPUT, email, timeout=10000)
                
                logs.append(f"[{self._now()}] Filling name field: {name}")
                await page.fill(self.NAME_INPUT, name, timeout=10000)
                
                logs.append(f"[{self._now()}] Filling website field: {website}")
                await page.fill(self.WEBSITE_INPUT, website, timeout=10000)
                
                # Wait for form ready
                await page.wait_for_timeout(500)
                logs.append(f"[{self._now()}] Form fields filled")
                
                # Take screenshot before submit
                screenshot_filled = os.path.join(
                    screenshot_dir,
                    f"amazon_filled_{datetime.utcnow().timestamp()}.png",
                )
                await page.screenshot(path=screenshot_filled, full_page=True)
                logs.append(f"[{self._now()}] Post-fill screenshot saved")
                
                # Submit form
                logs.append(f"[{self._now()}] Clicking submit button")
                await page.click(self.SUBMIT_BUTTON, timeout=10000)
                
                # Wait for response
                logs.append(f"[{self._now()}] Waiting for response")
                try:
                    await asyncio.wait_for(
                        page.wait_for_url("**/success**", timeout=10000),
                        timeout=15
                    )
                    logs.append(f"[{self._now()}] ✅ Success page detected")
                    success = True
                except asyncio.TimeoutError:
                    # Check for success text
                    logs.append(f"[{self._now()}] No URL change, checking for success message")
                    try:
                        success_text = await page.query_selector(":has-text('Thank you') >> nth=0")
                        if success_text:
                            logs.append(f"[{self._now()}] ✅ Found success message")
                            success = True
                        else:
                            logs.append(f"[{self._now()}] ❌ No success indicator")
                            success = False
                    except:
                        success = False
                
                # Take post-submit screenshot
                screenshot_after = os.path.join(
                    screenshot_dir,
                    f"amazon_after_{datetime.utcnow().timestamp()}.png",
                )
                await page.screenshot(path=screenshot_after, full_page=True)
                screenshots["after"] = screenshot_after
                logs.append(f"[{self._now()}] Post-submit screenshot saved")
                
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
                    logs.append(f"[{self._now()}] ❌ AUTOMATION FAILED")
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
