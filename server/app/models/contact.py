import time

from sqlalchemy import BigInteger, Boolean, Column, Integer

from app.database import Base


class Contact(Base):
    __tablename__ = "contacts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, nullable=False, index=True)
    contact_user_id = Column(BigInteger, nullable=False, index=True)
    mutual = Column(Boolean, default=False)
    added_at = Column(Integer, default=lambda: int(time.time()))


class BlockedUser(Base):
    __tablename__ = "blocked_users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, nullable=False, index=True)
    blocked_user_id = Column(BigInteger, nullable=False, index=True)
    blocked_at = Column(Integer, default=lambda: int(time.time()))
