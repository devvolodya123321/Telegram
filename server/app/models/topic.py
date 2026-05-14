import time

from sqlalchemy import Boolean, Column, Integer, String
from app.database import Base


class Topic(Base):
    __tablename__ = "topics"
    id = Column(Integer, primary_key=True, autoincrement=True)
    chat_id = Column(Integer, nullable=False, index=True)
    title = Column(String(256), nullable=False)
    icon_emoji = Column(String(16), nullable=True)
    creator_id = Column(Integer, nullable=False)
    is_closed = Column(Boolean, default=False)
    is_pinned = Column(Boolean, default=False)
    created_at = Column(Integer, default=lambda: int(time.time()))
