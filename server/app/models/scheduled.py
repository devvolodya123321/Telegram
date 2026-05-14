import time
from typing import Optional

from sqlalchemy import Boolean, Column, Integer, String, Text
from app.database import Base


class ScheduledMessage(Base):
    __tablename__ = "scheduled_messages"
    id = Column(Integer, primary_key=True, autoincrement=True)
    chat_id = Column(Integer, nullable=False, index=True)
    from_id = Column(Integer, nullable=False)
    text = Column(Text, nullable=False, default="")
    send_at = Column(Integer, nullable=False)
    is_sent = Column(Boolean, default=False)
    created_at = Column(Integer, default=lambda: int(time.time()))
