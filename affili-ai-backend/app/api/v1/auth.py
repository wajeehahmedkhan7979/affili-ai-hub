"""
Authentication API endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from app.core.time import utcnow
from app.db.session import get_db
from app.models.user import User, UserRole
from app.models.tenant import Tenant
from app.schemas.auth import UserLogin, TokenResponse, TokenRefresh, UserRegister, UserResponse
from app.services.auth_service import (
    verify_password, 
    get_password_hash,
    create_access_token, 
    create_refresh_token,
    decode_token
)
from app.api.dependencies import get_current_user
import uuid

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/login", response_model=TokenResponse)
async def login(
    login_in: UserLogin, 
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Authenticate user and return tokens with behavioral risk check.
    """
    from app.services import security_service as sec_svc
    import asyncio
    
    client_ip = request.client.host
    user_agent = request.headers.get("User-Agent", "unknown")

    user = db.query(User).filter(
        User.tenant_id == login_in.tenant_id,
        User.email == login_in.email,
        User.is_active == True
    ).first()

    if not user:
        # Record attempt for non-existent user
        sec_svc.record_login_attempt(
            db, email=login_in.email, ip_address=client_ip, 
            user_agent=user_agent, status="FAILED", 
            risk_score=50.0, tenant_id=login_in.tenant_id
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    # 1. Behavioral Risk Check
    risk_assessment = sec_svc.evaluate_login_risk(db, user, client_ip, user_agent)
    risk_score = risk_assessment["risk_score"]
    
    if not risk_assessment["allowed"]:
        sec_svc.record_login_attempt(
            db, email=user.email, ip_address=client_ip,
            user_agent=user_agent, status="BLOCKED",
            risk_score=risk_score, user=user,
            meta_data={"reason": risk_assessment["reason"]}
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Security Policy: Access restricted due to high risk score ({risk_score}). Reason: {risk_assessment['reason']}"
        )
        
    # 2. Progressive Backoff
    if risk_assessment["delay_seconds"] > 0:
        await asyncio.sleep(risk_assessment["delay_seconds"])

    # 3. Identity Verification
    if not user.hashed_password or not verify_password(login_in.password, user.hashed_password):
        sec_svc.record_login_attempt(
            db, email=user.email, ip_address=client_ip,
            user_agent=user_agent, status="FAILED",
            risk_score=risk_score, user=user
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # 4. Success Path
    sec_svc.record_login_attempt(
        db, email=user.email, ip_address=client_ip,
        user_agent=user_agent, status="SUCCESS",
        risk_score=risk_score, user=user
    )
        
    access_token = create_access_token(user.id, user.tenant_id, user.role)
    refresh_token = create_refresh_token(user.id, user.refresh_token_version)
    
    # Phase 19 Hardening: Store refresh token hash and update login time
    user.refresh_token_hash = get_password_hash(refresh_token)
    user.last_login_at = utcnow()
    db.commit()
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "email": user.email,
            "role": user.role,
            "tenant_id": user.tenant_id,
            "is_active": user.is_active
        }
    }

@router.post("/signup", response_model=TokenResponse)
def signup(register_in: UserRegister, db: Session = Depends(get_db)):
    """
    Register a new user and create a tenant.
    """
    # 1. Check if user already exists
    existing_user = db.query(User).filter(User.email == register_in.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists"
        )
    
    # 2. Create new Tenant
    tenant = Tenant(
        id=uuid.uuid4(),
        name=register_in.tenant_name or f"{register_in.email}'s Team"
    )
    db.add(tenant)
    db.flush() # Get tenant ID
    
    # 3. Create User as OWNER of the new tenant
    user = User(
        id=uuid.uuid4(),
        tenant_id=tenant.id,
        email=register_in.email,
        hashed_password=get_password_hash(register_in.password),
        role=UserRole.OWNER.value,
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    
    access_token = create_access_token(user.id, user.tenant_id, user.role)
    refresh_token = create_refresh_token(user.id, user.refresh_token_version)
    
    # Phase 19 Hardening: Store refresh token hash and update login time
    from datetime import datetime
    user.refresh_token_hash = get_password_hash(refresh_token)
    user.last_login_at = utcnow()
    db.commit()
    db.refresh(user)
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "email": user.email,
            "role": user.role,
            "tenant_id": user.tenant_id,
            "is_active": user.is_active
        }
    }

@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    """
    Get current user profile.
    """
    return {
        "id": current_user.id,
        "email": current_user.email,
        "role": current_user.role,
        "tenant_id": current_user.tenant_id,
        "is_active": current_user.is_active
    }

@router.post("/refresh", response_model=TokenResponse)
def refresh_token(refresh_in: TokenRefresh, db: Session = Depends(get_db)):
    """
    Refresh access token using a valid refresh token.
    """
    payload = decode_token(refresh_in.refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
        
    user_id = payload.get("sub")
    version = payload.get("ver")
    
    user = db.query(User).filter(User.id == uuid.UUID(user_id)).first()
    if not user or user.refresh_token_version != version or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired or user inactive"
        )
    
    # Phase 19 Hardening: Verify refresh token hash
    if not user.refresh_token_hash or not verify_password(refresh_in.refresh_token, user.refresh_token_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Revoked or invalid refresh token"
        )
        
    access_token = create_access_token(user.id, user.tenant_id, user.role)
    refresh_token = create_refresh_token(user.id, user.refresh_token_version)
    
    # Update hash for rotation (optional but safer)
    user.refresh_token_hash = get_password_hash(refresh_token)
    db.commit()
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "email": user.email,
            "role": user.role,
            "tenant_id": user.tenant_id,
            "is_active": user.is_active
        }
    }