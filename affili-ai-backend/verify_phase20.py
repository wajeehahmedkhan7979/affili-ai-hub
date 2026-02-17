"""
Verification script for Phase 20 AI features.
"""

from unittest.mock import patch, MagicMock
from app.services.llm_service import predict_field_value
from app.db.session import Session, get_engine_instance
from app.models.llm_usage_log import LLMUsageLog
from app.models.tenant import Tenant
import uuid
import json

def verify_ai_flow():
    engine = get_engine_instance()
    with Session(engine) as db:
        # 1. Get a tenant ID for the test
        tenant = db.query(Tenant).first()
        if not tenant:
            print("ERROR: No tenant found in DB. Run seed_dev_user.py first.")
            return
        
        tenant_id = tenant.id
        print(f"Using Tenant: {tenant.name} ({tenant_id})")

        # 2. Mock Gemini to simulate success
        print("\n--- Triggering MOCKED field prediction ---")
        mock_response = MagicMock()
        mock_response.text = json.dumps({
            "value": "https://example-mock.com",
            "confidence": 0.95,
            "source": "heuristic",
            "reasoning": "Mocked successful response"
        })
        
        with patch("google.generativeai.GenerativeModel.generate_content", return_value=mock_response):
            prediction = predict_field_value(
                field_label="Business Website",
                field_type="url",
                rag_candidates=[],
                user_context={"website": "https://example.com"},
                tenant_id=tenant_id,
                db=db
            )
        
        print(f"Result: {prediction['value']}")
        print(f"Confidence: {prediction['confidence']}")
        print(f"Source: {prediction['source']}")
        print(f"Prompt Version: {prediction.get('prompt_version_id')}")
        print(f"Latency: {prediction.get('latency_ms')}ms")

        # 3. Verify DB Log
        print("\n--- Verifying DB Log ---")
        log = db.query(LLMUsageLog).order_by(LLMUsageLog.created_at.desc()).first()
        
        if not log:
            print("ERROR: No LLMUsageLog found.")
            return
            
        print(f"Logged Prompt Version: {log.prompt_version_id}")
        print(f"Logged Confidence: {log.confidence}")
        print(f"Logged Latency: {log.latency_ms}ms")
        
        if log.prompt_version_id and round(float(log.confidence), 2) == 0.95 and log.latency_ms is not None:
             print("\nVerification SUCCESS: Phase 20 metrics (mocked) recorded correctly!")
        else:
             print("\nVerification FAILED: Metrics mismatch in log.")
             if not log.prompt_version_id: print("- Prompt version was not logged")
             if round(float(log.confidence), 2) != 0.95: print(f"- Confidence mismatch: {log.confidence} != 0.95")
             if log.latency_ms is None: print("- Latency was not logged")

if __name__ == "__main__":
    verify_ai_flow()

if __name__ == "__main__":
    verify_ai_flow()
