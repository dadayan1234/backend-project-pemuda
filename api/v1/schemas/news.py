from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional

class NewsPhotoResponse(BaseModel):
    id: int
    photo_url: str
    uploaded_at: datetime

class NewsBase(BaseModel):
    title: str
    description: str
    date: datetime
    is_published: bool = True

class NewsCreate(NewsBase):
    pass

class NewsUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    date: Optional[datetime] = None
    is_published: Optional[bool] = None

class NewsResponse(NewsBase):
    id: int
    created_by: int
    created_at: datetime
    updated_at: datetime
    photos: List[NewsPhotoResponse] = []