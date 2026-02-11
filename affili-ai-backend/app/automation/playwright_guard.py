"""
Playwright Guard - Intelligent stability wrapper for Playwright automation.

Provides:
- Selector retry envelope with exponential backoff
- DOM mutation observer for SPA async rendering
- Navigation watchdog for soft hangs
- Classified failure modes

Ensures reliable automation under real-world web variance.
"""

from playwright.async_api import Page, TimeoutError as PlaywrightTimeoutError
from app.core.logging import logger
from typing import Optional, Callable, Any, Dict
import asyncio
import time


class SelectorRetryEnvelope:
    """
    Retry selectors with exponential backoff and classified failures.
    
    Prevents brittle automation from failing on transient DOM issues.
    """
    
    def __init__(
        self,
        max_attempts: int = 3,
        base_delay: float = 1.0,
        timeout_per_attempt: float = 5.0
    ):
        self.max_attempts = max_attempts
        self.base_delay = base_delay
        self.timeout_per_attempt = timeout_per_attempt
    
    async def find_element(
        self,
        page: Page,
        selector: str,
        attempt_num: int = 1
    ) -> Optional[Any]:
        """
        Retry finding an element with exponential backoff.
        
        Args:
            page: Playwright page
            selector: CSS selector
            attempt_num: Current attempt number
            
        Returns:
            Element locator or None if failed after all retries
        """
        try:
            element = page.locator(selector)
            await element.wait_for(
                state="visible",
                timeout=self.timeout_per_attempt * 1000
            )
            logger.debug(f"Found element '{selector}' on attempt {attempt_num}")
            return element
        except PlaywrightTimeoutError:
            if attempt_num >= self.max_attempts:
                logger.warning(f"Element '{selector}' not found after {self.max_attempts} attempts")
                return None
            
            # Exponential backoff
            delay = self.base_delay * (2 ** (attempt_num - 1))
            logger.info(f"Retry {attempt_num}/{self.max_attempts} for '{selector}' after {delay}s")
            await asyncio.sleep(delay)
            
            return await self.find_element(page, selector, attempt_num + 1)
    
    async def fill_with_retry(
        self,
        page: Page,
        selector: str,
        value: str
    ) -> Dict[str, Any]:
        """
        Fill a field with retry logic.
        
        Returns:
            {
                "success": bool,
                "attempts": int,
                "failure_reason": str | None
            }
        """
        for attempt in range(1, self.max_attempts + 1):
            try:
                element = await self.find_element(page, selector, attempt)
                
                if not element:
                    return {
                        "success": False,
                        "attempts": attempt,
                        "failure_reason": "SELECTOR_NOT_FOUND"
                    }
                
                await element.fill(value)
                logger.info(f"Successfully filled '{selector}' on attempt {attempt}")
                
                return {
                    "success": True,
                    "attempts": attempt,
                    "failure_reason": None
                }
            except Exception as e:
                logger.error(f"Fill attempt {attempt} failed for '{selector}': {e}")
                
                if attempt >= self.max_attempts:
                    return {
                        "success": False,
                        "attempts": attempt,
                        "failure_reason": f"FILL_ERROR: {type(e).__name__}"
                    }
                
                await asyncio.sleep(self.base_delay * (2 ** (attempt - 1)))
        
        return {
            "success": False,
            "attempts": self.max_attempts,
            "failure_reason": "MAX_RETRIES_EXCEEDED"
        }


class NavigationWatchdog:
    """
    Detect soft hangs (no DOM changes for extended period).
    
    Prevents infinite waits on broken SPAs.
    """
    
    def __init__(self, timeout_seconds: float = 30.0):
        self.timeout_seconds = timeout_seconds
        self.last_mutation_time = None
    
    async def watch_navigation(
        self,
        page: Page,
        expected_url_pattern: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Watch for navigation completion or soft hang.
        
        Args:
            page: Playwright page
            expected_url_pattern: Optional regex pattern for expected URL
            
        Returns:
            {
                "success": bool,
                "failure_type": str | None,
                "final_url": str
            }
        """
        start_time = time.time()
        self.last_mutation_time = start_time
        
        # Install mutation observer
        await page.evaluate("""
            (timeoutMs) => {
                window._navigationWatchdog = {
                    lastMutationTime: Date.now()
                };
                
                const observer = new MutationObserver(() => {
                    window._navigationWatchdog.lastMutationTime = Date.now();
                });
                
                observer.observe(document.body, {
                    childList: true,
                    subtree: true,
                    attributes: true
                });
            }
        """, self.timeout_seconds * 1000)
        
        # Poll for mutations or timeout
        while True:
            elapsed = time.time() - start_time
            
            if elapsed > self.timeout_seconds:
                logger.warning("Navigation watchdog timeout - soft hang detected")
                return {
                    "success": False,
                    "failure_type": "TIMEOUT_SOFT",
                    "final_url": page.url
                }
            
            # Check for DOM mutations
            try:
                last_mutation_ms = await page.evaluate(
                    "window._navigationWatchdog ? window._navigationWatchdog.lastMutationTime : Date.now()"
                )
                
                time_since_mutation = time.time() - (last_mutation_ms / 1000)
                
                # If no mutations for 5 seconds, consider stable
                if time_since_mutation > 5.0:
                    logger.info("Navigation complete - DOM stable")
                    
                    # Check URL pattern if provided
                    if expected_url_pattern:
                        import re
                        if not re.search(expected_url_pattern, page.url):
                            return {
                                "success": False,
                                "failure_type": "URL_MISMATCH",
                                "final_url": page.url
                            }
                    
                    return {
                        "success": True,
                        "failure_type": None,
                        "final_url": page.url
                    }
                
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.error(f"Watchdog error: {e}")
                return {
                    "success": False,
                    "failure_type": f"WATCHDOG_ERROR: {type(e).__name__}",
                    "final_url": page.url
                }


class PlaywrightGuard:
    """
    Main guard wrapper combining all stability features.
    """
    
    def __init__(self):
        self.selector_retry = SelectorRetryEnvelope()
        self.nav_watchdog = NavigationWatchdog()
    
    async def safe_fill(
        self,
        page: Page,
        selector: str,
        value: str
    ) -> Dict[str, Any]:
        """Fill field with full retry logic."""
        return await self.selector_retry.fill_with_retry(page, selector, value)
    
    async def safe_click(
        self,
        page: Page,
        selector: str
    ) -> Dict[str, Any]:
        """Click element with retry logic."""
        for attempt in range(1, self.selector_retry.max_attempts + 1):
            try:
                element = await self.selector_retry.find_element(page, selector, attempt)
                
                if not element:
                    return {
                        "success": False,
                        "attempts": attempt,
                        "failure_reason": "SELECTOR_NOT_FOUND"
                    }
                
                await element.click()
                logger.info(f"Successfully clicked '{selector}' on attempt {attempt}")
                
                return {
                    "success": True,
                    "attempts": attempt,
                    "failure_reason": None
                }
            except Exception as e:
                logger.error(f"Click attempt {attempt} failed: {e}")
                
                if attempt >= self.selector_retry.max_attempts:
                    return {
                        "success": False,
                        "attempts": attempt,
                        "failure_reason": f"CLICK_ERROR: {type(e).__name__}"
                    }
                
                await asyncio.sleep(self.selector_retry.base_delay * (2 ** (attempt - 1)))
        
        return {
            "success": False,
            "attempts": self.selector_retry.max_attempts,
            "failure_reason": "MAX_RETRIES_EXCEEDED"
        }
    
    async def safe_navigate(
        self,
        page: Page,
        url: str,
        expected_url_pattern: Optional[str] = None
    ) -> Dict[str, Any]:
        """Navigate with watchdog protection."""
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)
            return await self.nav_watchdog.watch_navigation(page, expected_url_pattern)
        except Exception as e:
            logger.error(f"Navigation failed: {e}")
            return {
                "success": False,
                "failure_type": f"NAV_ERROR: {type(e).__name__}",
                "final_url": page.url
            }
