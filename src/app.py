import streamlit as st
import pandas as pd
from sqlalchemy import create_engine

# --- 1. Setup & Theming ---
st.set_page_config(
    page_title="TrialIntel AI | Clinical Eligibility",
    page_icon="🧬",
    layout="wide"
)

# Database connection
engine = create_engine("sqlite:///./trials.db")

# Custom CSS for a professional "Medical/Biotech" feel
# FIXED: Changed 'unsafe_all_with_labels' to 'unsafe_allow_html'
st.markdown("""
    <style>
    .main { background-color: #f0f2f6; }
    div[data-testid="stMetric"] {
        background-color: #ffffff; 
        padding: 20px; 
        border-radius: 12px; 
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        border: 1px solid #eef0f2;
    }
    .stDataFrame { background-color: #ffffff; border-radius: 12px; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. Data Loading Helpers ---
@st.cache_data
def get_filter_options():
    """Retrieves unique Trial IDs and Conditions to prepopulate filters."""
    try:
        # Get unique Trial IDs for the dropdown
        ncts = pd.read_sql("SELECT DISTINCT nct_id FROM trials", engine)
        # Get unique conditions for search suggestions or metadata
        conditions = pd.read_sql(
            "SELECT DISTINCT entity FROM criteria_items WHERE category='Condition' AND entity IS NOT NULL", 
            engine
        )
        return ncts['nct_id'].tolist(), conditions['entity'].tolist()
    except Exception as e:
        st.error(f"Database Error: {e}")
        return [], []

def load_data(nct_id=None, condition=None, age=None):
    """
    Core engine: Joins Trials and Criteria with numeric age and text search.
    """
    # Fetch all relevant columns including our new numeric age ranges
    query = """
    SELECT 
        t.nct_id, 
        t.title, 
        c.type, 
        c.category, 
        c.entity, 
        c.icd10_code, 
        c.value, 
        c.min_age, 
        c.max_age
    FROM trials t
    JOIN criteria_items c ON t.nct_id = c.trial_id
    WHERE 1=1
    """
    params = {}
    
    # Filter by specific Trial ID if selected
    if nct_id and nct_id != "All":
        query += " AND t.nct_id = :nct"
        params['nct'] = nct_id
        
    # Filter by Condition name or ICD-10 code
    if condition:
        query += " AND (c.entity LIKE :cond OR c.icd10_code LIKE :cond)"
        params['cond'] = f"%{condition}%"

    df = pd.read_sql(query, engine, params=params)

    # --- HIGH PERFORMANCE AGE FILTERING ---
    if age is not None and not df.empty:
        # A trial is disqualified if the user's age is outside the specified range
        # Note: We filter the WHOLE trial out if one age criteria is failed
        disqualified_ids = df[
            (df['category'] == 'Age') & 
            ((age < df['min_age']) | (age > df['max_age']))
        ]['nct_id'].unique()
        
        # Keep only trials that passed the age check
        df = df[~df['nct_id'].isin(disqualified_ids)]
    
    return df

# --- 3. Sidebar UI ---
st.sidebar.header("🔍 Discovery Filters")
all_ncts, all_conditions = get_filter_options()

# Prepopulated dropdown
selected_nct = st.sidebar.selectbox(
    "Select Trial ID", 
    ["All"] + all_ncts,
    help="Select a specific trial or view all matches"
)

# Text-based condition search
target_condition = st.sidebar.text_input(
    "Search Condition", 
    placeholder="e.g. Cancer or C50",
    help="Searches clinical terms and ICD-10 codes"
)

# Interactive age slider
target_age = st.sidebar.slider(
    "Patient Age", 
    min_value=0, 
    max_value=100, 
    value=45,
    help="Excludes trials where the patient age is out of bounds"
)

# --- 4. Main Dashboard Layout ---
st.title("🧬 TrialIntel: Clinical Eligibility Engine")
st.caption("Structured Insights for Clinical Trial Discovery")

# Fetch filtered data based on user input
data = load_data(selected_nct, target_condition, target_age)

if data.empty:
    st.warning("No trials match the current filters. Try adjusting the age or condition.")
else:
    # Row 1: Key Metrics
    m1, m2, m3 = st.columns(3)
    with m1:
        st.metric("Eligible Trials", len(data['nct_id'].unique()))
    with m2:
        st.metric("Criteria Points", len(data))
    with m3:
        icd_coverage = data['icd10_code'].notna().mean()
        st.metric("ICD-10 Mapping", f"{icd_coverage:.0%}")

    st.divider()

    # Row 2: Data Table
    st.subheader("📋 Eligibility Details")
    # Show clean data (replace NaN with '-')
    st.dataframe(
        data.fillna("-"), 
        use_container_width=True, 
        height=400,
        column_config={
            "nct_id": "Trial ID",
            "icd10_code": "ICD-10",
            "min_age": "Min Age",
            "max_age": "Max Age",
            "value": "Original Text"
        }
    )

    # Row 3: Visual Analytics
    col_left, col_right = st.columns(2)
    
    with col_left:
        st.write("### Category Distribution")
        st.bar_chart(data['category'].value_counts(), color="#2e7d32")

    with col_right:
        st.write("### Top Conditions Found")
        top_conditions = data[data['category'] == 'Condition']['entity'].value_counts().head(5)
        if not top_conditions.empty:
            st.table(top_conditions)
        else:
            st.info("No medical conditions identified in the current view.")

# Refresh Button
if st.sidebar.button("Refresh Data"):
    st.cache_data.clear()
    st.rerun()