#!/bin/bash
set -euo pipefail

# Configuration
# In production, these should be injected or loaded from secrets
DB_HOST="${POSTGRES_SERVER:-localhost}"
DB_USER="${POSTGRES_USER:-postgres}"
DB_NAME="${POSTGRES_DB:-affili_ai}"
BACKUP_DIR="/backups/postgres"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="${BACKUP_DIR}/${DB_NAME}_${DATE}.dump"
ENCRYPTED_FILE="${BACKUP_FILE}.enc"

# Ensure backup directory exists
mkdir -p ${BACKUP_DIR}

echo "[START] creating backup for ${DB_NAME}..."

# 1. Create Dump (Compressed Custom Format)
# -Fc: Custom format (compressed by default)
# -Z9: Max compression
export PGPASSWORD="${POSTGRES_PASSWORD}"
pg_dump -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" \
  -Fc -Z9 \
  -f "${BACKUP_FILE}"

if [ ! -f "${BACKUP_FILE}" ]; then
    echo "❌ Backup file creation failed!"
    exit 1
fi

echo "Backup size: $(du -h ${BACKUP_FILE} | cut -f1)"

# 2. Encrypt (AES-256-CBC)
# Requires a password file at /run/secrets/backup_password
if [ -f "/run/secrets/backup_password" ]; then
    echo "Encrypting backup..."
    openssl enc -aes-256-cbc -salt -pbkdf2 \
      -pass file:/run/secrets/backup_password \
      -in "${BACKUP_FILE}" \
      -out "${ENCRYPTED_FILE}"
      
    # Remove unencrypted file
    rm "${BACKUP_FILE}"
    echo "✅ Backup encrypted: ${ENCRYPTED_FILE}"
    
    # Verify encryption artifact exists
    if [ ! -f "${ENCRYPTED_FILE}" ]; then
         echo "❌ Encryption failed!"
         exit 1
    fi
else
    echo "⚠️  WARNING: No encryption password found at /run/secrets/backup_password"
    echo "⚠️  Backup left UNENCRYPTED: ${BACKUP_FILE}"
    # In strict mode, we might want to fail here
    # exit 1
fi

# 3. Simulate S3 Upload (placeholder)
# aws s3 cp ...
echo "[SUCCESS] Backup process completed."
