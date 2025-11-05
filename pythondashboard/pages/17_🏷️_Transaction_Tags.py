import streamlit as st
import pandas as pd
from datetime import datetime
import sys
from pathlib import Path

# Add parent directory to path to import utils
sys.path.append(str(Path(__file__).parent.parent))

from utils.api_client import FireflyAPIClient
from utils.navigation import render_sidebar_navigation
from utils.config import get_firefly_url, get_firefly_token

# Page configuration
st.set_page_config(
    page_title="Transaction Tags - Firefly III",
    page_icon="🏷️",
    layout="wide"
)

# Render custom navigation
render_sidebar_navigation()

# Compact CSS styling
st.markdown("""
<style>
    .block-container {
        padding-top: 1rem;
        padding-bottom: 0rem;
        padding-left: 2rem;
        padding-right: 2rem;
    }
    h1 {
        padding-top: 0rem;
        padding-bottom: 0.5rem;
        font-size: 2rem;
    }
    h2 {
        padding-top: 0.5rem;
        padding-bottom: 0.25rem;
        font-size: 1.5rem;
    }
    h3 {
        padding-top: 0.25rem;
        padding-bottom: 0.25rem;
        font-size: 1.2rem;
    }
    .dataframe {
        font-size: 0.85rem !important;
    }
</style>
""", unsafe_allow_html=True)

st.title("🏷️ Transaction Tags - Import Dates")

# Get API configuration
base_url = get_firefly_url()
api_token = get_firefly_token()

if not base_url or not api_token:
    st.error("⚠️ Please configure your Firefly III API connection first.")
    st.info("Go to the Net Worth Dashboard to set up your API connection.")
    st.stop()

# Initialize API client
client = FireflyAPIClient(base_url, api_token)

# Add date range selector in sidebar
st.sidebar.markdown("### 📅 Date Range")
date_range_option = st.sidebar.selectbox(
    "Select date range",
    ["Last 30 Days", "Last 90 Days", "Last 6 Months", "Last Year", "Year to Date", "All Time", "Custom"],
    index=5
)

# Calculate date range
end_date = datetime.now()
if date_range_option == "Last 30 Days":
    start_date = end_date - pd.Timedelta(days=30)
elif date_range_option == "Last 90 Days":
    start_date = end_date - pd.Timedelta(days=90)
elif date_range_option == "Last 6 Months":
    start_date = end_date - pd.Timedelta(days=180)
elif date_range_option == "Last Year":
    start_date = end_date - pd.Timedelta(days=365)
elif date_range_option == "Year to Date":
    start_date = datetime(end_date.year, 1, 1)
elif date_range_option == "Custom":
    col1, col2 = st.sidebar.columns(2)
    with col1:
        start_date = st.date_input("Start Date", end_date - pd.Timedelta(days=90))
    with col2:
        end_date = st.date_input("End Date", end_date)
    start_date = pd.to_datetime(start_date)
    end_date = pd.to_datetime(end_date)
else:  # All Time
    start_date = None
    end_date = None

# Add refresh button
if st.sidebar.button("🔄 Refresh Data", use_container_width=True):
    st.cache_data.clear()
    st.rerun()

# Fetch transactions
@st.cache_data(ttl=300)
def fetch_transactions(base_url, api_token, start_date, end_date):
    client = FireflyAPIClient(base_url, api_token)
    start_str = start_date.strftime('%Y-%m-%d') if start_date else None
    end_str = end_date.strftime('%Y-%m-%d') if end_date else None
    transactions_raw = client.get_transactions(start_date=start_str, end_date=end_str)
    return client.parse_transaction_data(transactions_raw)

with st.spinner("Loading transactions..."):
    transactions_df = fetch_transactions(base_url, api_token, start_date, end_date)

if transactions_df.empty:
    st.warning("No transactions found for the selected period.")
    st.stop()

# Check if tags and created_at columns exist
if 'tags' not in transactions_df.columns or 'created_at' not in transactions_df.columns:
    st.error("Transaction data doesn't include tags or import dates.")
    st.stop()

# Prepare data: explode tags and extract import date
df = transactions_df.copy()

# Ensure created_at is datetime
if not pd.api.types.is_datetime64_any_dtype(df['created_at']):
    df['created_at'] = pd.to_datetime(df['created_at'], utc=True)

# Remove timezone
if hasattr(df['created_at'].dt, 'tz') and df['created_at'].dt.tz is not None:
    df['created_at'] = df['created_at'].dt.tz_localize(None)

# Ensure date is datetime
if not pd.api.types.is_datetime64_any_dtype(df['date']):
    df['date'] = pd.to_datetime(df['date'], utc=True)

# Remove timezone
if hasattr(df['date'].dt, 'tz') and df['date'].dt.tz is not None:
    df['date'] = df['date'].dt.tz_localize(None)

# Extract import date (date only, no time)
df['import_date'] = df['created_at'].dt.date

# Explode tags to get one row per tag
df_exploded = df.explode('tags')

# Filter out rows without tags
df_with_tags = df_exploded[df_exploded['tags'].notna()].copy()

if df_with_tags.empty:
    st.warning("No tagged transactions found in the selected period.")
    st.stop()

# Group by tag and import date to count transactions
tag_import_summary = df_with_tags.groupby(['tags', 'import_date']).agg({
    'id': 'count',
    'date': ['min', 'max']
}).reset_index()

tag_import_summary.columns = ['Tag', 'Import Date', 'Transaction Count', 'Earliest Transaction', 'Latest Transaction']

# Format dates
tag_import_summary['Import Date'] = pd.to_datetime(tag_import_summary['Import Date']).dt.strftime('%Y-%m-%d')
tag_import_summary['Earliest Transaction'] = pd.to_datetime(tag_import_summary['Earliest Transaction']).dt.strftime('%Y-%m-%d')
tag_import_summary['Latest Transaction'] = pd.to_datetime(tag_import_summary['Latest Transaction']).dt.strftime('%Y-%m-%d')

# Sort by tag and import date
tag_import_summary = tag_import_summary.sort_values(['Tag', 'Import Date'], ascending=[True, False])

# Display summary metrics
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Total Tags", len(df_with_tags['tags'].unique()))
with col2:
    st.metric("Import Batches", len(df['import_date'].unique()))
with col3:
    st.metric("Tagged Transactions", len(df_with_tags))

st.markdown("---")

# Display table
st.markdown("### 📊 Import Dates by Tag")
st.markdown("This table shows when transactions with each tag were imported into Firefly III.")

st.dataframe(
    tag_import_summary,
    width='stretch',
    hide_index=True,
    column_config={
        'Tag': st.column_config.TextColumn('Tag', width='medium'),
        'Import Date': st.column_config.TextColumn('Import Date', width='small'),
        'Transaction Count': st.column_config.NumberColumn('Count', width='small'),
        'Earliest Transaction': st.column_config.TextColumn('Earliest Txn', width='small'),
        'Latest Transaction': st.column_config.TextColumn('Latest Txn', width='small'),
    }
)

# Export option
st.markdown("---")
if st.button("📥 Export to CSV"):
    csv = tag_import_summary.to_csv(index=False)
    st.download_button(
        label="Download CSV",
        data=csv,
        file_name=f"transaction_tags_import_dates_{datetime.now().strftime('%Y%m%d')}.csv",
        mime="text/csv"
    )
