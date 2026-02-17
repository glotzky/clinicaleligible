import sys
import os

# Ensure we can find the src folder
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from database import Session, CriteriaItem
from processor import get_icd10_codes # Updated import

def enrich_metadata():
    session = Session()
    
    # NEW LOGIC: Map everything in 'Other' that doesn't have a code yet
    unmapped = session.query(CriteriaItem).filter(
        CriteriaItem.icd10_code == None,
        CriteriaItem.category.in_(['Condition', 'Other', 'Medication'])
    ).all()

    print(f"🧬 Found {len(unmapped)} items to investigate for medical codes.")

    for item in unmapped:
        print(f"🔍 Mapping: {item.value[:50]}...")
        codes = get_icd10_codes(item.value)
        
        if codes:
            # We'll take the first/primary code for the main database column
            item.icd10_code = codes[0]
            print(f"✅ Assigned: {codes[0]}")
        else:
            print("⚠️ No code found.")
            
    session.commit()
    session.close()
    print("✨ Enrichment complete!")

if __name__ == "__main__":
    enrich_metadata()