from pydantic import BaseModel, HttpUrl
from typing import Optional
from datetime import date, datetime

from sqlalchemy import Date

class MeetingMinutesBase(BaseModel):
    title: str
    description: Optional[str] = None
    date: date
    document_url: Optional[HttpUrl] = None
    event_id: int  # Foreign Key ke tabel events

# class MeetingMinutesCreate(MeetingMinutesBase):
#     created_by: int  # User ID yang membuat catatan rapat

class MeetingMinutesUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    date: Optional[Date] = None
    document_url: Optional[HttpUrl] = None
    event_id: Optional[int] = None
    
    class Config:
        arbitrary_types_allowed = True
        schema_extra = {
            "example": {
                "title": "Judul Notulensi yang Diperbarui",
                "description": "Deskripsi baru untuk notulensi rapat.",
                "date": "2025-06-24",
                "document_url": "https://example.com/dokumen/notulensi_baru.pdf",
                "event_id": 1
            }
        }

class MeetingMinutesResponse(MeetingMinutesBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
        arbitrary_types_allowed = True
