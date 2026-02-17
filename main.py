import time
import sys
import os

# Ensure src is in the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from api_client import fetch_trial_data
from processor import parse_criteria
from database import init_db, save_structured_trial

TRIAL_LIST = [
    "NCT03529110", "NCT05894954", "NCT02485626", "NCT06589310", "NCT03688126"
]

def run_batch():
    init_db()
    for nct_id in TRIAL_LIST:
        print(f"\n🚀 Processing {nct_id}...")
        try:
            trial = fetch_trial_data(nct_id)
            if not trial: continue
            
            raw_text = trial['criteria']
            
            # 1. Split text to find the Exclusion section
            # ClinicalTrials.gov usually uses 'Exclusion Criteria:' as a header
            parts = raw_text.split("Exclusion Criteria:")
            
            inc_text = parts[0]
            exc_text = parts[1] if len(parts) > 1 else ""

            # 2. Process both sections separately
            print(f"   Parsing Inclusion...")
            structured_inc = parse_criteria(inc_text)
            
            # Force the type to 'Exclusion' for the second pass
            structured_exc = None
            if exc_text:
                print(f"   Parsing Exclusion...")
                structured_exc = parse_criteria(exc_text)
                for item in structured_exc.items:
                    item.type = "Exclusion"

            # 3. Combine and Save
            if structured_exc:
                structured_inc.items.extend(structured_exc.items)
            
            save_structured_trial(trial, structured_inc)
            
            print(f"✅ Successfully ingested: {trial['title'][:50]}...")
            time.sleep(1) 
            
        except Exception as e:
            print(f"❌ Failed {nct_id}: {e}")

if __name__ == "__main__":
    run_batch()