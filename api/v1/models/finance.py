from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Enum, DECIMAL
from sqlalchemy.orm import relationship
from datetime import datetime
from core.database import Base

class Finance(Base):
    __tablename__ = "finances"

    id = Column(Integer, primary_key=True, index=True)
    amount = Column(DECIMAL(10, 2), nullable=False)
    category = Column(Enum("Pemasukan", "Pengeluaran"), nullable=False)
    date = Column(DateTime, nullable=False)
    description = Column(Text, nullable=False)
    document_url = Column(String(255))
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    creator = relationship("User", back_populates="created_finances")
