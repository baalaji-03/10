from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import List
from backend.app.database import get_db
from backend.app.models import User, AuditLog
from backend.app.schemas import TokenResponse, UserCreate, UserUpdate, UserResponse
from backend.app.auth import hash_password, verify_password, create_access_token, get_current_user, require_roles

router = APIRouter(prefix="/api/auth", tags=["Authentication & Users"])

@router.post("/login", response_model=TokenResponse)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated. Contact administrator.",
        )
    
    access_token = create_access_token(data={"sub": user.username, "role": user.role, "user_id": user.id})

    # Log login action
    audit = AuditLog(user_id=user.id, username=user.username, action="USER_LOGIN", module="AUTH", details=f"User {user.username} logged in successfully")
    db.add(audit)
    db.commit()

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_id": user.id,
        "username": user.username,
        "full_name": user.full_name,
        "role": user.role
    }

@router.get("/me", response_model=UserResponse)
def get_current_user_profile(current_user: User = Depends(get_current_user)):
    return current_user

@router.get("/users", response_model=List[UserResponse])
def get_all_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["Admin"]))
):
    return db.query(User).order_by(User.id).all()

@router.post("/users", response_model=UserResponse)
def create_new_user(
    user_in: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["Admin"]))
):
    existing_user = db.query(User).filter(
        (User.username == user_in.username) | (User.email == user_in.email)
    ).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Username or Email already registered.")

    new_user = User(
        username=user_in.username,
        email=user_in.email,
        full_name=user_in.full_name,
        password_hash=hash_password(user_in.password),
        role=user_in.role,
        is_active=user_in.is_active
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@router.put("/users/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int,
    user_in: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["Admin"]))
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if user_in.email is not None:
        user.email = user_in.email
    if user_in.full_name is not None:
        user.full_name = user_in.full_name
    if user_in.role is not None:
        user.role = user_in.role
    if user_in.is_active is not None:
        user.is_active = user_in.is_active
    if user_in.password:
        user.password_hash = hash_password(user_in.password)

    db.commit()
    db.refresh(user)
    return user
