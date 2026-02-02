"""
Base class for affiliate program automations.

Provides common interface and utilities for all program-specific automations.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, Any, Optional, Tuple
import os


class BaseAffiliateAutomation(ABC):
    """Abstract base class for affiliate program automations."""
    
    @property
    @abstractmethod
    def PROGRAM_NAME(self) -> str:
        """Human-readable program name."""
        pass
    
    @property
    @abstractmethod
    def SIGNUP_URL(self) -> str:
        """URL to the affiliate signup page."""
        pass
    
    @abstractmethod
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
        Execute the automation for this affiliate program.
        
        Args:
            email: Applicant email
            name: Applicant name
            website: Applicant website URL
            headless: Run browser in headless mode
            screenshot_dir: Directory to save screenshots
            **kwargs: Program-specific additional fields
            
        Returns:
            Tuple of (success: bool, metadata: dict)
            metadata includes:
            - screenshots: {before, filled, after} paths
            - logs: execution log
            - error: error message if failed
            - submitted_at: timestamp
        """
        pass
    
    def _now(self) -> str:
        """Return current ISO timestamp."""
        return datetime.utcnow().isoformat()
    
    async def _check_for_captcha(self, page) -> Dict[str, Any]:
        """
        Check if current page contains CAPTCHA.
        
        Args:
            page: Playwright Page object
            
        Returns:
            Dict with: detected (bool), reason (str), url (str)
        """
        from app.automation.captcha_detector import detect_captcha
        return await detect_captcha(page)
    
    def _prepare_screenshot_dir(self, screenshot_dir: Optional[str], task_id: Optional[str] = None) -> str:
        """Prepare and return screenshot directory path."""
        if screenshot_dir is None:
            program_slug = self.PROGRAM_NAME.lower().replace(" ", "_")
            if task_id:
                screenshot_dir = os.path.join("storage", "screenshots", str(task_id), program_slug)
            else:
                screenshot_dir = os.path.join("storage", "screenshots", program_slug)
        os.makedirs(screenshot_dir, exist_ok=True)
        return screenshot_dir
