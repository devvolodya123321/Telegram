import time

from sqlalchemy import Boolean, Column, Integer, String, Text
from app.database import Base


class Poll(Base):
    __tablename__ = "polls"
    id = Column(Integer, primary_key=True, autoincrement=True)
    chat_id = Column(Integer, nullable=False, index=True)
    message_id = Column(Integer, nullable=True)
    creator_id = Column(Integer, nullable=False)
    question = Column(Text, nullable=False)
    is_anonymous = Column(Boolean, default=True)
    multiple_choice = Column(Boolean, default=False)
    is_closed = Column(Boolean, default=False)
    created_at = Column(Integer, default=lambda: int(time.time()))


class PollOption(Base):
    __tablename__ = "poll_options"
    id = Column(Integer, primary_key=True, autoincrement=True)
    poll_id = Column(Integer, nullable=False, index=True)
    text = Column(String(256), nullable=False)
    position = Column(Integer, default=0)


class PollVote(Base):
    __tablename__ = "poll_votes"
    id = Column(Integer, primary_key=True, autoincrement=True)
    poll_id = Column(Integer, nullable=False, index=True)
    option_id = Column(Integer, nullable=False)
    user_id = Column(Integer, nullable=False)
    created_at = Column(Integer, default=lambda: int(time.time()))
