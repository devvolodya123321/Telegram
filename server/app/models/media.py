import time

from sqlalchemy import BigInteger, Column, Integer, String

from app.database import Base


class MediaFile(Base):
    __tablename__ = "media_files"

    id = Column(Integer, primary_key=True, autoincrement=True)
    uploader_id = Column(Integer, nullable=False, index=True)
    file_name = Column(String(512), nullable=False)
    file_path = Column(String(1024), nullable=False)
    file_size = Column(Integer, nullable=False, default=0)
    mime_type = Column(String(128), nullable=False, default="application/octet-stream")
    media_type = Column(String(32), nullable=False, default="document")  # photo, video, document, audio, voice
    width = Column(Integer, nullable=True)
    height = Column(Integer, nullable=True)
    duration = Column(Integer, nullable=True)
    uploaded_at = Column(Integer, default=lambda: int(time.time()))
