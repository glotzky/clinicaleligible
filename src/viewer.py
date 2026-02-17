import pandas as pd
from sqlalchemy import create_engine
import os

# Connect to the database we just created
DB_URL = "sqlite:///./trials.db"
engine = create_engine(DB_URL)

def view_data():
    print("\n" + "="*50)
    print("       CLINICAL TRIAL STRUCTURED DATA")
    print("="*50)

    try:
        # 1. Load the data using Pandas
        query = """
        SELECT 
            t.nct_id, 
            c.type, 
            c.category, 
            c.entity, 
            c.icd10_code, -- New Column added here!
            c.operator, 
            c.value 
        FROM trials t
        JOIN criteria_items c ON t.nct_id = c.trial_id
        """
        df = pd.read_sql(query, engine)

        if df.empty:
            print("No data found in the database.")
            return

        # 2. Display the table
        print(df.to_string(index=False))
        print("="*50 + "\n")

    except Exception as e:
        print(f"❌ Error reading database: {e}")

if __name__ == "__main__":
    view_data()