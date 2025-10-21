from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from core.security import create_access_token, verify_token
from core.database import SessionLocal, admin_required, get_db
from ..schemas.user import UserCreate, UserCreateWithRole, UserOut
from ..models.user import User
from passlib.context import CryptContext
import re

router = APIRouter()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ======================
# 🔐 Password Utilities
# ======================
def get_password_hash(password):
    return pwd_context.hash(password)

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


# ======================
# 👑 Admin Register
# ======================
@router.post("/admin/register", summary="Register user with custom role", tags=["Admin Only"])
# @admin_required()
async def admin_register(user: UserCreateWithRole, db: Session = Depends(get_db)):
    if db.query(User).filter(User.username == user.username).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )

    hashed_password = get_password_hash(user.password)

    new_user = User(
        username=user.username,
        password=hashed_password,
        role=user.role
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"message": f"User with role '{user.role}' registered successfully"}


# ======================
# 🙋 Public Register
# ======================
@router.post("/register", summary="Public register - always member")
async def public_register(user: UserCreate, db: Session = Depends(get_db)):

    # 🔎 Username validation
    if len(user.username) < 3:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username must be at least 3 characters long."
        )

    if db.query(User).filter(User.username == user.username).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username is already taken. Please choose another one."
        )

    # 🔒 Password validation
    if len(user.password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 8 characters long."
        )

    if not re.search(r"[A-Z]", user.password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must contain at least one uppercase letter."
        )

    if not re.search(r"[a-z]", user.password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must contain at least one lowercase letter."
        )

    if not re.search(r"\d", user.password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must contain at least one number."
        )

    # ✅ Create user
    hashed_password = get_password_hash(user.password)

    new_user = User(
        username=user.username,
        password=hashed_password,
        role="Member"
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"message": "User registered successfully."}


# ======================
# 🔑 Login
# ======================
@router.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    db = SessionLocal()
    user = db.query(User).filter(User.username == form_data.username).first()

    # ❌ Username not found
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid username or password."
        )

    # ❌ Incorrect password
    if not verify_password(form_data.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid username or password."
        )

    # ✅ Create access token
    try:
        access_token = create_access_token(data={"sub": user.username})
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Token generation failed: {str(e)}"
        )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "message": "Login successful."
    }


# ======================
# 👤 Current User
# ======================
@router.get("/me", response_model=UserOut)
async def read_users_me(current_user: User = Depends(verify_token)):
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token."
        )
    return current_user
