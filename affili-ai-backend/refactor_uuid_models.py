#!/usr/bin/env python3
"""
Automated script to refactor all models from postgresql.UUID to sqlalchemy.UUID.
This ensures Python 3.13 compatibility and multi-dialect support.
"""
import re
from pathlib import Path

MODEL_DIR = Path("app/models")

def refactor_uuid_imports(file_path):
    """Refactor a single file's UUID import."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original = content
    
    # Pattern 1: from sqlalchemy.dialects.postgresql import UUID, JSONB
    content = re.sub(
        r'from sqlalchemy\.dialects\.postgresql import UUID, JSONB',
        'from sqlalchemy import UUID\nfrom sqlalchemy.dialects.postgresql import JSONB',
        content
    )
    
    # Pattern 2: from sqlalchemy.dialects.postgresql import UUID, JSONB, JSON
    content = re.sub(
        r'from sqlalchemy\.dialects\.postgresql import UUID, JSONB, JSON',
        'from sqlalchemy import UUID\nfrom sqlalchemy.dialects.postgresql import JSONB, JSON',
        content
    )
    
    # Pattern 3: from sqlalchemy.dialects.postgresql import UUID (only)
    content = re.sub(
        r'from sqlalchemy\.dialects\.postgresql import UUID\s*$',
        'from sqlalchemy import UUID',
        content,
        flags=re.MULTILINE
    )
    
    if content != original:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    return False

if __name__ == "__main__":
    files_to_refactor = [
        "audit_log.py", "human_feedback.py", "form_field_embedding.py",
        "export_job.py", "credential.py", "billing.py", "application.py",
        "agent.py", "llm_usage_log.py", "retention.py", "program.py",
        "policy.py", "outreach_log.py", "metrics.py", "operator_action_log.py",
        "tenant_runtime_flag.py", "usage.py", "user.py", "webhook.py"
    ]
    
    modified_count = 0
    for filename in files_to_refactor:
        file_path = MODEL_DIR / filename
        if file_path.exists():
            if refactor_uuid_imports(file_path):
                print(f"✓ Refactored: {filename}")
                modified_count += 1
        else:
            print(f"✗ Not found: {filename}")
    
    print(f"\n{modified_count} files modified successfully.")
