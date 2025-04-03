import os
from dotenv import load_dotenv

load_dotenv()

SQLALCHEMY_DATABASE_URI = os.environ.get("SQLALCHEMY_DATABASE_URI")
SECRET_KEY = os.environ.get("SECRET_KEY")
ALGORITHM = os.environ.get("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.environ.get("ACCESS_TOKEN_EXPIRE_MINUTES"))
DEFAULT_USER_BALANCE = float(os.environ.get("DEFAULT_USER_BALANCE"))
SESSION_EXPIRES = int(os.environ.get("SESSION_EXPIRES"))
OTP_EXPIRES = int(os.environ.get("OTP_EXPIRES"))
