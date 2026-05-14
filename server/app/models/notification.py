from sqlalchemy import Boolean, Column, Integer, String

from app.database import Base


class NotificationSettings(Base):
    __tablename__ = "notification_settings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False, index=True)
    chat_id = Column(Integer, nullable=True, index=True)
    muted = Column(Boolean, default=False)
    mute_until = Column(Integer, nullable=True)
    sound = Column(String(128), nullable=True, default="default")
    show_previews = Column(Boolean, default=True)


class PrivacySettings(Base):
    __tablename__ = "privacy_settings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False, unique=True, index=True)
    phone_visibility = Column(String(32), default="contacts")       # everyone, contacts, nobody
    last_seen_visibility = Column(String(32), default="everyone")   # everyone, contacts, nobody
    profile_photo_visibility = Column(String(32), default="everyone")
    forwards_visibility = Column(String(32), default="everyone")
    calls_visibility = Column(String(32), default="everyone")
    groups_visibility = Column(String(32), default="everyone")
    stories_visibility = Column(String(32), default="everyone")     # everyone, contacts, close_friends, nobody


class ProfilePhoto(Base):
    __tablename__ = "profile_photos"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False, index=True)
    file_path = Column(String(512), nullable=False)
    is_current = Column(Boolean, default=True)
    uploaded_at = Column(Integer, nullable=False)
