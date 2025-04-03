from pydantic import BaseModel
from typing import Optional


# user account schema
class UserAccountSchema(BaseModel):
    balance: float
    account_number: str
    book_balance: float

    class Config:
        from_attributes = True


class UserDataForAccountSchema(BaseModel):
    first_name: str
    last_name: str


class UserForAccountSchema(BaseModel):
    user_data: Optional[UserDataForAccountSchema]


class UserAccountResolveSchema(BaseModel):
    account_number: str
    user: Optional[UserForAccountSchema]

    class Config:
        from_attributes = True


# user data schema
class UserDataSchema(BaseModel):
    first_name: str
    last_name: str
    phone_number: str
    address: str
    country: str
    state: str
    city: str

    class Config:
        from_attributes = True


class ShowUserSchema(BaseModel):
    username: str
    email: str
    user_data: Optional[UserDataSchema]
    user_account: Optional[UserAccountSchema]

    class Config:
        from_attributes = True


class LoginSchema(BaseModel):
    email: str
    password: str


class RegisterSchema(BaseModel):
    username: str
    email: str
    password: str


class CompleteRegSchema(BaseModel):
    first_name: str
    last_name: str
    phone_number: str
    address: str
    country: str
    state: str
    city: str


# verify email schema
class VerifyEmailSchema(BaseModel):
    email: str
    otp: str


# resend otp schema
class ResendOTPSchema(BaseModel):
    email: str


class ChangePasswordSchema(BaseModel):
    old_password: str
    confirm_password: str
    password: str


class ResetTokenSchema(BaseModel):
    email: str
    token: str
    password: str
    confirm_password: str
