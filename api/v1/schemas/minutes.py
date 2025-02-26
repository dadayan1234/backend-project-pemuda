from pydantic import BaseModel, HttpUrl
from typing import Optional
from datetime import date, datetime

class MeetingMinutesBase(BaseModel):
    title: str
    description: Optional[str] = None
    date: date
    document_url: Optional[HttpUrl] = None
    event_id: int  # Foreign Key ke tabel events

class MeetingMinutesCreate(MeetingMinutesBase):
    created_by: int  # User ID yang membuat catatan rapat

class MeetingMinutesUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    date: Optional[datetime.date] = None
    document_url: Optional[HttpUrl] = None
    event_id: Optional[int] = None
    
    class Config:
        arbitrary_types_allowed = True

class MeetingMinutesResponse(MeetingMinutesBase):
    id: int
    created_by: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True
        arbitrary_types_allowed = True
