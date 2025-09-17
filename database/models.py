from sqlalchemy import Column, Integer, String, Float, ForeignKey, JSON
from database.database import Base
from sqlalchemy.orm import relationship
from sqlalchemy.ext.mutable import MutableList


class Users(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    loans = relationship("Loans", back_populates="owner")

class Loans(Base):
    __tablename__ = "loans"
    
    id = Column(Integer, primary_key=True, index=True)

    owner_id = Column(Integer, ForeignKey("users.id"))
    #foreign key to users table
    owner = relationship("Users", back_populates="loans")
    amount = Column(Float)
    annual_interest_rate = Column(Float)
    loan_term_in_months = Column(Integer)
    shared_with = Column(MutableList.as_mutable(JSON), default=[])