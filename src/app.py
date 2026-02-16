import streamlit as st
import pandas as pd
from sqlalchemy import create_engine

# Setup
engine = create_engine("sqlite:///./trials.db")

st.set_page_config(page_title="Clinical Trial Parser", layout="wide")

st.title("clinical Trial Eligibility Intelligence")
st.write("Structured criteria extraction using AI & ICD-10 Mapping")

# Sidebar for filtering
st.sidebar.header("Filters")
nct_filter = st.sidebar.text_input("Filter by NCT ID (e.g., NCT03529110)")

# Load Data
query = "SELECT * FROM criteria_items"
df = pd.read_sql(query, engine)

# Clean up display
df = df.fillna("-") 

# Application Logic
if nct_filter:
    df = df[df['trial_id'].str.contains(nct_filter)]

# UI Layout
col1, col2 = st.columns([1, 3])

with col1:
    st.metric("Total Criteria Extracted", len(df))
    st.write("### Category Breakdown")
    st.bar_chart(df['category'].value_counts())

with col2:
    st.write("### Extracted Data")
    st.dataframe(df, use_container_width=True)

if st.button("Refresh Data"):
    st.rerun()