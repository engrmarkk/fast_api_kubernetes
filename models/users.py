from database import Base
from sqlalchemy import (
    Column,
    String,
    Boolean,
    Text,
    ForeignKey,
    DateTime,
    Float,
)
from utils import generate_uuid, generate_account_number
from sqlalchemy.orm import relationship
from datetime import datetime


class AccountLevels(Base):
    __tablename__ = "account_levels"
    id = Column(String(50), primary_key=True, default=generate_uuid)
    level = Column(String(255), nullable=True)
    max_balance = Column(Float, nullable=True)
    max_tf_per_day = Column(Float, nullable=True)
    max_tf_once = Column(Float, nullable=True)
    unlimited = Column(Boolean, default=False)
    users = relationship("Users", back_populates="account_level", uselist=False)


class Users(Base):
    __tablename__ = "users"
    id = Column(String(50), primary_key=True, default=generate_uuid)
    username = Column(String(255), nullable=False, unique=True)
    email = Column(String(255), nullable=False, unique=True)
    password = Column(Text, nullable=False)
    is_active = Column(Boolean, default=True)
    verify_email = Column(Boolean, default=False)
    date = Column(DateTime, default=datetime.now)
    account_level_id = Column(
        String(50), ForeignKey("account_levels.id"), nullable=True
    )

    account_level = relationship("AccountLevels", back_populates="users")
    user_data = relationship("UserData", back_populates="user", uselist=False)
    user_account = relationship("UserAccount", back_populates="user", uselist=False)
    transactions = relationship("Transactions", back_populates="user")
    beneficiaries = relationship("Beneficiaries", back_populates="user")
    user_sessions = relationship("UserSessions", back_populates="user", uselist=False)

    def __repr__(self):
        return f"User(id={self.id}, username={self.username}, email={self.email})"


class UserData(Base):
    __tablename__ = "user_data"
    id = Column(String(50), primary_key=True, default=generate_uuid)
    first_name = Column(String(255), nullable=False)
    last_name = Column(String(255), nullable=False)
    phone_number = Column(String(255), nullable=False)
    address = Column(String(255), nullable=False)
    country = Column(String(255), nullable=False)
    state = Column(String(255), nullable=False)
    city = Column(String(255), nullable=False)
    user_id = Column(String(50), ForeignKey("users.id"), nullable=False)
    date = Column(DateTime, default=datetime.now)
    user = relationship("Users", back_populates="user_data", uselist=False)


class UserAccount(Base):
    __tablename__ = "user_account"
    id = Column(String(50), primary_key=True, default=generate_uuid)
    balance = Column(Float, nullable=False)
    book_balance = Column(Float, nullable=True)
    account_number = Column(String(255), default=generate_account_number)
    date = Column(DateTime, default=datetime.now)
    user_id = Column(String(50), ForeignKey("users.id"), nullable=False)
    user = relationship("Users", back_populates="user_account", uselist=False)


# user session  model
class UserSessions(Base):
    __tablename__ = "user_sessions"
    id = Column(String(50), primary_key=True, default=generate_uuid)
    user_id = Column(String(50), ForeignKey("users.id"), nullable=False)
    user = relationship("Users", back_populates="user_sessions", uselist=False)
    token = Column(String(255), nullable=True)
    token_expired_date = Column(DateTime)
    otp = Column(String(6), nullable=True)
    otp_expired_date = Column(DateTime)
    used_otp = Column(Boolean, default=False)
    used_token = Column(Boolean, default=False)
    date = Column(DateTime, default=datetime.now)
