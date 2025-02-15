from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional
from .user import User

class NewsBase(BaseModel):
    title: str
    description: str
    date: datetime
    photo_url: Optional[str] = None

class NewsCreate(NewsBase):
    pass

class News(NewsBase):
    id: int
    created_by: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True