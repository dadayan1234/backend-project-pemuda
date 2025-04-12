from pydantic import BaseModel, Field
from datetime import datetime, time
from typing import List, Optional
from enum import Enum

class EventBase(BaseModel):
    title: str
    description: str
    date: datetime
    time: time
    location: str
    status: str = "akan datang"  # default status

class EventCreate(EventBase):
    pass

class EventUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    date: Optional[datetime] = None
    event_time: Optional[time] = None
    location: Optional[str] = None
    status: Optional[str] = "akan datang"

class EventPhotoResponse(BaseModel):
    id: int
    photo_url: str
    uploaded_at: datetime

    class Config:
        from_attributes = True

class EventResponse(EventBase):
    id: int
    created_by: int
    created_at: datetime
    updated_at: datetime
    photos: List[EventPhotoResponse] = Field(default_factory=list) 

    class Config:
        from_attributes = True

class AttendanceCreate(BaseModel):
    member_id: int
    status: str
    notes: Optional[str] = None

class AttendanceUpdate(BaseModel):
    status: str
    notes: Optional[str] = None

class AttendanceResponse(BaseModel):
    id: int
    member_id: int
    event_id: int
    status: str
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
        
class EventStatus(str, Enum):
    upcoming = "akan datang"
    completed = "selesai"
        
class EventSearch(BaseModel):
    id: int
    title: str
    description: str
    date: datetime
    time: time
    location: str
    status: EventStatus

    class Config:
        from_attributes = True

