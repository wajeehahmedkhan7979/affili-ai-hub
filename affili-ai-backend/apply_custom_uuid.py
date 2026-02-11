#!/usr/bin/env python3
"""
Replace sqlalchemy.UUID with app.db.uuid_type.UUID across all model files.
"""
import re
from pathlib import Path

MODEL_DIR = Path("app/models")

def refactor_to_custom_uuid(file_path):
    """Refactor a single file to use custom UUID type."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original = content
    
    # Replace: from sqlalchemy import ... UUID ...
    # With: from sqlalchemy import ... (without UUID)
    # And add: from app.db.uuid_type import UUID
    
    # Pattern 1: UUID is in a multi-import from sqlalchemy
    if 'from sqlalchemy import' in content and ', UUID' in content:
        # Remove UUID from the sqlalchemy import
        content = re.sub(r', UUID(?=\W)', '', content)
        content = re.sub(r'UUID, ', '', content)
        
        # Add custom UUID import after sqlalchemy imports
        if 'from app.db.uuid_type import UUID' not in content:
            # Find the last sqlalchemy import line
            lines = content.split('\n')
            insert_idx = None
            for i, line in enumerate(lines):
                if line.strip().startswith('from sqlalchemy'):
                    insert_idx = i + 1
            
            if insert_idx:
                lines.insert(insert_idx, 'from app.db.uuid_type import UUID')
                content = '\n'.join(lines)
    
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
        if refactor_to_custom_uuid(file_path):
            print(f"✓ Refactored: {file_path.name}")
            modified_count += 1
    
    print(f"\n{modified_count} files modified to use custom UUID type.")
