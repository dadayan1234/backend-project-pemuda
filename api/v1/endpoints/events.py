from datetime import timezone
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from typing import List, Optional
from datetime import datetime, timedelta
from core.database import get_db, admin_required
from core.security import verify_token
from ..models.events import Event, Attendance
from ..models.user import Member, User
from ..schemas.events import (
    EventCreate, EventStatus, EventUpdate, EventResponse,
    AttendanceCreate, AttendanceUpdate, AttendanceResponse, EventSearch, PaginatedEventResponse
)
from ..models.notification import Notification
from ..models.events import EventPhoto  # Model yang menyimpan foto event
from core.utils.file_handler import FileHandler  # Fungsi untuk menghapus file
from .notification_service import send_notification

import io
from fastapi.responses import StreamingResponse
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.units import inch

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
            user_id=member.id, # type: ignore
            title=f"Acara Baru : {event.title}",
            content=f"Acara Baru Dijadwalkan pada {event.date}",
            # --- TAMBAHKAN PAYLOAD DATA ---
            data={"type": "event", "id": str(db_event.id)}
        )

    return db_event

# @router.get("/", response_model=List[EventResponse])
# async def get_events(
#     skip: int = 0,
#     limit: int = 10,
#     current_user: User = Depends(verify_token),
#     db: Session = Depends(get_db)
# ):  # sourcery skip: inline-immediately-returned-variable
#     events = (db.query(Event)
#         .order_by(Event.date.desc())
#         .offset(skip)
#         .limit(limit)
#         .all())
#     return events
@router.get("/", response_model=PaginatedEventResponse)
async def get_events(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    current_user: User = Depends(verify_token),
    db: Session = Depends(get_db)
):
    total = db.query(Event).count()
    offset = (page - 1) * limit
    events = (db.query(Event)
              .order_by(Event.date.desc())
              .offset(offset)
              .limit(limit)
              .all())

    return {
        "data": events,
        "meta": {
            "page": page,
            "limit": limit,
            "total": total,
            "total_pages": (total + limit - 1) // limit  # pembulatan ke atas
        }
    }



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
                title=f"Acara Dijawalkan Ulang: {db_event.title}",
                content=f"Acara Dijadwalkan pada {db_event.date}",
                data={"type": "event", "id": str(db_event.id)}
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
        existing_attendance = (
            db.query(Attendance)
            .filter(
                Attendance.event_id == event_id,
                Attendance.member_id == attendance.member_id,
            )
            .first()
        )
        if existing_attendance:
            # Update jika sudah ada
            for field, value in attendance.dict(exclude_unset=True).items():
                setattr(existing_attendance, field, value)
            db.commit()
            db.refresh(existing_attendance)
            updated_attendances.append(existing_attendance)
        else:
            # Tambah baru jika belum ada
            new_attendance = Attendance(
                event_id=event_id,
                **attendance.dict()
            )
            db.add(new_attendance)
            db.commit()
            db.refresh(new_attendance)
            updated_attendances.append(new_attendance)

    # Bentuk response manual agar ada full_name
    response_data = []
    for att in updated_attendances:
        response_data.append({
            "id": att.id,
            "member_id": att.member_id,
            "event_id": att.event_id,
            "full_name": att.member.full_name if att.member else "",
            "status": att.status,
            "notes": att.notes,
            "created_at": att.created_at,
            "updated_at": att.updated_at
        })

    return response_data

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
    db: Session = Depends(get_db),
    current_user: User = Depends(verify_token)
):
    attendances = db.query(Attendance).join(Member).filter(Attendance.event_id == event_id).all()

    result = [
        AttendanceResponse(
            id=att.id,
            member_id=att.member_id,
            event_id=att.event_id,
            full_name=att.member.full_name,  # Ambil dari relasi
            status=att.status,
            notes=att.notes,
            created_at=att.created_at,
            updated_at=att.updated_at
        )
        for att in attendances
    ]

    return result

@router.get("/{event_id}/attendance/pdf", response_class=StreamingResponse)
async def download_attendance_pdf(
    event_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(verify_token)
):
    """
    Endpoint untuk mengunduh daftar hadir event dalam format PDF.
    """
    # 1. Ambil data event dari database
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    # 2. Ambil data kehadiran, urutkan berdasarkan nama untuk kerapian
    attendances = (
        db.query(Attendance)
        .join(Member)
        .filter(Attendance.event_id == event_id)
        .order_by(Member.full_name.asc())
        .all()
    )

    if not attendances:
        raise HTTPException(
            status_code=404, 
            detail="Belum ada data kehadiran untuk event ini."
        )

    # 3. Buat PDF di dalam memori
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=1*inch, bottomMargin=1*inch)
    
    elements = []
    styles = getSampleStyleSheet()

    # Tambahkan Judul Event dan Tanggal
    elements.append(Paragraph(f"Daftar Hadir Peserta", styles['Title']))
    elements.append(Spacer(1, 0.2*inch))
    elements.append(Paragraph(f"<b>Acara:</b> {event.title}", styles['Normal']))
    elements.append(Paragraph(f"<b>Tanggal:</b> {event.date.strftime('%d %B %Y')}", styles['Normal']))
    elements.append(Spacer(1, 0.4*inch))

    # 4. Siapkan data untuk tabel
    table_data = [['No.', 'Nama Peserta', 'Status', 'Keterangan']]
    table_data.extend([
        [
            str(i + 1),
            att.member.full_name,
            str(getattr(att, "status", None) or "N/A"),
            str(getattr(att, "notes", "") or "")
        ]
        for i, att in enumerate(attendances)
    ])
    # 5. Buat dan styling tabel
    table = Table(table_data, colWidths=[0.5*inch, 3*inch, 1.5*inch, 2*inch])
    
    style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4a4a4a')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f0f0f0')),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ])
    table.setStyle(style)
    
    elements.append(table)

    # Build PDF
    doc.build(elements)
    
    buffer.seek(0) # Pindahkan kursor ke awal buffer

    # 6. Kirim response sebagai file yang bisa diunduh
    safe_title = "".join(str(c) for c in event.title if str(c).isalnum() or c in (' ', '_')).rstrip()
    filename = f"daftar_hadir_{safe_title.replace(' ', '_').lower()}.pdf"

    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )