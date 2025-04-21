from pydantic import BaseModel, EmailStr, model_validator
from datetime import date, datetime
from typing import Literal, Optional, ForwardRef


class UserBase(BaseModel):
    username: str

class UserCreate(UserBase):
    password: str
    
class UserCreateWithRole(BaseModel):
    username: str
    password: str
    role: Literal["Member", "Admin"]  # atau pakai Enum kalau kamu sudah define role

class UserLogin(UserBase):
    password: str

class MemberCreate(BaseModel):
    full_name: str
    email: EmailStr
    phone_number: str
    birth_place: str
    birth_date: datetime
    division: str
    address: str
    photo_url: str

class MemberUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone_number: Optional[str] = None
    division: Optional[str] = None
    birth_place: Optional[str] = None
    birth_date: datetime
    address: Optional[str] = None
    photo_url: Optional[str] = None

# Forward declaration to handle circular reference
MemberResponse = ForwardRef('MemberResponse')

class MemberResponseBase(BaseModel):
    id: int
    full_name: str
    birth_place: Optional[str]
    birth_date: date
    age: int  # Tambahkan field ini
    email: Optional[EmailStr]
    phone_number: Optional[str]
    division: Optional[str]
    address: Optional[str]
    photo_url: Optional[str]
    
    class Config:
        from_attributes = True

    @model_validator(mode='before')
    def calculate_age(cls, values):
        if 'birth_date' in values:
            today = date.today()
            birth_date = values['birth_date']
            if isinstance(birth_date, str):
                birth_date = datetime.strptime(birth_date, '%Y-%m-%d').date()
            age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
            values['age'] = age
        return values

class User(UserBase):
    id: int
    username: str
    role: str
    member_info: Optional[MemberResponse] = None
    
    class Config:
        from_attributes = True

# Now properly define MemberResponse
class MemberResponse(MemberResponseBase):
    pass

class UserOut(BaseModel):
    id: int
    username: str
    role: str
    created_at: datetime
    updated_at: datetime
    fcm_token: Optional[str] = None

    class Config:
        from_attributes = True

# Resolve the forward references
MemberResponse.model_rebuild()
User.model_rebuild()