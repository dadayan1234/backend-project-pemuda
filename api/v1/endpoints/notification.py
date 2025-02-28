from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from core.security import verify_token
from core.database import get_db
from ..models.notification import Notification
from ..models.user import User

router = APIRouter()

async def create_notification(db: Session, title: str, content: str):
    notification = Notification(
        title=title,
        content=content
    )
    db.add(notification)
    db.commit()

@router.get("/")
async def get_notifications(
    current_user: User = Depends(verify_token),
    db: Session = Depends(get_db)
):
    return (
        db.query(Notification)
        .order_by(Notification.created_at.desc())
        .all()
    )

@router.post("/{notification_id}/read")
async def mark_notification_as_read(
    notification_id: int,
    current_user: User = Depends(verify_token),
    db: Session = Depends(get_db)
):
    notification = db.query(Notification)\
        .filter(
            Notification.id == notification_id,
        ).first()
    
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
        
    # notification.is_read = True
    db.commit()
    return {"status": "success"}