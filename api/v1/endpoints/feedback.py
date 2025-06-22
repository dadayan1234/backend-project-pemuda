from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from core.database import get_db, admin_required
from core.security import verify_token
from ..models.events import Event
from ..models.feedback import Feedback
from ..models.user import Member, User
from ..schemas.feedback import FeedbackCreate, FeedbackUpdate, FeedbackResponse

router = APIRouter()

@router.post("/event/{event_id}/feedback", response_model=FeedbackResponse)
async def create_feedback(
    event_id: int,
    feedback: FeedbackCreate,
    current_user: User = Depends(verify_token),
    db: Session = Depends(get_db)
):
    # Cek apakah event ada
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    # Cek apakah member dari user ini ada
    member = db.query(Member).filter(Member.user_id == current_user.id).first()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")

    # Simpan feedback
    new_feedback = Feedback(
        event_id=event_id,
        member_id=member.id,
        content=feedback.content
    )

    db.add(new_feedback)
    db.commit()
    db.refresh(new_feedback)

    # Bangun response secara manual agar sesuai dengan schema
    return FeedbackResponse(
        id=new_feedback.id,
        content=new_feedback.content,
        member_id=new_feedback.member_id,
        event_id=new_feedback.event_id,
        full_name=member.full_name,
        created_at=new_feedback.created_at
    )


@router.get("/event/{event_id}/feedback", response_model=List[FeedbackResponse])
async def get_feedbacks(
    event_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(verify_token)
):
    feedback = (db.query(Feedback)
                .join(Member)
                .filter(Feedback.event_id == event_id).all()
                
    )       
    result = [
        FeedbackResponse(
            id=getattr(att, "id", 0),
            content=getattr(att, "content", ""),
            member_id=getattr(att, "member_id", 0),
            event_id=getattr(att, "event_id", 0),
            full_name=getattr(att.member, "full_name", "") if hasattr(att, "member") else "",
            created_at=getattr(att, "created_at", None) or datetime.now()
        )
        for att in feedback
    ]
    return result

@router.get("/feedback/{feedback_id}", response_model=FeedbackResponse)
async def get_single_feedback(
    feedback_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(verify_token)
):
    feedback = (db.query(Feedback)
                .join(Member)
                .filter(Feedback.id == feedback_id).first()
    )

    if not feedback:
        raise HTTPException(status_code=404, detail="Feedback not found")

    return FeedbackResponse(
        id=getattr(feedback, "id", 0),
        content=getattr(feedback, "content", ""),
        member_id=getattr(feedback, "member_id", 0),
        event_id=getattr(feedback, "event_id", 0),
        full_name=getattr(feedback.member, "full_name", "") if hasattr(feedback, "member") else "",
        created_at=getattr(feedback, "created_at", None) or datetime.now()
    )

@router.put("/feedback/{feedback_id}", response_model=FeedbackResponse)
async def update_feedback(
    feedback_id: int,
    feedback_update: FeedbackUpdate,
    current_user: User = Depends(verify_token),
    db: Session = Depends(get_db)
):
    feedback = db.query(Feedback).filter(Feedback.id == feedback_id).first()
    if not feedback:
        raise HTTPException(status_code=404, detail="Feedback not found")
    if getattr(feedback, "member_id", None) != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to update this feedback")

    for field, value in feedback_update.dict(exclude_unset=True).items():
        setattr(feedback, field, value)

    db.commit()
    db.refresh(feedback)
    return feedback

@router.delete("/feedback/{feedback_id}")
async def delete_feedback(
    feedback_id: int,
    current_user: User = Depends(verify_token),
    db: Session = Depends(get_db)
):
    feedback = db.query(Feedback).filter(Feedback.id == feedback_id).first()
    if not feedback:
        raise HTTPException(status_code=404, detail="Feedback not found")
    if getattr(feedback, "member_id", None) != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this feedback")

    db.delete(feedback)
    db.commit()
    return {"message": "Feedback deleted successfully"}
