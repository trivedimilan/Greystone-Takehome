from typing import Union

from fastapi import FastAPI

from database.database import SessionLocal, create_tables
from utilities import insert_sql_query, select_sql_query
from database.models import Users, Loans

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
            "loan_term_in_months": loan.loan_term_in_months
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








