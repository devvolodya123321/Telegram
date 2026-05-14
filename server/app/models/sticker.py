import time

from sqlalchemy import Boolean, Column, Integer, String, Text

from app.database import Base


class StickerSet(Base):
    __tablename__ = "sticker_sets"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(128), nullable=False, unique=True, index=True)
    title = Column(String(256), nullable=False)
    creator_id = Column(Integer, nullable=False, index=True)
    is_animated = Column(Boolean, default=False)
    is_video = Column(Boolean, default=False)
    thumb_path = Column(String(512), nullable=True)
    created_at = Column(Integer, default=lambda: int(time.time()))


class Sticker(Base):
    __tablename__ = "stickers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    set_id = Column(Integer, nullable=False, index=True)
    emoji = Column(String(32), nullable=False, default="")
    file_path = Column(String(512), nullable=False)
    file_size = Column(Integer, default=0)
    width = Column(Integer, default=512)
    height = Column(Integer, default=512)
    position = Column(Integer, default=0)


class UserStickerSet(Base):
    __tablename__ = "user_sticker_sets"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False, index=True)
    set_id = Column(Integer, nullable=False, index=True)
    added_at = Column(Integer, default=lambda: int(time.time()))
