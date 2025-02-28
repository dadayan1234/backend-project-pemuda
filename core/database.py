from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from functools import wraps
from fastapi import HTTPException

from dotenv import load_dotenv
import os

load_dotenv()

SQLALCHEMY_DATABASE_URL = os.getenv("SQLALCHEMY_DATABASE_URL")

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
    """
    The `admin_required` function is a decorator in Python that restricts access to functions based on
    the role of the current user.
    :return: The `admin_required` function is returning a decorator function that checks if the current
    user has the role of "Admin". If the user is not an admin, it raises an HTTPException with a status
    code of 403 and a detail message indicating that admin access is required. If the user is an admin,
    it calls the original function that the decorator is applied to.
    """
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