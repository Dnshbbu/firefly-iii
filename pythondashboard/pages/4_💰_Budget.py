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
from utils.navigation import render_sidebar_navigation
from utils.config import get_firefly_url, get_firefly_token

# Page configuration
st.set_page_config(
    page_title="Budget Dashboard - Firefly III",
    page_icon="💰",
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
st.title("💰 Budget Dashboard")

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

# Sidebar budget period selection
st.sidebar.header("📅 Budget Period")

period_type = st.sidebar.selectbox(
    "Select Period",
    ["Last 7 Days", "Last 30 Days", "Last 3 Months", "Last 6 Months", "Last 12 Months",
     "Last Exact 3 Months", "Last Exact 6 Months", "Last Exact 12 Months",
     "Current Month", "Current Quarter", "Current Year", 
     "Last Month", "Last Quarter", "Last Year", "Year to Date", "Custom"],
    index=8  # Default to "Current Month"
)

today = datetime.now()
first_day_of_month = datetime(today.year, today.month, 1)

if period_type == "Last 7 Days":
    start_date_str = (today - timedelta(days=7)).strftime('%Y-%m-%d')
    end_date_str = today.strftime('%Y-%m-%d')
elif period_type == "Last 30 Days":
    start_date_str = (today - timedelta(days=30)).strftime('%Y-%m-%d')
    end_date_str = today.strftime('%Y-%m-%d')
elif period_type == "Last 3 Months":
    start_date_str = (today - timedelta(days=90)).strftime('%Y-%m-%d')
    end_date_str = today.strftime('%Y-%m-%d')
elif period_type == "Last 6 Months":
    start_date_str = (today - timedelta(days=180)).strftime('%Y-%m-%d')
    end_date_str = today.strftime('%Y-%m-%d')
elif period_type == "Last 12 Months":
    start_date_str = (today - timedelta(days=365)).strftime('%Y-%m-%d')
    end_date_str = today.strftime('%Y-%m-%d')
elif period_type == "Last Exact 3 Months":
    # Get complete months only (e.g., if today is Oct 26, show Jul 1 - Sep 30)
    if today.month <= 3:
        start_date = datetime(today.year - 1, today.month + 9, 1)
        end_date = datetime(today.year, today.month - 1, 1) - timedelta(days=1) if today.month > 1 else datetime(today.year - 1, 12, 31)
    else:
        start_date = datetime(today.year, today.month - 3, 1)
        end_date = datetime(today.year, today.month, 1) - timedelta(days=1)
    start_date_str = start_date.strftime('%Y-%m-%d')
    end_date_str = end_date.strftime('%Y-%m-%d')
elif period_type == "Last Exact 6 Months":
    # Get complete months only
    if today.month <= 6:
        start_date = datetime(today.year - 1, today.month + 6, 1)
        end_date = datetime(today.year, today.month - 1, 1) - timedelta(days=1) if today.month > 1 else datetime(today.year - 1, 12, 31)
    else:
        start_date = datetime(today.year, today.month - 6, 1)
        end_date = datetime(today.year, today.month, 1) - timedelta(days=1)
    start_date_str = start_date.strftime('%Y-%m-%d')
    end_date_str = end_date.strftime('%Y-%m-%d')
elif period_type == "Last Exact 12 Months":
    # Get complete months only (previous 12 full months)
    start_date = datetime(today.year - 1, today.month, 1)
    end_date = datetime(today.year, today.month, 1) - timedelta(days=1)
    start_date_str = start_date.strftime('%Y-%m-%d')
    end_date_str = end_date.strftime('%Y-%m-%d')
elif period_type == "Current Month":
    date_ranges = get_date_ranges('month')
    start_date_str, end_date_str = date_ranges['current']
elif period_type == "Current Quarter":
    date_ranges = get_date_ranges('quarter')
    start_date_str, end_date_str = date_ranges['current']
elif period_type == "Current Year":
    date_ranges = get_date_ranges('year')
    start_date_str, end_date_str = date_ranges['current']
elif period_type == "Last Month":
    if today.month == 1:
        start_date = datetime(today.year - 1, 12, 1)
        end_date = first_day_of_month - timedelta(days=1)
    else:
        start_date = datetime(today.year, today.month - 1, 1)
        end_date = first_day_of_month - timedelta(days=1)
    start_date_str = start_date.strftime('%Y-%m-%d')
    end_date_str = end_date.strftime('%Y-%m-%d')
elif period_type == "Last Quarter":
    quarter = (today.month - 1) // 3
    if quarter == 0:
        start_date = datetime(today.year - 1, 10, 1)
        end_date = datetime(today.year - 1, 12, 31)
    else:
        start_date = datetime(today.year, (quarter - 1) * 3 + 1, 1)
        end_date = datetime(today.year, quarter * 3, 1) - timedelta(days=1)
    start_date_str = start_date.strftime('%Y-%m-%d')
    end_date_str = end_date.strftime('%Y-%m-%d')
elif period_type == "Last Year":
    start_date_str = f"{today.year - 1}-01-01"
    end_date_str = f"{today.year - 1}-12-31"
elif period_type == "Year to Date":
    start_date_str = f"{today.year}-01-01"
    end_date_str = today.strftime('%Y-%m-%d')
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

        # Display all metrics in single compact section
        st.markdown("### 💰 Budget Summary")

        # Row 1: Main metrics
        cols = st.columns(7)
        cols[0].metric("Total Budgeted", f"€{total_budgeted:,.0f}")
        cols[1].metric("Total Spent", f"€{total_spent:,.0f}")
        cols[2].metric("Remaining", f"€{total_remaining:,.0f}")
        cols[3].metric("Utilization", f"{overall_utilization:.1f}%")
        cols[4].metric("✅ On Track", on_track_count)
        cols[5].metric("⚠️ Warning", warning_count)
        cols[6].metric("🚨 Over", over_budget_count)

        # Related dashboards navigation - compact
        st.markdown('<div style="background-color: rgba(49, 51, 63, 0.2); padding: 0.3rem 0.5rem; border-radius: 0.3rem; font-size: 0.75rem;">💡 <b>Related:</b> <a href="/Budget_Timeline" style="color: #58a6ff;">📅 Timeline</a> • <a href="/Cash_Flow" style="color: #58a6ff;">📈 Cash Flow</a> • <a href="/Categories" style="color: #58a6ff;">🏷️ Categories</a></div>', unsafe_allow_html=True)

        st.markdown("---")

        # Budget charts - side by side
        st.markdown("### 📊 Budget Performance")

        chart_col1, chart_col2 = st.columns(2)

        with chart_col1:
            fig_budget_vs_actual = create_budget_vs_actual_chart(
                budget_performance,
                title="Budget vs. Actual Spending",
                height=350
            )
            st.plotly_chart(fig_budget_vs_actual, use_container_width=True, config={'displayModeBar': False})

        with chart_col2:
            fig_progress = create_budget_progress_bars(budget_performance, height=350)
            st.plotly_chart(fig_progress, use_container_width=True, config={'displayModeBar': False})

        st.markdown("---")

        # Top 6 budget gauges - compact 3x2 grid
        st.markdown("### 🎯 Budget Utilization Overview")

        top_budgets = budget_performance.head(6)
        cols = st.columns(3)
        for idx, (_, budget) in enumerate(top_budgets.iterrows()):
            with cols[idx % 3]:
                fig_gauge = create_budget_utilization_gauges(
                    budget['budget_name'],
                    budget['utilization_pct'],
                    height=200
                )
                st.plotly_chart(fig_gauge, use_container_width=True, config={'displayModeBar': False})

        st.markdown("---")

        # Burn Rate Analysis - compact
        st.markdown("### 🔥 Burn Rate Analysis")

        if total_budgeted > 0:
            burn_rate_metrics = calculate_budget_burn_rate(
                total_budgeted,
                total_spent,
                start_date_str,
                end_date_str
            )

            daily_budget = total_budgeted / burn_rate_metrics['total_days'] if burn_rate_metrics['total_days'] > 0 else 0

            # All metrics in one row
            cols = st.columns(7)
            cols[0].metric("Days Elapsed", burn_rate_metrics['days_elapsed'])
            cols[1].metric("Days Left", burn_rate_metrics['days_remaining'])
            cols[2].metric("Daily Budget", f"€{daily_budget:,.0f}")
            cols[3].metric("Actual Burn", f"€{burn_rate_metrics['burn_rate']:,.0f}")
            cols[4].metric("Projected Spend", f"€{burn_rate_metrics['projected_spend']:,.0f}")

            delta_value = burn_rate_metrics['projected_over_under']
            if delta_value >= 0:
                cols[5].metric("Under Budget", f"€{abs(delta_value):,.0f}")
                cols[6].markdown("**✅ On Track**")
            else:
                cols[5].metric("Over Budget", f"€{abs(delta_value):,.0f}")
                cols[6].markdown("**⚠️ Warning**")

            # Compact burn rate chart
            col1, col2 = st.columns([2, 3])
            with col1:
                fig_burn_rate = create_burn_rate_chart(
                    burn_rate_metrics['burn_rate'],
                    daily_budget,
                    title="Daily Spending: Ideal vs. Actual",
                    height=250
                )
                st.plotly_chart(fig_burn_rate, use_container_width=True, config={'displayModeBar': False})

            with col2:
                if burn_rate_metrics['projected_over_under'] < 0:
                    st.markdown(f"**⚠️ Budget Alert**\n\nAt the current spending rate, you are projected to exceed your budget by **€{abs(burn_rate_metrics['projected_over_under']):,.0f}**")
                else:
                    st.markdown(f"**✅ Budget Status**\n\nAt the current spending rate, you are projected to stay within budget with **€{burn_rate_metrics['projected_over_under']:,.0f}** remaining")

        st.markdown("---")

        # Budget Details Table - collapsible
        with st.expander("📋 Budget Details", expanded=False):
            # Add filter for status - compact
            col1, col2 = st.columns([3, 3])
            with col1:
                status_filter = st.multiselect(
                    "Filter by Status",
                    options=['On Track', 'Warning', 'Over Budget'],
                    default=['On Track', 'Warning', 'Over Budget']
                )

            # Apply filter
            budget_display = budget_performance.copy()
            if status_filter:
                budget_display = budget_display[budget_display['status'].isin(status_filter)]

            st.dataframe(
                budget_display[['budget_name', 'budgeted', 'spent', 'remaining', 'utilization_pct', 'status']],
                use_container_width=True,
                hide_index=True,
                column_config={
                    'budget_name': 'Budget',
                    'budgeted': st.column_config.NumberColumn('Budgeted', format="€%.2f"),
                    'spent': st.column_config.NumberColumn('Spent', format="€%.2f"),
                    'remaining': st.column_config.NumberColumn('Remaining', format="€%.2f"),
                    'utilization_pct': st.column_config.NumberColumn('Utilization', format="%.1f%%"),
                    'status': 'Status'
                },
                height=400
            )

            # Export option
            csv = budget_display.to_csv(index=False)
            st.download_button(
                label="📥 Download CSV",
                data=csv,
                file_name=f"firefly_budgets_{start_date_str}_to_{end_date_str}.csv",
                mime="text/csv"
            )

except Exception as e:
    st.error(f"An error occurred: {str(e)}")
    st.exception(e)
