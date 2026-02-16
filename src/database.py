from sqlalchemy import create_engine, Column, String, Integer, Text, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from sqlalchemy.dialects.sqlite import insert

# The 'Base' class is what all our database models will inherit from
Base = declarative_base()
DB_URL = "sqlite:///./trials.db"
engine = create_engine(DB_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class TrialRecord(Base):
    __tablename__ = "trials"
    
    nct_id = Column(String, primary_key=True, index=True)
    title = Column(String)
    raw_criteria = Column(Text)
    
    # Relationship to the individual parsed items
    structured_items = relationship("CriterionRecord", back_populates="trial")

class CriterionRecord(Base):
    __tablename__ = "criteria_items"
    
    id = Column(Integer, primary_key=True, index=True)
    trial_id = Column(String, ForeignKey("trials.nct_id"))
    category = Column(String)
    type = Column(String)
    entity = Column(String)
    # --- ADD THIS LINE ---
    operator = Column(String, nullable=True) 
    # ---------------------
    value = Column(String)
    
    trial = relationship("TrialRecord", back_populates="structured_items")

# Create the tables
def init_db():
    Base.metadata.create_all(bind=engine)

def save_structured_trial(trial_data: dict, structured_data):
    """
    Saves the fetched trial and its AI-parsed criteria.
    'structured_data' is the Pydantic object from processor.py
    """
    db = SessionLocal()
    try:
        # 1. Save the main Trial record
        db_trial = TrialRecord(
            nct_id=trial_data['nct_id'],
            title=trial_data['title'],
            raw_criteria=trial_data['criteria']
        )
        db.merge(db_trial) # 'merge' handles updates if the NCT_ID already exists
        
        # 2. Save the individual criteria
        for item in structured_data.items:
            db_item = CriterionRecord(
                trial_id=trial_data['nct_id'],
                **item.model_dump() # Effortlessly convert Pydantic to DB model
            )
            db.add(db_item)
            
        db.commit()
    finally:
        db.close()