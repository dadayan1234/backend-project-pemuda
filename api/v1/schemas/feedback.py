from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class FeedbackBase(BaseModel):
    content: str

class FeedbackCreate(FeedbackBase):
    pass

class FeedbackUpdate(BaseModel):
    content: Optional[str] = None

class FeedbackResponse(FeedbackBase):
    id: int
    full_name: str
    member_id: int
    event_id: int
    created_at: datetime

    class Config:
        from_attributes = True
