from typing import Union
from pydantic import BaseModel
from fastapi import FastAPI
from fastapi import status
from fastapi import HTTPException
from pydantic import EmailStr

from database.database import SessionLocal, create_tables
from database.models import Users, Loans
from sqlalchemy.exc import IntegrityError

import math

app = FastAPI()

# Initialize database tables on startup
@app.on_event("startup")
def startup_event():
    create_tables()

"""
touch ups
- add pagination to get loans and loan schedule
- add v1
- add query strings only for filtering
- make user with email address in body
- fix database connection issues
"""

"""
SCHEMAS
"""
class UserCreate(BaseModel):
    email_address: EmailStr

class LoanCreate(BaseModel):
    amount: float
    annual_interest_rate: float
    loan_term_in_months: int

"""
ENDPOINTS
"""
@app.post("/v1/users", status_code=status.HTTP_201_CREATED)
def create_user(user: UserCreate):
    db = SessionLocal()
    try:
        new_user = Users(email=user.email_address)
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return {"user_id": new_user.id}
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already exists"
        )
    finally:
        db.close()

@app.post("/v1/users/{user_id}/loans", status_code=status.HTTP_201_CREATED)
def create_loan(user_id: int, loan: LoanCreate):
    # Validate loan parameters first
    if loan.amount <= 0 or loan.annual_interest_rate < 0 or loan.loan_term_in_months <= 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid loan parameters"
        )

    db = SessionLocal()

    user = None
    try:
        # Check if user exists
        user = db.query(Users).filter(Users.id == user_id).first()
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {e}"
        )
    finally:
        db.close()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id {user_id} not found"
        )

    # Create loan
    new_loan = Loans(
        owner_id=user_id,
        amount=loan.amount,
        annual_interest_rate=loan.annual_interest_rate,
        loan_term_in_months=loan.loan_term_in_months
    )

    try:
        db.add(new_loan)
        db.commit()
        db.refresh(new_loan)
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {e}"
        )
    finally:
        db.close()

    return {
        "loan_id": new_loan.id,
        "owner_id": new_loan.owner_id,
        "amount": new_loan.amount,
        "annual_interest_rate": new_loan.annual_interest_rate,
        "loan_term_in_months": new_loan.loan_term_in_months
    }

@app.get("/v1/users/{user_id}/loans")
def get_loans(user_id: int):
    db = SessionLocal()

    user = None
    try:
        # Check if user exists
        user = db.query(Users).filter(Users.id == user_id).first()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {e}"
        )
    finally:
        db.close()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id {user_id} not found"
        )

    # Fetch loans
    loans = None
    try:
        loans = db.query(Loans).filter(Loans.owner_id == user_id).all()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {e}"
        )
    finally:
        db.close()

    loans_list = [{"loan_id": loan.id} for loan in loans]

    return loans_list

@app.patch("/v1/users/{user_id}/loans/{loan_id}/share/{shared_with_user_id}", status_code=status.HTTP_200_OK)
def share_loan(user_id: int, loan_id: int, shared_with_user_id: int):
    db = SessionLocal()

    loan = None
    try:
        # Fetch loan from DB
        loan = db.query(Loans).filter(Loans.id == loan_id).first()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {e}"
        )
    finally:
        db.close()

    # Validate loan exists
    if not loan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Loan with id {loan_id} not found"
        )

    # Validate user permission
    if not (user_id == loan.owner_id or user_id in loan.shared_with):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to share this loan"
        )

    # Validate target user
    if shared_with_user_id in loan.shared_with or shared_with_user_id == loan.owner_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is already shared or is the loan owner"
        )

    # Update shared_with
    loan.shared_with.append(shared_with_user_id)

    try:
        db = SessionLocal()
        db.add(loan)
        db.commit()
        db.refresh(loan)
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {e}"
        )
    finally:
        db.close()

    return {
        "loan_id": loan.id,
        "shared_with": {
            "user_ids": loan.shared_with
        }
    }

@app.get("/v1/users/{user_id}/loans/{loan_id}/schedule")
def get_loan_schedule(user_id: int, loan_id: int):

    db = SessionLocal()
    # Fetch loan from DB
    loan = None
    try:
        db = SessionLocal()
        loan = db.query(Loans).filter(Loans.id == loan_id).first()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {e}"
        )
    finally:
        db.close()

    if not loan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Loan with id {loan_id} not found"
        )

    # Authorization check
    if user_id != loan.owner_id and user_id not in loan.shared_with:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Loan is not shared with user"
        )

    # Loan details
    principal = loan.amount
    annual_interest_rate = loan.annual_interest_rate
    months = loan.loan_term_in_months
    monthly_rate = annual_interest_rate / 12.0

    if monthly_rate > 0:
        monthly_payment = (
            principal * monthly_rate / (1 - math.pow(1 + monthly_rate, -months))
        )
    else:
        monthly_payment = principal / months

    balance = principal
    schedule = []

    for month in range(1, months + 1):
        interest = balance * monthly_rate
        principal_payment = monthly_payment - interest
        balance -= principal_payment
        balance = max(balance, 0)

        schedule.append({
            "month": month,
            "monthly_payment": round(monthly_payment, 2),
            "remaining_balance": round(balance, 2)
        })

    return {
        "schedule": schedule
    }

@app.get("/v1/users/{user_id}/loans/{loan_id}/schedule/{month}")
def get_loan_summary(user_id: int, loan_id: int, month: int):
    # Fetch loan from DB
    loan = None
    try:
        db = SessionLocal()
        loan = db.query(Loans).filter(Loans.id == loan_id).first()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {e}"
        )
    finally:
        db.close()

    if not loan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Loan with id {loan_id} not found"
        )

    # Authorization check
    if user_id != loan.owner_id and user_id not in loan.shared_with:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Loan is not shared with user"
        )

    # Validate month
    if month < 1 or month > loan.loan_term_in_months:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Month must be between 1 and {loan.loan_term_in_months}"
        )

    # Loan Calculations
    principal = loan.amount
    annual_interest_rate = loan.annual_interest_rate
    months = loan.loan_term_in_months
    monthly_rate = annual_interest_rate / 12.0

    if monthly_rate > 0:
        monthly_payment = principal * monthly_rate / (1 - math.pow(1 + monthly_rate, -months))
    else:
        monthly_payment = principal / months

    principal_balance = principal
    total_interest_paid = 0
    total_principal_paid = 0

    for m in range(1, month + 1):
        interest = principal_balance * monthly_rate
        principal_payment = monthly_payment - interest
        principal_balance -= principal_payment
        principal_balance = max(principal_balance, 0)

        total_interest_paid += interest
        total_principal_paid += principal_payment

    return {
        "loan_id": loan.id,
        "month": month,
        "principal_balance": round(principal_balance, 2),
        "aggregate_principal_paid": round(total_principal_paid, 2),
        "aggregate_interest_paid": round(total_interest_paid, 2),
    }







