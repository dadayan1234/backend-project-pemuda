from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from decimal import Decimal

class FinanceBase(BaseModel):
    amount: Decimal
    category: str  # "Pemasukan" or "Pengeluaran"
    date: datetime
    description: str

class FinanceCreate(FinanceBase):
    pass

class FinanceUpdate(BaseModel):
    amount: Optional[Decimal] = None
    category: Optional[str] = None
    date: Optional[datetime] = None
    description: Optional[str] = None

class FinanceResponse(FinanceBase):
    id: int
    balance_before: Decimal  # Saldo sebelum transaksi ini
    balance_after: Decimal   # Saldo setelah transaksi ini
    document_url: Optional[str]
    created_by: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class FinanceHistoryResponse(BaseModel):
    transactions: list[FinanceResponse]
    current_balance: Decimal  # Saldo terkini