from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from ..models.minutes import MeetingMinutes
from ..models.events import Event  # Import the Event model
from ..schemas.minutes import MeetingMinutesBase, MeetingMinutesUpdate, MeetingMinutesResponse
from core.database import get_db, admin_required
from core.security import verify_token  # Sesuaikan dengan sistem autentikasi Anda
from .notification_service import send_notification

router = APIRouter()

# ✅ Create Meeting Minutes
@router.post("/", response_model=MeetingMinutesResponse)
@admin_required()
async def create_meeting_minutes(
    meeting_minutes: MeetingMinutesBase,
    background_tasks: BackgroundTasks, # Tambahkan ini
    current_user: int = Depends(verify_token),
    db: Session = Depends(get_db)
):
    # Validasi event sudah ada
    event = db.query(Event).filter(Event.id == meeting_minutes.event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    new_minutes = MeetingMinutes(**meeting_minutes.dict())
    db.add(new_minutes)
    db.commit()
    db.refresh(new_minutes)

    # --- Logika Notifikasi Dimulai ---
    # Kirim notifikasi ke pengguna yang membuat event
    if event.created_by:
        notification_title = f"Notulensi Ditambahkan: {event.title}"
        notification_content = f"Sebuah notulensi baru telah ditambahkan untuk acara '{event.title}'."
        
        background_tasks.add_task(
            send_notification,
            db=db,
            user_id=event.created_by,
            title=notification_title,
            content=notification_content
        )
    # --- Logika Notifikasi Selesai ---

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
    background_tasks: BackgroundTasks, # Tambahkan ini
    db: Session = Depends(get_db),
    current_user: int = Depends(verify_token)
):
    meeting = db.query(MeetingMinutes).filter(MeetingMinutes.id == minutes_id).first()
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting minutes not found")

    # Validasi event baru jika event_id diubah
    if update_data.event_id and update_data.event_id != meeting.event_id:
        event = db.query(Event).filter(Event.id == update_data.event_id).first()
        if not event:
            raise HTTPException(status_code=404, detail="Event not found")

    for key, value in update_data.dict(exclude_unset=True).items():
        setattr(meeting, key, value)

    db.commit()
    db.refresh(meeting)

    # --- Logika Notifikasi Dimulai ---
    # Dapatkan data event terbaru untuk notifikasi
    final_event = db.query(Event).filter(Event.id == meeting.event_id).first()
    if final_event and final_event.created_by:
        notification_title = f"Notulensi Diperbarui: {final_event.title}"
        notification_content = f"Notulensi untuk acara '{final_event.title}' telah diperbarui."
        
        background_tasks.add_task(
            send_notification,
            db=db,
            user_id=final_event.created_by,
            title=notification_title,
            content=notification_content
        )
    # --- Logika Notifikasi Selesai ---

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