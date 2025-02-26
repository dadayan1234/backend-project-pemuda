from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime, timedelta
from core.database import get_db, admin_required
from core.security import verify_token
from ..models.events import Event, Attendance
from ..models.user import User
from ..schemas.events import (
    EventCreate, EventUpdate, EventResponse,
    AttendanceCreate, AttendanceUpdate, AttendanceResponse, EventSearch
)
from ..models.notification import Notification

router = APIRouter()

async def create_notification(db: Session, user_id: int, title: str, content: str):
    notification = Notification(
        user_id=user_id,
        title=title,
        content=content
    )
    db.add(notification)
    db.commit()
    
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

    # Send notification to all members
    # members = db.query(User).filter(User.role == "Member").all()
    # for member in members:
    background_tasks.add_task(
        create_notification,
        db=db,
        title=f"New Event: {event.title}",
        content=f"A new event has been scheduled for {event.date}"
    )

    return db_event

@router.get("/", response_model=List[EventResponse])
async def get_events(
    skip: int = 0,
    limit: int = 10,
    current_user: User = Depends(verify_token),
    db: Session = Depends(get_db)
):
    return (
        db.query(Event)
        .order_by(Event.date.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    
@router.get("/", response_model=List[EventSearch])
async def search_events(
    title: str = None,
    description: str = None,
    date: datetime = None,
    time: timedelta = None,
    location: str = None,
    db: Session = Depends(get_db)
):
    query = db.query(Event)
    if title:
        query = query.filter(Event.title.ilike(f"%{title}%"))
    if description:
        query = query.filter(Event.description.ilike(f"%{description}%"))
    if date:
        query = query.filter(Event.date == date)
    if time:
        query = query.filter(Event.time == time)
    if location:
        query = query.filter(Event.location.ilike(f"%{location}%"))
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

    db.delete(event)
    db.commit()
    return {"message": "Event deleted"}

@router.post("/{event_id}/attendance", response_model=List[AttendanceResponse])
@admin_required()
async def create_attendance(
    event_id: int,
    attendances: List[AttendanceCreate],
    current_user: User = Depends(verify_token),
    db: Session = Depends(get_db)
):
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    created_attendances = []
    for attendance in attendances:
        db_attendance = Attendance(
            event_id=event_id,
            **attendance.dict()
        )
        db.add(db_attendance)
        created_attendances.append(db_attendance)

    db.commit()
    return created_attendances

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