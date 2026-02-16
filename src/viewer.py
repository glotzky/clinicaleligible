import pandas as pd
from sqlalchemy import create_engine
from database import DB_URL

def view_results():
    engine = create_engine(DB_URL)
    
    # Use Pandas to read the SQL tables
    try:
        df_trials = pd.read_sql("SELECT * FROM trials", engine)
        df_items = pd.read_sql("SELECT * FROM criteria_items", engine)
        
        print("\n=== STORED TRIALS ===")
        print(df_trials[['nct_id', 'title']].to_string(index=False))
        
        print("\n=== STRUCTURED CRITERIA (Sample) ===")
        # Merge them to see which criteria belongs to which trial
        merged = pd.merge(df_items, df_trials[['nct_id']], left_on='trial_id', right_on='nct_id')
        print(merged[['trial_id', 'type', 'category', 'entity', 'value']].head(20).to_string(index=False))
        
    except Exception as e:
        print(f"No data found yet! Error: {e}")

if __name__ == "__main__":
    view_results()