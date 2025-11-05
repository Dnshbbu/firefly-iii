import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import sys
from pathlib import Path

# Add parent directory to path to import utils
sys.path.append(str(Path(__file__).parent.parent))

from utils.api_client import FireflyAPIClient
from utils.charts import (
    create_category_trend_chart,
    create_category_comparison_chart
)
from utils.calculations import (
    calculate_category_spending,
    calculate_category_trends,
    get_top_transactions_by_category,
    calculate_category_statistics,
    calculate_category_monthly_comparison
)
from utils.navigation import render_sidebar_navigation
from utils.config import get_firefly_url, get_firefly_token

# Page configuration
st.set_page_config(
    page_title="Category Details - Firefly III",
    page_icon="🔍",
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

    /* Compact dataframes */
    .dataframe {
        font-size: 0.75rem !important;
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

    /* Compact expanders */
    .streamlit-expanderHeader {
        font-size: 0.9rem !important;
        padding: 0.3rem !important;
    }

    /* Compact buttons */
    .stButton button {
        padding: 0.25rem 0.75rem !important;
        font-size: 0.85rem !important;
    }
</style>
""", unsafe_allow_html=True)

# Main app
st.title("🔍 Category Details & Trends")

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
       FIREFLY_III_URL=http://localhost
       FIREFLY_III_TOKEN=your_token_here
       ```
    3. **Restart the app** for changes to take effect

    Once configured, your dashboard data will be displayed automatically.
    """)
    st.stop()

# Sidebar date range selection
st.sidebar.header("📅 Date Range")

preset_range = st.sidebar.selectbox(
    "Select Period",
    ["Last 7 Days", "Last 30 Days", "Last 3 Months", "Last 6 Months", "Last 12 Months",
     "Last Exact 3 Months", "Last Exact 6 Months", "Last Exact 12 Months",
     "Current Month", "Current Quarter", "Current Year",
     "Last Month", "Last Quarter", "Last Year", "Year to Date", "Custom"],
    index=2  # Default to "Last 3 Months"
)

today = datetime.now()
first_day_of_month = datetime(today.year, today.month, 1)

if preset_range == "Last 7 Days":
    start_date = today - timedelta(days=7)
    end_date = today
elif preset_range == "Last 30 Days":
    start_date = today - timedelta(days=30)
    end_date = today
elif preset_range == "Last 3 Months":
    start_date = today - timedelta(days=90)
    end_date = today
elif preset_range == "Last 6 Months":
    start_date = today - timedelta(days=180)
    end_date = today
elif preset_range == "Last 12 Months":
    start_date = today - timedelta(days=365)
    end_date = today
elif preset_range == "Last Exact 3 Months":
    # Get complete months only (e.g., if today is Oct 26, show Jul 1 - Sep 30)
    if today.month <= 3:
        start_date = datetime(today.year - 1, today.month + 9, 1)
        end_date = datetime(today.year, today.month - 1, 1) - timedelta(days=1) if today.month > 1 else datetime(today.year - 1, 12, 31)
    else:
        start_date = datetime(today.year, today.month - 3, 1)
        end_date = datetime(today.year, today.month, 1) - timedelta(days=1)
elif preset_range == "Last Exact 6 Months":
    # Get complete months only
    if today.month <= 6:
        start_date = datetime(today.year - 1, today.month + 6, 1)
        end_date = datetime(today.year, today.month - 1, 1) - timedelta(days=1) if today.month > 1 else datetime(today.year - 1, 12, 31)
    else:
        start_date = datetime(today.year, today.month - 6, 1)
        end_date = datetime(today.year, today.month, 1) - timedelta(days=1)
elif preset_range == "Last Exact 12 Months":
    # Get complete months only (previous 12 full months)
    start_date = datetime(today.year - 1, today.month, 1)
    end_date = datetime(today.year, today.month, 1) - timedelta(days=1)
elif preset_range == "Current Month":
    start_date = first_day_of_month
    end_date = today
elif preset_range == "Current Quarter":
    quarter = (today.month - 1) // 3
    start_date = datetime(today.year, quarter * 3 + 1, 1)
    end_date = today
elif preset_range == "Current Year":
    start_date = datetime(today.year, 1, 1)
    end_date = today
elif preset_range == "Last Month":
    if today.month == 1:
        start_date = datetime(today.year - 1, 12, 1)
        end_date = first_day_of_month - timedelta(days=1)
    else:
        start_date = datetime(today.year, today.month - 1, 1)
        end_date = first_day_of_month - timedelta(days=1)
elif preset_range == "Last Quarter":
    quarter = (today.month - 1) // 3
    if quarter == 0:
        start_date = datetime(today.year - 1, 10, 1)
        end_date = datetime(today.year - 1, 12, 31)
    else:
        start_date = datetime(today.year, (quarter - 1) * 3 + 1, 1)
        end_date = datetime(today.year, quarter * 3, 1) - timedelta(days=1)
elif preset_range == "Last Year":
    start_date = datetime(today.year - 1, 1, 1)
    end_date = datetime(today.year - 1, 12, 31)
elif preset_range == "Year to Date":
    start_date = datetime(today.year, 1, 1)
    end_date = today
else:  # Custom
    col1, col2 = st.sidebar.columns(2)
    with col1:
        start_date = st.date_input("Start Date", today - timedelta(days=180))
    with col2:
        end_date = st.date_input("End Date", today)

start_date_str = start_date.strftime('%Y-%m-%d')
end_date_str = end_date.strftime('%Y-%m-%d')

# Main content
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

    st.markdown("---")

    # Cache data fetching
    @st.cache_data(ttl=300)
    def fetch_category_data(_client, start, end):
        """Fetch transactions with caching"""
        return _client.get_transactions(start_date=start, end_date=end)

    # Fetch data
    with st.spinner("Loading category data..."):
        transactions_data = fetch_category_data(client, start_date_str, end_date_str)

        if not transactions_data:
            st.warning("No transactions found in the selected date range.")
            st.stop()

        # Parse transaction data
        df_transactions = client.parse_transaction_data(transactions_data)

        # Filter for expenses only
        df_expenses = df_transactions[df_transactions['type'] == 'withdrawal'].copy()

        if df_expenses.empty:
            st.warning("No expense transactions found in the selected date range.")
            st.stop()

        # Calculate category spending
        category_spending = calculate_category_spending(df_expenses, start_date_str, end_date_str)

        # Related dashboards navigation - compact
        st.markdown('<div style="background-color: rgba(49, 51, 63, 0.2); padding: 0.3rem 0.5rem; border-radius: 0.3rem; font-size: 0.75rem;">💡 <b>Related:</b> <a href="/Categories" style="color: #58a6ff;">🏷️ Category Overview</a> • <a href="/Budget" style="color: #58a6ff;">💰 Budget</a> • <a href="/Cash_Flow" style="color: #58a6ff;">📈 Cash Flow</a></div>', unsafe_allow_html=True)

        st.markdown("---")

        # Tab selection using radio buttons - let Streamlit manage the state via key
        selected_tab = st.radio(
            "View",
            ["📈 Trends (multiple categories)", "🔍 Deep Dive (single category)"],
            index=0,  # Default to Trends
            horizontal=True,
            key="category_tab_selector",
            label_visibility="collapsed"
        )

        # Determine active tab based on selection
        if selected_tab == "📈 Trends (multiple categories)":
            active_tab = "Trends"
        else:
            active_tab = "Deep Dive"

        st.markdown("---")

        if active_tab == "Trends":
            st.markdown("**Category Spending Trends**")

            # Calculate trends
            category_trends = calculate_category_trends(df_expenses, period='ME')

            # Select categories to display
            all_categories_list = category_spending['category_name'].tolist()
            top_5_categories = category_spending.head(5)['category_name'].tolist()

            # Initialize the multiselect state with top 5 if not exists
            if "trends_multiselect" not in st.session_state:
                st.session_state.trends_multiselect = top_5_categories

            # Checkbox to select all categories
            col1, col2 = st.columns([3, 1])
            with col1:
                st.write("")  # Spacing
            with col2:
                if st.button("Select All Categories", key="trends_select_all_btn"):
                    # Directly set the multiselect widget's state to all categories
                    st.session_state.trends_multiselect = all_categories_list
                    st.rerun()

            selected_categories = st.multiselect(
                "Select categories to display",
                options=all_categories_list,
                key="trends_multiselect"
            )

            if selected_categories:
                # Show info about number of categories being displayed
                if len(selected_categories) > 10:
                    st.info(f"📊 Displaying trends for {len(selected_categories)} categories")

                fig_trends = create_category_trend_chart(
                    category_trends,
                    categories=selected_categories,
                    title="",  # Title moved to markdown above for compactness
                    height=400
                )
                st.plotly_chart(fig_trends, config={'displayModeBar': False, 'responsive': True})
            else:
                st.info("Please select at least one category to display trends")

        else:  # Deep Dive tab
            st.markdown("**Detailed Category Analysis**")

            # Category selector
            selected_category = st.selectbox(
                "Select a category to analyze",
                options=category_spending['category_name'].tolist()
            )

            if selected_category:
                # Calculate statistics
                stats = calculate_category_statistics(df_expenses, selected_category)
                monthly_data = calculate_category_monthly_comparison(df_expenses, selected_category)

                # Get all transactions for this category
                category_transactions = df_expenses[df_expenses['category_name'] == selected_category].copy()

                # Calculate total spending for this category
                total_spending = category_transactions['amount'].sum()

                # Display statistics - compact row
                cols = st.columns(6)
                cols[0].metric("Transactions", f"{int(stats['count'])}")
                cols[1].metric("Total", f"€{total_spending:,.0f}")
                cols[2].metric("Avg/Month", f"€{stats['mean']:,.0f}")
                cols[3].metric("Median", f"€{stats['median']:,.0f}")
                cols[4].metric("Min", f"€{stats['min']:,.0f}")
                cols[5].metric("Max", f"€{stats['max']:,.0f}")

                # Monthly comparison chart - compact
                if not monthly_data.empty:
                    st.markdown("**Monthly Trend**")

                    fig_comparison = create_category_comparison_chart(
                        monthly_data,
                        selected_category,
                        height=300
                    )
                    st.plotly_chart(fig_comparison, config={'displayModeBar': False, 'responsive': True})

                # All transactions - collapsible
                with st.expander(f"📋 All Transactions ({len(category_transactions)})", expanded=False):
                    if not category_transactions.empty:
                        # Sort by date descending and prepare display
                        transactions_display = category_transactions.sort_values('date', ascending=False)[['date', 'description', 'destination_name', 'amount']].copy()

                        # Ensure date is datetime before formatting
                        if not pd.api.types.is_datetime64_any_dtype(transactions_display['date']):
                            transactions_display['date'] = pd.to_datetime(transactions_display['date'], utc=True)
                        # Remove timezone if present
                        if hasattr(transactions_display['date'].dt, 'tz') and transactions_display['date'].dt.tz is not None:
                            transactions_display['date'] = transactions_display['date'].dt.tz_localize(None)
                        transactions_display['date'] = transactions_display['date'].dt.strftime('%Y-%m-%d')

                        st.dataframe(
                            transactions_display,
                            width='stretch',
                            hide_index=True,
                            column_config={
                                'date': 'Date',
                                'description': 'Description',
                                'destination_name': 'Merchant',
                                'amount': st.column_config.NumberColumn('Amount', format="€%.2f")
                            },
                            height=400
                        )
                    else:
                        st.info("No transactions found for this category")

except Exception as e:
    st.error(f"An error occurred: {str(e)}")
    st.exception(e)
