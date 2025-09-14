from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Example for SQLite
DATABASE_URL = "sqlite:///./database.db"

engine = create_engine(DATABASE_URL, echo=True)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

# Create tables
def create_tables():
    Base.metadata.create_all(bind=engine)
