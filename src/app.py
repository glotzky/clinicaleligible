import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
import time
import datetime
import re
import sys
import os

# Get the absolute path to the directory this script is in (src/)
current_dir = os.path.dirname(os.path.abspath(__file__))

# Point to the database in the PROJECT ROOT (one level up from src/)
db_path = os.path.join(os.path.dirname(current_dir), "trials.db")

# Create engine using the absolute path
engine = create_engine(f"sqlite:///{db_path}")

# Ensure we can find the modules in src
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
# --- 1. Setup ---
st.set_page_config(page_title="TrialIntel", layout="wide", page_icon="🧬")

# Go up one level to the project root where trials.db usually lives
project_root = os.path.dirname(current_dir)

# Create engine using the absolute path

from processor import get_icd10_codes

# --- 1. Setup ---
st.set_page_config(page_title="TrialIntel", layout="wide", page_icon="🧬")
engine = create_engine("sqlite:///./trials.db")

# --- 2. Helper Functions ---
def get_wait_time(error_message):
    match = re.search(r"again in (?:(\d+)h)?(?:(\d+)m)?([\d\.]+)s", error_message)
    if match:
        hrs = int(match.group(1)) if match.group(1) else 0
        mins = int(match.group(2)) if match.group(2) else 0
        secs = float(match.group(3))
        return (hrs * 3600) + (mins * 60) + secs
    return 60 

def get_local_trials():
    try:
        return pd.read_sql("SELECT DISTINCT nct_id, title FROM trials", engine)
    except:
        return pd.DataFrame()

def get_trial_criteria(nct_id):
    try:
        query = "SELECT type, category, entity, value, icd10_code FROM criteria_items WHERE trial_id = :id"
        return pd.read_sql(query, engine, params={"id": nct_id})
    except:
        return pd.DataFrame()

def check_exists(nct_id):
    try:
        res = pd.read_sql("SELECT nct_id FROM trials WHERE nct_id = :id", engine, params={"id": nct_id})
        return not res.empty
    except:
        return False

# --- 3. Sidebar: Discovery ---
st.sidebar.title("🧬 Trial Discovery")

if "cooldown_until" not in st.session_state:
    st.session_state.cooldown_until = None

is_cooling_down = False
if st.session_state.cooldown_until:
    if datetime.datetime.now() < st.session_state.cooldown_until:
        is_cooling_down = True
    else:
        st.session_state.cooldown_until = None

search_query = st.sidebar.text_input("New API Search", placeholder="e.g. Melanoma", disabled=is_cooling_down)

if st.sidebar.button("🔍 Fetch from Web", disabled=is_cooling_down):
    if not search_query:
        st.sidebar.warning("Please enter a condition.")
    else:
        from api_client import search_trials_by_condition, fetch_trial_data
        from processor import parse_criteria
        from database import save_structured_trial
        
        status = st.sidebar.empty()
        status.info(f"Searching web for '{search_query}'...")
        
        new_ids = search_trials_by_condition(search_query, max_results=5)
        processed_count = 0
        skipped_count = 0

        for nct_id in new_ids:
            if check_exists(nct_id):
                skipped_count += 1
                continue
            
            try:
                status.text(f"Processing: {nct_id}...")
                trial = fetch_trial_data(nct_id)
                if trial:
                    structured = parse_criteria(trial['criteria'])
                    save_structured_trial(trial, structured)
                    processed_count += 1
                    time.sleep(1)
            except Exception as e:
                raw_err = str(e)
                if "429" in raw_err or "rate_limit" in raw_err:
                    total_seconds = get_wait_time(raw_err)
                    st.session_state.cooldown_until = datetime.datetime.now() + datetime.timedelta(seconds=total_seconds)
                    st.rerun()
                else:
                    st.sidebar.error(f"❌ Failed {nct_id}")
                    with st.sidebar.expander("View Diagnostic Log"):
                        st.code(raw_err)
                break 

        if processed_count > 0:
            st.sidebar.success(f"Added {processed_count} new trials!")
            st.rerun()

# --- 4. Main Page Navigation ---
tab1, tab2 = st.tabs(["🎯 Patient Matcher", "📂 Trial Database"])

with tab1:
    st.header("Patient Eligibility Engine")
    patient_desc = st.text_area("Enter Patient Medical Summary:", 
                                placeholder="e.g. 65 year old female with HER2+ breast cancer and a history of hypertension.")
    
    if st.button("Calculate Matches"):
        if not patient_desc:
            st.warning("Please enter details first.")
        else:
            with st.spinner("Analyzing medical codes..."):
                p_codes = get_icd10_codes(patient_desc)
                
            if not p_codes:
                st.error("No medical codes identified.")
            else:
                st.write(f"🧬 **Identified Codes:** {', '.join(p_codes)}")
                
                # Matching Logic
                prefixes = list(set(c[:3] for c in p_codes))
                
                # Fetch all relevant criteria for these prefixes
                placeholders = ', '.join([f"'{p}%'" for p in prefixes])
                query = f"""
                    SELECT c.*, t.title 
                    FROM criteria_items c
                    JOIN trials t ON c.trial_id = t.nct_id
                    WHERE c.icd10_code LIKE ANY (ARRAY[{placeholders}])
                """
                # Simplified SQL for SQLite compatibility
                criteria_query = "SELECT * FROM criteria_items WHERE icd10_code IS NOT NULL"
                try:
                    all_criteria = pd.read_sql("SELECT * FROM criteria_items", engine)
                except Exception as e:
                    st.error("Database table not found. Please ensure trials.db is initialized and uploaded.")
                    st.stop()
                
                scored_results = {}
                for _, row in all_criteria.iterrows():
                    code_prefix = row['icd10_code'][:3]
                    if code_prefix in prefixes:
                        tid = row['trial_id']
                        if tid not in scored_results:
                            scored_results[tid] = {"score": 0, "matches": [], "alerts": []}
                        
                        if row['type'] == 'Inclusion':
                            scored_results[tid]["matches"].append(row['value'])
                            weight = 10 if code_prefix.startswith(('C', 'D', 'I', 'J')) else 2
                            scored_results[tid]["score"] += weight
                
                # Safety Check (Exclusions)
                for tid in scored_results:
                    excl_query = "SELECT value, icd10_code FROM criteria_items WHERE trial_id = :tid AND type = 'Exclusion'"
                    excl_df = pd.read_sql(excl_query, engine, params={"tid": tid})
                    for _, erow in excl_df.iterrows():
                        # ADD THIS CHECK: Ensure the code exists before slicing it
                        if erow['icd10_code'] and erow['icd10_code'][:3] in prefixes:
                            scored_results[tid]["alerts"].append(f"Exclusion hit: {erow['value']}")
                            scored_results[tid]["score"] -= 100

                # Display Results
                ranked = sorted(scored_results.items(), key=lambda x: x[1]['score'], reverse=True)
                
                for tid, data in ranked:
                    with st.container(border=True):
                        c1, c2 = st.columns([4, 1])
                        c1.subheader(f"{tid}")
                        c2.metric("Score", data['score'])
                        
                        if data['alerts']:
                            for a in data['alerts']:
                                st.error(f"⚠️ {a}")
                        
                        st.write("**Matched Criteria:**")
                        for m in data['matches'][:3]: # Show top 3
                            st.markdown(f"- {m}")
                        
                        st.link_button("View Trial", f"https://clinicaltrials.gov/study/{tid}")

with tab2:
    st.header("Saved Trial Explorer")
    local_trials = get_local_trials()
    if not local_trials.empty:
        local_trials['display_name'] = local_trials['nct_id'] + ": " + local_trials['title'].str[:60]
        choice = st.selectbox("Select Trial to Inspect", options=local_trials['display_name'].tolist())
        sel_id = choice.split(":")[0]
        
        df_items = get_trial_criteria(sel_id)
        st.dataframe(df_items, use_container_width=True)
    else:
        st.info("Database is empty.")