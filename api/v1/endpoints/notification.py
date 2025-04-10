# routers/notifications.py

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
import json

from pyfcm import FCMNotification

from core.security import verify_token
from core.database import get_db
from ..models.notification import Notification
from ..models.user import User
from ..schemas.notification import NotificationResponse, NotificationCreate

router = APIRouter()

# 🔑 FCM Server Key (ambil dari Firebase Console)
FCM_SERVER_KEY = "ISI_DENGAN_FIREBASE_SERVER_KEY_MU"
fcm = FCMNotification(api_key=FCM_SERVER_KEY)

# --- Kirim Notifikasi dan Simpan ke DB
async def create_notification_db(db: Session, title: str, content: str, user_id: int):
    notification = Notification(
        title=title,
        content=content,
        user_id=user_id,
        created_at=datetime.now()
    )
    db.add(notification)
    db.commit()
    db.refresh(notification)

    # Ambil FCM token
    user = db.query(User).filter(User.id == user_id).first()
    if user and user.fcm_token:
        try:
            result = fcm.notify_single_device(
                registration_id=user.fcm_token,
                data_message={
                    "id": notification.id,
                    "title": notification.title,
                    "content": notification.content,
                    "created_at": notification.created_at.isoformat(),
                    "is_read": notification.is_read
                },
                notification={
                    "title": title,
                    "body": content
                }
            )
            print(f"[FCM] Notification sent to user {user_id}: {result}")
        except Exception as e:
            print(f"[FCM] Failed to send FCM to user {user_id}: {e}")
    else:
        print(f"[FCM] No FCM token for user {user_id}, skipping push.")

    return notification

# --- Endpoint Kirim Notifikasi
@router.post("/", response_model=NotificationResponse)
async def create_notification(
    payload: NotificationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(verify_token),
):
    print(f"[POST] Create notification: to user {payload.user_id}, from user {current_user.id}")
    return await create_notification_db(
        db=db,
        title=payload.title,
        content=payload.content,
        user_id=payload.user_id
    )

# --- Endpoint Ambil Semua Notifikasi User
@router.get("/", response_model=List[NotificationResponse])
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

# --- Tandai Sudah Dibaca
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

# --- Simpan FCM Token (buat dipanggil dari Android)
@router.post("/fcm-token")
async def save_fcm_token(
    token: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(verify_token),
):
    user = db.query(User).filter(User.id == current_user.id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.fcm_token = token
    db.commit()
    return {"message": "FCM token saved successfully"}
