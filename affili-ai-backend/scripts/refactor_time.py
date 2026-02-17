
import os
import re

TARGET_DIR = "d:\\PROJECTS-REPOS\\AFFILIATE-PROJ\\affili-ai-hub\\affili-ai-backend\\app"
TIME_IMPORT = "from app.core.time import utcnow"

def process_file(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    if "datetime.utcnow" not in content:
        return False

    # Replace usages
    new_content = content.replace("datetime.utcnow", "utcnow")
    
    # Add import
    # Try to find existing app imports or standard lib imports
    if TIME_IMPORT not in new_content:
        # Naive insertion: find first newline after docstring or imports
        lines = new_content.splitlines()
        insert_idx = 0
        
        # Skip shebang or encoding
        if lines and lines[0].startswith("#"):
            insert_idx += 1
            
        # Skip docstring
        if insert_idx < len(lines) and (lines[insert_idx].startswith('"""') or lines[insert_idx].startswith("'''")):
            insert_idx += 1
            while insert_idx < len(lines) and not (lines[insert_idx].endswith('"""') or lines[insert_idx].endswith("'''")):
                insert_idx += 1
            insert_idx += 1 # Skip closing quote
            
        # Find place to insert
        # Look for "from app." imports to group with
        app_import_idx = -1
        for i, line in enumerate(lines[insert_idx:], start=insert_idx):
            if line.startswith("from app."):
                app_import_idx = i
                break
        
        if app_import_idx != -1:
            lines.insert(app_import_idx, TIME_IMPORT)
        else:
            # Insert after last import, or at top
            last_import_idx = -1
            for i, line in enumerate(lines[insert_idx:], start=insert_idx):
                if line.startswith("import ") or line.startswith("from "):
                    last_import_idx = i
            
            if last_import_idx != -1:
                lines.insert(last_import_idx + 1, TIME_IMPORT)
            else:
                lines.insert(insert_idx, TIME_IMPORT)
                
        new_content = "\n".join(lines)

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(new_content)
    
    return True

def main():
    count = 0
    for root, dirs, files in os.walk(TARGET_DIR):
        for file in files:
            if file.endswith(".py") and file != "time.py":
                path = os.path.join(root, file)
                if process_file(path):
                    print(f"Refactored: {path}")
                    count += 1
    print(f"Total files refactored: {count}")

if __name__ == "__main__":
    main()
