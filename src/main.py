from api_client import fetch_trial_data
from processor import parse_criteria

def run_pipeline(nct_id: str):
    print(f"--- Processing {nct_id} ---")
    
    # Step 1: Fetch
    trial = fetch_trial_data(nct_id)
    if not trial: return
    
    # Step 2: Parse (The AI Part)
    print("🤖 AI is structuring the criteria...")
    structured = parse_criteria(trial['criteria'])
    
    # Step 3: Display
    print(f"\nResults for: {trial['title']}")
    for item in structured.items:
        print(f" - {item.type}: {item.entity} ({item.value})")

if __name__ == "__main__":
    run_pipeline("NCT06253572") # Try the same ID you used before!