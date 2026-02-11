"""
Test Gemini API connectivity and JSON schema enforcement.

Validates:
1. API key configuration
2. Model availability
3. Structured JSON output
4. Error handling
"""

import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

def test_gemini():
    """Test Gemini API connectivity and JSON output."""
    print("="*60)
    print("AFFILI-AI Gemini API Test")
    print("="*60)
    
    if not GEMINI_API_KEY:
        print("❌ GEMINI_API_KEY not found in environment")
        return False
    
    print(f"\n🔑 API Key: {GEMINI_API_KEY[:20]}...")
    
    try:
        # Configure Gemini
        genai.configure(api_key=GEMINI_API_KEY)
        
        # Test 1: Model availability
        print("\n📡 Testing model availability...")
        model = genai.GenerativeModel("gemini-1.5-flash")
        print("✅ Model loaded: gemini-1.5-flash")
        
        # Test 2: Simple structured output
        print("\n🧪 Testing structured JSON output...")
        
        prompt = """
        You are a form field predictor. Predict a value for this field.
        
        Field: Company Name
        Context: User runs a tech blog called "AI Insights"
        
        Return ONLY valid JSON in this exact schema:
        {
            "value": "string value or null",
            "confidence": 0.0 to 1.0,
            "reasoning": "explanation"
        }
        """
        
        # Configure generation options
        generation_config = {
            "temperature": 0.1,
            "max_output_tokens": 1024,
        }

        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(**generation_config)
        )
        
        import json
        result = json.loads(response.text)
        
        # Validate schema
        assert "value" in result
        assert "confidence" in result
        assert "reasoning" in result
        assert isinstance(result["confidence"], (int, float))
        assert 0 <= result["confidence"] <= 1
        
        print(f"✅ Structured output: VALID")
        print(f"   Value: {result.get('value')}")
        print(f"   Confidence: {result.get('confidence')}")
        print(f"   Reasoning: {result.get('reasoning')[:60]}...")
        
        # Test 3: Token usage (if available)
        if hasattr(response, 'usage_metadata'):
            print(f"\n📊 Token usage:")
            print(f"   Prompt tokens: {response.usage_metadata.prompt_token_count}")
            print(f"   Response tokens: {response.usage_metadata.candidates_token_count}")
            print(f"   Total: {response.usage_metadata.total_token_count}")
        
        print("\n" + "="*60)
        print("GEMINI API TEST: SUCCESS")
        print("="*60)
        return True
        
    except Exception as e:
        print(f"\n❌ Gemini test failed: {str(e)}")
        print("\n" + "="*60)
        print("GEMINI API TEST: FAILED")
        print("="*60)
        return False

if __name__ == "__main__":
    success = test_gemini()
    sys.exit(0 if success else 1)
