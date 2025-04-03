from database import Base
from sqlalchemy import (
    Column,
    String,
    ForeignKey,
    DateTime,
    Float,
    Enum,
)
from utils import generate_uuid
from sqlalchemy.orm import relationship
from datetime import datetime
from enum import Enum as PyEnum


# transaction types
class TransactionType(str, PyEnum):
    CREDIT = "credit"
    DEBIT = "debit"


class TransactionStatus(str, PyEnum):
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"
    REFUNDED = "refunded"


# categories table
class Categories(Base):
    __tablename__ = "categories"
    id = Column(String(50), primary_key=True, default=generate_uuid)
    name = Column(String(255), nullable=False)
    transactions = relationship("Transactions", back_populates="category")

    def __init__(self, name):
        self.name = name.lower()

    # class methods
    @classmethod
    def get_by_name(cls, name):
        return cls.query.filter_by(name=name.lower()).first()


class Transactions(Base):
    __tablename__ = "transactions"
    id = Column(String(50), primary_key=True, default=generate_uuid)
    amount = Column(Float, nullable=False)
    transaction_type = Column(Enum(TransactionType), nullable=True)
    transaction_status = Column(Enum(TransactionStatus), nullable=True)
    category_id = Column(String(50), ForeignKey("categories.id"), nullable=True)
    category = relationship("Categories", back_populates="transactions")
    receiver_account_number = Column(String(255), nullable=True)
    session_id = Column(String(255), nullable=True)
    transaction_ref = Column(String(255), nullable=True)
    sender_account_number = Column(String(255), nullable=True)
    receiver_name = Column(String(255), nullable=True)
    sender_name = Column(String(255), nullable=True)
    current_balance = Column(Float, nullable=True)
    book_balance = Column(Float, nullable=True)
    user_id = Column(String(50), ForeignKey("users.id"), nullable=True)
    user = relationship("Users", back_populates="transactions")
    description = Column(String(255), nullable=True)
    date = Column(DateTime, default=datetime.now)

    def to_dict(self):
        trans_obj = {
            "id": self.id,
            "amount": self.amount,
            "transaction_type": self.transaction_type,
            "transaction_status": self.transaction_status,
            "category": self.category.name,
            "receiver_account_number": self.receiver_account_number,
            "session_id": self.session_id,
            "transaction_ref": self.transaction_ref,
            "sender_account_number": self.sender_account_number,
            "receiver_name": self.receiver_name,
            "sender_name": self.sender_name,
            "current_balance": self.current_balance,
            "description": self.description,
            "date": self.date.strftime("%Y-%b-%d %H:%M:%S"),
        }
        return {key: value for key, value in trans_obj.items() if value}


class Beneficiaries(Base):
    __tablename__ = "beneficiaries"
    id = Column(String(50), primary_key=True, default=generate_uuid)
    name = Column(String(255), nullable=False)
    account_number = Column(String(255), nullable=False)
    user_id = Column(String(50), ForeignKey("users.id"), nullable=False)
    user = relationship("Users", back_populates="beneficiaries")
    date = Column(DateTime, default=datetime.now)
