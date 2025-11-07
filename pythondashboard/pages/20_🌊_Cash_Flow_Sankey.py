import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, date
import sys
from pathlib import Path
from typing import Optional, Tuple

# Add parent directory to path to import utils
sys.path.append(str(Path(__file__).parent.parent))

from utils.api_client import FireflyAPIClient
from utils.d3_sankey_helper import prepare_sankey_data, generate_d3_sankey_html
from utils.calculations import (
    calculate_category_spending,
    calculate_income_sources,
    calculate_destination_accounts_spending,
    calculate_destination_to_category_mapping
)
from utils.navigation import render_sidebar_navigation
from utils.config import get_firefly_url, get_firefly_token


def resolve_date_range(preset: str, today: datetime) -> Tuple[Optional[datetime], Optional[datetime]]:
    """Return start/end datetimes for the given preset. Custom returns (None, None)."""
    first_day_of_month = datetime(today.year, today.month, 1)

    if preset == "Last 7 Days":
        return today - timedelta(days=7), today
    if preset == "Last 30 Days":
        return today - timedelta(days=30), today
    if preset == "Last 3 Months":
        return today - timedelta(days=90), today
    if preset == "Last 6 Months":
        return today - timedelta(days=180), today
    if preset == "Last 12 Months":
        return today - timedelta(days=365), today
    if preset == "Last Exact 3 Months":
        if today.month <= 3:
            start = datetime(today.year - 1, today.month + 9, 1)
            if today.month > 1:
                end = datetime(today.year, today.month - 1, 1) - timedelta(days=1)
            else:
                end = datetime(today.year - 1, 12, 31)
        else:
            start = datetime(today.year, today.month - 3, 1)
            end = datetime(today.year, today.month, 1) - timedelta(days=1)
        return start, end
    if preset == "Last Exact 6 Months":
        if today.month <= 6:
            start = datetime(today.year - 1, today.month + 6, 1)
            if today.month > 1:
                end = datetime(today.year, today.month - 1, 1) - timedelta(days=1)
            else:
                end = datetime(today.year - 1, 12, 31)
        else:
            start = datetime(today.year, today.month - 6, 1)
            end = datetime(today.year, today.month, 1) - timedelta(days=1)
        return start, end
    if preset == "Last Exact 12 Months":
        start = datetime(today.year - 1, today.month, 1)
        end = datetime(today.year, today.month, 1) - timedelta(days=1)
        return start, end
    if preset == "Current Month":
        return first_day_of_month, today
    if preset == "Current Quarter":
        quarter = (today.month - 1) // 3
        return datetime(today.year, quarter * 3 + 1, 1), today
    if preset == "Current Year":
        return datetime(today.year, 1, 1), today
    if preset == "Last Month":
        if today.month == 1:
            start = datetime(today.year - 1, 12, 1)
            end = first_day_of_month - timedelta(days=1)
        else:
            start = datetime(today.year, today.month - 1, 1)
            end = first_day_of_month - timedelta(days=1)
        return start, end
    if preset == "Last Quarter":
        quarter = (today.month - 1) // 3
        if quarter == 0:
            start = datetime(today.year - 1, 10, 1)
            end = datetime(today.year - 1, 12, 31)
        else:
            start = datetime(today.year, (quarter - 1) * 3 + 1, 1)
            end = datetime(today.year, quarter * 3, 1) - timedelta(days=1)
        return start, end
    if preset == "Last Year":
        return datetime(today.year - 1, 1, 1), datetime(today.year - 1, 12, 31)
    if preset == "Year to Date":
        return datetime(today.year, 1, 1), today
    if preset == "Custom":
        return None, None
    # Default fallback
    return today - timedelta(days=90), today


def normalize_transaction_labels(df: pd.DataFrame) -> pd.DataFrame:
    """Ensure key label columns have readable fallback values."""
    if df.empty:
        return df

    df['source_name'] = df['source_name'].fillna('Unknown').replace('', 'Unknown')
    df['destination_name'] = df['destination_name'].fillna('Unknown').replace('', 'Unknown')
    df['category_name'] = df['category_name'].fillna('Uncategorized').replace('', 'Uncategorized')
    return df

# Page configuration
st.set_page_config(
    page_title="Cash Flow Sankey - Firefly III",
    page_icon="🌊",
    layout="wide"
)

# Render custom navigation
render_sidebar_navigation()

# Ultra-compact CSS styling - DENSE dashboard
st.markdown("""
<style>
    /* Minimal padding for maximum density */
    .block-container {
        padding-top: 3rem !important;
        padding-bottom: 0rem !important;
        padding-left: 1rem !important;
        padding-right: 1rem !important;
        max-width: 100% !important;
    }

    /* Compact headers */
    h1 {
        padding-top: 0rem !important;
        padding-bottom: 0.3rem !important;
        margin-top: 0 !important;
        margin-bottom: 0.3rem !important;
        font-size: 1.8rem !important;
    }
    h2 {
        padding-top: 0.2rem !important;
        padding-bottom: 0.2rem !important;
        margin-top: 0.3rem !important;
        margin-bottom: 0.3rem !important;
        font-size: 1.3rem !important;
    }
    h3 {
        padding-top: 0.1rem !important;
        padding-bottom: 0.1rem !important;
        margin-top: 0.2rem !important;
        margin-bottom: 0.2rem !important;
        font-size: 1.1rem !important;
    }

    /* Compact metrics */
    [data-testid="stMetricValue"] {
        font-size: 1.3rem !important;
    }
    [data-testid="stMetricLabel"] {
        font-size: 0.75rem !important;
        margin-bottom: 0 !important;
    }
    [data-testid="stMetric"] {
        padding: 0.3rem !important;
    }

    /* Reduce spacing between elements */
    .element-container {
        margin-bottom: 0.2rem !important;
    }

    /* Compact dividers */
    hr {
        margin-top: 0.3rem !important;
        margin-bottom: 0.3rem !important;
    }

    /* Reduce plot margins */
    .js-plotly-plot {
        margin-bottom: 0 !important;
    }

    /* Compact buttons */
    .stButton button {
        padding: 0.25rem 0.75rem !important;
        font-size: 0.85rem !important;
    }
</style>
""", unsafe_allow_html=True)

# Main app
st.title("🌊 Cash Flow Sankey Diagram")

# Sidebar for API configuration
st.sidebar.header("🔧 API Configuration")

# Initialize session state for API credentials from .env
if 'firefly_url' not in st.session_state:
    st.session_state.firefly_url = get_firefly_url()
if 'firefly_token' not in st.session_state:
    st.session_state.firefly_token = get_firefly_token()
if 'api_connected' not in st.session_state:
    st.session_state.api_connected = False

# Auto-connect if credentials are available and not yet connected
if not st.session_state.api_connected and st.session_state.firefly_url and st.session_state.firefly_token:
    client = FireflyAPIClient(st.session_state.firefly_url, st.session_state.firefly_token)
    success, message = client.test_connection()
    if success:
        st.session_state.api_connected = True

# Connection status
if st.session_state.api_connected:
    st.sidebar.success(f"✅ Connected to {st.session_state.firefly_url}")
else:
    st.sidebar.error("❌ Connection failed")
    st.sidebar.markdown("Check your `.env` file configuration")

# Display help if not connected
if not st.session_state.api_connected:
    st.info("""
    ### 🔑 Getting Started

    Configure your Firefly III credentials in the `.env` file:

    1. **Edit the `.env` file** in the `pythondashboard` directory
    2. **Add your credentials**:
       ```
       FIREFLY_III_URL=http://192.168.0.242
       FIREFLY_III_TOKEN=your_token_here
       ```
    3. **Restart the app** for changes to take effect

    Once configured, your cash flow Sankey diagram will be displayed automatically.
    """)
    st.stop()

# Sidebar date range selection
st.sidebar.header("📅 Date Range")

# Preset date ranges
preset_range = st.sidebar.selectbox(
    "Select Period",
    ["Last 7 Days", "Last 30 Days", "Last 3 Months", "Last 6 Months", "Last 12 Months",
     "Last Exact 3 Months", "Last Exact 6 Months", "Last Exact 12 Months",
     "Current Month", "Current Quarter", "Current Year",
     "Last Month", "Last Quarter", "Last Year", "Year to Date", "Custom"],
    index=1  # Default to "Last 30 Days"
)

today = datetime.now()
start_date, end_date = resolve_date_range(preset_range, today)

if start_date is None or end_date is None:
    col1, col2 = st.sidebar.columns(2)
    with col1:
        start_input = st.date_input(
            "Start Date",
            (today - timedelta(days=90)).date(),
            key="cash_flow_main_start"
        )
    with col2:
        end_input = st.date_input(
            "End Date",
            today.date(),
            key="cash_flow_main_end"
        )
    if isinstance(start_input, date):
        start_date = datetime.combine(start_input, datetime.min.time())
    else:
        start_date = start_input
    if isinstance(end_input, date):
        end_date = datetime.combine(end_input, datetime.min.time())
    else:
        end_date = end_input

# Convert to string format
start_date_str = start_date.strftime('%Y-%m-%d')
end_date_str = end_date.strftime('%Y-%m-%d')

# Trend range controls
st.sidebar.header("📈 Trend Range")
trend_preset_range = st.sidebar.selectbox(
    "Trend Period",
    ["Last 7 Days", "Last 30 Days", "Last 3 Months", "Last 6 Months", "Last 12 Months",
     "Last Exact 3 Months", "Last Exact 6 Months", "Last Exact 12 Months",
     "Current Month", "Current Quarter", "Current Year",
     "Last Month", "Last Quarter", "Last Year", "Year to Date", "Custom"],
    index=2,
    key="trend_period_selector"
)

trend_start_date, trend_end_date = resolve_date_range(trend_preset_range, today)

if trend_start_date is None or trend_end_date is None:
    trend_col1, trend_col2 = st.sidebar.columns(2)
    with trend_col1:
        trend_start_input = st.date_input(
            "Trend Start",
            (today - timedelta(days=365)).date(),
            key="trend_start_custom"
        )
    with trend_col2:
        trend_end_input = st.date_input(
            "Trend End",
            today.date(),
            key="trend_end_custom"
        )
    if isinstance(trend_start_input, date):
        trend_start_date = datetime.combine(trend_start_input, datetime.min.time())
    else:
        trend_start_date = trend_start_input
    if isinstance(trend_end_input, date):
        trend_end_date = datetime.combine(trend_end_input, datetime.min.time())
    else:
        trend_end_date = trend_end_input

trend_start_date_str = trend_start_date.strftime('%Y-%m-%d')
trend_end_date_str = trend_end_date.strftime('%Y-%m-%d')

# Sankey diagram configuration
st.sidebar.header("🎨 Diagram Settings")

top_n_income = st.sidebar.slider(
    "Top Income Sources",
    min_value=3,
    max_value=20,
    value=10,
    step=1,
    help="Number of top income sources to display"
)

top_n_destination = st.sidebar.slider(
    "Top Destination Accounts",
    min_value=5,
    max_value=30,
    value=15,
    step=1,
    help="Number of top destination accounts to display"
)

top_n_expense = st.sidebar.slider(
    "Top Expense Categories",
    min_value=5,
    max_value=100,
    value=30,
    step=1,
    help="Number of top expense categories to display"
)

# Main content - Fetch and display data
try:
    client = FireflyAPIClient(st.session_state.firefly_url, st.session_state.firefly_token)

    # Add refresh button - compact
    col1, col2 = st.columns([1, 5])
    with col1:
        if st.button("🔄 Refresh"):
            st.cache_data.clear()
            st.rerun()
    with col2:
        st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Period: {start_date_str} to {end_date_str}")

    # Cache transaction data
    @st.cache_data(ttl=300)
    def fetch_transactions(_client, start, end):
        """Fetch transactions with caching"""
        return _client.get_transactions(start_date=start, end_date=end)

    # Fetch transaction data
    with st.spinner("Loading transaction data..."):
        transactions_data = fetch_transactions(client, start_date_str, end_date_str)

        if transactions_data:
            # Parse transaction data
            df = client.parse_transaction_data(transactions_data)

            # Separate transfers from income/expenses
            df_filtered = df[df['type'].isin(['deposit', 'withdrawal'])].copy()
            df_filtered = normalize_transaction_labels(df_filtered)

            # Prepare dataset for trend analysis (can reuse filtered data when ranges match)
            if trend_start_date_str == start_date_str and trend_end_date_str == end_date_str:
                trend_df_filtered = df_filtered.copy()
            else:
                trend_transactions_data = fetch_transactions(client, trend_start_date_str, trend_end_date_str)
                trend_df = client.parse_transaction_data(trend_transactions_data)
                trend_df_filtered = trend_df[trend_df['type'].isin(['deposit', 'withdrawal'])].copy()
                trend_df_filtered = normalize_transaction_labels(trend_df_filtered)

            if df_filtered.empty:
                st.warning("No income or expense transactions found in the selected date range.")
                st.stop()

            # Calculate totals
            total_income = df_filtered[df_filtered['type'] == 'deposit']['amount'].sum()
            total_expenses = df_filtered[df_filtered['type'] == 'withdrawal']['amount'].sum()
            net_flow = total_income - total_expenses

            # Calculate income sources, destination accounts, and categories
            income_sources = calculate_income_sources(df_filtered, start_date_str, end_date_str)
            destination_accounts = calculate_destination_accounts_spending(df_filtered, start_date_str, end_date_str)
            category_spending = calculate_category_spending(df_filtered, start_date_str, end_date_str)
            destination_category_mapping = calculate_destination_to_category_mapping(df_filtered, start_date_str, end_date_str)

            # Display summary metrics
            st.markdown("### 💰 Financial Summary")

            cols = st.columns(4)
            cols[0].metric("Total Income", f"€{total_income:,.0f}")
            cols[1].metric("Total Expenses", f"€{total_expenses:,.0f}")
            cols[2].metric("Net Flow", f"€{net_flow:,.0f}")
            cols[3].metric("Savings Rate", f"{(net_flow / total_income * 100) if total_income > 0 else 0:.1f}%")

            # Related dashboards navigation - compact
            st.markdown('<div style="background-color: rgba(49, 51, 63, 0.2); padding: 0.3rem 0.5rem; border-radius: 0.3rem; font-size: 0.75rem;">💡 <b>Related:</b> <a href="/Cash_Flow" style="color: #58a6ff;">📈 Cash Flow</a> • <a href="/Categories" style="color: #58a6ff;">🏷️ Categories</a> • <a href="/Budget" style="color: #58a6ff;">💰 Budget</a></div>', unsafe_allow_html=True)

            st.markdown("---")

            # Display Sankey diagram
            if not income_sources.empty and not destination_accounts.empty and not category_spending.empty:

                # Prepare data for D3 Sankey
                sankey_data = prepare_sankey_data(
                    income_df=income_sources,
                    destination_df=destination_accounts,
                    destination_category_mapping_df=destination_category_mapping,
                    income_source_col='source_name',
                    income_amount_col='total_amount',
                    destination_account_col='destination_name',
                    destination_amount_col='total_amount',
                    category_col='category_name',
                    mapping_amount_col='total_amount',
                    top_n_income=top_n_income,
                    top_n_destination=top_n_destination,
                    top_n_category=top_n_expense
                )

                # Package transaction rows for drill-down interactions inside the D3 component
                transactions_view = df_filtered[
                    ['id', 'date', 'type', 'source_name', 'destination_name', 'category_name', 'description', 'amount']
                ].copy()

                trend_transactions_view = trend_df_filtered[
                    ['id', 'date', 'type', 'source_name', 'destination_name', 'category_name', 'description', 'amount']
                ].copy()

                def _prepare_transactions_view(view_df: pd.DataFrame) -> pd.DataFrame:
                    if view_df.empty:
                        return view_df

                    if pd.api.types.is_datetime64_any_dtype(view_df['date']):
                        view_df['date'] = view_df['date'].dt.tz_localize(None)
                    else:
                        view_df['date'] = pd.to_datetime(view_df['date'], utc=True)
                        view_df['date'] = view_df['date'].dt.tz_localize(None)

                    view_df['date'] = view_df['date'].dt.strftime('%Y-%m-%d')
                    view_df['description'] = view_df['description'].fillna('')
                    view_df['amount'] = view_df['amount'].astype(float)
                    return view_df

                transactions_view_prepared = _prepare_transactions_view(transactions_view)
                trend_transactions_view_prepared = _prepare_transactions_view(trend_transactions_view)

                sankey_data['transactions'] = (
                    transactions_view_prepared.to_dict(orient='records')
                    if not transactions_view_prepared.empty else []
                )
                sankey_data['trend_transactions'] = (
                    trend_transactions_view_prepared.to_dict(orient='records')
                    if not trend_transactions_view_prepared.empty else []
                )
                sankey_data['trend_range'] = {
                    'label': trend_preset_range,
                    'start': trend_start_date_str,
                    'end': trend_end_date_str
                }

                # Generate D3 Sankey HTML
                import streamlit.components.v1 as components

                sankey_html = generate_d3_sankey_html(
                    data=sankey_data,
                    title=f"Cash Flow Sankey Diagram ({start_date_str} to {end_date_str})",
                    height=700
                )

                # Display using components.html (extra height so the drilldown table is fully visible)
                components.html(sankey_html, height=1250, scrolling=True)
                st.caption("Tip: Click any node in the Sankey to populate the transaction drilldown panel below the chart.")

                # Show detailed breakdown in expanders
                col1, col2, col3 = st.columns(3)

                with col1:
                    with st.expander("💵 Income Sources Details", expanded=False):
                        st.dataframe(
                            income_sources,
                            width='stretch',
                            hide_index=True,
                            column_config={
                                'source_name': 'Source',
                                'total_amount': st.column_config.NumberColumn('Total Income', format="€%.2f"),
                                'transaction_count': 'Count'
                            },
                            height=400
                        )

                with col2:
                    with st.expander("🏢 Destination Accounts Details", expanded=False):
                        st.dataframe(
                            destination_accounts,
                            width='stretch',
                            hide_index=True,
                            column_config={
                                'destination_name': 'Destination',
                                'total_amount': st.column_config.NumberColumn('Total', format="€%.2f"),
                                'transaction_count': 'Count'
                            },
                            height=400
                        )

                with col3:
                    with st.expander("💸 Expense Categories Details", expanded=False):
                        st.dataframe(
                            category_spending,
                            width='stretch',
                            hide_index=True,
                            column_config={
                                'category_name': 'Category',
                                'total_amount': st.column_config.NumberColumn('Total Spent', format="€%.2f"),
                                'transaction_count': 'Count'
                            },
                            height=400
                        )

            else:
                if income_sources.empty:
                    st.warning("No income sources found in the selected date range.")
                if destination_accounts.empty:
                    st.warning("No destination accounts found in the selected date range.")
                if category_spending.empty:
                    st.warning("No categorized expenses found in the selected date range.")

        else:
            st.warning("No transactions found in the selected date range. Please adjust your date range or check your API connection.")

except Exception as e:
    st.error(f"An error occurred: {str(e)}")
    st.exception(e)
