import requests
import os
from dotenv import load_dotenv

load_dotenv()

BASE_URL = os.getenv("CT_API_BASE_URL", "https://clinicaltrials.gov/api/v2")

def fetch_trial_data(nct_id: str):
    """
    Fetches a single trial's data by its NCT ID.
    Example nct_id: 'NCT00000102'
    """
    url = f"{BASE_URL}/studies/{nct_id}"
    
    try:
        response = requests.get(url)
        response.raise_for_status() # Raises an error for 404s, 500s, etc.
        data = response.json()
        
        # Digging into the specific module we need for Project 1
        protocol = data.get("protocolSection", {})
        eligibility = protocol.get("eligibilityModule", {})
        criteria_text = eligibility.get("eligibilityCriteria", "No criteria found.")
        
        # Get the title so the UI looks nice
        title = protocol.get("identificationModule", {}).get("officialTitle", "No Title")
        
        return {
            "nct_id": nct_id,
            "title": title,
            "criteria": criteria_text
        }
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Error fetching {nct_id}: {e}")
        return None

if __name__ == "__main__":
    # Quick test to see if it works
    test_id = "NCT06253572" # A recent study on Heart Failure
    result = fetch_trial_data(test_id)
    if result:
        print(f"✅ Successfully fetched: {result['title']}")
        print(f"--- Criteria Snippet ---\n{result['criteria'][:200]}...")