"""
Discovery Agent - Automated affiliate program discovery.

Crawls websites to detect affiliate program signup opportunities
using keyword-based heuristics.
"""

import asyncio
import re
from typing import List, Dict, Any, Optional, Tuple
from urllib.parse import urljoin, urlparse

from playwright.async_api import async_playwright, Page, Browser, BrowserContext


class DiscoveryAgent:
    """
    Discovers affiliate programs by scanning websites for affiliate/partner links.
    
    Uses deterministic keyword matching, no ML/AI.
    """
    
    # Keywords that indicate affiliate program links
    AFFILIATE_KEYWORDS = [
        "affiliate",
        "affiliates",
        "partner",
        "partners",
        "referral",
        "earn",
        "associates",
        "reseller",
    ]
    
    # Additional keywords that boost confidence
    SIGNUP_KEYWORDS = ["signup", "sign-up", "join", "register", "apply"]
    
    def __init__(self, headless: bool = True, timeout: int = 30000):
        """
        Initialize discovery agent.
        
        Args:
            headless: Run browser in headless mode
            timeout: Page load timeout in milliseconds
        """
        self.headless = headless
        self.timeout = timeout
    
    async def discover_programs(self, seed_url: str) -> Tuple[bool, List[Dict[str, Any]]]:
        """
        Discover affiliate programs from a seed URL.
        
        Args:
            seed_url: Starting URL to crawl
            
        Returns:
            Tuple of (success, list of discovered programs)
        """
        browser: Optional[Browser] = None
        context: Optional[BrowserContext] = None
        page: Optional[Page] = None
        
        # Normalize URL
        if not seed_url.startswith(("http://", "https://")):
            seed_url = "https://" + seed_url
        
        discovered_programs = [] # Renamed from 'discovered'
        logs = []
        
        try:
            async with async_playwright() as p:
                logs.append(f"Launching browser (headless={self.headless})")
                browser = await p.chromium.launch(
                    headless=self.headless,
                    args=["--disable-gpu", "--no-sandbox", "--disable-dev-shm-usage"]
                )
                context = await browser.new_context()
                page = await context.new_page()
                
                # Navigate to seed URL
                logs.append(f"Navigating to {seed_url}")
                # Use domcontentloaded instead of networkidle to prevent strict timeouts on heavy sites
                await page.goto(seed_url, wait_until="domcontentloaded", timeout=60000)
                logs.append("Page loaded successfully")
                
                # Extract all links
                links = await page.evaluate("""
                    () => {
                        return Array.from(document.querySelectorAll('a')).map(a => ({
                            href: a.href,
                            text: a.textContent.trim(),
                            inFooter: a.closest('footer') !== null
                        }));
                    }
                """)
                
                logs.append(f"Found {len(links)} links on page")
                
                # Filter and score affiliate links
                for link_data in links:
                    href = link_data.get("href", "")
                    text = link_data.get("text", "").lower()
                    in_footer = link_data.get("inFooter", False)
                    
                    if not href or href.startswith(("javascript:", "mailto:", "#")):
                        continue
                    
                    # Check if link contains affiliate keywords
                    href_lower = href.lower()
                    matches_keyword = any(
                        keyword in href_lower or keyword in text
                        for keyword in self.AFFILIATE_KEYWORDS
                    )
                    
                    if matches_keyword:
                        # Calculate confidence score
                        confidence = self._calculate_confidence(
                            href=href_lower,
                            text=text,
                            in_footer=in_footer
                        )
                        
                        # Extract program name
                        program_name = self._extract_program_name(
                            href=href,
                            text=text,
                            seed_url=seed_url
                        )
                        
                        # Make absolute URL
                        absolute_url = urljoin(seed_url, href)
                        
                        discovered_programs.append({
                            "name": program_name,
                            "signup_url": absolute_url,
                            "base_url": seed_url,
                            "confidence": round(confidence, 2),
                            "link_text": text[:100],  # First 100 chars for reference
                        })
                        
                        logs.append(
                            f"Found: {program_name} ({absolute_url}) - confidence: {confidence:.2f}"
                        )
                
                logs.append(f"Discovery complete. Found {len(discovered_programs)} potential programs.")
                
                return True, discovered_programs
                
        except Exception as e:
            import traceback
            traceback.print_exc()
            logs.append(f"Error during discovery: {str(e)}")
            return False, []
        finally:
            # Safely close resources ignoring errors if already closed
            if page:
                try: await page.close()
                except: pass
            if context:
                try: await context.close()
                except: pass
            if browser:
                try: await browser.close()
                except: pass
            
            # Print logs
            for log in logs:
                print(f"[Discovery] {log}")
    
    def _calculate_confidence(
        self,
        href: str,
        text: str,
        in_footer: bool
    ) -> float:
        """
        Calculate confidence score for a potential affiliate link.
        
        Scoring rules:
        - Contains "affiliate": +0.4
        - Contains "partner": +0.3
        - Contains signup keyword: +0.3
        - In footer: +0.2
        - HTTPS: +0.1
        
        Max score: 1.0
        """
        score = 0.0
        
        # Primary keyword check
        if "affiliate" in href or "affiliate" in text:
            score += 0.4
        elif "partner" in href or "partner" in text:
            score += 0.3
        
        # Signup indicators
        if any(kw in href or kw in text for kw in self.SIGNUP_KEYWORDS):
            score += 0.3
        
        # Location boost
        if in_footer:
            score += 0.2
        
        # Security
        if href.startswith("https"):
            score += 0.1
        
        return min(score, 1.0)
    
    def _extract_program_name(
        self,
        href: str,
        text: str,
        seed_url: str
    ) -> str:
        """
        Extract a readable program name from link data.
        
        Priority:
        1. Link text (if meaningful)
        2. Domain from seed_url
        3. Fallback to "Unknown Program"
        """
        # If link text is meaningful (not just "click here", etc.)
        trash_words = ["click", "here", "learn more", "read more", "→", ">"]
        if text and len(text) > 3 and not any(tw in text.lower() for tw in trash_words):
            # Clean up and title case
            cleaned = re.sub(r'[^\w\s-]', '', text)
            return cleaned[:100].title()
        
        # Extract domain from seed URL
        try:
            domain = urlparse(seed_url).netloc
            domain = domain.replace("www.", "")
            return f"{domain.split('.')[0].title()} Affiliates"
        except:
            return "Unknown Program"
