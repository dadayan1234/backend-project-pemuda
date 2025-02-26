from pydantic import BaseModel, HttpUrl
from typing import Optional
from datetime import date, datetime

class MeetingMinutesBase(BaseModel):
    title: str
    description: Optional[str] = None
    date: date
    document_url: Optional[HttpUrl] = None

class MeetingMinutesCreate(MeetingMinutesBase):
    created_by: int  # User ID yang membuat catatan rapat

class MeetingMinutesUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    date: Optional[date] = None # type: ignore
    document_url: Optional[HttpUrl] = None

class MeetingMinutesResponse(MeetingMinutesBase):
    id: int
    created_by: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True
