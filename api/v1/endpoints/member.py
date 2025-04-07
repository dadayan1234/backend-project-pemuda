from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Dict, List
from datetime import datetime, timedelta
from core.database import get_db, admin_required
from core.security import verify_token
from ..models.events import Event, Attendance
from ..models.user import Member
from ..schemas.user import *
from ..models.notification import Notification

router = APIRouter()

@router.get("/", response_model=Dict[str, List[MemberResponse]])
@admin_required()
async def get_members(
    current_user: User = Depends(verify_token),
    db: Session = Depends(get_db)
):
    members = db.query(Member).all()
    
    return {"members": [MemberResponse.model_validate(member.__dict__) for member in members]}



@router.post("/biodata", response_model=MemberResponse)
async def create_biodata(
    biodata: MemberCreate,
    current_user: User = Depends(verify_token),
    db: Session = Depends(get_db)
):
    if (
        existing_member := db.query(Member)
        .filter(Member.user_id == current_user.id)
        .first()
    ):
        raise HTTPException(status_code=400, detail="User already has biodata")

    # Buat entri baru di tabel Member
    new_member = Member(
        user_id=current_user.id,
        email=biodata.email,
        full_name=biodata.full_name,
        birth_date=biodata.birth_date,
        division=biodata.division,
        address=biodata.address,
        position=biodata.position
    )

    # Simpan ke database
    db.add(new_member)
    db.commit()
    db.refresh(new_member)

    # Kembalikan response
    return MemberResponse(
        id=new_member.id,
        full_name=new_member.full_name,
        division=new_member.division,
        position=new_member.position
    )

@router.put("/biodata/", response_model=MemberResponse)
async def update_biodata(
    biodata: MemberUpdate,
    current_user: User = Depends(verify_token),
    db: Session = Depends(get_db)
):
    # Cari member berdasarkan user_id
    member = db.query(Member).filter(Member.user_id == current_user.id).first()
    
    if not member:
        raise HTTPException(status_code=200, detail="Member not found")
    
    # Pastikan hanya pemilik biodata yang bisa mengedit atau admin
    if current_user.role != "Admin" and member.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to update this profile")
    
    # Update biodata
    for key, value in biodata.dict(exclude_unset=True).items():
        setattr(member, key, value)
    
    db.commit()
    db.refresh(member)
    
    return MemberResponse(
        id=member.id,
        full_name=member.full_name,
        division=member.division,
        position=member.position
    )

@router.delete("/user/{user_id}")
@admin_required()
async def delete_user(
    user_id: int,
    current_user: User = Depends(verify_token),
    db: Session = Depends(get_db)
):
    # Cari user berdasarkan ID
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Hapus user (akan otomatis menghapus data Member jika ada karena relasi)
    db.delete(user)
    db.commit()
    
    return {"message": "User deleted successfully"}
