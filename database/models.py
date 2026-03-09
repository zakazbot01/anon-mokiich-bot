from sqlalchemy import Column, Integer, BigInteger, String, Boolean, DateTime, Text, func
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class User(Base):
    __tablename__ = "users"
    id = Column(BigInteger, primary_key=True)
    username = Column(String(64), nullable=True)
    is_premium = Column(Boolean, default=False)
    premium_expires = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now())


class AskLink(Base):
    __tablename__ = "ask_links"
    id = Column(Integer, primary_key=True)
    owner_id = Column(BigInteger)
    secret = Column(String(32), unique=True, index=True)
    destination_type = Column(String(10))  # "private" или "channel_both"
    destination_id = Column(BigInteger, nullable=True)
    reveal_in_channel = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())


class Message(Base):
    __tablename__ = "messages"
    id = Column(Integer, primary_key=True)
    link_id = Column(Integer)
    sender_id = Column(BigInteger)
    sender_username = Column(String(64), nullable=True)
    sender_first_name = Column(String(255), nullable=True)   # добавлено
    sender_last_name = Column(String(255), nullable=True)    # добавлено
    text = Column(Text)
    reply_to = Column(Integer, nullable=True)
    created_at = Column(DateTime, server_default=func.now())