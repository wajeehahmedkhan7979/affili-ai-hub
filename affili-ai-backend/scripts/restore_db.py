import os
import subprocess
import argparse
from cryptography.fernet import Fernet

# --- CONFIGURATION ---
BACKUP_PASSWORD = os.getenv("BACKUP_PASSWORD", "dev-secret-key-12345")
DB_URL = os.getenv("DATABASE_URL", "sqlite:///./affili_ai.db")

def get_cipher():
    import base64
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    
    salt = b'affili-ai-salt'
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
    )
    key = base64.urlsafe_b64encode(kdf.derive(BACKUP_PASSWORD.encode()))
    return Fernet(key)

def decrypt_file(enc_path, out_path):
    cipher = get_cipher()
    with open(enc_path, "rb") as f:
        encrypted_data = f.read()
    
    data = cipher.decrypt(encrypted_data)
    with open(out_path, "wb") as f:
        f.write(data)
    print(f"🔓 Backup decrypted: {out_path}")

def restore_sqlite(temp_path, target_path):
    import shutil
    print(f"🔄 Restoring SQLite database to: {target_path}")
    shutil.copy2(temp_path, target_path)

def restore_postgres(temp_path, db_url):
    print(f"🐘 Restoring Postgres database: {db_url}")
    # Requirement: psql must be in PATH
    # Note: This assumes the database exists or we use --create flags in restore
    subprocess.run(["psql", "--dbname=" + db_url, "--file=" + temp_path], check=True)

def validate_restore():
    """Simple check to see if we can query the restored DB."""
    try:
        from sqlalchemy import create_all_engines, text, create_engine
        engine = create_engine(DB_URL)
        with engine.connect() as conn:
            # Check for a few core tables
            tables = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table';")).fetchall()
            table_names = [t[0] for t in tables]
            print(f"📊 Restored tables: {table_names}")
            if "tasks" in table_names and "tenants" in table_names:
                print("✅ Integrity Check Passed.")
                return True
            else:
                print("⚠️ Missing core tables.")
                return False
    except Exception as e:
        print(f"❌ Validation failed: {e}")
        return False

def run_restore(file_path):
    print(f"🚀 Starting Database Restore from: {file_path}")
    
    temp_decrypted = "temp_restore.bak"
    
    try:
        decrypt_file(file_path, temp_decrypted)
        
        if DB_URL.startswith("sqlite:///"):
            sqlite_path = DB_URL.replace("sqlite:///", "")
            if sqlite_path.startswith("./"):
                sqlite_path = sqlite_path[2:]
            restore_sqlite(temp_decrypted, sqlite_path)
        else:
            restore_postgres(temp_decrypted, DB_URL)
            
        validate_restore()
        print("✅ Restore Operation Finished.")
        
    except Exception as e:
        print(f"❌ Restore failed: {str(e)}")
    finally:
        if os.path.exists(temp_decrypted):
            os.remove(temp_decrypted)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", required=True, help="Path to the .enc backup file")
    args = parser.parse_args()
    
    run_restore(args.file)
