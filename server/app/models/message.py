import time

from sqlalchemy import BigInteger, Boolean, Column, Integer, String, Text

from app.database import Base


class Chat(Base):
    __tablename__ = "chats"

    id = Column(Integer, primary_key=True, autoincrement=True)
    chat_type = Column(String(16), nullable=False, default="private")  # private, group, channel
    title = Column(String(256), nullable=True)
    username = Column(String(64), nullable=True, unique=True, index=True)
    description = Column(Text, nullable=False, default="")
    photo_path = Column(String(512), nullable=True)
    creator_id = Column(BigInteger, nullable=True)
    pinned_message_id = Column(BigInteger, nullable=True)
    created_at = Column(Integer, default=lambda: int(time.time()))


class ChatMember(Base):
    __tablename__ = "chat_members"

    id = Column(Integer, primary_key=True, autoincrement=True)
    chat_id = Column(BigInteger, nullable=False, index=True)
    user_id = Column(BigInteger, nullable=False, index=True)
    role = Column(String(16), nullable=False, default="member")  # member, admin, owner
    joined_at = Column(Integer, default=lambda: int(time.time()))
    is_active = Column(Boolean, default=True)


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    chat_id = Column(Integer, nullable=False, index=True)
    from_id = Column(Integer, nullable=False, index=True)
    text = Column(Text, nullable=False, default="")
    media_type = Column(String(32), nullable=True)  # photo, video, document, audio, voice, sticker
    media_path = Column(String(512), nullable=True)
    reply_to_msg_id = Column(BigInteger, nullable=True)
    forward_from_id = Column(BigInteger, nullable=True)
    forward_from_msg_id = Column(BigInteger, nullable=True)
    is_edited = Column(Boolean, default=False)
    is_deleted = Column(Boolean, default=False)
    date = Column(Integer, default=lambda: int(time.time()))
    edit_date = Column(Integer, nullable=True)


class Dialog(Base):
    __tablename__ = "dialogs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, nullable=False, index=True)
    chat_id = Column(BigInteger, nullable=False, index=True)
    top_message_id = Column(BigInteger, nullable=True)
    unread_count = Column(Integer, default=0)
    last_read_inbox_id = Column(BigInteger, default=0)
    last_read_outbox_id = Column(BigInteger, default=0)
    pinned = Column(Boolean, default=False)
    muted = Column(Boolean, default=False)
