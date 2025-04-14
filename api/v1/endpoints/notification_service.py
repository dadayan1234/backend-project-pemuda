from sqlalchemy.orm import Session
from ..models.notification import Notification
from ..models.user import User
from firebase_admin import messaging

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