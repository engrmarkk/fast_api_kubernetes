from models import (
    Users,
    UserData,
    UserAccount,
    Categories,
    Transactions,
    TransactionStatus,
    TransactionType,
    Beneficiaries,
    UserSessions,
    AccountLevels,
)
from utils import hash_password
from constant import DEFAULT_USER_BALANCE, SESSION_EXPIRES, OTP_EXPIRES
from datetime import datetime, timedelta
from celery_config.utils.cel_workers import send_mail
from fastapi import Request, HTTPException
from logger import logger
from sqlalchemy import func


# if username exists (fastapi)
def username_exists(db, username: str):
    return db.query(Users).filter(Users.username == username.lower()).first()


# if email exists (fastapi)
def email_exists(db, email: str):
    return db.query(Users).filter(Users.email == email.lower()).first()


# save users
def save_user(db, username, email, password, otp):
    new_user = Users(
        username=username.lower(),
        email=email.lower(),
        password=hash_password(password),
        account_level_id=get_account_level(db, "level 1").id,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    create_or_update_user_session(db, new_user, otp=otp)
    return new_user


# check if user has userdata
def user_has_userdata(db, user_id):
    return db.query(UserData).filter(UserData.user_id == user_id).first()


def get_active_user(db, user_id):
    return db.query(Users).filter(Users.id == user_id, Users.is_active == True).first()


# save user data
def save_user_data(
    db, user, first_name, last_name, phone_number, address, country, state, city
):
    new_user_data = UserData(
        user=user,
        first_name=first_name,
        last_name=last_name,
        phone_number=phone_number,
        address=address,
        country=country,
        state=state,
        city=city,
    )
    db.add(new_user_data)
    db.commit()
    db.refresh(new_user_data)
    if not user.user_account:
        logger.info("creating user account")
        create_user_account(db, user)
    return new_user_data


# create user account
def create_user_account(db, user):
    new_user_account = UserAccount(
        user=user, balance=DEFAULT_USER_BALANCE, book_balance=DEFAULT_USER_BALANCE
    )
    db.add(new_user_account)
    db.commit()
    db.refresh(new_user_account)
    return new_user_account


# user has account already
def user_has_account(db, user_id):
    return db.query(UserAccount).filter(UserAccount.user_id == user_id).first()


# phone number exists
def phone_number_exists(db, phone_number):
    return db.query(UserData).filter(UserData.phone_number == phone_number).first()


# add category
def add_new_category(db, name):
    cat_ex = category_exists(db, name)
    if cat_ex:
        logger.info("category exists")
        return cat_ex
    new_category = Categories(name=name)
    db.add(new_category)
    db.commit()
    db.refresh(new_category)
    return new_category


# category exists
def category_exists(db, name):
    return db.query(Categories).filter(Categories.name == name.lower()).first()


# get categories
def get_categories(db):
    return db.query(Categories).order_by(Categories.name).all()


# get user account number
def get_user_account_number(db, account_number, current_user):
    return (
        db.query(UserAccount)
        .filter(
            UserAccount.account_number == account_number,
            UserAccount.user != current_user,
        )
        .first()
    )


def process_transaction(
    db,
    user,
    amount,
    description,
    receiver_account_number,
    transaction_ref,
    session_id,
    receiver_name,
    receiver_user,
    receiver_transaction_ref,
    save_beneficiary,
):
    debit_user_transaction(
        db,
        user,
        amount,
        description,
        receiver_account_number,
        transaction_ref,
        session_id,
        receiver_name,
        receiver_user,
        receiver_transaction_ref,
        save_beneficiary,
    )
    return None


def debit_user_transaction(
    db,
    user,
    amount,
    description,
    receiver_account_number,
    transaction_ref,
    session_id,
    receiver_name,
    receiver_user,
    receiver_transaction_ref,
    save_beneficiary,
):

    if not check_sender_balance(user, amount):
        return "Insufficient balance"

    bal = user.user_account.balance
    new_bal = bal - amount
    user.user_account.balance = new_bal
    user.user_account.book_balance = new_bal
    new_transaction = Transactions(
        user=user,
        amount=amount,
        transaction_type=TransactionType.DEBIT,
        transaction_status=TransactionStatus.SUCCESS,
        receiver_account_number=receiver_account_number,
        description=description,
        category=get_category(db, "transfer"),
        transaction_ref=transaction_ref,
        current_balance=new_bal,
        book_balance=new_bal,
        session_id=session_id,
        receiver_name=receiver_name,
    )
    db.add(new_transaction)
    credit_user_transaction(
        db,
        receiver_user,
        amount,
        description,
        user.user_account.account_number,
        receiver_transaction_ref,
        session_id,
        f"{user.user_data.last_name} {user.user_data.first_name}",
    )
    db.commit()
    db.refresh(new_transaction)
    debit_payload = {
        "amount": amount,
        "receiver_account_number": receiver_account_number,
        "receiver_name": receiver_name,
        "description": description,
        "transaction_ref": transaction_ref,
        "session_id": session_id,
        "transaction_type": new_transaction.transaction_type.title(),
        "transaction_status": new_transaction.transaction_status.title(),
        "current_balance": "{:,.2f}".format(new_transaction.current_balance),
        "date": new_transaction.date,
        "sender_name": f"{user.user_data.last_name} {user.user_data.first_name}",
        "template_name": "debit.html",
        "subject": "Debit Transaction",
        "email": user.email,
    }
    send_mail.delay(debit_payload)
    if save_beneficiary:
        save_beneficiary_details(db, user, receiver_account_number, receiver_name)
    return new_transaction


def credit_user_transaction(
    db,
    user,
    amount,
    description,
    sender_account_number,
    transaction_ref,
    session_id,
    sender_name,
):
    bal = user.user_account.balance
    new_bal = bal + amount
    user.user_account.balance = new_bal
    user.user_account.book_balance = new_bal
    new_transaction = Transactions(
        user=user,
        amount=amount,
        transaction_type=TransactionType.CREDIT,
        transaction_status=TransactionStatus.SUCCESS,
        sender_account_number=sender_account_number,
        description=description,
        current_balance=new_bal,
        book_balance=new_bal,
        transaction_ref=transaction_ref,
        category=get_category(db, "top-up"),
        session_id=session_id,
        sender_name=sender_name,
    )
    db.add(new_transaction)
    db.commit()
    db.refresh(new_transaction)
    credit_payload = {
        "amount": amount,
        "transaction_type": new_transaction.transaction_type.title(),
        "transaction_status": new_transaction.transaction_status.title(),
        "sender_account_number": sender_account_number,
        "sender_name": sender_name,
        "description": description,
        "transaction_ref": transaction_ref,
        "current_balance": "{:,.2f}".format(new_transaction.current_balance),
        "date": new_transaction.date,
        "session_id": session_id,
        "receiver_name": f"{user.user_data.last_name} {user.user_data.first_name}",
        "template_name": "credit.html",
        "subject": "Credit Transaction",
        "email": user.email,
    }
    send_mail.delay(credit_payload)
    return new_transaction


# save beneficiary
def save_beneficiary_details(db, user, account_number, name):
    try:
        # Check if the beneficiary already exists
        existing_beneficiary = (
            db.query(Beneficiaries)
            .filter_by(account_number=account_number, user=user, name=name.lower())
            .first()
        )

        if existing_beneficiary:
            return existing_beneficiary  # Return the existing beneficiary object

        # Create and save the new beneficiary
        beneficiary = Beneficiaries(
            name=name.lower(), account_number=account_number, user=user
        )
        db.add(beneficiary)
        db.commit()
        db.refresh(beneficiary)
        return beneficiary

    except Exception as e:
        logger.exception("An error occurred while saving the beneficiary")
        db.rollback()  # Rollback the transaction on error
        raise ValueError(f"An error occurred while saving the beneficiary: {e}")


# check if sender has enough balance
def check_sender_balance(user, amount):
    return user.user_account.balance >= amount


def get_category(db, name):
    return db.query(Categories).filter(Categories.name == name.lower()).first()


# Get all transactions with filter and pagination
def get_transactions(
    db,
    user,
    page,
    per_page,
    trans_status=None,
    trans_type=None,
    session_id=None,
    trans_ref=None,
):
    base_query = db.query(Transactions).filter(Transactions.user == user)

    # Apply filters based on provided parameters
    if trans_status:
        base_query = base_query.filter(Transactions.transaction_status == trans_status)
    if trans_type:
        base_query = base_query.filter(Transactions.transaction_type == trans_type)
    if session_id:
        base_query = base_query.filter(Transactions.session_id == session_id)
    if trans_ref:
        base_query = base_query.filter(Transactions.transaction_ref == trans_ref)

    # Count total items before applying pagination
    total_count = base_query.count()

    # Order by date (recent first) and apply pagination
    transactions = (
        base_query.order_by(Transactions.date.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )

    # Return the pagination object
    return {
        "transactions": [t.to_dict() for t in transactions],
        "total_items": total_count,
        "page": page,
        "per_page": per_page,
        "total_pages": (total_count + per_page - 1) // per_page,
    }


# get beneficiaries
def get_beneficiaries_for_user(db, user, name):
    base_query = db.query(Beneficiaries).filter(Beneficiaries.user == user)
    if name:
        base_query = base_query.filter(Beneficiaries.name.ilike(f"%{name}%")).order_by(
            Beneficiaries.date.desc()
        )
    beneficiaries = base_query.all()
    return beneficiaries


def create_or_update_user_session(db, user, otp=None, token=None):
    user_session = db.query(UserSessions).filter_by(user_id=user.id).first()
    if user_session:
        if token:
            user_session.token = token
            user_session.used_token = False
            user_session.token_expired_date = datetime.now() + timedelta(
                minutes=SESSION_EXPIRES
            )
        if otp:
            user_session.otp = otp
            user_session.used_otp = False
            user_session.otp_expired_date = datetime.now() + timedelta(
                minutes=OTP_EXPIRES
            )
    else:
        user_session = UserSessions(user_id=user.id)
        if token:
            user_session.token = token
            user_session.used_token = False
            user_session.token_expired_date = datetime.now() + timedelta(
                minutes=SESSION_EXPIRES
            )
        if otp:
            user_session.otp = otp
            user_session.used_otp = False
            user_session.otp_expired_date = datetime.now() + timedelta(
                minutes=OTP_EXPIRES
            )
        db.add(user_session)
    db.commit()
    return user_session


def get_one_beneficiaries_for_user(db, user, ben_id):
    return (
        db.query(Beneficiaries)
        .filter(Beneficiaries.id == ben_id, Beneficiaries.user == user)
        .first()
    )


# extract user_id from request for rate limit
def get_user_id_from_request(request: Request):
    user_id = request.state.user_id
    logger.info(f"user_id: {user_id}")
    if not user_id:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return user_id


def add_levels(db):
    levels = [
        {
            "level": "level 1",
            "max_balance": 20000,
            "max_tf_per_day": 10000,
            "max_tf_once": 5000,
            "unlimited": False,
        },
        {
            "level": "level 2",
            "max_balance": 300000,
            "max_tf_per_day": 100000,
            "max_tf_once": 50000,
            "unlimited": False,
        },
        {
            "level": "level 3",
            "max_balance": 0,
            "max_tf_per_day": 10000000,
            "max_tf_once": 10000000,
            "unlimited": True,
        },
    ]
    for level in levels:
        if (
            not db.query(AccountLevels)
            .filter(AccountLevels.level == level["level"])
            .first()
        ):
            print("Adding level", level["level"])
            account_lev = AccountLevels(**level)
            db.add(account_lev)
            db.commit()
            db.refresh(account_lev)
    return True


def get_account_level(db, level):
    if not db.query(AccountLevels).first():
        add_levels(db)
    return db.query(AccountLevels).filter(AccountLevels.level == level).first()


# check user level limit
def check_user_level_limit(db, user, amount, category):
    try:
        # Get the user's account level details
        account_level = user.account_level

        # Calculate the new balance after the proposed transaction
        new_balance = user.user_account.balance + amount

        # If the account level is unlimited, we still want to check limits
        if account_level.unlimited:
            # Skip checks for max_balance if it is 0
            if 0 < account_level.max_balance < new_balance:
                return "Add to book balance", account_level.max_balance, new_balance

        # Check limits based on transaction category
        if category == "deposit":
            # Skip max_balance restriction if it is 0
            if 0 < account_level.max_balance < new_balance:
                return "Add to book balance", account_level.max_balance, new_balance

        # Additional checks for transfer limits
        if category == "transfer":
            # Check max_tf_once limit
            if 0 < account_level.max_tf_once < amount:
                return (
                    "Transfer amount exceeds the maximum allowed for this level",
                    None,
                    None,
                )

            # Calculate total transferred today
            today = datetime.now().date()
            daily_transfer_amount = (
                db.query(func.sum(Transactions.amount))
                .filter(Transactions.user_id == user.id, Transactions.date >= today)
                .scalar()
                or 0
            )  # Default to 0 if no transactions found

            # Check max_tf_per_day limit
            if 0 < account_level.max_tf_per_day < (daily_transfer_amount + amount):
                return "Daily transfer limit exceeded", None, None

        return True  # Return True only if all checks are passed
    except Exception as e:
        logger.exception("Error checking user level limit")
        return False, None, None
