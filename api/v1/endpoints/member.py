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

