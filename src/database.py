from sqlalchemy import create_engine, Column, String, Integer, Text, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker, relationship

# 1. Setup Base and Engine
Base = declarative_base()
DB_URL = "sqlite:///./trials.db"
engine = create_engine(DB_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 2. Define Trial Model
class TrialRecord(Base):
    __tablename__ = "trials"
    
    nct_id = Column(String, primary_key=True, index=True)
    title = Column(String)
    raw_criteria = Column(Text)
    
    # Mirroring the relationship name in CriterionRecord
    structured_items = relationship("CriterionRecord", back_populates="trial", cascade="all, delete-orphan")

# 3. Define Criterion Model (The "Child" table)
class CriterionRecord(Base):
    __tablename__ = "criteria_items"
    
    id = Column(Integer, primary_key=True, index=True)
    trial_id = Column(String, ForeignKey("trials.nct_id"))
    category = Column(String)
    type = Column(String)
    entity = Column(String)
    icd10_code = Column(String, nullable=True) # Supports Step 3 (ICD-10)
    operator = Column(String, nullable=True)   # Supports operators
    value = Column(String)

    trial = relationship("TrialRecord", back_populates="structured_items")

# 4. Database Operations
def init_db():
    Base.metadata.create_all(bind=engine)

def save_structured_trial(trial_data: dict, structured_data):
    """Saves the fetched trial and its AI-parsed criteria."""
    db = SessionLocal()
    try:
        # Save the Trial (using merge to handle updates/duplicates)
        db_trial = TrialRecord(
            nct_id=trial_data['nct_id'],
            title=trial_data['title'],
            raw_criteria=trial_data['criteria']
        )
        db.merge(db_trial)
        
        # Save the individual criteria
        for item in structured_data.items:
            db_item = CriterionRecord(
                trial_id=trial_data['nct_id'],
                **item.model_dump() 
            )
            db.add(db_item)
            
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"Error saving to DB: {e}")
        raise
    finally:
        db.close()