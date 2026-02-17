import os
import re

def fix_uuid_imports():
    models_dir = 'app/models'
    fixed_files = []
    
    for filename in os.listdir(models_dir):
        if not filename.endswith('.py') or filename == '__init__.py':
            continue
            
        path = os.path.join(models_dir, filename)
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        original_content = content
        
        # Scenario 1: from sqlalchemy import ..., UUID, ...
        # Scenario 2: from sqlalchemy import UUID
        
        # Replace 'from sqlalchemy import UUID'
        content = content.replace('from sqlalchemy import UUID', 'from app.db.uuid_type import UUID')
        
        # Handle cases like 'from sqlalchemy import Column, String, UUID'
        content = re.sub(r'from sqlalchemy import (.*), UUID, (.*)', 
                         r'from sqlalchemy import \1, \2\nfrom app.db.uuid_type import UUID', content)
        content = re.sub(r'from sqlalchemy import (.*), UUID', 
                         r'from sqlalchemy import \1\nfrom app.db.uuid_type import UUID', content)
        
        # Cleanup duplicate or messy imports if any
        if original_content != content:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(content)
            fixed_files.append(filename)
            
    print(f"Fixed UUID imports in: {fixed_files}")

if __name__ == "__main__":
    fix_uuid_imports()
