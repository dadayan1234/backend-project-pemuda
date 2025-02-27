from pydantic import BaseModel, Field
from datetime import datetime, time
from typing import List, Optional

class EventBase(BaseModel):
    title: str
    description: str
    date: datetime
    time: time
    location: str

class EventCreate(EventBase):
    pass

class EventUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    date: Optional[datetime] = None
    time: Optional[time] = None # type: ignore
    location: Optional[str] = None

class EventPhotoResponse(BaseModel):
    id: int
    photo_url: str
    uploaded_at: datetime

    class Config:
        orm_mode = True

class EventResponse(EventBase):
    id: int
    created_by: int
    created_at: datetime
    updated_at: datetime
    photos: List[EventPhotoResponse] = Field(default_factory=list) 

    class Config:
        orm_mode = True

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
        orm_mode = True
        
class EventSearch(BaseModel):
    title: str
    description: str
    date: datetime
    