from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class UserRegister(BaseModel):
    full_name: str
    email: str
    password: str

class UserLogin(BaseModel):
    email: str
    password: str

class EventCreate(BaseModel):
    title: str
    description: str
    event_date: datetime
    location: str

class FinanceCreate(BaseModel):
    amount: float
    description: str
    date: datetime
    category: str

class AttendanceCreate(BaseModel):
    event_id: int
    user_id: int
    status: str

class ScheduleCreate(BaseModel):
    title: str
    date: datetime
    description: str
    status: str

class NewsCreate(BaseModel):
    title: str
    description: str
    date: datetime

class OrganizationCreate(BaseModel):
    category: str
    details: str

class MinutesCreate(BaseModel):
    event_id: int
    content: str
