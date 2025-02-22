from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class UserBase(BaseModel):
    username: str
    
class UserCreate(UserBase):
    password: str
    role: str = "Member"

class UserLogin(UserBase):
    password: str

class MemberCreate(BaseModel):
    full_name: str
    birth_date: datetime
    division: str
    address: str
    position: str

class MemberUpdate(BaseModel):
    full_name: Optional[str] = None
    division: Optional[str] = None
    address: Optional[str] = None
    position: Optional[str] = None

class MemberResponse(BaseModel):
    id: int
    full_name: str
    division: str
    position: str
    
    class Config:
        orm_mode = True

class User(UserBase):
    id: int
    role: str
    member_info: Optional[MemberResponse] = None
    
    class Config:
        orm_mode = True