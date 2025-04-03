from functools import wraps
from fastapi import Depends, status, HTTPException
from database import get_db
from sqlalchemy.orm import Session
from func import get_active_user


def email_verified(get_current_user: Depends):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            db: Session = kwargs.get("db") or next(get_db())
            current_user = get_current_user(db=db)

            user = get_active_user(db, current_user)
            if not user.verify_email:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Email not verified",
                )
            return func(*args, **kwargs)

        return wrapper
