"""
Agent Trust Security Utilities.
Phase 26.5: Signed Identities.
"""
import base64
import logging
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.exceptions import InvalidSignature

logger = logging.getLogger(__name__)

def verify_agent_signature(public_key_b64: str, signature_b64: str, message: str) -> bool:
    """
    Verify an Ed25519 signature from an agent.
    
    Args:
        public_key_b64: Base64 encoded public key (Ed25519)
        signature_b64: Base64 encoded signature
        message: The signed message (usually "task_id:timestamp")
        
    Returns:
        bool: True if signature is valid, False otherwise.
    """
    try:
        # Decode public key and signature
        public_key_bytes = base64.b64decode(public_key_b64)
        signature_bytes = base64.b64decode(signature_b64)
        message_bytes = message.encode("utf-8")
        
        # Load public key
        public_key = ed25519.Ed25519PublicKey.from_public_bytes(public_key_bytes)
        
        # Verify
        public_key.verify(signature_bytes, message_bytes)
        return True
    except (ValueError, TypeError, base64.binascii.Error) as e:
        logger.warning(f"Malformed public key or signature: {e}")
        return False
    except InvalidSignature:
        logger.warning("Signature verification failed")
        return False
    except Exception as e:
        logger.error(f"Unexpected error during signature verification: {e}")
        return False
