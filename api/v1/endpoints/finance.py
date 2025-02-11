from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from decimal import Decimal
from core.database import get_db, admin_required
from core.security import verify_token
from ..models.finance import Finance
from ..models.user import User
from ..schemas.finance import FinanceCreate, FinanceUpdate, FinanceResponse

router = APIRouter()

@router.post("/", response_model=FinanceResponse)
@admin_required()
async def create_finance(
    finance: FinanceCreate,
    current_user: User = Depends(verify_token),
    db: Session = Depends(get_db)
):
    db_finance = Finance(**finance.dict(), created_by=current_user.id)
    db.add(db_finance)
    db.commit()
    db.refresh(db_finance)
    return db_finance

@router.get("/", response_model=List[FinanceResponse])
async def get_finances(
    skip: int = 0,
    limit: int = 10,
    category: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    current_user: User = Depends(verify_token),
    db: Session = Depends(get_db)
):
    query = db.query(Finance)

    if category:
        query = query.filter(Finance.category == category)
    if start_date:
        query = query.filter(Finance.date >= start_date)
    if end_date:
        query = query.filter(Finance.date <= end_date)

    return query.order_by(Finance.date.desc()).offset(skip).limit(limit).all()

@router.get("/summary")
async def get_finance_summary(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    current_user: User = Depends(verify_token),
    db: Session = Depends(get_db)
):
    query = db.query(Finance)
    
    if start_date:
        query = query.filter(Finance.date >= start_date)
    if end_date:
        query = query.filter(Finance.date <= end_date)

    income = query.filter(Finance.category == "Pemasukan")\
        .with_entities(func.sum(Finance.amount))\
        .scalar() or Decimal('0')
        
    expense = query.filter(Finance.category == "Pengeluaran")\
        .with_entities(func.sum(Finance.amount))\
        .scalar() or Decimal('0')

    return {
        "total_income": float(income),
        "total_expense": float(expense),
        "balance": float(income - expense)
    }

@router.get("/{finance_id}", response_model=FinanceResponse)
async def get_finance(
    finance_id: int,
    current_user: User = Depends(verify_token),
    db: Session = Depends(get_db)
):
    if finance := db.query(Finance).filter(Finance.id == finance_id).first():
        return finance
    else:
        raise HTTPException(status_code=404, detail="Finance record not found")

@router.put("/{finance_id}", response_model=FinanceResponse)
@admin_required()
async def update_finance(
    finance_id: int,
    finance_update: FinanceUpdate,
    current_user: User = Depends(verify_token),
    db: Session = Depends(get_db)
):
    db_finance = db.query(Finance).filter(Finance.id == finance_id).first()
    if not db_finance:
        raise HTTPException(status_code=404, detail="Finance record not found")

    for field, value in finance_update.dict(exclude_unset=True).items():
        setattr(db_finance, field, value)

    db.commit()
    db.refresh(db_finance)
    return db_finance

@router.delete("/{finance_id}")
@admin_required()
async def delete_finance(
    finance_id: int,
    current_user: User = Depends(verify_token),
    db: Session = Depends(get_db)
):
    finance = db.query(Finance).filter(Finance.id == finance_id).first()
    if not finance:
        raise HTTPException(status_code=404, detail="Finance record not found")

    db.delete(finance)
    db.commit()
    return {"message": "Finance record deleted"}