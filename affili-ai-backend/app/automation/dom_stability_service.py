"""
DOM Stability Service - Detect SPA async rendering completion.

Ensures form extraction happens AFTER React/Vue/Angular finish rendering.
"""

from playwright.async_api import Page
from app.core.logging import logger
from typing import Dict, Any
import asyncio
import time


async def wait_for_dom_stability(
    page: Page,
    timeout_seconds: float = 10.0,
    stability_threshold_ms: float = 500.0
) -> Dict[str, Any]:
    """
    Wait for DOM to stabilize (no mutations for threshold period).
    
    Critical for SPAs that load forms asynchronously.
    
    Args:
        page: Playwright page
        timeout_seconds: Max wait time
        stability_threshold_ms: Time without mutations to consider stable
        
    Returns:
        {
            "stable": bool,
            "wait_time_ms": float,
            "mutation_count": int
        }
    """
    logger.info("Waiting for DOM stability...")
    
    start_time = time.time()
    
    # Inject mutation observer
    await page.evaluate(f"""
        (stabilityThresholdMs) => {{
            window._domStability = {{
                mutationCount: 0,
                lastMutationTime: Date.now(),
                isStable: false
            }};
            
            const observer = new MutationObserver((mutations) => {{
                window._domStability.mutationCount += mutations.length;
                window._domStability.lastMutationTime = Date.now();
                window._domStability.isStable = false;
            }});
            
            observer.observe(document.body, {{
                childList: true,
                subtree: true,
                attributes: true,
                characterData: true
            }});
            
            // Check stability periodically
            setInterval(() => {{
                const timeSinceLastMutation = Date.now() - window._domStability.lastMutationTime;
                if (timeSinceLastMutation > stabilityThresholdMs) {{
                    window._domStability.isStable = true;
                }}
            }}, 100);
        }}
    """, stability_threshold_ms)
    
    # Poll for stability
    while True:
        elapsed = time.time() - start_time
        
        if elapsed > timeout_seconds:
            logger.warning(f"DOM stability timeout after {timeout_seconds}s")
            
            # Get final stats
            stats = await page.evaluate("""
                window._domStability || { mutationCount: 0, isStable: false }
            """)
            
            return {
                "stable": False,
                "wait_time_ms": elapsed * 1000,
                "mutation_count": stats.get("mutationCount", 0)
            }
        
        # Check if stable
        try:
            stats = await page.evaluate("""
                window._domStability || { mutationCount: 0, isStable: false }
            """)
            
            if stats.get("isStable", False):
                wait_time_ms = elapsed * 1000
                mutation_count = stats.get("mutationCount", 0)
                
                logger.info(f"DOM stable after {wait_time_ms:.0f}ms ({mutation_count} mutations)")
                
                return {
                    "stable": True,
                    "wait_time_ms": wait_time_ms,
                    "mutation_count": mutation_count
                }
            
            await asyncio.sleep(0.1)
            
        except Exception as e:
            logger.error(f"DOM stability check error: {e}")
            return {
                "stable": False,
                "wait_time_ms": elapsed * 1000,
                "mutation_count": 0
            }


async def detect_spa_framework(page: Page) -> Dict[str, Any]:
    """
    Detect which SPA framework is used (React, Vue, Angular, etc.).
    
    Helps tune stability waiting strategies.
    
    Returns:
        {
            "framework": str | None,
            "version": str | None,
            "detected_libraries": List[str]
        }
    """
    try:
        result = await page.evaluate("""
            () => {
                const libs = [];
                
                // React
                if (window.React) {
                    libs.push('React');
                }
                if (document.querySelector('[data-reactroot]') || 
                    document.querySelector('[data-reactid]')) {
                    libs.push('React (legacy)');
                }
                
                // Vue
                if (window.Vue) {
                    libs.push('Vue');
                }
                if (document.querySelector('[data-v-]')) {
                    libs.push('Vue (detected)');
                }
                
                // Angular
                if (window.ng) {
                    libs.push('Angular');
                }
                if (document.querySelector('[ng-app]') || 
                    document.querySelector('[ng-version]')) {
                    libs.push('Angular (detected)');
                }
                
                // jQuery
                if (window.jQuery || window.$) {
                    libs.push('jQuery');
                }
                
                return {
                    framework: libs[0] || null,
                    detected_libraries: libs
                };
            }
        """)
        
        logger.info(f"Detected frameworks: {result.get('detected_libraries', [])}")
        return result
        
    except Exception as e:
        logger.error(f"Framework detection error: {e}")
        return {
            "framework": None,
            "version": None,
            "detected_libraries": []
        }


async def wait_for_network_idle(
    page: Page,
    timeout_seconds: float = 10.0,
    idle_time_ms: float = 500.0
) -> Dict[str, Any]:
    """
    Wait for network activity to cease.
    
    Useful for waiting for API calls to complete before DOM extraction.
    
    Args:
        page: Playwright page
        timeout_seconds: Max wait time
        idle_time_ms: Time without requests to consider idle
        
    Returns:
        {
            "idle": bool,
            "wait_time_ms": float,
            "request_count": int
        }
    """
    logger.info("Waiting for network idle...")
    
    start_time = time.time()
    
    try:
        # Wait for network idle using Playwright's built-in
        await page.wait_for_load_state("networkidle", timeout=timeout_seconds * 1000)
        
        elapsed_ms = (time.time() - start_time) * 1000
        logger.info(f"Network idle after {elapsed_ms:.0f}ms")
        
        return {
            "idle": True,
            "wait_time_ms": elapsed_ms,
            "request_count": 0  # Playwright doesn't expose this
        }
    except Exception as e:
        elapsed_ms = (time.time() - start_time) * 1000
        logger.warning(f"Network idle timeout after {elapsed_ms:.0f}ms: {e}")
        
        return {
            "idle": False,
            "wait_time_ms": elapsed_ms,
            "request_count": 0
        }
