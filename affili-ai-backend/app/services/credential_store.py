"""
Credential store service for encrypted storage and retrieval of secrets.
"""

from sqlalchemy.orm import Session
from app.models.credential import Credential
from app.core.security import encrypt_secret, decrypt_secret
from typing import Optional
import uuid
import json


def store_credential(
    db: Session,
    name: str,
    credential_type: str,
    secret: str,
    metadata: Optional[dict] = None,
) -> Credential:
    """Store an encrypted credential.
    
    Args:
        db: Database session
        name: Credential name
        credential_type: Type (gmail, stripe, sendgrid, etc.)
        secret: The secret to encrypt
        metadata: Optional unencrypted metadata dict
    
    Returns:
        Stored Credential object
    """
    encrypted_value = encrypt_secret(secret)
    metadata_json = json.dumps(metadata) if metadata else None
    
    credential = Credential(
        name=name,
        credential_type=credential_type,
        encrypted_value=encrypted_value,
        metadata=metadata_json,
    )
    db.add(credential)
    db.commit()
    db.refresh(credential)
    return credential


def get_credential(db: Session, credential_id: uuid.UUID) -> Optional[Credential]:
    """Get a credential by ID (returns encrypted value only)."""
    return db.query(Credential).filter(Credential.id == credential_id).first()


def decrypt_credential_secret(
    db: Session,
    credential_id: uuid.UUID,
) -> Optional[str]:
    """Decrypt and return the secret for a credential.
    
    NOTE: This should only be called when the actual secret is needed
    (e.g., before using it for API calls). Normally, only metadata is returned.
    """
    credential = get_credential(db, credential_id)
    if not credential:
        return None
    
    try:
        return decrypt_secret(credential.encrypted_value)
    except ValueError:
        return None


def list_credentials(db: Session) -> list[Credential]:
    """List all credentials (metadata only, no secrets)."""
    return db.query(Credential).all()


def delete_credential(db: Session, credential_id: uuid.UUID) -> bool:
    """Delete a credential."""
    credential = get_credential(db, credential_id)
    if not credential:
        return False
    
    db.delete(credential)
    db.commit()
    return True
