import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
from datetime import datetime, timedelta
import sys
from pathlib import Path

# Add parent directory to path to import utils
sys.path.append(str(Path(__file__).parent.parent))

from utils.api_client import FireflyAPIClient
from utils.charts import create_net_flow_chart, create_pie_chart, create_waterfall_chart
from utils.calculations import calculate_cash_flow, calculate_category_spending, calculate_income_sources
from utils.navigation import render_sidebar_navigation
from utils.config import get_firefly_url, get_firefly_token

# Page configuration
st.set_page_config(
    page_title="Cash Flow Dashboard - Firefly III",
    page_icon="📈",
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
st.title("📈 Cash Flow Dashboard")

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

    Once configured, your cash flow data will be displayed automatically.
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
        start_date = st.date_input("Start Date", today - timedelta(days=90))
    with col2:
        end_date = st.date_input("End Date", today)

# Convert to string format
start_date_str = start_date.strftime('%Y-%m-%d')
end_date_str = end_date.strftime('%Y-%m-%d')

# Aggregation period
st.sidebar.header("📊 Aggregation")
aggregation = st.sidebar.selectbox(
    "Group by",
    ["Daily", "Weekly", "Monthly", "Quarterly"],
    index=2  # Default to Monthly
)

aggregation_map = {
    "Daily": "D",
    "Weekly": "W",
    "Monthly": "ME",
    "Quarterly": "QE"
}

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
            df_transfers = df[df['type'] == 'transfer'].copy()

            if df_filtered.empty:
                st.warning("No income or expense transactions found in the selected date range.")
                st.stop()

            # Calculate cash flow by period
            cash_flow_df = calculate_cash_flow(df_filtered, period=aggregation_map[aggregation])

            # Calculate totals
            total_income = df_filtered[df_filtered['type'] == 'deposit']['amount'].sum()
            total_expenses = df_filtered[df_filtered['type'] == 'withdrawal']['amount'].sum()
            net_flow = total_income - total_expenses

            # Calculate transfers total (not included in cash flow)
            total_transfers = len(df_transfers)
            total_transfer_amount = df_transfers['amount'].sum() if not df_transfers.empty else 0

            # Calculate useful metrics
            days_in_range = (end_date - start_date).days
            months_in_range = max(1, days_in_range / 30)
            avg_monthly_income = total_income / months_in_range
            avg_monthly_expenses = total_expenses / months_in_range
            avg_monthly_net = net_flow / months_in_range
            savings_rate = (net_flow / total_income * 100) if total_income > 0 else 0

            # Calculate daily burn rate and runway
            daily_expenses = total_expenses / max(1, days_in_range)

            # Transaction counts
            income_count = len(df_filtered[df_filtered['type'] == 'deposit'])
            expense_count = len(df_filtered[df_filtered['type'] == 'withdrawal'])

            # Display all metrics in single compact section
            st.markdown("### 💰 Financial Summary")

            # Row 1: Totals and rates
            cols = st.columns(7)
            cols[0].metric("Total Income", f"€{total_income:,.0f}")
            cols[1].metric("Total Expenses", f"€{total_expenses:,.0f}")
            cols[2].metric("Net Flow", f"€{net_flow:,.0f}")
            cols[3].metric("Savings Rate", f"{savings_rate:.1f}%")
            cols[4].metric("Avg Monthly Net", f"€{avg_monthly_net:,.0f}")
            cols[5].metric("Daily Burn", f"€{daily_expenses:,.0f}")
            cols[6].metric("Transactions", f"{income_count + expense_count}")

            # Show transfers info if any exist
            if total_transfers > 0:
                st.markdown("**ℹ️ Note:** This period includes **{:,} transfer(s)** totaling **€{:,.0f}** between your accounts (not included in cash flow calculations)".format(total_transfers, total_transfer_amount))

            # Related dashboards navigation - compact
            st.markdown('<div style="background-color: rgba(49, 51, 63, 0.2); padding: 0.3rem 0.5rem; border-radius: 0.3rem; font-size: 0.75rem;">💡 <b>Related:</b> <a href="/Budget" style="color: #58a6ff;">💰 Budget</a> • <a href="/Budget_Timeline" style="color: #58a6ff;">📅 Timeline</a> • <a href="/Categories" style="color: #58a6ff;">🏷️ Categories</a></div>', unsafe_allow_html=True)

            st.markdown("---")

            # Cash flow charts - side by side
            st.markdown("### 📈 Cash Flow Analysis")

            chart_col1, chart_col2 = st.columns(2)

            with chart_col1:
                if not cash_flow_df.empty:
                    # Format period for display
                    if aggregation == "Monthly":
                        cash_flow_df['period_display'] = cash_flow_df['period'].dt.strftime('%b %Y')
                    elif aggregation == "Weekly":
                        cash_flow_df['period_display'] = cash_flow_df['period'].dt.strftime('%Y-W%U')
                    elif aggregation == "Quarterly":
                        # Remove timezone before converting to period to avoid warning
                        # Note: to_period() still uses 'Q' (not 'QE' like resample)
                        cash_flow_df['period_display'] = cash_flow_df['period'].dt.tz_localize(None).dt.to_period('Q').astype(str)
                    else:  # Daily
                        cash_flow_df['period_display'] = cash_flow_df['period'].dt.strftime('%Y-%m-%d')

                    fig = create_net_flow_chart(
                        cash_flow_df,
                        x='period_display',
                        income_col='income',
                        expense_col='expenses',
                        title=f"Income vs. Expenses ({aggregation})",
                        height=350
                    )

                    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
                else:
                    st.warning("No data available for the selected period.")

            with chart_col2:
                if aggregation == "Monthly" and not cash_flow_df.empty:
                    # Create waterfall data
                    waterfall_categories = ['Starting'] + cash_flow_df['period_display'].tolist() + ['Ending']
                    waterfall_values = [0] + cash_flow_df['net_flow'].tolist() + [net_flow]

                    fig_waterfall = create_waterfall_chart(
                        waterfall_categories,
                        waterfall_values,
                        title="Cash Flow Waterfall",
                        height=350
                    )

                    st.plotly_chart(fig_waterfall, use_container_width=True, config={'displayModeBar': False})
                else:
                    st.info("Waterfall chart is only available for monthly aggregation.")

            st.markdown("---")

            # Category spending and income sources - more compact
            col1, col2 = st.columns(2)

            with col1:
                st.markdown("**💸 Expense Categories**")

                category_spending = calculate_category_spending(df_filtered, start_date_str, end_date_str)

                if not category_spending.empty:
                    # Show top 10 categories
                    top_categories = category_spending.head(10)

                    # Create pie chart - smaller
                    fig_categories = create_pie_chart(
                        top_categories,
                        labels='category_name',
                        values='total_amount',
                        title="Top 10 Expense Categories (Click to drill down)",
                        height=300
                    )

                    # Display chart with click events
                    from streamlit_plotly_events import plotly_events

                    selected_points = plotly_events(
                        fig_categories,
                        click_event=True,
                        hover_event=False,
                        select_event=False,
                        override_height=300,
                        override_width="100%",
                        key="category_pie_chart"
                    )

                    # Show category details when clicked
                    if selected_points and len(selected_points) > 0:
                        # Get the clicked point data
                        point_data = selected_points[0]

                        # Try to get category name from different possible keys
                        selected_category = None
                        if 'pointNumber' in point_data:
                            point_index = point_data['pointNumber']
                            selected_category = top_categories.iloc[point_index]['category_name']
                        elif 'pointIndex' in point_data:
                            point_index = point_data['pointIndex']
                            selected_category = top_categories.iloc[point_index]['category_name']
                        elif 'label' in point_data:
                            selected_category = point_data['label']
                        elif 'x' in point_data:
                            selected_category = point_data['x']

                        if selected_category and selected_category in category_spending['category_name'].values:
                            st.markdown(f"### 🔍 {selected_category}")

                            # Get transactions for this category
                            category_txns = df_filtered[
                                (df_filtered['category_name'] == selected_category) &
                                (df_filtered['type'] == 'withdrawal')
                            ].copy()

                            if not category_txns.empty:
                                # Statistics
                                cols = st.columns(5)
                                cols[0].metric("Transactions", len(category_txns))
                                cols[1].metric("Total", f"€{category_txns['amount'].sum():,.0f}")
                                cols[2].metric("Average", f"€{category_txns['amount'].mean():,.0f}")
                                cols[3].metric("Min", f"€{category_txns['amount'].min():,.0f}")
                                cols[4].metric("Max", f"€{category_txns['amount'].max():,.0f}")

                                # Transaction table
                                st.caption("📋 All Transactions:")

                                # Show all transactions sorted by date
                                category_txns_sorted = category_txns.sort_values('date', ascending=False)
                                display_df = category_txns_sorted[['date', 'description', 'destination_name', 'amount']].copy()
                                # Ensure date is datetime before formatting
                                if not pd.api.types.is_datetime64_any_dtype(display_df['date']):
                                    display_df['date'] = pd.to_datetime(display_df['date'], utc=True)
                                # Remove timezone if present
                                if hasattr(display_df['date'].dt, 'tz') and display_df['date'].dt.tz is not None:
                                    display_df['date'] = display_df['date'].dt.tz_localize(None)
                                display_df['date'] = display_df['date'].dt.strftime('%Y-%m-%d')
                                display_df['amount'] = display_df['amount'].apply(lambda x: f"€{x:,.2f}")

                                st.dataframe(
                                    display_df,
                                    use_container_width=True,
                                    hide_index=True,
                                    column_config={
                                        'date': 'Date',
                                        'description': 'Description',
                                        'destination_name': 'Merchant',
                                        'amount': 'Amount'
                                    },
                                    height=350
                                )

                    # Show table in expander
                    with st.expander("View All Categories", expanded=False):
                        category_spending_display = category_spending.copy()
                        category_spending_display['total_amount'] = category_spending_display['total_amount'].apply(lambda x: f"€{x:,.2f}")
                        st.dataframe(
                            category_spending_display,
                            use_container_width=True,
                            hide_index=True,
                            height=250,
                            column_config={
                                'category_name': 'Category',
                                'total_amount': 'Total Spent',
                                'transaction_count': 'Count'
                            }
                        )
                else:
                    st.info("No categorized expenses found.")

            with col2:
                st.markdown("**💵 Income Sources**")

                income_sources = calculate_income_sources(df_filtered, start_date_str, end_date_str)

                if not income_sources.empty:
                    # Create pie chart - smaller
                    fig_income = create_pie_chart(
                        income_sources,
                        labels='source_name',
                        values='total_amount',
                        title="Income by Source",
                        height=300
                    )

                    st.plotly_chart(fig_income, use_container_width=True, config={'displayModeBar': False})

                    # Show table in expander
                    with st.expander("View All Sources", expanded=False):
                        income_sources_display = income_sources.copy()
                        income_sources_display['total_amount'] = income_sources_display['total_amount'].apply(lambda x: f"€{x:,.2f}")
                        st.dataframe(
                            income_sources_display,
                            use_container_width=True,
                            hide_index=True,
                            height=250,
                            column_config={
                                'source_name': 'Source',
                                'total_amount': 'Total Income',
                                'transaction_count': 'Count'
                            }
                        )
                else:
                    st.info("No income sources found.")

            # Transaction details table - collapsible
            with st.expander("📋 Transaction Details", expanded=False):
                # Add tab for transfers vs income/expenses
                tab1, tab2 = st.tabs(["💸 Income & Expenses", "🔄 Transfers"])

                with tab1:
                    # Add filters - compact
                    col1, col2, col3 = st.columns(3)

                    with col1:
                        transaction_type_filter = st.multiselect(
                            "Type",
                            options=['deposit', 'withdrawal'],
                            default=['deposit', 'withdrawal']
                        )

                    with col2:
                        # Get unique categories (replace None with 'Uncategorized')
                        unique_categories = df_filtered['category_name'].fillna('Uncategorized').unique().tolist()
                        categories = sorted(unique_categories)
                        category_filter = st.multiselect(
                            "Category",
                            options=categories,
                            default=[]
                        )

                    with col3:
                        min_amount = st.number_input(
                            "Min Amount",
                            min_value=0.0,
                            value=0.0,
                            step=10.0
                        )

                    # Apply filters
                    df_display = df_filtered.copy()

                    if transaction_type_filter:
                        df_display = df_display[df_display['type'].isin(transaction_type_filter)]

                    if category_filter:
                        df_display = df_display[df_display['category_name'].isin(category_filter)]

                    if min_amount > 0:
                        df_display = df_display[df_display['amount'] >= min_amount]

                    # Sort by date descending
                    df_display = df_display.sort_values('date', ascending=False)

                    # Format for display
                    df_display_formatted = df_display[['date', 'description', 'type', 'category_name', 'amount', 'currency_code']].copy()
                    # Ensure date is datetime before formatting
                    if not pd.api.types.is_datetime64_any_dtype(df_display_formatted['date']):
                        df_display_formatted['date'] = pd.to_datetime(df_display_formatted['date'], utc=True)
                    # Remove timezone if present
                    if hasattr(df_display_formatted['date'].dt, 'tz') and df_display_formatted['date'].dt.tz is not None:
                        df_display_formatted['date'] = df_display_formatted['date'].dt.tz_localize(None)
                    df_display_formatted['date'] = df_display_formatted['date'].dt.strftime('%Y-%m-%d')
                    df_display_formatted['amount'] = df_display_formatted['amount'].apply(lambda x: f"{x:,.2f}")

                    st.dataframe(
                        df_display_formatted,
                        use_container_width=True,
                        hide_index=True,
                        column_config={
                            'date': 'Date',
                            'description': 'Description',
                            'type': 'Type',
                            'category_name': 'Category',
                            'amount': 'Amount',
                            'currency_code': 'Currency'
                        },
                        height=400
                    )

                    # Export option
                    csv = df_display.to_csv(index=False)
                    st.download_button(
                        label="📥 Download CSV",
                        data=csv,
                        file_name=f"firefly_cashflow_{start_date_str}_to_{end_date_str}.csv",
                        mime="text/csv"
                    )

                with tab2:
                    # Transfers tab
                    if not df_transfers.empty:
                        st.markdown(f"**Total Transfers:** {total_transfers} | **Total Amount:** €{total_transfer_amount:,.2f}")
                        st.caption("ℹ️ Transfers between your accounts are not included in cash flow calculations (income/expenses)")

                        # Sort by date descending
                        df_transfers_display = df_transfers.sort_values('date', ascending=False)

                        # Check if source and destination columns exist
                        display_cols = ['date', 'description', 'amount', 'currency_code']
                        if 'source_name' in df_transfers_display.columns and 'destination_name' in df_transfers_display.columns:
                            display_cols = ['date', 'source_name', 'destination_name', 'description', 'amount', 'currency_code']

                        # Format for display
                        df_transfers_formatted = df_transfers_display[display_cols].copy()
                        # Ensure date is datetime before formatting
                        if not pd.api.types.is_datetime64_any_dtype(df_transfers_formatted['date']):
                            df_transfers_formatted['date'] = pd.to_datetime(df_transfers_formatted['date'], utc=True)
                        # Remove timezone if present
                        if hasattr(df_transfers_formatted['date'].dt, 'tz') and df_transfers_formatted['date'].dt.tz is not None:
                            df_transfers_formatted['date'] = df_transfers_formatted['date'].dt.tz_localize(None)
                        df_transfers_formatted['date'] = df_transfers_formatted['date'].dt.strftime('%Y-%m-%d')
                        df_transfers_formatted['amount'] = df_transfers_formatted['amount'].apply(lambda x: f"{x:,.2f}")

                        column_config = {
                            'date': 'Date',
                            'description': 'Description',
                            'amount': 'Amount',
                            'currency_code': 'Currency'
                        }
                        if 'source_name' in display_cols:
                            column_config['source_name'] = 'From'
                            column_config['destination_name'] = 'To'

                        st.dataframe(
                            df_transfers_formatted,
                            use_container_width=True,
                            hide_index=True,
                            column_config=column_config,
                            height=400
                        )

                        # Export option for transfers
                        csv_transfers = df_transfers_display.to_csv(index=False)
                        st.download_button(
                            label="📥 Download Transfers CSV",
                            data=csv_transfers,
                            file_name=f"firefly_transfers_{start_date_str}_to_{end_date_str}.csv",
                            mime="text/csv"
                        )
                    else:
                        st.info("No transfers found in the selected date range.")

        else:
            st.warning("No transactions found in the selected date range. Please adjust your date range or check your API connection.")

except Exception as e:
    st.error(f"An error occurred: {str(e)}")
    st.exception(e)
