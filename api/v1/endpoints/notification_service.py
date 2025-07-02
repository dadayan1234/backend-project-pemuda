from typing import Optional, Dict, List
from sqlalchemy.orm import Session
from ..models.notification import Notification
from ..models.user import User
from firebase_admin import messaging

async def send_notification(
    db: Session,
    user_id: int,
    title: str,
    content: str,
    data: Optional[Dict[str, str]] = None
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
            # 1. Buat payload data dasar dengan judul dan isi
            fcm_data_payload = {
                "title": title,
                "body": content
            }
            # 2. Jika ada data navigasi (tipe & id), tambahkan ke payload
            if data:
                fcm_data_payload.update(data)

            # 3. Buat pesan FCM menggunakan 'data', bukan 'notification'
            message = messaging.Message(
                data=fcm_data_payload,
                token=user.fcm_token,
                android=messaging.AndroidConfig(
                    priority="high"  # Meminta prioritas tinggi agar pop-up muncul
                ),
                apns=messaging.APNSConfig(
                    payload=messaging.APNSPayload(
                        aps=messaging.Aps(content_available=True)
                    )
                ),
            )
            # --- AKHIR PERUBAHAN ---

            response = messaging.send(message)
            print(f"[FCM] Notification sent with data: {response}")
        except Exception as e:
            print(f"[FCM] Error sending notification: {e}")
    else:
        print(f"[FCM] No FCM token available for user {user_id}")

    return notification