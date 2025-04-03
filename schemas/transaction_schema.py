from pydantic import BaseModel
from typing import Optional


class CreateTransactionSchema(BaseModel):
    amount: float
    account_number: str
    receiver_name: str
    save_beneficiary: Optional[bool] = False
    description: Optional[str] = None


class ShowTransactionSchema(BaseModel):
    amount: float
    transaction_type: str
    transaction_status: str
    category_id: str
    receiver_account_number: str
    session_id: str
    transaction_ref: str
    sender_account_number: str
    receiver_name: str
    sender_name: str
    current_balance: float
    user_id: str
    description: str
    date: str

    class Config:
        from_attributes = True


class ShowBeneficiarySchema(BaseModel):
    id: str
    account_number: str
    name: str

    class Config:
        from_attributes = True


class CategorySchema(BaseModel):
    id: str
    name: str

    @property
    def name_title(self):
        return self.name.title()

    class Config:
        from_attributes = True
