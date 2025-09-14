from sqlalchemy import Column, Integer, String, Float
from database.database import Base
from sqlalchemy.orm import relationship


class Users(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    loans = relationship("Loan", back_populates="owner")
