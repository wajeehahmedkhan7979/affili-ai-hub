"""
Security service for behavioral authentication and risk scoring.
"""
from sqlalchemy.orm import Session
from app.models.security import LoginHistory, RiskProfile
from app.models.user import User
from app.core.time import utcnow
from datetime import timedelta
import hashlib
import json

# Risk Thresholds
RISK_THRESHOLD_BLOCK = 80.0
RISK_THRESHOLD_WARN = 50.0

def get_device_fingerprint(user_agent: str) -> str:
    """Generate a simple fingerprint derived from User-Agent."""
    if not user_agent:
        return "unknown"
    return hashlib.sha256(user_agent.encode()).hexdigest()

def evaluate_login_risk(
    db: Session, 
    user: User, 
    ip_address: str, 
    user_agent: str
) -> dict:
    """
    Evaluate login risk based on user history.
    
    Returns:
        dict: {
            "allowed": bool,
            "risk_score": float,
            "reason": str,
            "delay_seconds": float
        }
    """
    
    # Get or create risk profile
    profile = db.query(RiskProfile).filter(RiskProfile.user_id == user.id).first()
    if not profile:
        # First time user is analyzed, created with defaults
        profile = RiskProfile(
            user_id=user.id,
            known_ips=[],
            known_devices=[],
            baseline_risk_score=0.0
        )
        db.add(profile)
        db.commit()
        db.refresh(profile)
    
    current_score = profile.baseline_risk_score
    reasons = []
    
    # 1. Device Check
    device_hash = get_device_fingerprint(user_agent)
    known_devices = profile.known_devices or []
    if device_hash not in known_devices:
        current_score += 20.0
        reasons.append("New Device")
    
    # 2. IP Check
    known_ips = profile.known_ips or []
    if ip_address not in known_ips:
        current_score += 20.0
        reasons.append("New IP Address")
        
    # 3. Recent Failures (Velocity Check)
    # Count failed logins in last 15 minutes for this user
    since = utcnow() - timedelta(minutes=15)
    recent_failures = db.query(LoginHistory).filter(
        LoginHistory.user_id == user.id,
        LoginHistory.status == "FAILED",
        LoginHistory.created_at >= since
    ).count()
    
    if recent_failures > 0:
        penalty = recent_failures * 10.0
        current_score += penalty
        reasons.append(f"Recent Failures ({recent_failures})")
        
    # Cap score
    current_score = min(current_score, 100.0)
    
    # Determine Action
    allowed = True
    delay = 0.0
    
    if current_score >= RISK_THRESHOLD_BLOCK:
        allowed = False
        reasons.append("Risk Threshold Exceeded")
    elif current_score >= RISK_THRESHOLD_WARN:
        # Progressive delay: 1s per 10 points over 50
        delay = (current_score - 50.0) / 10.0
        
    return {
        "allowed": allowed,
        "risk_score": current_score,
        "reason": ", ".join(reasons) if reasons else "Normal",
        "delay_seconds": delay
    }

def record_login_attempt(
    db: Session,
    email: str,
    ip_address: str,
    user_agent: str,
    status: str,
    risk_score: float,
    tenant_id: str = None,
    user: User = None,
    meta_data: dict = None
):
    """Log the login attempt."""
    try:
        # Resolve tenant_id if possible
        target_tenant_id = None
        if user:
            target_tenant_id = user.tenant_id
        elif tenant_id:
            try:
                import uuid
                target_tenant_id = uuid.UUID(str(tenant_id))
            except:
                pass

        if not target_tenant_id:
            # Fallback to a system-level or unknown tenant if we can't resolve it
            # In multi-tenant login, we usually have tenant_id in the request
            pass

        history = LoginHistory(
            tenant_id=target_tenant_id,
            user_id=user.id if user else None,
            email=email,
            ip_address=ip_address,
            user_agent=user_agent,
            status=status,
            risk_score=risk_score,
            meta_data=meta_data
        )
        db.add(history)
        
        # If successful, update Risk Profile (Reinforcement learning lite)
        if status == "SUCCESS" and user:
            profile = db.query(RiskProfile).filter(RiskProfile.user_id == user.id).first()
            if profile:
                # Add IP if new
                known_ips = list(profile.known_ips) if profile.known_ips else []
                if ip_address not in known_ips:
                    known_ips.append(ip_address)
                    # Keep max 10 IPs
                    if len(known_ips) > 10:
                        known_ips.pop(0)
                    profile.known_ips = known_ips
                
                # Add Device if new
                device_hash = get_device_fingerprint(user_agent)
                known_devices = list(profile.known_devices) if profile.known_devices else []
                if device_hash not in known_devices:
                    known_devices.append(device_hash)
                    if len(known_devices) > 10:
                        known_devices.pop(0)
                    profile.known_devices = known_devices
                    
                # Decay baseline risk
                profile.baseline_risk_score = max(0.0, profile.baseline_risk_score - 5.0)
                profile.last_risk_update = utcnow()
        
        db.commit()
    except Exception as e:
        import traceback
        print(f"Failed to record login attempt: {e}")
        print(traceback.format_exc())
        db.rollback()
