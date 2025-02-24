from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from functools import wraps
from fastapi import HTTPException

SQLALCHEMY_DATABASE_URL = "mysql+pymysql://root:@localhost/project_pemuda"

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def admin_required():
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            current_user = kwargs.get('current_user')
            if not current_user or current_user.role != "Admin":
                raise HTTPException(
                    status_code=403,
                    detail="Admin access required"
                )
            return await func(*args, **kwargs)
        return wrapper
    return decorator