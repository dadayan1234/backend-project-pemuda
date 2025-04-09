from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import Dict
import asyncio
import json
from core.security import verify_token
from core.database import get_db
from ..models.notification import Notification
from ..models.user import User
from ..schemas.notification import NotificationResponse, NotificationCreate

router = APIRouter()
notification_queues: Dict[int, asyncio.Queue] = {}

# --- SSE Generator
async def notification_event_generator(user_id: int, request: Request):
    queue = asyncio.Queue()
    notification_queues[user_id] = queue

    try:
        while True:
            if await request.is_disconnected():
                break

            try:
                data = await asyncio.wait_for(queue.get(), timeout=15.0)
                yield f"data: {data}\n\n"
            except asyncio.TimeoutError:
                # Optional: keep-alive message
                yield "data: {}\n\n"

    except asyncio.CancelledError:
        pass
    finally:
        notification_queues.pop(user_id, None)

# --- Endpoint SSE
@router.get("/sse")
async def stream_notifications(
    request: Request,
    current_user: User = Depends(verify_token)
):
    return StreamingResponse(
        notification_event_generator(current_user.id, request),
        media_type="text/event-stream"
    )

# --- Fungsi Reusable untuk buat dan push notifikasi
async def create_notification_db(db: Session, title: str, content: str, user_id: int):
    notification = Notification(
        title=title,
        content=content,
        user_id=user_id
    )
    db.add(notification)
    db.commit()
    db.refresh(notification)

    # Kirim ke client via SSE
    if queue := notification_queues.get(user_id):
        data = json.dumps({
            "id": notification.id,
            "title": notification.title,
            "content": notification.content,
            "created_at": notification.created_at.isoformat(),
            "is_read": notification.is_read
        })
        await queue.put(data)
        print(f"[SSE] Pushed to user {user_id}")

    return notification

# --- POST manual
@router.post("/", response_model=NotificationResponse)
async def create_notification(
    payload: NotificationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(verify_token),
):
    return await create_notification_db(
        db=db,
        title=payload.title,
        content=payload.content,
        user_id=payload.user_id
    )

# --- Get semua notifikasi
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

# --- Mark as read
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
