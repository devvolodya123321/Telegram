import time

from sqlalchemy import Column, Integer, String, Text
from app.database import Base


class Bot(Base):
    __tablename__ = "bots"
    id = Column(Integer, primary_key=True, autoincrement=True)
    owner_id = Column(Integer, nullable=False, index=True)
    name = Column(String(128), nullable=False)
    username = Column(String(64), nullable=False, unique=True, index=True)
    token = Column(String(256), nullable=False)
    description = Column(Text, nullable=False, default="")
    created_at = Column(Integer, default=lambda: int(time.time()))


class BotCommand(Base):
    __tablename__ = "bot_commands"
    id = Column(Integer, primary_key=True, autoincrement=True)
    bot_id = Column(Integer, nullable=False, index=True)
    command = Column(String(64), nullable=False)
    description = Column(String(256), nullable=False, default="")
