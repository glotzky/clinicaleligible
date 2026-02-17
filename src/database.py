from sqlalchemy import create_engine, Column, String, Integer, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()

class Trial(Base):
    __tablename__ = 'trials'
    nct_id = Column(String, primary_key=True)
    title = Column(String)
    criteria_raw = Column(Text)

class CriteriaItem(Base):
    __tablename__ = 'criteria_items'
    id = Column(Integer, primary_key=True)
    trial_id = Column(String, ForeignKey('trials.nct_id'))
    type = Column(String) 
    category = Column(String)
    entity = Column(String)
    icd10_code = Column(String, nullable=True)
    operator = Column(String, nullable=True) # Added to match AI output
    value = Column(String)

# Database Setup
engine = create_engine("sqlite:///./trials.db")
Session = sessionmaker(bind=engine)

def init_db():
    Base.metadata.create_all(engine)
    print("Database initialized successfully.")

def save_structured_trial(trial_data, structured_obj):
    session = Session()
    try:
        # 1. Save or Update the Trial header
        new_trial = Trial(
            nct_id=trial_data['nct_id'],
            title=trial_data['title'],
            criteria_raw=trial_data['criteria']
        )
        session.merge(new_trial)
        
        # 2. CLEAR PREVIOUS ITEMS for this NCT ID
        session.query(CriteriaItem).filter(CriteriaItem.trial_id == trial_data['nct_id']).delete()
        
        # 3. Add New Items
        for item in structured_obj.items:
            new_item = CriteriaItem(
                trial_id=trial_data['nct_id'],
                type=item.type,
                category=item.category,
                entity=item.entity,
                icd10_code=getattr(item, 'icd10_code', None), # Safe access
                operator=getattr(item, 'operator', 'NOT_APPLICABLE'),
                value=item.value
            )
            session.add(new_item)
            
        session.commit()
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()