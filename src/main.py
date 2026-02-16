from api_client import fetch_trial_data
from processor import parse_criteria
from database import init_db, save_structured_trial

def run_pipeline(nct_id: str):
    init_db() # Ensure tables exist
    print(f"--- Processing {nct_id} ---")
    
    trial = fetch_trial_data(nct_id)
    if not trial: return
    
    print("🤖 AI is structuring the criteria...")
    structured = parse_criteria(trial['criteria'])
    
    print("💾 Saving to database...")
    save_structured_trial(trial, structured)
    
    print(f"\n✅ Done! Trial '{trial['title']}' is now stored locally.")

if __name__ == "__main__":
    run_pipeline("NCT06253572")