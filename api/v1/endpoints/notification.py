from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from firebase_admin import credentials, initialize_app, messaging
from pydantic import BaseModel
from core.security import verify_token
from core.database import get_db
from ..models.notification import Notification
from ..models.user import User
from ..schemas.notification import NotificationResponse, NotificationCreate, FCMTokenPayload

import firebase_admin
if not firebase_admin._apps:
    cred = credentials.Certificate("opn-2da62-firebase-adminsdk-fbsvc-f8fa7b5817.json")
    initialize_app(cred)

router = APIRouter()

# === Fungsi reusable: Simpan dan kirim notifikasi ===
async def send_notification(
    db: Session,
    user_id: int,
    title: str,
    content: str
) -> Notification:
    # Simpan ke DB
    notification = Notification(
        title=title,
        content=content,
        user_id=user_id
    )
    db.add(notification)
    db.commit()
    db.refresh(notification)

    # Kirim FCM jika token tersedia
    user = db.query(User).filter(User.id == user_id).first()
    if user and user.fcm_token:
        try:
            message = messaging.Message(
                notification=messaging.Notification(
                    title=title,
                    body=content
                ),
                token=user.fcm_token
            )
            response = messaging.send(message)
            print(f"[FCM] Notification sent: {response}")
        except Exception as e:
            print(f"[FCM] Error sending notification: {e}")
    else:
        print(f"[FCM] No FCM token available for user {user_id}")

    return notification

# --- POST: Manual trigger notifikasi
@router.post("/", response_model=NotificationResponse)
async def create_notification(
    payload: NotificationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(verify_token),
):
    print(f"[POST] Create notification: to user {payload.user_id}, from user {current_user.id}")
    return await send_notification(
        db=db,
        user_id=payload.user_id,
        title=payload.title,
        content=payload.content
    )

# --- GET: Semua notifikasi milik user
@router.get("/", response_model=List[NotificationResponse])
async def get_notifications(
    current_user: User = Depends(verify_token),
    db: Session = Depends(get_db)
):
    print(f"[GET] Fetch notifications for user {current_user.id}")
    return (
        db.query(Notification)
        .filter(Notification.user_id == current_user.id)
        .order_by(Notification.created_at.desc())
        .all()
    )

# --- POST: Tandai notifikasi terbaca (hapus dari DB)
@router.post("/{notification_id}/read", response_model=NotificationResponse)
async def mark_notification_as_read(
    notification_id: int,
    current_user: User = Depends(verify_token),
    db: Session = Depends(get_db)
):
    print(f"[POST] Mark as read & delete: user {current_user.id}, notif {notification_id}")
    notification = db.query(Notification).filter(
        Notification.id == notification_id,
        Notification.user_id == current_user.id
    ).first()

    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")

    db.delete(notification)
    db.commit()
    return notification

# --- POST: Simpan token FCM user
@router.post("/fcm-token")
def update_fcm_token(
    payload: FCMTokenPayload,
    db: Session = Depends(get_db),
    current_user: User = Depends(verify_token)
):
    user = db.query(User).filter(User.id == current_user.id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.fcm_token = payload.token
    db.commit()
    print(f"[FCM] Token updated for user {user.id}")
    return {"message": "FCM token updated"}
