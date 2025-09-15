from typing import Union

from fastapi import FastAPI

from database.database import SessionLocal, create_tables
from utilities import insert_sql_query, select_sql_query
from database.models import Users, Loans

import math

app = FastAPI()

# Create tables on startup
@app.on_event("startup")
def startup_event():
    create_tables()

#endpoint to make a user with a email address
@app.post("/users/{email_address}")
def create_user(email_address: str):
    db = SessionLocal()
    user_id = get_user_id_by_email_address(db, email_address)
    if user_id is None:
        make_new_user(db, email_address)
        user_id = get_user_id_by_email_address(db, email_address)

    return {"user_id": user_id}

def make_new_user(db: SessionLocal, email_address: str):
    user = Users(email=email_address)
    db.add(user)
    db.commit()
    db.refresh(user)
    return True

def get_user_id_by_email_address(db: SessionLocal, email_address: str):
    user = db.query(Users).filter(Users.email == email_address).first()
    if user:
        return user.id
    return None

@app.post("/loans/{user_id}")
def create_loan(user_id: int, amount: float, annual_interest_rate: float, loan_term_in_months: int):
    db = SessionLocal()

    loan = Loans(
        owner_id=user_id,
        amount=amount,
        annual_interest_rate=annual_interest_rate,
        loan_term_in_months=loan_term_in_months
    )

    db.add(loan)
    db.commit()
    db.refresh(loan)

    return {
        "loan_id": loan.id,
        "owner_id": loan.owner_id,
        "amount": loan.amount,
        "annual_interest_rate": loan.annual_interest_rate,
        "loan_term_in_months": loan.loan_term_in_months
    }

@app.get("/loans/{loan_id}")
def get_loan(loan_id: int):
    db = SessionLocal()
    try:
        loan = db.query(Loans).filter(Loans.id == loan_id).first()
        
        return {
            "loan_id": loan.id,
            "owner_id": loan.owner_id,
            "amount": loan.amount,
            "annual_interest_rate": loan.annual_interest_rate,
            "loan_term_in_months": loan.loan_term_in_months, 
            "shared_with": loan.shared_with
        }
    finally:
        db.close()

@app.get("/loans/user/{user_id}")
def get_loans(user_id: int):
    db = SessionLocal()
    loans = db.query(Loans).filter(Loans.owner_id == user_id).all()
    loans_list = []
    for loan in loans:
        loans_list.append({
            "loan_id": loan.id,
        })
    return loans_list

@app.post("/loans/share/{loan_id}")
def share_loan(loan_id: int, user_id: int):
    db = SessionLocal()
    loan = db.query(Loans).filter(Loans.id == loan_id).first()
    if user_id not in loan.shared_with and user_id != loan.owner_id:
        #add to shared with json 
        shared_with = loan.shared_with.copy()
        shared_with.append(user_id)
        loan.shared_with = shared_with
    db.commit()
    db.refresh(loan)
    return {
        "loan_id": loan.id,
        "shared_with": loan.shared_with
    }

@app.get("/loans/loan_schedule/{loan_id}")
def get_loan_schedule(loan_id: int):
    db = SessionLocal()
    loan = db.query(Loans).filter(Loans.id == loan_id).first()
    

@app.get("/loans/{loan_id}/schedule")
def get_loan_schedule(loan_id: int):
    db = SessionLocal()
    loan = db.query(Loans).filter(Loans.id == loan_id).first()

    if not loan:
        return {"error": "Loan not found"}

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

@app.get("/loans/{loan_id}/summary/{month}")
def get_loan_summary(loan_id: int, month: int):
    db = SessionLocal()
    loan = db.query(Loans).filter(Loans.id == loan_id).first()

    if not loan:
        return {"error": "Loan not found"}

    # Loan details
    principal = loan.amount
    annual_interest_rate = loan.annual_interest_rate
    months = loan.loan_term_in_months
    monthly_rate = annual_interest_rate / 12.0

    if month < 1 or month > months:
        return {"error": f"Month must be between 1 and {months}"}

    if monthly_rate > 0:
        monthly_payment = (
            principal * monthly_rate / (1 - math.pow(1 + monthly_rate, -months))
        )
    else:
        monthly_payment = principal / months

    balance = principal
    total_interest_paid = 0
    total_principal_paid = 0

    for m in range(1, month + 1):
        interest = balance * monthly_rate
        principal_payment = monthly_payment - interest
        balance -= principal_payment
        balance = max(balance, 0)

        total_interest_paid += interest
        total_principal_paid += principal_payment

    return {
        "loan_id": loan.id,
        "month": month,
        "remaining_balance": round(balance, 2),
        "aggregate_principal_paid": round(total_principal_paid, 2),
        "aggregate_interest_paid": round(total_interest_paid, 2),
    }








