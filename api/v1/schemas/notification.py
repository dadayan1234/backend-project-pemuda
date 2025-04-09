from pydantic import BaseModel
from datetime import datetime
from typing import Optional

# Base schema (bisa dipakai saat membuat notifikasi, kalau diperlukan)
class NotificationBase(BaseModel):
    title: str
    content: str
    
class NotificationCreate(NotificationBase):
    user_id: int  # Menentukan notifikasi ditujukan ke user mana

# Schema untuk response
class NotificationResponse(NotificationBase):
    id: int
    is_read: bool
    created_at: datetime

    class Config:
        orm_mode = True
