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
from ..schemas.finance import FinanceCreate, FinanceUpdate, FinanceResponse, FinanceHistoryResponse

router = APIRouter()

def get_current_balance(db: Session):
    last_transaction = db.query(Finance).order_by(Finance.date.desc(), Finance.id.desc()).first()
    return last_transaction.balance_after if last_transaction else Decimal('0')

@router.post("/", response_model=FinanceResponse)
@admin_required()
async def create_finance(
    finance: FinanceCreate,
    current_user: User = Depends(verify_token),
    db: Session = Depends(get_db)
):
    # Ambil saldo terakhir sebagai balance_before
    balance_before = get_current_balance(db)
    
    # Hitung balance_after
    balance_after = balance_before + finance.amount if finance.category == "Pemasukan" else balance_before - finance.amount

    # Simpan transaksi
    db_finance = Finance(
        **finance.dict(),
        balance_after=balance_after,
        created_by=current_user.id
    )
    db.add(db_finance)
    db.commit()
    db.refresh(db_finance)
    
    # Tambahkan balance_before ke response
    response = FinanceResponse(
        **db_finance.__dict__,
        balance_before=balance_before
    )
    return response

@router.get("/history", response_model=FinanceHistoryResponse)
async def get_finance_history(
    skip: int = 0,
    limit: int = 10,
    category: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    current_user: User = Depends(verify_token),
    db: Session = Depends(get_db)
):
    # Query dasar
    query = db.query(Finance)
    
    # Filter
    if category:
        query = query.filter(Finance.category == category)
    if start_date:
        query = query.filter(Finance.date >= start_date)
    if end_date:
        query = query.filter(Finance.date <= end_date)
    
    # Eksekusi query
    transactions = query.order_by(Finance.date.desc(), Finance.id.desc()).offset(skip).limit(limit).all()
    
    # Hitung balance_before untuk setiap transaksi
    transactions_with_balance = []
    for i, transaction in enumerate(transactions):
        if i == 0:
            # Untuk transaksi terbaru, balance_before adalah balance_after dari transaksi sebelumnya
            prev_transaction = db.query(Finance)\
                .filter(
                    (Finance.date < transaction.date) |
                    ((Finance.date == transaction.date) & (Finance.id < transaction.id))
                )\
                .order_by(Finance.date.desc(), Finance.id.desc())\
                .first()
            balance_before = prev_transaction.balance_after if prev_transaction else Decimal('0')
        else:
            # Untuk transaksi lainnya, balance_before adalah balance_after dari transaksi sebelumnya dalam hasil
            balance_before = transactions[i-1].balance_after
            
        transactions_with_balance.append(
            FinanceResponse(
                **transaction.__dict__,
                balance_before=balance_before
            )
        )
    
    return FinanceHistoryResponse(
        transactions=transactions_with_balance,
        current_balance=get_current_balance(db)
    )


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
    # Dapatkan transaksi yang akan diupdate
    db_finance = db.query(Finance).filter(Finance.id == finance_id).first()
    if not db_finance:
        raise HTTPException(status_code=404, detail="Finance record not found")

    # Simpan nilai lama untuk perhitungan
    old_amount = db_finance.amount
    old_category = db_finance.category
    old_date = db_finance.date

    # Dapatkan nilai baru dari request
    new_amount = finance_update.amount if finance_update.amount is not None else old_amount
    new_category = finance_update.category if finance_update.category is not None else old_category
    new_date = finance_update.date if finance_update.date is not None else old_date

    # 1. Dapatkan transaksi sebelumnya (untuk menghitung balance_before)
    prev_transaction = db.query(Finance).filter(
        (Finance.date < old_date) |
        ((Finance.date == old_date) & (Finance.id < db_finance.id))
    ).order_by(Finance.date.desc(), Finance.id.desc()).first()

    balance_before = prev_transaction.balance_after if prev_transaction else Decimal('0')

    # 2. Hitung ulang saldo untuk transaksi ini dan semua transaksi setelahnya
    transactions_to_update = db.query(Finance).filter(
        (Finance.date > old_date) |
        ((Finance.date == old_date) & (Finance.id >= db_finance.id))
    ).order_by(Finance.date.asc(), Finance.id.asc()).all()

    # 3. Update transaksi ini
    for field, value in finance_update.dict(exclude_unset=True).items():
        setattr(db_finance, field, value)

    # Hitung balance_after baru untuk transaksi ini
    if new_category == "Pemasukan":
        db_finance.balance_after = balance_before + new_amount
    else:
        db_finance.balance_after = balance_before - new_amount

    current_balance = db_finance.balance_after

    # 4. Update semua transaksi setelahnya
    for transaction in transactions_to_update[1:]:  # Skip transaksi pertama (yang sedang diupdate)
        if transaction.category == "Pemasukan":
            current_balance += transaction.amount
        else:
            current_balance -= transaction.amount
        
        transaction.balance_after = current_balance

    db.commit()
    db.refresh(db_finance)

    # Siapkan response dengan balance_before
    response = FinanceResponse(
        **db_finance.__dict__,
        balance_before=balance_before
    )
    return response


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

    # Ambil saldo terakhir
    last_balance = db.query(Finance.balance_after).order_by(Finance.date.desc()).first()
    last_balance = last_balance[0] if last_balance else Decimal('0')

    # Hitung saldo baru setelah penghapusan
    if finance.category == "Pemasukan":
        new_balance = last_balance - finance.amount
    else:
        new_balance = last_balance + finance.amount

    # Hapus transaksi
    db.delete(finance)
    db.commit()

    if (
        last_transaction := db.query(Finance)
        .order_by(Finance.date.desc())
        .first()
    ):
        last_transaction.balance = new_balance
        db.commit()
        db.refresh(last_transaction)

    return {"message": "Finance record deleted"}
