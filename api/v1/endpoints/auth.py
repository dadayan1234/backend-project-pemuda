from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from core.security import create_access_token, verify_token
from core.database import SessionLocal, admin_required, get_db
from ..schemas.user import UserCreate, UserCreateWithRole, UserOut  # Relative import
from ..models.user import User  # Relative import
from passlib.context import CryptContext

router = APIRouter()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password):
    return pwd_context.hash(password)

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

@router.post("/admin/register", summary="Register user with custom role", tags=["Admin Only"])
# @admin_required()
async def admin_register(user: UserCreateWithRole, db: Session = Depends(get_db)):
    if db.query(User).filter(User.username == user.username).first():
        raise HTTPException(status_code=400, detail="Username already registered")

    hashed_password = get_password_hash(user.password)

    new_user = User(
        username=user.username,
        password=hashed_password,
        role=user.role  # 🟡 Bisa 'Admin' atau lainnya
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"message": f"User with role '{user.role}' registered successfully"}


@router.post("/register", summary="Public register - always member")
async def public_register(user: UserCreate):
    db = SessionLocal()
    if db.query(User).filter(User.username == user.username).first():
        raise HTTPException(status_code=400, detail="Username already registered")

    hashed_password = get_password_hash(user.password)

    new_user = User(
        username=user.username,
        password=hashed_password,
        role="Member"  # 🔒 Enforce member role
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"message": "User registered successfully"}


@router.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    db = SessionLocal()
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.password):
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=UserOut)
async def read_users_me(current_user: User = Depends(verify_token)):
    return current_user