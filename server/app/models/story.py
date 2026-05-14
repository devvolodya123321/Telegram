import time

from sqlalchemy import Boolean, Column, Integer, String, Text

from app.database import Base


class Story(Base):
    __tablename__ = "stories"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False, index=True)
    media_type = Column(String(32), nullable=False, default="photo")  # photo, video
    media_path = Column(String(512), nullable=False)
    caption = Column(Text, nullable=False, default="")
    privacy = Column(String(32), nullable=False, default="everyone")  # everyone, contacts, close_friends, nobody
    is_pinned = Column(Boolean, default=False)
    views_count = Column(Integer, default=0)
    expires_at = Column(Integer, default=lambda: int(time.time()) + 86400)
    created_at = Column(Integer, default=lambda: int(time.time()))
    is_deleted = Column(Boolean, default=False)


class StoryView(Base):
    __tablename__ = "story_views"

    id = Column(Integer, primary_key=True, autoincrement=True)
    story_id = Column(Integer, nullable=False, index=True)
    viewer_id = Column(Integer, nullable=False, index=True)
    viewed_at = Column(Integer, default=lambda: int(time.time()))
