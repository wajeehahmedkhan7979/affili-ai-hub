"""
Vision/LLM adapter for analyzing screenshots and form fields.
Pluggable interface for different providers (stub, Gemini, OpenAI).
"""

from typing import Optional, Dict, Any, List
from app.core.config import get_settings
import base64

settings = get_settings()


class FieldHint(dict):
    """Field hint from vision analysis."""
    def __init__(self, name_hint: str, bounding_box: tuple, confidence: float):
        super().__init__(
            name_hint=name_hint,
            bounding_box=bounding_box,
            confidence=confidence
        )


class VisionAdapterBase:
    """Base class for vision adapters."""
    
    async def analyze_screenshot(
        self,
        image_bytes: bytes,
        task_context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Analyze screenshot and extract fields.
        
        Args:
            image_bytes: Raw image bytes (PNG/JPG)
            task_context: Optional context about the task
        
        Returns:
            {
                "fields": [
                    {"name_hint": "email", "bounding_box": [x, y, w, h], "confidence": 0.95},
                    ...
                ],
                "captcha_detected": bool,
                "text_blocks": [{"text": "...", "position": [x, y]}],
            }
        """
        raise NotImplementedError


class StubVisionAdapter(VisionAdapterBase):
    """Stub vision adapter for MVP - uses heuristic DOM/text parsing."""
    
    async def analyze_screenshot(
        self,
        image_bytes: bytes,
        task_context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Analyze using simple heuristics."""
        # TODO: Implement:
        # - OCR using pytesseract or paddleOCR
        # - DOM element detection from screenshot
        # - CAPTCHA detection using known patterns
        
        return {
            "fields": [
                FieldHint("email", (100, 200, 200, 40), 0.8),
                FieldHint("password", (100, 250, 200, 40), 0.8),
            ],
            "captcha_detected": False,
            "text_blocks": [],
            "provider": "stub",
        }


class GeminiVisionAdapter(VisionAdapterBase):
    """Vision adapter using Google Gemini."""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
    
    async def analyze_screenshot(
        self,
        image_bytes: bytes,
        task_context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Analyze using Gemini Vision API."""
        # TODO: Implement Gemini integration
        # import google.generativeai as genai
        # genai.configure(api_key=self.api_key)
        # model = genai.GenerativeModel('gemini-pro-vision')
        # response = model.generate_content([
        #     "Extract form fields and detect CAPTCHA",
        #     {"mime_type": "image/png", "data": base64.b64encode(image_bytes)}
        # ])
        
        raise NotImplementedError("Gemini adapter not yet implemented")


class OpenAIVisionAdapter(VisionAdapterBase):
    """Vision adapter using OpenAI GPT-4 Vision."""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
    
    async def analyze_screenshot(
        self,
        image_bytes: bytes,
        task_context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Analyze using OpenAI GPT-4 Vision."""
        # TODO: Implement OpenAI Vision integration
        # import openai
        # openai.api_key = self.api_key
        # response = openai.ChatCompletion.create(
        #     model="gpt-4-vision-preview",
        #     messages=[{
        #         "role": "user",
        #         "content": [
        #             {"type": "text", "text": "Extract form fields..."},
        #             {"type": "image_url", "image_url": {"url": f"data:image/png;base64,..."}},
        #         ]
        #     }]
        # )
        
        raise NotImplementedError("OpenAI adapter not yet implemented")


def get_vision_adapter() -> VisionAdapterBase:
    """Get the configured vision adapter."""
    provider = settings.VISION_PROVIDER.lower()
    
    if provider == "stub":
        return StubVisionAdapter()
    elif provider == "gemini":
        if not settings.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY not configured")
        return GeminiVisionAdapter(settings.GEMINI_API_KEY)
    elif provider == "openai":
        if not settings.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY not configured")
        return OpenAIVisionAdapter(settings.OPENAI_API_KEY)
    else:
        raise ValueError(f"Unknown vision provider: {provider}")
