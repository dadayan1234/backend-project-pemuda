from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from core.security import verify_token
from core.database import get_db
from ..models.notification import Notification
from ..models.user import User
from ..schemas.notification import NotificationResponse, NotificationCreate
from typing import Dict
import asyncio
import json

router = APIRouter()

# In-memory queue untuk masing-masing user
notification_queues: Dict[int, asyncio.Queue] = {}

# Generator SSE untuk setiap client
async def notification_event_generator(user_id: int):
    queue = asyncio.Queue()
    notification_queues[user_id] = queue
    try:
        while True:
            data = await queue.get()
            yield f"data: {data}\n\n"
    except asyncio.CancelledError:
        # Hapus queue jika client disconnect
        notification_queues.pop(user_id, None)

# Endpoint SSE - real-time stream
@router.get("/sse")
async def stream_notifications(
    request: Request,
    current_user: User = Depends(verify_token)
):
    return StreamingResponse(
        notification_event_generator(current_user.id),
        media_type="text/event-stream"
    )

# Endpoint untuk mengambil semua notifikasi user
@router.get("/", response_model=list[NotificationResponse])
async def get_notifications(
    current_user: User = Depends(verify_token),
    db: Session = Depends(get_db)
):
    return (
        db.query(Notification)
        .filter(Notification.user_id == current_user.id)
        .order_by(Notification.created_at.desc())
        .all()
    )

# Endpoint untuk menandai notifikasi sudah dibaca
@router.post("/{notification_id}/read", response_model=NotificationResponse)
async def mark_notification_as_read(
    notification_id: int,
    current_user: User = Depends(verify_token),
    db: Session = Depends(get_db)
):
    notification = db.query(Notification).filter(
        Notification.id == notification_id,
        Notification.user_id == current_user.id
    ).first()

    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")

    notification.is_read = True
    db.commit()
    db.refresh(notification)

    return notification

# Endpoint untuk membuat/push notifikasi baru ke user tertentu
@router.post("/", response_model=NotificationResponse)
async def create_notification(
    payload: NotificationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(verify_token),
):
    notification = Notification(
        title=payload.title,
        content=payload.content,
        user_id=payload.user_id
    )
    db.add(notification)
    db.commit()
    db.refresh(notification)

    if queue := notification_queues.get(payload.user_id):
        data = json.dumps({
            "id": notification.id,
            "title": notification.title,
            "content": notification.content,
            "created_at": notification.created_at.isoformat() if hasattr(notification.created_at, "isoformat") else str(notification.created_at),
            "is_read": notification.is_read
        })
        await queue.put(data)

    return notification
