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
import os
from dotenv import load_dotenv
import firebase_admin
from firebase_admin import credentials
from firebase_admin import initialize_app
from .notification_service import send_notification

load_dotenv()

# Ambil kredensial dari variabel environment
firebase_cred = {
    "type": "service_account",
    "project_id": os.getenv("FIREBASE_PROJECT_ID"),
    "private_key_id": os.getenv("FIREBASE_PRIVATE_KEY_ID"),
    "private_key": os.getenv("FIREBASE_PRIVATE_KEY").replace("\\n", "\n"),
    "client_email": os.getenv("FIREBASE_CLIENT_EMAIL"),
    "client_id": os.getenv("FIREBASE_CLIENT_ID"),
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/firebase-adminsdk-fbsvc%40opn-2da62.iam.gserviceaccount.com",
}

if not firebase_admin._apps:
    cred = credentials.Certificate(firebase_cred)
    initialize_app(cred)

router = APIRouter()

# === Fungsi reusable: Simpan dan kirim notifikasi ===

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
