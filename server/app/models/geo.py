import time

from sqlalchemy import Boolean, Column, Float, Integer
from app.database import Base


class LocationMessage(Base):
    __tablename__ = "location_messages"
    id = Column(Integer, primary_key=True, autoincrement=True)
    message_id = Column(Integer, nullable=False, index=True)
    chat_id = Column(Integer, nullable=False, index=True)
    from_id = Column(Integer, nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    is_live = Column(Boolean, default=False)
    live_period = Column(Integer, default=0)
    is_stopped = Column(Boolean, default=False)
    created_at = Column(Integer, default=lambda: int(time.time()))
