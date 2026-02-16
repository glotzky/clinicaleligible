import requests
import os
from dotenv import load_dotenv

load_dotenv()

BASE_URL = os.getenv("CT_API_BASE_URL", "https://clinicaltrials.gov/api/v2")

def search_trials_by_condition(condition, max_results=10):  # Increased default to 10
    """Fetches a list of NCT IDs for a specific condition."""
    search_url = f"{BASE_URL}/studies"
    params = {
        "query.cond": condition,
        "pageSize": max_results,
        "fields": "NCTId",
        "format": "json"
    }
    
    try:
        response = requests.get(search_url, params=params)
        response.raise_for_status()
        data = response.json()
        
        nct_ids = []
        for study in data.get('studies', []):
            ident = study.get('protocolSection', {}).get('identificationModule', {})
            nct_id = ident.get('nctId')
            if nct_id:
                nct_ids.append(nct_id)
        return nct_ids
    except Exception as e:
        print(f"❌ Error searching API: {e}")
        return []

def fetch_trial_data(nct_id: str):
    """Fetches full data and generates the public study link."""
    url = f"{BASE_URL}/studies/{nct_id}"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        
        protocol = data.get("protocolSection", {})
        ident = protocol.get("identificationModule", {})
        
        return {
            "nct_id": nct_id,
            "title": ident.get("officialTitle") or ident.get("briefTitle") or "No Title",
            "criteria": protocol.get("eligibilityModule", {}).get("eligibilityCriteria", "No criteria found."),
            "study_url": f"https://clinicaltrials.gov/study/{nct_id}" # Standard V2 Link
        }
    except Exception as e:
        print(f"❌ Error fetching {nct_id}: {e}")
        return None