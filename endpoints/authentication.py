from fastapi import APIRouter, status, Depends, HTTPException
from schemas import (
    RegisterSchema,
    LoginSchema,
    VerifyEmailSchema,
    ResendOTPSchema,
    ResetTokenSchema,
)
from func import (
    save_user,
    email_exists,
    username_exists,
    create_or_update_user_session,
    add_levels,
)
from utils import (
    validate_password,
    validate_email,
    verify_password,
    generate_otp,
    generate_token,
    hash_password,
)
from database import get_db
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm
from ac_token import create_access_token
from celery_config.utils.cel_workers import send_mail

# from custom_except import NoUserDataHTTPException
import traceback
from datetime import datetime, timedelta
from constant import OTP_EXPIRES
from logger import logger

auth_router = APIRouter(prefix="/auth", tags=["Authentication"])


# register endpoint
@auth_router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(register_data: RegisterSchema, db: Session = Depends(get_db)):
    try:
        username = register_data.username
        email = register_data.email
        password = register_data.password

        if not validate_email(email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid email"
            )

        if email_exists(db, email):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail="Email already exists"
            )

        if username_exists(db, username):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail="Username already exists"
            )

        val_pass = validate_password(password)
        if val_pass:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=val_pass
            )

        otp = generate_otp()

        user = save_user(db, username, email, password, otp)
        saved_otp = user.user_sessions.otp
        logger.info(f"{saved_otp}: saved_otp")
        send_mail.delay(
            {
                "email": email,
                "subject": "Email Verification",
                "template_name": "otp.html",
                "name": user.username.title(),
                "otp": saved_otp,
            }
        )
        return {
            "details": "User created successfully, check your email for verification otp"
        }
    except HTTPException as http_exc:
        # Log the HTTPException if needed
        logger.exception("traceback from register")
        raise http_exc
    except Exception as e:
        logger.exception("traceback from register")
        logger.error(e, "error from register")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Network Error"
        )


@auth_router.post("/login", status_code=status.HTTP_200_OK)
async def login(login_data: LoginSchema, db: Session = Depends(get_db)):
    try:
        email = login_data.email
        password = login_data.password

        # add_levels(db) # This is to add account levels

        logger.info(f"{email}: email")
        logger.info(f"{password}: password")

        if not validate_email(email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid email"
            )

        user = email_exists(db, email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Invalid Credentials"
            )

        if not verify_password(password, user.password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid Credentials"
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Account is inactive"
            )

        if not user.verify_email:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Email not verified"
            )

        access_token = create_access_token(data={"sub": user.id})
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "complete_registration": bool(user.user_data),
        }
    except HTTPException as http_exc:
        # Log the HTTPException if needed
        logger.exception("traceback from login")
        raise http_exc
    except Exception as e:
        logger.exception("traceback from login")
        logger.error(f"{e} : error from login")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Network Error"
        )


# For Swagger UI login interface
@auth_router.post(
    "/get_token",
    status_code=status.HTTP_200_OK,
    description="This is for Swagger UI login interface",
)
async def get_token(
    login_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)
):
    try:
        email = login_data.username
        password = login_data.password

        if not validate_email(email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid email"
            )

        user = email_exists(db, email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Invalid Credentials"
            )

        if not verify_password(password, user.password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid Credentials"
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Account is inactive"
            )

        if not user.verify_email:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Email not verified"
            )

        access_token = create_access_token(data={"sub": user.id})
        return {"access_token": access_token, "token_type": "bearer"}
    except HTTPException as http_exc:
        # Log the HTTPException if needed
        logger.exception("traceback error from login")
        raise http_exc
    except Exception as e:
        logger.exception("traceback error from login")
        logger.error(f"{e} : error from login")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Network Error"
        )


# verify email
@auth_router.patch("/verify_email", status_code=status.HTTP_200_OK)
async def verify_email(verify_data: VerifyEmailSchema, db: Session = Depends(get_db)):
    try:
        email = verify_data.email
        otp = verify_data.otp

        if not validate_email(email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid email"
            )
        user = email_exists(db, email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Email does not belong to any user",
            )

        if user.verify_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Email already verified"
            )

        if user.user_sessions.used_otp:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid OTP"
            )

        # check if the otp has expired
        if user.user_sessions.otp_expired_date < datetime.now():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="OTP has expired"
            )

        if user.user_sessions.otp != otp:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid OTP"
            )

        user.verify_email = True
        user.user_sessions.used_otp = True
        db.commit()
        send_mail.delay(
            {
                "email": email,
                "subject": "Welcome",
                "template_name": "welcome.html",
                "name": user.username.title(),
            }
        )
        return {"message": "Email verified"}
    except HTTPException as http_exc:
        # Log the HTTPException if needed
        logger.exception("traceback error from verify email")
        raise http_exc
    except Exception as e:
        logger.exception("traceback error from verify email")
        logger.error(f"{e} : error from login")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Network Error"
        )


# resend otp
@auth_router.post("/resend_otp", status_code=status.HTTP_200_OK)
async def resend_otp(request_data: ResendOTPSchema, db: Session = Depends(get_db)):
    try:
        email = request_data.email
        if not validate_email(email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid email"
            )
        user = email_exists(db, email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Email does not belong to any user",
            )
        if user.verify_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Email already verified"
            )
        otp = generate_otp()
        user.user_sessions.otp = otp
        user.user_sessions.otp_expired_date = datetime.now() + timedelta(
            minutes=OTP_EXPIRES
        )
        db.commit()
        saved_otp = user.user_sessions.otp
        logger.info(f"saved_otp: {saved_otp}")
        send_mail.delay(
            {
                "email": email,
                "subject": "Email Verification",
                "template_name": "otp.html",
                "name": user.username.title(),
                "otp": saved_otp,
            }
        )
        return {"details": "OTP sent successfully"}
    except HTTPException as http_exc:
        # Log the HTTPException if needed
        logger.exception("traceback error from resend otp")
        raise http_exc
    except Exception as e:
        logger.exception("traceback error from resend otp")
        logger.error(f"{e} : error from login")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Network Error"
        )


# reset password request
@auth_router.post(
    "/reset_password_request",
    status_code=status.HTTP_200_OK,
)
async def reset_password_req(
    request_data: ResendOTPSchema, db: Session = Depends(get_db)
):
    try:
        email = request_data.email
        if not validate_email(email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid email"
            )
        user = email_exists(db, email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )
        token = generate_token()
        res = create_or_update_user_session(db, user, token=token)
        send_mail.delay(
            {
                "email": email,
                "subject": "Reset Password",
                "template_name": "token.html",
                "name": user.username.title(),
                "token": res.token,
            }
        )
        return {"detail": "Token sent"}
    except HTTPException as http_exc:
        # Log the HTTPException if needed
        logger.exception("traceback error from reset password request")
        raise http_exc
    except Exception as e:
        logger.exception("traceback error from reset password request")
        logger.error(f"{e} : error from reset password request")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Network Error"
        )


# reset password
@auth_router.patch("/reset_password", status_code=status.HTTP_200_OK)
async def reset_password(request_data: ResetTokenSchema, db: Session = Depends(get_db)):
    try:
        email = request_data.email
        token = request_data.token
        password = request_data.password
        confirm_password = request_data.confirm_password

        if not validate_email(email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid email"
            )
        user = email_exists(db, email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )

        if not token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Pls input your token"
            )
        if user.user_sessions.used_token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid Token"
            )
        if user.user_sessions.token_expired_date < datetime.now():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Token has expired"
            )
        if user.user_sessions.token != token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid Token"
            )
        res = validate_password(password)
        if res:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=res)
        if password != confirm_password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password does not match",
            )

        user.password = hash_password(password)
        user.user_sessions.used_token = True
        db.commit()
        return {"detail": "Password Reset successfully"}
    except HTTPException as http_exc:
        # Log the HTTPException if needed
        logger.exception("traceback error from reset password")
        raise http_exc
    except Exception as e:
        logger.exception("traceback error from reset password")
        logger.error(f"{e} : error from reset password")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Network Error"
        )
