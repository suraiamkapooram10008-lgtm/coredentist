"""
Staff Management Endpoints
CRUD operations for practice staff (staff users)
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from typing import List, Any
from uuid import UUID
from datetime import datetime, timezone

from app.core.database import get_db
from app.api.deps import get_current_user, require_role, verify_csrf
from app.models.user import User, UserRole
from app.core.audit import log_audit_event
from app.core.security import get_password_hash, validate_password_strength
from app.schemas.user import UserResponse

router = APIRouter()

@router.get("/", response_model=List[UserResponse])
async def list_staff(
    request: Request,
    is_active: bool = Query(True, description="Filter by active status"),
    current_user: User = Depends(require_role(UserRole.OWNER, UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    List all staff members in the practice
    """
    # HIPAA Audit: Tracking access to workforce lists
    await log_audit_event(
        db, current_user, "staff_list_viewed", "user", None, request
    )
    await db.commit()

    stmt = select(User).where(
        User.practice_id == current_user.practice_id,
        User.is_active == is_active
    ).order_by(User.role, User.last_name)
    
    result = await db.execute(stmt)
    return result.scalars().all()

@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_staff(
    request: Request,
    staff_data: dict, # Simplified for demo, should use schema
    current_user: User = Depends(require_role(UserRole.OWNER, UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
    _csrf: bool = Depends(verify_csrf),
) -> Any:
    """
    Add a new staff member to the practice
    """
    # Check if email exists
    email = staff_data.get("email")
    stmt = select(User).where(User.email == email)
    result = await db.execute(stmt)
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this email already exists"
        )

    # Initial temporary password (staff should change on first login)
    password = staff_data.get("password", "CoreDent123!")
    is_valid, msg = validate_password_strength(password)
    if not is_valid:
        raise HTTPException(status_code=400, detail=msg)

    new_staff = User(
        email=email,
        password_hash=get_password_hash(password),
        first_name=staff_data.get("first_name"),
        last_name=staff_data.get("last_name"),
        role=staff_data.get("role", UserRole.FRONT_DESK),
        practice_id=current_user.practice_id,
        is_active=True
    )
    
    db.add(new_staff)
    await db.commit()
    await db.refresh(new_staff)

    # HIPAA Audit: Tracking account provision
    await log_audit_event(
        db, current_user, "staff_created", "user", new_staff.id, request
    )
    await db.commit()
    
    return new_staff

@router.put("/{user_id}", response_model=UserResponse)
async def update_staff(
    request: Request,
    user_id: UUID,
    staff_data: dict,
    current_user: User = Depends(require_role(UserRole.OWNER, UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
    _csrf: bool = Depends(verify_csrf),
) -> Any:
    """
    Update staff member details
    """
    stmt = select(User).where(
        User.id == user_id,
        User.practice_id == current_user.practice_id
    )
    result = await db.execute(stmt)
    staff = result.scalar_one_or_none()
    
    if not staff:
        raise HTTPException(status_code=404, detail="Staff member not found")

    # SECURITY: Only OWNER can promote/demote roles
    if "role" in staff_data and current_user.role != UserRole.OWNER:
         raise HTTPException(
             status_code=403, 
             detail="Only practice owners can modify staff roles"
         )

    for field, value in staff_data.items():
        if field == "password":
             staff.password_hash = get_password_hash(value)
             staff.password_changed_at = datetime.now(timezone.utc)
        else:
             setattr(staff, field, value)
    
    await db.commit()
    await db.refresh(staff)

    # HIPAA Audit
    await log_audit_event(
        db, current_user, "staff_updated", "user", staff.id, request
    )
    await db.commit()
    
    return staff

@router.delete("/{user_id}")
async def inactivate_staff(
    request: Request,
    user_id: UUID,
    current_user: User = Depends(require_role(UserRole.OWNER, UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
    _csrf: bool = Depends(verify_csrf),
) -> Any:
    """
    Inactivate a staff member (Soft Delete)
    """
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="You cannot inactivate your own account")

    stmt = select(User).where(
        User.id == user_id,
        User.practice_id == current_user.practice_id
    )
    result = await db.execute(stmt)
    staff = result.scalar_one_or_none()
    
    if not staff:
        raise HTTPException(status_code=404, detail="Staff member not found")

    # Expert Hardening: Only an OWNER can inactivate an account with OWNER role
    # This prevents an ADMIN from locking out a practice OWNER.
    if staff.role == UserRole.OWNER and current_user.role != UserRole.OWNER:
        raise HTTPException(
            status_code=403, 
            detail="Insufficient permissions to inactivate a practice owner"
        )

    staff.is_active = False
    
    # Expert Hardening: Terminate all active sessions IMMEDIATELY upon inactivation
    # We use UserSession from app.models.audit
    from app.models.audit import Session as UserSession
    await db.execute(
        update(UserSession)
        .where(UserSession.user_id == user_id)
        .values(expires_at=datetime.now(timezone.utc) - timedelta(seconds=1))
    )
    
    await db.commit()

    # HIPAA Audit
    await log_audit_event(
        db, current_user, "staff_inactivated", "user", staff.id, request
    )
    await db.commit()
    
    return {"message": "Staff member inactivated successfully"}
