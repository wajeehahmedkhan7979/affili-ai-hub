#!/usr/bin/env python3
"""
Remove as_uuid=True from all UUID column definitions.
"""
import re
from pathlib import Path

MODEL_DIR = Path("app/models")

def remove_as_uuid(file_path):
    """Remove as_uuid=True parameter from UUID columns."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original = content
    
    # Replace UUID(as_uuid=True) with UUID()
    content = re.sub(r'UUID\(as_uuid=True\)', 'UUID()', content)
    
    if content != original:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    return False

if __name__ == "__main__":
    model_files = list(MODEL_DIR.glob("*.py"))
    modified_count = 0
    
    for file_path in model_files:
        if file_path.name == '__init__.py':
            continue
        if remove_as_uuid(file_path):
            print(f"✓ Cleaned: {file_path.name}")
            modified_count += 1
    
    print(f"\n{modified_count} files cleaned.")
