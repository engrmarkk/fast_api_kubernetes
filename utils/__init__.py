import uuid
from passlib.hash import pbkdf2_sha256 as hasher
import re
import random
import secrets
import string
from datetime import datetime


def generate_otp():
    return str(random.randint(100000, 999999))


# generate token
def generate_token():
    return str(random.randint(10000000, 99999999))


def generate_uuid():
    return str(uuid.uuid4().hex)


# generate 10 random digit for account numbebr
def generate_account_number():
    return random.randint(1000000000, 9999999999)


def generate_session_id():
    # Generate a random 30-digit integer
    return str(secrets.randbelow(10**30))


def generate_transaction_reference():
    # Get current date and time in YYYYMMDDHHMMSS format
    today_date = datetime.now().strftime("%Y%m%d%H%M%S")

    # Generate a random 12-character alphanumeric string (letters + digits)
    random_suffix = "".join(random.choices(string.ascii_uppercase + string.digits, k=7))

    # Combine the date/time and random suffix
    return today_date + random_suffix


def hash_password(password):
    return hasher.hash(password)


# validate password
def validate_password(password):
    """
    :param password:
    :return:

    TODO:
    - length must be at least 8
    - must contain at least one lowercase letter
    - must contain at least one uppercase letter
    - must contain at least one digit
    """
    if len(password) < 8:
        return "Password must be at least 8 characters long"

    if not any(char.islower() for char in password):
        return "Password must contain at least one lowercase letter"

    if not any(char.isupper() for char in password):
        return "Password must contain at least one uppercase letter"

    if not any(char.isdigit() for char in password):
        return "Password must contain at least one digit"

    return None


# verify password
def verify_password(password, hashed_password):
    return hasher.verify(password, hashed_password)


def validate_email(email):
    pattern = r"^[\w\.-]+@[\w\.-]+\.\w+$"
    return re.match(pattern, email)


# validate nigeria phone number
def validate_phone_number(phone_number):
    if not phone_number.startswith("0"):
        return "Your phone number must start with 0"
    if not len(phone_number) == 11:
        return "Your phone number must be 11 digits"
    if not phone_number.isdigit():
        return "Your phone number must be a number"
    return None
