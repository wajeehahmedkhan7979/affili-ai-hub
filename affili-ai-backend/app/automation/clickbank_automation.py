"""
ClickBank affiliate program automation.

Hardcoded automation for ClickBank signup process.
"""

import asyncio
import os
from datetime import datetime
from typing import Dict, Any, Optional, Tuple

from playwright.async_api import async_playwright, Page, Browser, BrowserContext

from app.core.time import utcnow
from app.automation.base_automation import BaseAffiliateAutomation


class ClickBankAutomation(BaseAffiliateAutomation):
    """Hardcoded ClickBank affiliate signup automation."""
    
    PROGRAM_NAME = "ClickBank"
    SIGNUP_URL = "https://accounts.clickbank.com/signup"
    
    # Form selectors (hardcoded for ClickBank)
    EMAIL_INPUT = "input[name='email'], input#email"
    PASSWORD_INPUT = "input[name='password'], input#password"
    NAME_INPUT = "input[name='firstName'], input#firstName"
    WEBSITE_INPUT = "input[name='website'], input#websiteUrl"
    CATEGORY_SELECT = "select[name='category'], select#category"
    SUBMIT_BUTTON = "button[type='submit'], input[type='submit']"
    
    async def run(
        self,
        email: str,
        name: str,
        website: str,
        category: str = "Technology",
        headless: bool = False,
        screenshot_dir: Optional[str] = None,
        **kwargs
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Execute ClickBank signup automation.
        
        Args:
            email: Affiliate email address
            name: Full name
            website: Business website URL
            category: Business category (default: Technology)
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
                    f"clickbank_before_{utcnow().timestamp()}.png",
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
                
                # Select category if dropdown exists
                try:
                    logs.append(f"[{self._now()}] Selecting category: {category}")
                    await page.select_option(self.CATEGORY_SELECT, category, timeout=5000)
                except:
                    logs.append(f"[{self._now()}] Category field not found, skipping")
                
                # Wait for form ready
                await page.wait_for_timeout(500)
                logs.append(f"[{self._now()}] Form fields filled")
                
                # Take screenshot before submit
                screenshot_filled = os.path.join(
                    screenshot_dir,
                    f"clickbank_filled_{utcnow().timestamp()}.png",
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
                        page.wait_for_url("**/dashboard**", timeout=10000),
                        timeout=15
                    )
                    logs.append(f"[{self._now()}] ✅ Dashboard detected")
                    success = True
                except asyncio.TimeoutError:
                    # Check for success text
                    logs.append(f"[{self._now()}] No URL change, checking for success message")
                    try:
                        success_indicators = [
                            ":has-text('confirmation') >> nth=0",
                            ":has-text('check your email') >> nth=0",
                            ":has-text('account created') >> nth=0"
                        ]
                        found = False
                        for selector in success_indicators:
                            element = await page.query_selector(selector)
                            if element:
                                logs.append(f"[{self._now()}] ✅ Found success indicator")
                                found = True
                                break
                        success = found
                        if not found:
                            logs.append(f"[{self._now()}] ❌ No success indicator")
                    except:
                        success = False
                
                # Take post-submit screenshot
                screenshot_after = os.path.join(
                    screenshot_dir,
                    f"clickbank_after_{utcnow().timestamp()}.png",
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
                    "category": category,
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