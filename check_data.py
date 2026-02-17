import sys
import os
from sqlalchemy import func

sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from database import Session, CriteriaItem, Trial

def run_diagnostics():
    session = Session()
    
    try:
        print("\n" + "="*50)
        print("📊 CLINICAL TRIAL DATABASE AUDIT")
        print("="*50)

        # 1. HIGH LEVEL TOTALS
        trial_count = session.query(Trial).count()
        criteria_count = session.query(CriteriaItem).count()
        
        print(f"Total Trials Processed:    {trial_count}")
        print(f"Total Structured Criteria: {criteria_count}")
        print("-" * 50)

        # 2. CATEGORY DISTRIBUTION
        print("🗂  CRITERIA BY CATEGORY:")
        stats = session.query(
            CriteriaItem.category, 
            func.count(CriteriaItem.id)
        ).group_by(CriteriaItem.category).order_by(func.count(CriteriaItem.id).desc()).all()

        for category, count in stats:
            print(f" - {category:<12}: {count}")
        print("-" * 50)

        # 3. ICD-10 ENRICHMENT STATUS
        print("🧬 MEDICAL CODING (ICD-10) STATUS:")
        conditions = session.query(CriteriaItem).filter(CriteriaItem.category == 'Condition').all()
        total_conditions = len(conditions)
        mapped_conditions = len([c for c in conditions if c.icd10_code])
        
        print(f" Total Conditions: {total_conditions}")
        print(f" Mapped to ICD-10: {mapped_conditions} ({ (mapped_conditions/total_conditions*100) if total_conditions > 0 else 0:.1f}%)")
        
        # Show top 5 mapped conditions
        if mapped_conditions > 0:
            print("\n Sample Mappings:")
            for c in conditions[:5]:
                code_str = f"[{c.icd10_code}]" if c.icd10_code else "[UNMAPPED]"
                print(f"   {code_str:<10} {c.value[:50]}...")
        print("-" * 50)

        # 4. TRIAL PROTOCOL STRICTNESS
        print("⚖️  TRIAL STRICTNESS (Inclusion vs Exclusion):")
        trial_stats = session.query(
            CriteriaItem.trial_id,
            func.count(CriteriaItem.id).filter(CriteriaItem.type == 'Inclusion'),
            func.count(CriteriaItem.id).filter(CriteriaItem.type == 'Exclusion')
        ).group_by(CriteriaItem.trial_id).all()

        print(f"{'NCT ID':<15} | {'Inclusion':<10} | {'Exclusion':<10}")
        for tid, inc, exc in trial_stats:
            print(f"{tid:<15} | {inc:<10} | {exc:<10}")

    except Exception as e:
        print(f"❌ Error running audit: {e}")
    finally:
        session.close()
        print("="*50 + "\n")

if __name__ == "__main__":
    run_diagnostics()