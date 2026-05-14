import time

from sqlalchemy import Column, Integer, String
from app.database import Base


class ChatFolder(Base):
    __tablename__ = "chat_folders"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False, index=True)
    title = Column(String(128), nullable=False)
    position = Column(Integer, default=0)
    created_at = Column(Integer, default=lambda: int(time.time()))


class ChatFolderEntry(Base):
    __tablename__ = "chat_folder_entries"
    id = Column(Integer, primary_key=True, autoincrement=True)
    folder_id = Column(Integer, nullable=False, index=True)
    chat_id = Column(Integer, nullable=False)
