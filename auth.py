from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import SessionLocal
from datetime import timezone
from models import User
from schemas import UserLogin, UserRegister, TokenResponse
import bcrypt
import jwt
from config import JWT_SECRET, JWT_ALGORITHM, JWT_EXPIRATION
from datetime import datetime, timedelta

auth_router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@auth_router.post("/register", response_model=TokenResponse)
def register(user_data: UserRegister, db: Session = Depends(get_db)):
    hashed_password = bcrypt.hashpw(user_data.password.encode("utf-8"), bcrypt.gensalt())
    user = User(full_name=user_data.full_name, email=user_data.email, password_hash=hashed_password)
    db.add(user)
    db.commit()
    return {"access_token": generate_token(user.id, user.is_admin)}

@auth_router.post("/login", response_model=TokenResponse)
def login(user_data: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == user_data.email).first()
    if not user or not bcrypt.checkpw(user_data.password.encode("utf-8"), user.password_hash.encode("utf-8")):
        raise HTTPException(status_code=400, detail="Invalid credentials")
    return {"access_token": generate_token(user.id, user.is_admin)}

def generate_token(user_id: int, is_admin: bool):
    expiration = datetime.now(timezone.utc) + timedelta(seconds=JWT_EXPIRATION)
    payload = {"sub": user_id, "exp": expiration, "is_admin": is_admin}
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
