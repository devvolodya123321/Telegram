import time

from sqlalchemy import Column, Integer, Text
from app.database import Base


class Draft(Base):
    __tablename__ = "drafts"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False, index=True)
    chat_id = Column(Integer, nullable=False, index=True)
    text = Column(Text, nullable=False, default="")
    reply_to_msg_id = Column(Integer, nullable=True)
    updated_at = Column(Integer, default=lambda: int(time.time()))
