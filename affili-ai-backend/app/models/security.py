"""
Security models for behavioral analysis and risk scoring.
"""
from sqlalchemy import Column, String, Boolean, DateTime, Float, ForeignKey, JSON
from app.core.time import utcnow
from app.db.uuid_type import UUID
from app.db.base import Base
import uuid

class LoginHistory(Base):
    """Audit log for login attempts."""
    __tablename__ = "login_history"
    
    id = Column(UUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(), ForeignKey("tenants.id"), nullable=False, index=True)
    user_id = Column(UUID(), ForeignKey("users.id"), nullable=True, index=True) # Nullable if user not found but attempt recorded
    email = Column(String(255), nullable=True, index=True) # Redundant but useful for failed attempts where user_id is unknown
    ip_address = Column(String(45), nullable=False, index=True)
    user_agent = Column(String(500), nullable=True)
    status = Column(String(20), nullable=False, index=True) # SUCCESS, FAILED, BLOCKED
    risk_score = Column(Float, default=0.0)
    meta_data = Column(JSON, nullable=True) # Device fingerprint, location, failure reason
    created_at = Column(DateTime, default=utcnow, index=True)

class RiskProfile(Base):
    """User risk profile and behavioral baseline."""
    __tablename__ = "risk_profiles"
    
    id = Column(UUID(), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(), ForeignKey("users.id"), unique=True, nullable=False)
    known_ips = Column(JSON, default=list) # List of trusted IP addresses/subnets
    known_devices = Column(JSON, default=list) # List of trusted device fingerprints
    baseline_risk_score = Column(Float, default=0.0)
    last_risk_update = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)
