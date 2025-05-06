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
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    new_feedback = Feedback(
        event_id=event_id,
        member_id=current_user.id,
        content=feedback.content
    )

    db.add(new_feedback)
    db.commit()
    db.refresh(new_feedback)
    return new_feedback

@router.get("/event/{event_id}/feedback", response_model=List[FeedbackResponse])
async def get_feedbacks(
    event_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(verify_token)
):
    return (
        db.query(Feedback, Member.full_name)
        .join(Member, Feedback.member_id == Member.id)
        .filter(Feedback.event_id == event_id)
        .with_entities(
            Feedback.id,
            Feedback.content,
            Feedback.event_id,
            Feedback.member_id,
            Feedback.created_at,
            Member.full_name
        )
        .all()
    )

@router.get("/feedback/{feedback_id}", response_model=FeedbackResponse)
async def get_single_feedback(
    feedback_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(verify_token)
):
    if (
        feedback := db.query(Feedback)
        .filter(Feedback.id == feedback_id)
        .first()
    ):
        return feedback
    else:
        raise HTTPException(status_code=404, detail="Feedback not found")

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
    if feedback.member_id != current_user.id:
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
    if feedback.member_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this feedback")

    db.delete(feedback)
    db.commit()
    return {"message": "Feedback deleted successfully"}
