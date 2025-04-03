from typing import Optional, List
from fastapi import APIRouter, status, Depends, HTTPException, Request
from schemas import (
    UserAccountResolveSchema,
    CreateTransactionSchema,
    ShowBeneficiarySchema,
)
from sqlalchemy.orm import Session
from func import (
    get_user_account_number,
    process_transaction,
    get_transactions,
    get_beneficiaries_for_user,
    get_one_beneficiaries_for_user,
    check_user_level_limit,
)
from ac_token import get_current_user
from models import Users
from database import get_db
from utils import generate_session_id, generate_transaction_reference
import traceback
from extensions import limiter
from logger import logger


transaction_router = APIRouter(prefix="/transaction", tags=["Transactions"])


@transaction_router.get(
    "/resolve_account/{account_number}",
    status_code=status.HTTP_200_OK,
    response_model=UserAccountResolveSchema,
)
async def resolve_account(
    account_number: str,
    current_user: Users = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        user_account = get_user_account_number(db, account_number, current_user)
        if not user_account:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Account does not exist"
            )
        return user_account
    except HTTPException as http_exc:
        # Log the HTTPException if needed
        logger.exception("An error occurred in resolve_account")
        raise http_exc
    except Exception as e:
        logger.exception("An error occurred in resolve_account")
        logger.error(f"{e} : error from resolve account")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Network Error"
        )


# send money
@transaction_router.post("/send", status_code=status.HTTP_200_OK)
@limiter.limit("1/second")
async def send_money(
    request: Request,
    send_data: CreateTransactionSchema,
    db: Session = Depends(get_db),
    current_user: Users = Depends(get_current_user),
):
    try:
        receiver_account_number = send_data.account_number
        amount = send_data.amount
        receiver_name = send_data.receiver_name
        description = send_data.description
        save_beneficiary = send_data.save_beneficiary

        receiver_user_account = get_user_account_number(
            db, receiver_account_number, current_user
        )
        if not receiver_user_account:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Account does not exist"
            )
        if amount <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Amount must be greater than 0",
            )
        if not receiver_name:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Receiver name is required",
            )
        # compare the receiver name with the receiver_user_account regardless of there arrangement
        if set(receiver_name.lower().split()) != set(
            f"{receiver_user_account.user.user_data.last_name} {receiver_user_account.user.user_data.first_name}".lower().split()
        ):
            logger.error(
                f"Receiver name sent {receiver_name} does not match {receiver_user_account.user.user_data.last_name} {receiver_user_account.user.user_data.first_name}"
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="The name sent does not belong to the account number",
            )
        resp = check_user_level_limit(db, current_user, amount, "transfer")
        if resp and not isinstance(resp, bool):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=resp)
        sender_trans_ref = generate_transaction_reference()
        receiver_trans_ref = generate_transaction_reference()
        session_id = generate_session_id()
        res = process_transaction(
            db,
            current_user,
            amount,
            description,
            receiver_account_number,
            sender_trans_ref,
            session_id,
            receiver_name,
            receiver_user_account.user,
            receiver_trans_ref,
            save_beneficiary,
        )
        if res and isinstance(res, str):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=res)
        return {"detail": "Money sent successfully"}
    except HTTPException as http_exc:
        # Log the HTTPException if needed
        logger.exception("An error occurred in send_money")
        raise http_exc
    except Exception as e:
        logger.exception("An error occurred in send_money")
        logger.error(f"{e} : error from send money")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Network Error"
        )


# get transaction history with pagination
@transaction_router.get("/history", status_code=status.HTTP_200_OK)
async def transaction_history(
    page: int = 1,
    per_page: int = 10,
    trans_status: Optional[str] = None,
    trans_type: Optional[str] = None,
    session_id: Optional[str] = None,
    trans_ref: Optional[str] = None,
    current_user: Users = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        trans_res = get_transactions(
            db,
            current_user,
            page,
            per_page,
            trans_status,
            trans_type,
            session_id,
            trans_ref,
        )
        return trans_res
    except HTTPException as http_exc:
        # Log the HTTPException if needed
        logger.exception("An error occurred in transaction_history")
        raise http_exc
    except Exception as e:
        logger.exception("An error occurred in transaction_history")
        logger.error(f"{e} : error from transaction history")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Network Error"
        )


# get beneficiaries
@transaction_router.get(
    "/beneficiaries",
    status_code=status.HTTP_200_OK,
    response_model=List[ShowBeneficiarySchema],
)
async def get_beneficiaries(
    name: Optional[str] = None,
    current_user: Users = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        beneficiaries = get_beneficiaries_for_user(db, current_user, name)
        return beneficiaries
    except HTTPException as http_exc:
        # Log the HTTPException if needed
        logger.exception("An error occurred in get_beneficiaries")
        raise http_exc
    except Exception as e:
        logger.exception("An error occurred in get_beneficiaries")
        logger.error(f"{e} : error from get beneficiaries")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Network Error"
        )


# load one beneficiary
@transaction_router.get(
    "/beneficiary/{beneficiary_id}",
    status_code=status.HTTP_200_OK,
    response_model=ShowBeneficiarySchema,
)
async def get_beneficiary(
    beneficiary_id: str,
    current_user: Users = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        beneficiary = get_one_beneficiaries_for_user(db, current_user, beneficiary_id)
        if not beneficiary:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Beneficiary not found"
            )
        return beneficiary
    except HTTPException as http_exc:
        # Log the HTTPException if needed
        logger.exception("An error occurred in get beneficiary")
        raise http_exc
    except Exception as e:
        logger.exception("An error occurred in get beneficiary")
        logger.error(f"{e} : error from get beneficiary")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Network Error"
        )
