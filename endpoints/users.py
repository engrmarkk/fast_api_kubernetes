from fastapi import APIRouter, status, Depends, HTTPException, Request
from ac_token import get_current_user
from sqlalchemy.orm import Session
from models import Users
from func import save_user_data, phone_number_exists
from utils import (
    validate_phone_number,
    validate_password,
    hash_password,
    verify_password,
)
from schemas import ShowUserSchema, CompleteRegSchema, ChangePasswordSchema
from database import get_db
import traceback
from extensions import limiter
from logger import logger


user_router = APIRouter(prefix="/users", tags=["Users"])


@user_router.get("", status_code=status.HTTP_200_OK, response_model=ShowUserSchema)
@limiter.limit("1/minute")
async def get_user(
    request: Request,
    current_user: Users = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Who are you?"
        )
    return current_user


@user_router.patch(
    "/complete_registration",
    status_code=status.HTTP_200_OK,
)
async def complete_registration(
    user_data: CompleteRegSchema,
    current_user: Users = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Invalid User"
        )
    if current_user.user_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User already has already completed registration",
        )
    first_name = user_data.first_name
    last_name = user_data.last_name
    phone_number = user_data.phone_number
    address = user_data.address
    country = user_data.country
    state = user_data.state
    city = user_data.city

    val_phone = validate_phone_number(phone_number)
    if val_phone:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=val_phone)

    if phone_number_exists(db, phone_number):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Phone number already exists"
        )

    saved_user = save_user_data(
        db,
        current_user,
        first_name,
        last_name,
        phone_number,
        address,
        country,
        state,
        city,
    )
    return {"detail": "User data saved"}


# change password
@user_router.patch(
    "/change_password",
    status_code=status.HTTP_200_OK,
)
async def change_password(
    request_data: ChangePasswordSchema,
    current_user: Users = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        password = request_data.password
        old_password = request_data.old_password
        confirm_password = request_data.confirm_password
        res = verify_password(old_password, current_user.password)
        if not res:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid Old password"
            )
        val_res = validate_password(password)
        if val_res:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=val_res)
        if password != confirm_password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Passwords do not match"
            )
        current_user.password = hash_password(password)
        db.commit()
        return {"detail": "Password changed"}
    except HTTPException as http_exc:
        # Log the HTTPException if needed
        logger.exception("traceback from change password")
        raise http_exc
    except Exception as e:
        logger.exception("traceback from change password")
        logger.error(f"{e} : error from change password")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Network Error"
        )
