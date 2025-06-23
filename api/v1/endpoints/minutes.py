from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from ..models.minutes import MeetingMinutes
from ..models.events import Event  # Import the Event model
from ..schemas.minutes import MeetingMinutesBase, MeetingMinutesUpdate, MeetingMinutesResponse
from core.database import get_db, admin_required
from core.security import verify_token  # Sesuaikan dengan sistem autentikasi Anda

router = APIRouter()

# ✅ Create Meeting Minutes
@router.post("/", response_model=MeetingMinutesResponse)
@admin_required()
async def create_meeting_minutes(
    meeting_minutes: MeetingMinutesBase,
    current_user: int = Depends(verify_token),
    db: Session = Depends(get_db)
):
    # Pastikan event_id ada di tabel events
    event = db.query(Event).filter(Event.id == meeting_minutes.event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    new_minutes = MeetingMinutes(**meeting_minutes.dict())
    db.add(new_minutes)
    db.commit()
    db.refresh(new_minutes)
    return new_minutes

# ✅ Get All Meeting Minutes
@router.get("/", response_model=List[MeetingMinutesResponse])
async def get_meeting_minutes(db: Session = Depends(get_db),
                              current_user: int = Depends(verify_token)):
    return db.query(MeetingMinutes).all()

# ✅ Get Single Meeting Minutes by ID
@router.get("/{minutes_id}", response_model=MeetingMinutesResponse)
async def get_meeting_minutes_by_id(minutes_id: int, db: Session = Depends(get_db),
                                    current_user: int = Depends(verify_token)
                                    ):
    if (
        meeting := db.query(MeetingMinutes)
        .filter(MeetingMinutes.id == minutes_id)
        .first()
    ):
        return meeting
    else:
        raise HTTPException(status_code=404, detail="Meeting minutes not found")
    
# ✅ Get Meeting Minutes by Event ID
@router.get("/event/{event_id}", response_model=List[MeetingMinutesResponse])
async def get_meeting_minutes_by_event_id(
    event_id: int,
    db: Session = Depends(get_db),
    current_user: int = Depends(verify_token)
):
    minutes = db.query(MeetingMinutes).filter(MeetingMinutes.event_id == event_id).all()
    if not minutes:
        raise HTTPException(status_code=404, detail="No meeting minutes found for this event")
    return minutes


# ✅ Update Meeting Minutes
@router.put("/{minutes_id}", response_model=MeetingMinutesResponse)
@admin_required()
async def update_meeting_minutes(
    minutes_id: int,
    update_data: MeetingMinutesUpdate,
    db: Session = Depends(get_db),
    current_user: int = Depends(verify_token)
):
    meeting = db.query(MeetingMinutes).filter(MeetingMinutes.id == minutes_id).first()
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting minutes not found")

    # Pastikan event_id yang baru ada di tabel events jika diupdate
    if update_data.event_id:
        event = db.query(Event).filter(Event.id == update_data.event_id).first()
        if not event:
            raise HTTPException(status_code=404, detail="Event not found")

    for key, value in update_data.dict(exclude_unset=True).items():
        setattr(meeting, key, value)

    db.commit()
    db.refresh(meeting)
    return meeting

# ✅ Delete Meeting Minutes
@router.delete("/{minutes_id}")
@admin_required()
async def delete_meeting_minutes(minutes_id: int, db: Session = Depends(get_db),
                                 current_user: int = Depends(verify_token)
                                 ):
    meeting = db.query(MeetingMinutes).filter(MeetingMinutes.id == minutes_id).first()
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting minutes not found")

    db.delete(meeting)
    db.commit()
    return {"message": "Meeting minutes deleted successfully"}