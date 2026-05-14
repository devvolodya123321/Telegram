import time

from sqlalchemy import Boolean, Column, Integer, String, Text

from app.database import Base


class Call(Base):
    __tablename__ = "calls"

    id = Column(Integer, primary_key=True, autoincrement=True)
    caller_id = Column(Integer, nullable=False, index=True)
    callee_id = Column(Integer, nullable=False, index=True)
    call_type = Column(String(16), nullable=False, default="voice")  # voice, video
    status = Column(String(16), nullable=False, default="pending")  # pending, ringing, active, ended, missed, declined
    duration = Column(Integer, default=0)
    rating = Column(Integer, nullable=True)
    comment = Column(Text, nullable=True)
    started_at = Column(Integer, nullable=True)
    ended_at = Column(Integer, nullable=True)
    created_at = Column(Integer, default=lambda: int(time.time()))
