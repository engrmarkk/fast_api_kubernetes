from fastapi import FastAPI, Request, HTTPException
from endpoints import (
    ping_router,
    user_router,
    auth_router,
    misc_router,
    transaction_router,
)
from database import engine, Base
from models import Users, UserData
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv
from extensions import limiter
from slowapi.errors import RateLimitExceeded

# noinspection PyProtectedMember
from slowapi import _rate_limit_exceeded_handler
from logger import logger

load_dotenv()

app = FastAPI(
    title="FastAPI Wallet API", description="FastAPI Wallet API", version="1.0.0"
)


def create_app():
    app.add_middleware(
        CORSMiddleware,
        allow_origins=os.getenv("ALLOWED_ORIGINS", "").split(","),
        # Example: "http://localhost:3000,https://example.com"
        allow_credentials=True,
        allow_methods=os.getenv("ALLOWED_METHODS", "GET,POST,PUT,DELETE").split(","),
        allow_headers=os.getenv("ALLOWED_HEADERS", "Authorization,Content-Type").split(
            ","
        ),
    )

    # noinspection PyUnresolvedReferences
    app.state.limiter = limiter

    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    @app.exception_handler(RateLimitExceeded)
    async def custom_rate_limit_exceeded_handler(
        request: Request, exc: RateLimitExceeded
    ):
        logger.error(exc.detail)
        raise HTTPException(status_code=429, detail="Rate limit exceeded")

    Base.metadata.create_all(engine)

    app.include_router(user_router)
    app.include_router(auth_router)
    app.include_router(ping_router)
    app.include_router(misc_router)
    app.include_router(transaction_router)
    return app
