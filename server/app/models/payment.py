import time

from sqlalchemy import Column, Integer, String, Text
from app.database import Base


class Invoice(Base):
    __tablename__ = "invoices"
    id = Column(Integer, primary_key=True, autoincrement=True)
    chat_id = Column(Integer, nullable=False, index=True)
    creator_id = Column(Integer, nullable=False)
    title = Column(String(256), nullable=False)
    description = Column(Text, nullable=False, default="")
    amount = Column(Integer, nullable=False)
    currency = Column(String(8), nullable=False, default="USD")
    status = Column(String(32), nullable=False, default="pending")
    created_at = Column(Integer, default=lambda: int(time.time()))


class Payment(Base):
    __tablename__ = "payments"
    id = Column(Integer, primary_key=True, autoincrement=True)
    invoice_id = Column(Integer, nullable=False, index=True)
    payer_id = Column(Integer, nullable=False, index=True)
    amount = Column(Integer, nullable=False)
    currency = Column(String(8), nullable=False, default="USD")
    status = Column(String(32), nullable=False, default="completed")
    created_at = Column(Integer, default=lambda: int(time.time()))
