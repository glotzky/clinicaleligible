import os
from sqlalchemy import create_engine, Column, String, Integer, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Trial(Base):
    __tablename__ = "trials"
    nct_id = Column(String, primary_key=True, index=True)
    condition = Column(String)
    raw_criteria = Column(String)
    structured_criteria = Column(JSON)  # This stores the AI output

def init_db():
    Base.metadata.create_all(bind=engine)