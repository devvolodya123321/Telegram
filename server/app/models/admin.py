import time

from sqlalchemy import Boolean, Column, Integer, String, Text
from app.database import Base


class AdminLog(Base):
    __tablename__ = "admin_log"
    id = Column(Integer, primary_key=True, autoincrement=True)
    chat_id = Column(Integer, nullable=False, index=True)
    admin_id = Column(Integer, nullable=False)
    action = Column(String(64), nullable=False)
    target_user_id = Column(Integer, nullable=True)
    details = Column(Text, nullable=True)
    created_at = Column(Integer, default=lambda: int(time.time()))


class ChatRestriction(Base):
    __tablename__ = "chat_restrictions"
    id = Column(Integer, primary_key=True, autoincrement=True)
    chat_id = Column(Integer, nullable=False, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    is_banned = Column(Boolean, default=False)
    can_send_messages = Column(Boolean, default=True)
    can_send_media = Column(Boolean, default=True)
    can_send_polls = Column(Boolean, default=True)
    can_invite_users = Column(Boolean, default=True)
    until_date = Column(Integer, nullable=True)
    created_at = Column(Integer, default=lambda: int(time.time()))
