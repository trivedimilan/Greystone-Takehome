from typing import Union

from fastapi import FastAPI

from database.database import SessionLocal, create_tables
from utilities import insert_sql_query, select_sql_query
from database.models import Users

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
        user_id = make_new_user(db, email_address)

    return {"user_id": user_id}

def make_new_user(db: SessionLocal, email_address: str):
    user = Users(email=email_address)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user.id

def get_user_id_by_email_address(db: SessionLocal, email_address: str):
    user = db.query(User).filter(User.email == email_address).first()
    if user:
        return user.id
    return None









