import os
import subprocess
import datetime
import uuid
from cryptography.fernet import Fernet
from pathlib import Path

# --- CONFIGURATION ---
BACKUP_DIR = "backups"
DB_URL = os.getenv("DATABASE_URL", "sqlite:///./affili_ai.db")
BACKUP_PASSWORD = os.getenv("BACKUP_PASSWORD", "dev-secret-key-12345") # In production, use os.environ

def get_cipher():
    # Derive a key from the password (simple implementation for dev)
    import base64
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    
    salt = b'affili-ai-salt' # Should be unique per install
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
    )
    key = base64.urlsafe_b64encode(kdf.derive(BACKUP_PASSWORD.encode()))
    return Fernet(key)

def backup_sqlite(db_path, backup_path):
    import shutil
    print(f"📦 Creating SQLite snapshot: {db_path}")
    shutil.copy2(db_path, backup_path)

def backup_postgres(db_url, backup_path):
    # Requirement: pg_dump must be in PATH
    print(f"🐘 Creating Postgres export: {db_url}")
    # Simplified command for demo; in prod use full pg_dump flags
    subprocess.run(["pg_dump", "--dbname=" + db_url, "--file=" + backup_path], check=True)

def encrypt_file(file_path):
    cipher = get_cipher()
    with open(file_path, "rb") as f:
        data = f.read()
    
    encrypted_data = cipher.encrypt(data)
    with open(file_path + ".enc", "wb") as f:
        f.write(encrypted_data)
    
    os.remove(file_path) # Remove unencrypted original
    print(f"🔒 Backup encrypted: {file_path}.enc")

def run_backup():
    print(f"🚀 Starting Database Backup: {datetime.datetime.now()}")
    
    if not os.path.exists(BACKUP_DIR):
        os.makedirs(BACKUP_DIR)
        
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    temp_backup = os.path.join(BACKUP_DIR, f"temp_{timestamp}.bak")
    
    try:
        if DB_URL.startswith("sqlite:///"):
            sqlite_path = DB_URL.replace("sqlite:///", "")
            if sqlite_path.startswith("./"):
                sqlite_path = sqlite_path[2:]
            backup_sqlite(sqlite_path, temp_backup)
        else:
            backup_postgres(DB_URL, temp_backup)
            
        encrypt_file(temp_backup)
        print(f"✅ Backup complete and secured.")
        
    except Exception as e:
        print(f"❌ Backup failed: {str(e)}")
        if os.path.exists(temp_backup):
            os.remove(temp_backup)

if __name__ == "__main__":
    run_backup()
