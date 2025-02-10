from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import SessionLocal
from datetime import timezone
from models import User
from schemas import UserRegister, UserLogin
import bcrypt
from config import JWT_SECRET, JWT_ALGORITHM, JWT_EXPIRATION
from datetime import datetime, timedelta
import jwt as pyjwt

router = APIRouter(prefix="/auth", tags=["Auth"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def generate_token(user_id: int):
    expiration = datetime.now(timezone.utc) + timedelta(seconds=JWT_EXPIRATION)
    payload = {"sub": user_id, "exp": expiration}
    return pyjwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

@router.post("/register")
def register(user_data: UserRegister, db: Session = Depends(get_db)):
    hashed_password = bcrypt.hashpw(user_data.password.encode("utf-8"), bcrypt.gensalt())
    user = User(full_name=user_data.full_name, email=user_data.email, password_hash=hashed_password)
    db.add(user)
    db.commit()
    return {"access_token": generate_token(user.id)}

@router.post("/login")
def login(user_data: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == user_data.email).first()
    if not user or not bcrypt.checkpw(user_data.password.encode("utf-8"), user.password_hash.encode("utf-8")):
        raise HTTPException(status_code=400, detail="Invalid credentials")
    return {"access_token": generate_token(user.id)}
