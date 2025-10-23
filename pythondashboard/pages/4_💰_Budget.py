import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import sys
from pathlib import Path

# Add parent directory to path to import utils
sys.path.append(str(Path(__file__).parent.parent))

from utils.api_client import FireflyAPIClient
from utils.charts import (
    create_budget_vs_actual_chart,
    create_budget_utilization_gauges,
    create_burn_rate_chart,
    create_budget_progress_bars
)
from utils.calculations import (
    calculate_budget_performance,
    calculate_budget_burn_rate,
    get_date_ranges
)

# Page configuration
st.set_page_config(
    page_title="Budget Dashboard - Firefly III",
    page_icon="💰",
    layout="wide"
)

# Compact CSS styling with dark mode support
st.markdown("""
<style>
    .block-container {
        padding-top: 5rem !important;
        padding-bottom: 0rem;
        padding-left: 2rem;
        padding-right: 2rem;
    }
    h1 {
        padding-top: 0rem;
        padding-bottom: 0.5rem;
        font-size: 2rem;
        margin-top: 0;
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
        font-size: 0.85rem;
    }
    [data-testid="stMetricValue"] {
        font-size: 1.5rem;
    }
    [data-testid="stMetricLabel"] {
        font-size: 0.85rem;
    }
</style>
""", unsafe_allow_html=True)

# Main app
st.title("💰 Budget Dashboard")

# Sidebar for API configuration
st.sidebar.header("🔧 API Configuration")

# Initialize session state for API credentials
if 'firefly_url' not in st.session_state:
    st.session_state.firefly_url = "http://192.168.0.242"
if 'firefly_token' not in st.session_state:
    st.session_state.firefly_token = ""
if 'api_connected' not in st.session_state:
    st.session_state.api_connected = False

# API configuration form
with st.sidebar.form("api_config"):
    firefly_url = st.text_input(
        "Firefly III URL",
        value=st.session_state.firefly_url,
        placeholder="http://192.168.0.242"
    )

    firefly_token = st.text_input(
        "API Token",
        value=st.session_state.firefly_token,
        type="password",
        help="Generate a Personal Access Token in Firefly III under Profile → OAuth"
    )

    submit_button = st.form_submit_button("Connect")

    if submit_button:
        if not firefly_url or not firefly_token:
            st.sidebar.error("Please provide both URL and API token")
        else:
            st.session_state.firefly_url = firefly_url
            st.session_state.firefly_token = firefly_token

            # Test connection
            client = FireflyAPIClient(firefly_url, firefly_token)
            success, message = client.test_connection()

            if success:
                st.session_state.api_connected = True
                st.sidebar.success(message)
                st.rerun()
            else:
                st.session_state.api_connected = False
                st.sidebar.error(message)

# Connection status
if st.session_state.api_connected:
    st.sidebar.success("✅ Connected to Firefly III")
else:
    st.sidebar.warning("⚠️ Not connected")

# Display help if not connected
if not st.session_state.api_connected:
    st.info("""
    ### 🔑 Getting Started

    To use this dashboard, you need to configure the API connection:

    1. **Generate an API Token** in Firefly III:
       - Go to your Firefly III instance
       - Navigate to **Profile → OAuth**
       - Click **Create New Token**
       - Copy the generated token

    2. **Enter your details** in the sidebar:
       - Firefly III URL (e.g., `http://192.168.0.242`)
       - Paste the API token
       - Click **Connect**

    Once connected, your budget data will be displayed automatically.
    """)
    st.stop()

# Sidebar budget period selection
st.sidebar.header("📅 Budget Period")

period_type = st.sidebar.selectbox(
    "Select Period",
    ["Current Month", "Current Quarter", "Current Year", "Custom"]
)

today = datetime.now()

if period_type == "Current Month":
    date_ranges = get_date_ranges('month')
    start_date_str, end_date_str = date_ranges['current']
elif period_type == "Current Quarter":
    date_ranges = get_date_ranges('quarter')
    start_date_str, end_date_str = date_ranges['current']
elif period_type == "Current Year":
    date_ranges = get_date_ranges('year')
    start_date_str, end_date_str = date_ranges['current']
else:  # Custom
    col1, col2 = st.sidebar.columns(2)
    with col1:
        start_date = st.date_input("Start Date", datetime(today.year, today.month, 1))
    with col2:
        if today.month == 12:
            end_date = st.date_input("End Date", datetime(today.year, 12, 31))
        else:
            end_date = st.date_input("End Date", datetime(today.year, today.month + 1, 1) - timedelta(days=1))

    start_date_str = start_date.strftime('%Y-%m-%d')
    end_date_str = end_date.strftime('%Y-%m-%d')

# Main content - Fetch and display data
try:
    client = FireflyAPIClient(st.session_state.firefly_url, st.session_state.firefly_token)

    # Add refresh button
    col1, col2, col3 = st.columns([1, 1, 4])
    with col1:
        if st.button("🔄 Refresh Data"):
            st.cache_data.clear()
            st.rerun()
    with col2:
        st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    st.divider()

    # Cache data fetching
    @st.cache_data(ttl=300)
    def fetch_budget_data(_client, start, end):
        """Fetch budgets, budget limits, and transactions with caching"""
        budgets = _client.get_budgets()

        # Fetch budget limits for each budget
        budget_limits = {}
        for budget in budgets:
            budget_id = budget.get('id')
            limits = _client.get_budget_limits(budget_id, start, end)
            budget_limits[budget_id] = limits

        # Fetch transactions
        transactions = _client.get_transactions(start_date=start, end_date=end)

        return budgets, budget_limits, transactions

    # Fetch data
    with st.spinner("Loading budget data..."):
        budgets_data, budget_limits_data, transactions_data = fetch_budget_data(
            client, start_date_str, end_date_str
        )

        if not budgets_data:
            st.warning("No budgets found. Please create budgets in Firefly III first.")
            st.info("""
            **To create budgets in Firefly III:**
            1. Go to your Firefly III instance
            2. Navigate to **Budgets** in the menu
            3. Click **Create a new budget**
            4. Set budget limits for the desired period
            """)
            st.stop()

        # Parse transaction data
        if transactions_data:
            df_transactions = client.parse_transaction_data(transactions_data)
        else:
            df_transactions = pd.DataFrame()

        # Calculate budget performance
        budget_performance = calculate_budget_performance(
            budgets_data,
            budget_limits_data,
            df_transactions,
            start_date_str,
            end_date_str
        )

        if budget_performance.empty:
            st.warning("No budget limits set for the selected period.")
            st.stop()

        # Calculate summary metrics
        total_budgeted = budget_performance['budgeted'].sum()
        total_spent = budget_performance['spent'].sum()
        total_remaining = budget_performance['remaining'].sum()
        overall_utilization = (total_spent / total_budgeted * 100) if total_budgeted > 0 else 0

        # Count budgets by status
        over_budget_count = len(budget_performance[budget_performance['status'] == 'Over Budget'])
        warning_count = len(budget_performance[budget_performance['status'] == 'Warning'])
        on_track_count = len(budget_performance[budget_performance['status'] == 'On Track'])

        # Display summary metrics
        st.header("💰 Budget Summary")

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(
                label="Total Budgeted",
                value=f"€{total_budgeted:,.2f}"
            )

        with col2:
            st.metric(
                label="Total Spent",
                value=f"€{total_spent:,.2f}"
            )

        with col3:
            color = "normal" if total_remaining >= 0 else "inverse"
            st.metric(
                label="Total Remaining",
                value=f"€{total_remaining:,.2f}"
            )

        with col4:
            st.metric(
                label="Overall Utilization",
                value=f"{overall_utilization:.1f}%"
            )

        st.divider()

        # Budget status counts
        st.subheader("📊 Budget Status")

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric(
                label="✅ On Track",
                value=on_track_count,
                help="Budgets under 80% utilization"
            )

        with col2:
            st.metric(
                label="⚠️ Warning",
                value=warning_count,
                help="Budgets between 80-100% utilization"
            )

        with col3:
            st.metric(
                label="🚨 Over Budget",
                value=over_budget_count,
                help="Budgets exceeding 100% utilization"
            )

        st.divider()

        # Budget vs Actual Chart
        st.header("📊 Budget vs. Actual Spending")

        fig_budget_vs_actual = create_budget_vs_actual_chart(
            budget_performance,
            title="Budget Performance by Category",
            height=500
        )
        st.plotly_chart(fig_budget_vs_actual, use_container_width=True)

        st.divider()

        # Budget Utilization Progress Bars
        st.header("📈 Budget Utilization")

        fig_progress = create_budget_progress_bars(budget_performance, height=400)
        st.plotly_chart(fig_progress, use_container_width=True)

        st.divider()

        # Individual Budget Gauges (top 6 by utilization)
        st.header("🎯 Top Budget Utilization Gauges")

        top_budgets = budget_performance.head(6)

        cols = st.columns(3)
        for idx, (_, budget) in enumerate(top_budgets.iterrows()):
            with cols[idx % 3]:
                fig_gauge = create_budget_utilization_gauges(
                    budget['budget_name'],
                    budget['utilization_pct'],
                    height=250
                )
                st.plotly_chart(fig_gauge, use_container_width=True)

        st.divider()

        # Burn Rate Analysis
        st.header("🔥 Budget Burn Rate Analysis")

        if total_budgeted > 0:
            burn_rate_metrics = calculate_budget_burn_rate(
                total_budgeted,
                total_spent,
                start_date_str,
                end_date_str
            )

            col1, col2 = st.columns(2)

            with col1:
                st.subheader("📅 Time Analysis")

                col_a, col_b, col_c = st.columns(3)
                with col_a:
                    st.metric(
                        label="Days Elapsed",
                        value=burn_rate_metrics['days_elapsed']
                    )
                with col_b:
                    st.metric(
                        label="Days Remaining",
                        value=burn_rate_metrics['days_remaining']
                    )
                with col_c:
                    st.metric(
                        label="Total Days",
                        value=burn_rate_metrics['total_days']
                    )

            with col2:
                st.subheader("💸 Burn Rate Metrics")

                daily_budget = total_budgeted / burn_rate_metrics['total_days'] if burn_rate_metrics['total_days'] > 0 else 0

                col_a, col_b = st.columns(2)
                with col_a:
                    st.metric(
                        label="Daily Budget",
                        value=f"€{daily_budget:,.2f}"
                    )
                with col_b:
                    st.metric(
                        label="Actual Burn Rate",
                        value=f"€{burn_rate_metrics['burn_rate']:,.2f}",
                        delta=f"€{burn_rate_metrics['burn_rate'] - daily_budget:,.2f}",
                        delta_color="inverse"
                    )

            st.divider()

            # Burn rate chart
            fig_burn_rate = create_burn_rate_chart(
                burn_rate_metrics['burn_rate'],
                daily_budget,
                title="Daily Spending: Ideal vs. Actual",
                height=350
            )
            st.plotly_chart(fig_burn_rate, use_container_width=True)

            # Projection
            st.subheader("🔮 End-of-Period Projection")

            col1, col2 = st.columns(2)
            with col1:
                st.metric(
                    label="Projected Total Spend",
                    value=f"€{burn_rate_metrics['projected_spend']:,.2f}"
                )
            with col2:
                delta_value = burn_rate_metrics['projected_over_under']
                if delta_value >= 0:
                    st.metric(
                        label="Projected Under Budget",
                        value=f"€{abs(delta_value):,.2f}",
                        delta="Under budget",
                        delta_color="normal"
                    )
                else:
                    st.metric(
                        label="Projected Over Budget",
                        value=f"€{abs(delta_value):,.2f}",
                        delta="Over budget",
                        delta_color="inverse"
                    )

            if burn_rate_metrics['projected_over_under'] < 0:
                st.warning(f"⚠️ At the current spending rate, you are projected to exceed your budget by €{abs(burn_rate_metrics['projected_over_under']):,.2f}")
            else:
                st.success(f"✅ At the current spending rate, you are projected to stay within budget with €{burn_rate_metrics['projected_over_under']:,.2f} remaining")

        st.divider()

        # Budget Details Table
        st.header("📋 Budget Details")

        # Add filter for status
        status_filter = st.multiselect(
            "Filter by Status",
            options=['On Track', 'Warning', 'Over Budget'],
            default=['On Track', 'Warning', 'Over Budget']
        )

        # Apply filter
        budget_display = budget_performance.copy()
        if status_filter:
            budget_display = budget_display[budget_display['status'].isin(status_filter)]

        # Format for display
        budget_display_formatted = budget_display.copy()
        budget_display_formatted['budgeted'] = budget_display_formatted['budgeted'].apply(lambda x: f"€{x:,.2f}")
        budget_display_formatted['spent'] = budget_display_formatted['spent'].apply(lambda x: f"€{x:,.2f}")
        budget_display_formatted['remaining'] = budget_display_formatted['remaining'].apply(lambda x: f"€{x:,.2f}")
        budget_display_formatted['utilization_pct'] = budget_display_formatted['utilization_pct'].apply(lambda x: f"{x:.1f}%")

        # Add color coding for status
        def color_status(val):
            if val == 'Over Budget':
                return 'background-color: rgba(248, 113, 113, 0.3)'
            elif val == 'Warning':
                return 'background-color: rgba(251, 191, 36, 0.3)'
            else:
                return 'background-color: rgba(74, 222, 128, 0.3)'

        st.dataframe(
            budget_display_formatted[['budget_name', 'budgeted', 'spent', 'remaining', 'utilization_pct', 'status']],
            use_container_width=True,
            hide_index=True,
            column_config={
                'budget_name': 'Budget',
                'budgeted': 'Budgeted',
                'spent': 'Spent',
                'remaining': 'Remaining',
                'utilization_pct': 'Utilization',
                'status': 'Status'
            },
            height=400
        )

        # Export option
        st.divider()
        csv = budget_display.to_csv(index=False)
        st.download_button(
            label="📥 Download Budget Data (CSV)",
            data=csv,
            file_name=f"firefly_budgets_{start_date_str}_to_{end_date_str}.csv",
            mime="text/csv"
        )

except Exception as e:
    st.error(f"An error occurred: {str(e)}")
    st.exception(e)
