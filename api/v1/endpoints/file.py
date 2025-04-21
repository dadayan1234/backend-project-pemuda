from fastapi import Depends, HTTPException, Request
from fastapi.responses import FileResponse
from fastapi.routing import APIRouter
import os
from api.v1.models.user import User
from core.security import verify_token
from core.database import get_db
from sqlalchemy.orm import Session

router = APIRouter()

@router.get("/{file_path:path}")
async def protected_file(
    request: Request,
    file_path: str,
    current_user: User = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """
    Endpoint untuk mengakses file yang diproteksi.
    Sekarang mendukung path dari database yang dimulai dengan '/uploads/'
    """
    # Normalisasi path (hilangkan leading slash jika ada)
    file_path = file_path.lstrip('/')
    
    # Jika path dari database dimulai dengan 'uploads/', kita sesuaikan
    if file_path.startswith('uploads/'):
        file_path = file_path[len('uploads/'):]
    
    physical_path = os.path.join("uploads", file_path)

    if not os.path.isfile(physical_path):
        raise HTTPException(status_code=404, detail="File not found")

    # Proteksi berdasarkan jenis file
    if file_path.startswith("users/"):
        # File user hanya bisa diakses oleh pemilik atau admin
        parts = file_path.split('/')
        if len(parts) >= 2 and parts[1].isdigit():
            user_id = int(parts[1])
            if current_user.id != user_id and current_user.role != "Admin":
                raise HTTPException(
                    status_code=403, 
                    detail="Forbidden: You can only access your own files"
                )

    elif file_path.startswith("events/"):
        if current_user.role != "Admin":
            raise HTTPException(
                status_code=403, 
                detail="Forbidden: Admin access required"
            )

    elif file_path.startswith("finances/"):
        if current_user.role != "Admin":
            raise HTTPException(
                status_code=403, 
                detail="Forbidden: Admin access required"
            )

    elif not file_path.startswith("news/"):
        if current_user.role != "Admin":
            raise HTTPException(
                status_code=403, 
                detail="Forbidden: Admin access required"
            )

    response = FileResponse(physical_path)
    response.headers["Cache-Control"] = "private, max-age=3600"
    return response