from sqlalchemy import create_engine, Column, String, Integer, Text, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker, relationship

# 1. Setup Base and Engine
Base = declarative_base()
DB_URL = "sqlite:///./trials.db"
engine = create_engine(DB_URL, connect_args={"check_same_thread": False})
# This is your session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 2. Define Trial Model
class TrialRecord(Base):
    __tablename__ = "trials"
    
    nct_id = Column(String, primary_key=True, index=True)
    title = Column(String)
    raw_criteria = Column(Text)
    
    structured_items = relationship("CriterionRecord", back_populates="trial", cascade="all, delete-orphan")

# 3. Define Criterion Model
class CriterionRecord(Base):
    __tablename__ = "criteria_items"
    
    id = Column(Integer, primary_key=True, index=True)
    trial_id = Column(String, ForeignKey("trials.nct_id"))
    category = Column(String)
    type = Column(String)
    entity = Column(String)
    icd10_code = Column(String, nullable=True) 
    operator = Column(String, nullable=True)   
    value = Column(String)
    min_age = Column(Integer, nullable=True)
    max_age = Column(Integer, nullable=True)
    
    trial = relationship("TrialRecord", back_populates="structured_items")

# 4. Database Operations
def init_db():
    Base.metadata.create_all(bind=engine)

def save_structured_trial(trial_data, structured_criteria):
    # Use SessionLocal() to create a new session instance
    session = SessionLocal()
    try:
        # 1. Save/Update the Trial header
        trial_rec = TrialRecord(
            nct_id=trial_data['nct_id'],
            title=trial_data['title'],
            raw_criteria=trial_data.get('criteria', "")
        )
        session.merge(trial_rec) 

        # 2. Save each Criterion item
        for item in structured_criteria.items:
            new_criterion = CriterionRecord(
                trial_id=trial_data['nct_id'],
                category=item.category,
                type=item.type,
                entity=item.entity,
                icd10_code=item.icd10_code,
                operator=item.operator,
                value=item.value,
                min_age=item.min_age,
                max_age=item.max_age
            )
            session.add(new_criterion)
        
        session.commit()
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()