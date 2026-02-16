import streamlit as st
import pandas as pd
from sqlalchemy import create_engine

# --- 1. Setup ---
st.set_page_config(page_title="TrialIntel | Criteria Inspector", layout="wide")
engine = create_engine("sqlite:///./trials.db")

# IMPROVED CSS: High contrast and theme-friendly
st.markdown("""
    <style>
    /* Metric Cards Styling */
    div[data-testid="stMetric"] {
        background-color: rgba(255, 255, 255, 0.05); /* Subtle tint */
        padding: 15px;
        border-radius: 10px;
        border: 1px solid #4e4e4e;
    }
    /* Force specific label colors if needed */
    div[data-testid="stMetricLabel"] {
        color: #7d7d7d !important;
        font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. Data Loading (Same as before) ---
def get_all_trials():
    try:
        return pd.read_sql("SELECT nct_id, title FROM trials", engine)
    except:
        return pd.DataFrame()

def get_trial_details(nct_id):
    query = "SELECT type, category, entity, icd10_code, value FROM criteria_items WHERE trial_id = :nct"
    return pd.read_sql(query, engine, params={"nct": nct_id})

# --- 3. Sidebar ---
st.sidebar.header("📂 Trial Selection")
trials_df = get_all_trials()

if not trials_df.empty:
    trial_options = {f"{row['nct_id']} | {row['title'][:50]}...": row['nct_id'] for _, row in trials_df.iterrows()}
    selection = st.sidebar.selectbox("Choose a Trial to Inspect", options=list(trial_options.keys()))
    selected_nct = trial_options[selection]
else:
    st.sidebar.error("No trials found. Run main.py first.")
    st.stop()

# --- 4. Main Inspector View ---
st.title("🔍 Criteria Extraction Inspector")
st.caption(f"Inspecting NCT ID: {selected_nct}")

details = get_trial_details(selected_nct)

if not details.empty:
    # --- METRICS ROW WITH HIGH CONTRAST ---
    m1, m2, m3 = st.columns(3)
    
    inclusion_count = len(details[details['type'] == 'Inclusion'])
    exclusion_count = len(details[details['type'] == 'Exclusion'])
    
    m1.metric("Total Entities", len(details))
    # We use 'delta' to add a color indicator (Green for inclusion, Red for exclusion)
    m2.metric("Inclusion Rules", inclusion_count, delta="Required", delta_color="normal")
    m3.metric("Exclusion Rules", exclusion_count, delta="Disqualifying", delta_color="inverse")

    st.divider()

    # --- THE DATA TABLE ---
    st.subheader("📋 Extracted Data Points")
    # Styling the dataframe to be readable
    st.subheader("📋 Split Criteria View")
    inc_col, exc_col = st.columns(2)

    with inc_col:
        st.success("✅ Inclusion Criteria")
        inc_df = details[details['type'] == 'Inclusion'][['category', 'entity', 'icd10_code']]
        st.table(inc_df)

    with exc_col:
        st.error("❌ Exclusion Criteria")
        exc_df = details[details['type'] == 'Exclusion'][['category', 'entity', 'icd10_code']]
        st.table(exc_df)

else:
    st.warning("No data found for this trial.")