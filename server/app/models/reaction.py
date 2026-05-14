import time

from sqlalchemy import Column, Integer, String

from app.database import Base


class Reaction(Base):
    __tablename__ = "reactions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    message_id = Column(Integer, nullable=False, index=True)
    chat_id = Column(Integer, nullable=False, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    emoji = Column(String(32), nullable=False)
    created_at = Column(Integer, default=lambda: int(time.time()))
