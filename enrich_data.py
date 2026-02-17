import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from database import Session, CriteriaItem
from processor import get_icd10_codes # Updated import

def enrich_metadata():
    session = Session()
    unmapped = session.query(CriteriaItem).filter(
        CriteriaItem.icd10_code == None,
        CriteriaItem.category.in_(['Condition', 'Other', 'Medication'])
    ).all()

    print(f"🧬 Found {len(unmapped)} items to investigate for medical codes.")

    for item in unmapped:
        print(f"🔍 Mapping: {item.value[:50]}...")
        codes = get_icd10_codes(item.value)
        
        if codes:
            item.icd10_code = codes[0]
            print(f"✅ Assigned: {codes[0]}")
        else:
            print("⚠️ No code found.")
            
    session.commit()
    session.close()
    print("✨ Enrichment complete!")

if __name__ == "__main__":
    enrich_metadata()