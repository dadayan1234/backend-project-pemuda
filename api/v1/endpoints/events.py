from datetime import timezone
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from typing import List, Optional
from datetime import datetime, timedelta
from core.database import get_db, admin_required
from core.security import verify_token
from ..models.events import Event, Attendance
from ..models.user import User
from ..schemas.events import (
    EventCreate, EventStatus, EventUpdate, EventResponse,
    AttendanceCreate, AttendanceUpdate, AttendanceResponse, EventSearch
)
from ..models.notification import Notification
from ..models.events import EventPhoto  # Model yang menyimpan foto event
from core.utils.file_handler import FileHandler  # Fungsi untuk menghapus file
from .notification_service import send_notification

router = APIRouter()

@router.post("/", response_model=EventResponse)
@admin_required()
async def create_event(
    event: EventCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(verify_token),
    db: Session = Depends(get_db)
):
    db_event = Event(**event.dict(), created_by=current_user.id)
    db.add(db_event)
    db.commit()
    db.refresh(db_event)

    # Notifikasi ke semua member
    members = db.query(User).filter(User.role == "Member").all()
    for member in members:
        background_tasks.add_task(
            send_notification,
            db=db,
            user_id=member.id,
            title=f"New Event: {event.title}",
            content=f"A new event has been scheduled for {event.date}",
            user_id=member.id
        )

    return db_event

@router.get("/", response_model=List[EventResponse])
async def get_events(
    skip: int = 0,
    limit: int = 10,
    current_user: User = Depends(verify_token),
    db: Session = Depends(get_db)
):  # sourcery skip: inline-immediately-returned-variable
    events = (db.query(Event)
        .order_by(Event.date.desc())
        .offset(skip)
        .limit(limit)
        .all())
    return events
@router.get("/search", response_model=List[EventSearch])
async def search_events(
    keyword: Optional[str] = None,
    date: Optional[datetime] = None,
    time: Optional[timedelta] = None,
    status: Optional[EventStatus] = None,
    db: Session = Depends(get_db)
):
    query = db.query(Event)

    # 🔍 Keyword search
    if keyword:
        search_pattern = f"%{keyword}%"
        query = query.filter(
            or_(
                Event.title.ilike(search_pattern),
                Event.description.ilike(search_pattern),
                Event.location.ilike(search_pattern)
            )
        )

    # 📅 Filter berdasarkan tanggal tertentu
    if date:
        query = query.filter(Event.date == date)
    else:
        # ✅ Default: satu bulan terakhir
        one_month_ago = datetime.now(timezone.utc) - timedelta(days=30)
        query = query.filter(Event.date >= one_month_ago)

    # ⏰ Filter waktu (optional)
    if time:
        query = query.filter(Event.time == time)

    # 📌 Filter berdasarkan status
    if status:
        query = query.filter(Event.status == status.value)

    query = query.order_by(Event.date.asc())

    return query.all()

@router.get("/{event_id}", response_model=EventResponse)
async def get_event(
    event_id: int,
    current_user: User = Depends(verify_token),
    db: Session = Depends(get_db)
):
    if event := db.query(Event).filter(Event.id == event_id).first():
        return event
    else:
        raise HTTPException(status_code=404, detail="Event not found")

@router.put("/{event_id}", response_model=EventResponse)
@admin_required()
async def update_event(
    event_id: int,
    event_update: EventUpdate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(verify_token),
    db: Session = Depends(get_db)
):
    db_event = db.query(Event).filter(Event.id == event_id).first()
    if not db_event:
        raise HTTPException(status_code=404, detail="Event not found")

    for field, value in event_update.dict(exclude_unset=True).items():
        setattr(db_event, field, value)

    db.commit()
    db.refresh(db_event)

    # Kirim notifikasi jika tanggal diubah
    if event_update.date:
        members = db.query(User).filter(User.role == "Member").all()
        for member in members:
            background_tasks.add_task(
                send_notification,
                db=db,
                user_id=member.id,
                title=f"Event Rescheduled: {db_event.title}",
                content=f"The event has been moved to {db_event.date}",
                user_id=member.id
            )

    return db_event

@router.delete("/{event_id}")
@admin_required()
async def delete_event(
    event_id: int,
    current_user: User = Depends(verify_token),
    db: Session = Depends(get_db)
):
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    # Ambil semua foto terkait event
    photos = db.query(EventPhoto).filter(EventPhoto.event_id == event_id).all()

    # Hapus file dari penyimpanan
    for photo in photos:
        file_handler = FileHandler()
        file_handler.delete_image(photo.photo_url) # Pastikan delete_image menangani lokasi file dengan benar
        db.delete(photo)  # Hapus referensi di database

    db.commit()  # Commit setelah menghapus semua foto

    # Hapus event setelah semua foto dihapus
    db.delete(event)
    db.commit()

    return {"message": "Event and associated photos deleted"}

@router.post("/{event_id}/attendance", response_model=List[AttendanceResponse])
@admin_required()
async def create_or_update_attendance(
    event_id: int,
    attendances: List[AttendanceCreate],
    current_user: User = Depends(verify_token),
    db: Session = Depends(get_db)
):
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    updated_attendances = []

    for attendance in attendances:
        if (
            existing_attendance := db.query(Attendance)
            .filter(
                Attendance.event_id == event_id,
                Attendance.member_id == attendance.member_id,
            )
            .first()
        ):
            # Jika sudah ada, update (PUT)
            for field, value in attendance.dict(exclude_unset=True).items():
                setattr(existing_attendance, field, value)
            db.commit()
            db.refresh(existing_attendance)
            updated_attendances.append(existing_attendance)
        else:
            # Jika belum ada, tambahkan baru (POST)
            new_attendance = Attendance(
                event_id=event_id,
                **attendance.dict()
            )
            db.add(new_attendance)
            db.commit()
            db.refresh(new_attendance)
            updated_attendances.append(new_attendance)

    return updated_attendances

@router.put("/{event_id}/attendance/{member_id}", response_model=AttendanceResponse)
@admin_required()
async def update_attendance(
    event_id: int,
    member_id: int,
    attendance: AttendanceUpdate,
    current_user: User = Depends(verify_token),
    db: Session = Depends(get_db)
):
    db_attendance = db.query(Attendance)\
        .filter(
            Attendance.event_id == event_id,
            Attendance.member_id == member_id
        ).first()
    
    if not db_attendance:
        raise HTTPException(status_code=404, detail="Attendance record not found")

    for field, value in attendance.dict(exclude_unset=True).items():
        setattr(db_attendance, field, value)

    db.commit()
    db.refresh(db_attendance)
    return db_attendance

@router.get("/{event_id}/attendance", response_model=List[AttendanceResponse])
async def get_attendance(
    event_id: int,
    current_user: User = Depends(verify_token),
    db: Session = Depends(get_db)
):
    return db.query(Attendance).filter(Attendance.event_id == event_id).all()
