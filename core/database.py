from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from functools import wraps
from fastapi import HTTPException
from typing import Callable, Union, Coroutine, Any
import asyncio

from dotenv import load_dotenv
import os

load_dotenv()

SQLALCHEMY_DATABASE_URL = os.getenv("SQLALCHEMY_DATABASE_URL")

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    pool_size=20,         # Jumlah koneksi standar di pool (default: 5)
    max_overflow=50,      # Jumlah koneksi "sementara" tambahan (default: 10)
    pool_timeout=30       # Waktu (detik) menunggu koneksi sebelum error (default: 30)
)

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
    Decorator yang memeriksa apakah user memiliki role 'Admin'.
    Berfungsi untuk kedua fungsi synchronous dan asynchronous.
    The `admin_required` function is a decorator in Python that restricts access to functions based on
    the role of the current user.
    :return: The `admin_required` function is returning a decorator function that checks if the current
    user has the role of "Admin". If the user is not an admin, it raises an HTTPException with a status
    code of 403 and a detail message indicating that admin access is required. If the user is an admin,
    it calls the original function that the decorator is applied to.
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            current_user = kwargs.get('current_user')
            if not current_user or current_user.role != "Admin":
                raise HTTPException(
                    status_code=403,
                    detail="Admin access required"
                )
            if asyncio.iscoroutinefunction(func):
                return await func(*args, **kwargs)
            return func(*args, **kwargs)
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            current_user = kwargs.get('current_user')
            if not current_user or current_user.role != "Admin":
                raise HTTPException(
                    status_code=403,
                    detail="Admin access required"
                )
            return func(*args, **kwargs)
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    return decorator