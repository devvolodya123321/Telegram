import time

from sqlalchemy import BigInteger, Boolean, Column, Integer, String, Text

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    phone = Column(String(32), unique=True, nullable=False, index=True)
    first_name = Column(String(128), nullable=False, default="")
    last_name = Column(String(128), nullable=False, default="")
    username = Column(String(64), unique=True, nullable=True, index=True)
    bio = Column(Text, nullable=False, default="")
    photo_path = Column(String(512), nullable=True)
    password_hash = Column(String(256), nullable=True)
    is_online = Column(Boolean, default=False)
    last_seen = Column(Integer, default=lambda: int(time.time()))
    created_at = Column(Integer, default=lambda: int(time.time()))


class AuthCode(Base):
    __tablename__ = "auth_codes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    phone = Column(String(32), nullable=False, index=True)
    code = Column(String(8), nullable=False)
    phone_code_hash = Column(String(64), nullable=False, unique=True)
    created_at = Column(Integer, default=lambda: int(time.time()))
    used = Column(Boolean, default=False)


class Session(Base):
    __tablename__ = "sessions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, nullable=False, index=True)
    auth_token = Column(String(512), nullable=False, unique=True, index=True)
    device_model = Column(String(256), nullable=False, default="")
    app_version = Column(String(64), nullable=False, default="")
    created_at = Column(Integer, default=lambda: int(time.time()))
    is_active = Column(Boolean, default=True)
