from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional

class NewsPhotoResponse(BaseModel):
    id: int
    photos_url: str
    uploaded_at: datetime

    class Config:
        from_attributes = True

class NewsBase(BaseModel):
    title: str
    description: str
    date: datetime

class NewsCreate(NewsBase):
    photos_url: Optional[List[str]] = []

class News(NewsBase):
    id: int
    created_by: int
    created_at: datetime
    updated_at: datetime
    photos_url: List[NewsPhotoResponse] = []

    class Config:
        from_attributes = True
