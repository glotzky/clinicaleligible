import time
from api_client import fetch_trial_data
from processor import parse_criteria
from database import init_db, save_structured_trial

# List of diverse trials for Batch Ingestion & ICD-10 testing
TRIAL_LIST = [
    "NCT03529110", # HER2+ Breast Cancer (Metastatic)
    "NCT05894954", # Early Dementia / Alzheimer's (Precision Medicine)
    "NCT02485626", # Cardiovascular Risk in Breast Cancer Survivors
    "NCT06589310", # Multi-cancer Early Detection (Registry)
    "NCT03688126", # Alzheimer's Prevention (POINTER study)
]

def run_batch():
    init_db()
    for nct_id in TRIAL_LIST:
        print(f"\n🚀 Processing {nct_id}...")
        try:
            trial = fetch_trial_data(nct_id)
            if not trial: continue
            
            structured = parse_criteria(trial['criteria'])
            save_structured_trial(trial, structured)
            
            print(f"✅ Successfully ingested: {trial['title'][:50]}...")
            time.sleep(1) # Brief pause to prevent rate limiting
        except Exception as e:
            print(f"❌ Failed {nct_id}: {e}")

if __name__ == "__main__":
    run_batch()