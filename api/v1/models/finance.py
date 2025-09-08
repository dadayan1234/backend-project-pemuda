from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Enum, DECIMAL
from sqlalchemy.orm import relationship
from datetime import datetime
from core.database import Base

class Finance(Base):
    __tablename__ = "finances"

    id = Column(Integer, primary_key=True, index=True)
    amount = Column(DECIMAL(12, 2), nullable=False)
    category = Column(Enum("Pemasukan", "Pengeluaran"), nullable=False)
    date = Column(DateTime, nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    balance_after = Column(DECIMAL(10, 2), nullable=False, comment="Saldo setelah transaksi ini")
    document_url = Column(String(255))
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
 