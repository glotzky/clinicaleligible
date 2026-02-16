import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
import time # Added for small delays if needed

# --- 1. Setup ---
st.set_page_config(page_title="TrialIntel | Criteria Inspector", layout="wide")
engine = create_engine("sqlite:///./trials.db")

# --- 2. Data Loading Helpers ---
def get_local_trials(query=None):
    try:
        if query:
            sql = """
                SELECT DISTINCT t.nct_id, t.title 
                FROM trials t
                LEFT JOIN criteria_items c ON t.nct_id = c.trial_id
                WHERE t.nct_id LIKE :q OR t.title LIKE :q OR c.entity LIKE :q
            """
            return pd.read_sql(sql, engine, params={"q": f"%{query}%"})
        return pd.read_sql("SELECT nct_id, title FROM trials", engine)
    except:
        return pd.DataFrame()

def get_trial_details(nct_id):
    query = "SELECT type, category, entity, icd10_code, value FROM criteria_items WHERE trial_id = :nct"
    return pd.read_sql(query, engine, params={"nct": nct_id})

def check_exists(nct_id):
    """Check if the trial is already in our local database."""
    query = "SELECT nct_id FROM trials WHERE nct_id = :id"
    res = pd.read_sql(query, engine, params={"id": nct_id})
    return not res.empty

# --- 3. Sidebar: Dual Search Mode ---
st.sidebar.title("🧬 Trial Discovery")
mode = st.sidebar.radio("Search Mode", ["Local Database", "Live API (Web)"])

search_query = st.sidebar.text_input("Search Condition/ID", placeholder="e.g. Breast Cancer")

selected_nct = None

if mode == "Local Database":
    trials_df = get_local_trials(search_query)
    if not trials_df.empty:
        trial_options = {f"{r['nct_id']} | {r['title'][:40]}...": r['nct_id'] for _, r in trials_df.iterrows()}
        selected_nct = trial_options[st.sidebar.selectbox(f"Local Matches ({len(trials_df)})", options=list(trial_options.keys()))]
    else:
        st.sidebar.info("No local matches found.")

else: # Live API Mode
    if search_query:
        if st.sidebar.button(f"🔍 Fetch 10 Results for '{search_query}'"):
            status_container = st.sidebar.empty()
            with st.spinner("Accessing ClinicalTrials.gov..."):
                from api_client import search_trials_by_condition, fetch_trial_data
                from processor import parse_criteria
                from database import save_structured_trial
                
                new_ids = search_trials_by_condition(search_query, max_results=10)
                
                if new_ids:
                    processed_count = 0
                    for nct_id in new_ids:
                        # 1. Skip if already processed
                        if check_exists(nct_id):
                            status_container.info(f"Skipping {nct_id} (Already in DB)")
                            continue
                        
                        # 2. Fetch and Parse
                        status_container.text(f"Processing {nct_id}...")
                        trial = fetch_trial_data(nct_id)
                        if trial:
                            try:
                                structured = parse_criteria(trial['criteria'])
                                save_structured_trial(trial, structured)
                                processed_count += 1
                                # Small sleep to respect Rate Limits on free tier
                                time.sleep(1) 
                            except Exception as e:
                                st.sidebar.error(f"Failed to parse {nct_id}: AI was too confused!")
                                continue
                                
                    st.sidebar.success(f"Added {processed_count} new trials!")
                    st.rerun()
    st.sidebar.info("Type a condition and click 'Fetch' to pull new trials from ClinicalTrials.gov.")

# --- 4. Main Inspector View ---
# (Rest of your code remains the same for viewing logic)
if selected_nct:
    st.title("🔍 Criteria Extraction Inspector")
    
    col_a, col_b = st.columns([3, 1])
    with col_a:
        st.caption(f"Currently inspecting: **{selected_nct}**")
    with col_b:
        st.markdown(f"[🌐 View on ClinicalTrials.gov](https://clinicaltrials.gov/study/{selected_nct})")

    details = get_trial_details(selected_nct)
    
    if not details.empty:
        m1, m2, m3 = st.columns(3)
        inc = details[details['type'] == 'Inclusion']
        exc = details[details['type'] == 'Exclusion']
        
        m1.metric("Total Entities", len(details))
        m2.metric("Inclusion Rules", len(inc), delta="Required")
        m3.metric("Exclusion Rules", len(exc), delta="Disqualifying", delta_color="inverse")

        st.divider()

        st.subheader("📋 Eligibility Breakdown")
        c1, c2 = st.columns(2)
        with c1:
            st.success("✅ Inclusion")
            st.dataframe(inc[['category', 'entity', 'icd10_code']], use_container_width=True)
        with c2:
            st.error("❌ Exclusion")
            st.dataframe(exc[['category', 'entity', 'icd10_code']], use_container_width=True)
else:
    st.title("Welcome to TrialIntel")
    st.info("Select a trial from the sidebar to begin inspection.")