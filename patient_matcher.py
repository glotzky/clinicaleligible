import sys
import os

# Ensure the script can locate the src directory
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from database import Session, CriteriaItem, Trial
from processor import get_icd10_codes 

def match_patient():
    print("\n" + "="*60)
    print("🧠 CLINICAL TRIAL INTELLIGENCE ENGINE (Ranked)")
    print("="*60)
    
    query = input("Describe the patient: ")
    patient_codes = get_icd10_codes(query)
    
    if not patient_codes:
        print("❌ Could not identify any medical codes.")
        return

    # Filter to unique 3-char families (e.g., C50, I42) to avoid redundant searches
    unique_prefixes = sorted(list(set(code[:3] for code in patient_codes)))
    session = Session()
    
    # Store results in a dictionary for easy scoring and grouping
    # trial_id -> { "trial": Trial object, "matches": [List of Criteria], "score": int, "alerts": [List of strings] }
    scored_results = {}

    for prefix in unique_prefixes:
        # Search all categories (including 'Other') for inclusion criteria matching the code family
        matches = session.query(CriteriaItem, Trial).join(Trial).filter(
            CriteriaItem.type == 'Inclusion',
            CriteriaItem.icd10_code.ilike(f"{prefix}%")
        ).all()
        
        for item, trial in matches:
            if trial.nct_id not in scored_results:
                scored_results[trial.nct_id] = {
                    "trial": trial, 
                    "matches": [], 
                    "score": 0,
                    "alerts": []
                }
            
            # Prevent adding the exact same criteria text twice
            if item.value not in [m.value for m in scored_results[trial.nct_id]["matches"]]:
                scored_results[trial.nct_id]["matches"].append(item)
            
            # SCORING LOGIC (Inclusion)
            # Heavy weight for primary diseases (C=Cancer, I=Circulatory, J=Respiratory)
            if prefix.startswith(('C', 'D', 'I', 'J')):
                scored_results[trial.nct_id]["score"] += 10
            # Medium weight for symptoms/signs
            elif prefix.startswith('R'):
                scored_results[trial.nct_id]["score"] += 5
            # Low weight for Z-codes (status, history, lifestyle)
            else:
                scored_results[trial.nct_id]["score"] += 1

    # POST-PROCESSING: SAFETY CHECK & DEMOTION
    # We check every trial found for potential exclusions based on ALL patient codes
    for nct_id, data in scored_results.items():
        for p_prefix in unique_prefixes:
            exclusion = session.query(CriteriaItem).filter(
                CriteriaItem.trial_id == nct_id,
                CriteriaItem.type == 'Exclusion',
                CriteriaItem.icd10_code.ilike(f"{p_prefix}%")
            ).first()
            
            if exclusion:
                data["alerts"].append(f"Excludes {p_prefix}: {exclusion.value[:80]}...")
                # THE REJECTION PENALTY: Sinks the trial to the bottom
                data["score"] -= 100 

    # Sort results by score (highest relevance first)
    sorted_trials = sorted(scored_results.values(), key=lambda x: x["score"], reverse=True)

    # OUTPUT RESULTS
    for result in sorted_trials:
        trial = result["trial"]
        score = result["score"]
        
        # Determine status color/icon based on score
        status_icon = "⭐" if score > 0 else "🚫"
        
        print(f"\n{status_icon} RANKING SCORE: {score}")
        print(f"🆔 {trial.nct_id}: {trial.title}")
        
        # Print the inclusion highlights
        for m in result["matches"]:
            print(f"   🔹 Matched Inclusion: {m.value[:100]}...")

        # Print safety alerts if any
        if result["alerts"]:
            for alert in result["alerts"]:
                print(f"   ⚠️  SAFETY ALERT: {alert}")
        
        print("-" * 60)

    if not sorted_trials:
        print("😔 No trial matches found in the current database.")

    session.close()

if __name__ == "__main__":
    match_patient()