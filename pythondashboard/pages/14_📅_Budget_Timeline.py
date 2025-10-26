import streamlit as st
import pandas as pd
import requests
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import calendar
import sys
from pathlib import Path

# Add parent directory to path to import utils
sys.path.append(str(Path(__file__).parent.parent))

from utils.api_client import FireflyAPIClient

# Page configuration
st.set_page_config(
    page_title="Budget Timeline - Firefly III",
    page_icon="📅",
    layout="wide"
)

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


def get_year_date_range(year: int) -> tuple[str, str]:
    """Get start and end dates for a year"""
    start_date = f"{year}-01-01"
    end_date = f"{year}-12-31"
    return start_date, end_date


def get_monthly_budget_data(
    budgets_data: List[Dict],
    budget_limits_data: Dict[str, List[Dict]],
    transactions_df: pd.DataFrame,
    year: int
) -> pd.DataFrame:
    """
    Calculate monthly budget data across all budgets.

    Returns DataFrame with columns:
    - month: Month number (1-12)
    - month_name: Month name
    - budgeted: Total budgeted amount for the month
    - spent: Total spent amount for the month
    - remaining: Remaining budget
    - deviation: Deviation from budget (negative = over budget)
    - deviation_pct: Deviation as percentage
    - status: Status indicator
    """
    monthly_data = []

    for month in range(1, 13):
        # Get start and end dates for this month
        start_date = datetime(year, month, 1)
        last_day = calendar.monthrange(year, month)[1]
        end_date = datetime(year, month, last_day)

        start_str = start_date.strftime('%Y-%m-%d')
        end_str = end_date.strftime('%Y-%m-%d')

        total_budgeted = 0.0
        total_spent = 0.0

        # Calculate budgeted amount for this month across all budgets
        for budget in budgets_data:
            budget_id = budget.get('id')
            budget_name = budget.get('attributes', {}).get('name', 'Unknown')

            # Get budget limits for this budget
            limits = budget_limits_data.get(budget_id, [])

            for limit in limits:
                limit_attrs = limit.get('attributes', {})
                limit_start = limit_attrs.get('start')
                limit_end = limit_attrs.get('end')
                limit_amount = float(limit_attrs.get('amount', 0))

                # Check if this limit overlaps with our month
                if limit_start and limit_end:
                    limit_start_date = datetime.strptime(limit_start, '%Y-%m-%dT%H:%M:%S%z').replace(tzinfo=None) if 'T' in limit_start else datetime.strptime(limit_start, '%Y-%m-%d')
                    limit_end_date = datetime.strptime(limit_end, '%Y-%m-%dT%H:%M:%S%z').replace(tzinfo=None) if 'T' in limit_end else datetime.strptime(limit_end, '%Y-%m-%d')

                    # Check for overlap
                    if limit_start_date <= end_date and limit_end_date >= start_date:
                        # Calculate the overlap proportion
                        overlap_start = max(limit_start_date, start_date)
                        overlap_end = min(limit_end_date, end_date)
                        overlap_days = (overlap_end - overlap_start).days + 1
                        total_limit_days = (limit_end_date - limit_start_date).days + 1

                        # Prorate the budget amount based on overlap
                        prorated_amount = (limit_amount * overlap_days) / total_limit_days if total_limit_days > 0 else limit_amount
                        total_budgeted += prorated_amount

            # Calculate spent amount for this budget in this month
            if not transactions_df.empty:
                # Make start_date and end_date timezone-aware if transactions have timezone info
                compare_start = start_date
                compare_end = end_date
                if transactions_df['date'].dt.tz is not None:
                    compare_start = pd.Timestamp(start_date).tz_localize(transactions_df['date'].dt.tz)
                    compare_end = pd.Timestamp(end_date).tz_localize(transactions_df['date'].dt.tz)

                budget_transactions = transactions_df[
                    (transactions_df['budget_name'] == budget_name) &
                    (transactions_df['type'] == 'withdrawal') &
                    (transactions_df['date'] >= compare_start) &
                    (transactions_df['date'] <= compare_end)
                ]
                total_spent += budget_transactions['amount'].sum()

        # Calculate metrics
        remaining = total_budgeted - total_spent
        deviation = -remaining  # Negative deviation means over budget
        deviation_pct = (deviation / total_budgeted * 100) if total_budgeted > 0 else 0

        # Determine status
        if month > datetime.now().month and year == datetime.now().year:
            status = 'Future'
        elif total_budgeted == 0:
            status = 'No Budget'
        elif deviation_pct > 0:
            status = 'Over Budget'
        elif deviation_pct > -20:
            status = 'On Track'
        else:
            status = 'Under Budget'

        monthly_data.append({
            'month': month,
            'month_name': calendar.month_abbr[month],
            'month_full': calendar.month_name[month],
            'budgeted': total_budgeted,
            'spent': total_spent,
            'remaining': remaining,
            'deviation': deviation,
            'deviation_pct': deviation_pct,
            'status': status
        })

    return pd.DataFrame(monthly_data)


def create_timeline_chart(monthly_df: pd.DataFrame, current_month: int) -> go.Figure:
    """Create a timeline chart showing budgeted vs actual spending"""
    fig = go.Figure()

    # Add expected (budgeted) bars
    fig.add_trace(go.Bar(
        x=monthly_df['month_name'],
        y=monthly_df['budgeted'],
        name='Expected',
        marker_color='steelblue',
        text=monthly_df['budgeted'].apply(lambda x: f'€{x:,.0f}' if x > 0 else ''),
        textposition='outside',
        textfont=dict(size=9)
    ))

    # Add actual spending bars with conditional coloring
    actual_colors = monthly_df.apply(
        lambda row: 'crimson' if row['spent'] > row['budgeted'] and row['budgeted'] > 0
        else 'lightgreen' if row['month'] <= current_month
        else 'lightgray',
        axis=1
    )

    fig.add_trace(go.Bar(
        x=monthly_df['month_name'],
        y=monthly_df['spent'],
        name='Actual',
        marker_color=actual_colors,
        text=monthly_df['spent'].apply(lambda x: f'€{x:,.0f}' if x > 0 else ''),
        textposition='outside',
        textfont=dict(size=9)
    ))

    fig.update_layout(
        title="Annual Budget Timeline: Expected vs Actual Spending",
        xaxis_title="Month",
        yaxis_title="Amount (€)",
        barmode='group',  # Changed from 'overlay' to 'group' for clustered bars
        height=400,
        margin=dict(t=60, b=40, l=60, r=20),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(size=10)
        ),
        font=dict(size=10),
        hovermode='x unified'
    )

    # Add vertical line for current month
    fig.add_vline(
        x=current_month - 1,
        line_dash="dash",
        line_color="orange",
        annotation_text="Today",
        annotation_position="top",
        annotation_font_size=9
    )

    return fig


def create_deviation_chart(monthly_df: pd.DataFrame, current_month: int) -> go.Figure:
    """Create a chart showing budget deviations by month"""
    # Filter to only show past and current months
    past_months = monthly_df[monthly_df['month'] <= current_month].copy()

    colors = past_months['deviation'].apply(
        lambda x: 'red' if x > 0 else 'green'
    )

    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=past_months['month_name'],
        y=past_months['deviation'],
        marker_color=colors,
        text=past_months['deviation'].apply(lambda x: f'€{x:,.0f}'),
        textposition='outside',
        textfont=dict(size=9),
        showlegend=False
    ))

    # Add zero line
    fig.add_hline(y=0, line_dash="solid", line_color="black", line_width=1)

    fig.update_layout(
        title="Budget Deviations (Over/Under Budget)",
        xaxis_title="Month",
        yaxis_title="Deviation (€)",
        height=300,
        margin=dict(t=40, b=30, l=60, r=20),
        font=dict(size=10)
    )

    return fig


def create_cumulative_chart(monthly_df: pd.DataFrame, current_month: int) -> go.Figure:
    """Create a chart showing cumulative budget vs actual over time"""
    # Calculate cumulative values
    monthly_df['cumulative_budgeted'] = monthly_df['budgeted'].cumsum()
    monthly_df['cumulative_spent'] = monthly_df['spent'].cumsum()

    fig = go.Figure()

    # Cumulative budgeted line
    fig.add_trace(go.Scatter(
        x=monthly_df['month_name'],
        y=monthly_df['cumulative_budgeted'],
        mode='lines+markers',
        name='Cumulative Budget',
        line=dict(color='blue', width=2),
        marker=dict(size=6)
    ))

    # Cumulative spent line (only up to current month)
    actual_data = monthly_df[monthly_df['month'] <= current_month]
    fig.add_trace(go.Scatter(
        x=actual_data['month_name'],
        y=actual_data['cumulative_spent'],
        mode='lines+markers',
        name='Cumulative Spent',
        line=dict(color='red', width=2, dash='dash'),
        marker=dict(size=6)
    ))

    # Projection line (from current month to end of year)
    if current_month < 12:
        # Calculate average monthly spending so far
        avg_monthly_spend = monthly_df[monthly_df['month'] <= current_month]['spent'].mean()

        # Project future spending
        projection_months = list(range(current_month, 13))
        projection_values = []
        last_cumulative = actual_data['cumulative_spent'].iloc[-1] if not actual_data.empty else 0

        for i, month in enumerate(projection_months):
            if i == 0:
                projection_values.append(last_cumulative)
            else:
                projection_values.append(projection_values[-1] + avg_monthly_spend)

        projection_names = [monthly_df[monthly_df['month'] == m]['month_name'].iloc[0] for m in projection_months]

        fig.add_trace(go.Scatter(
            x=projection_names,
            y=projection_values,
            mode='lines+markers',
            name='Projected Spending',
            line=dict(color='orange', width=2, dash='dot'),
            marker=dict(size=5, symbol='diamond')
        ))

    fig.update_layout(
        title="Cumulative Budget vs Actual Spending",
        xaxis_title="Month",
        yaxis_title="Cumulative Amount (€)",
        height=350,
        margin=dict(t=40, b=30, l=60, r=20),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(size=9)
        ),
        font=dict(size=10),
        hovermode='x unified'
    )

    return fig


def create_monthly_breakdown_table(monthly_df: pd.DataFrame) -> pd.DataFrame:
    """Format monthly data for display"""
    df = monthly_df.copy()

    # Format currency columns
    for col in ['budgeted', 'spent', 'remaining', 'deviation']:
        df[col] = df[col].apply(lambda x: f'€{x:,.2f}')

    df['deviation_pct'] = df['deviation_pct'].apply(lambda x: f'{x:.1f}%')

    return df[['month_full', 'budgeted', 'spent', 'remaining', 'deviation', 'deviation_pct', 'status']]


# Main app
st.title("📅 Budget Timeline & Roadmap")

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

    Once connected, your budget timeline will be displayed automatically.
    """)
    st.stop()

# Sidebar year selection
st.sidebar.header("📅 Timeline Period")
current_year = datetime.now().year
selected_year = st.sidebar.selectbox(
    "Select Year",
    options=[current_year - 1, current_year, current_year + 1],
    index=1
)

# Main content
try:
    client = FireflyAPIClient(st.session_state.firefly_url, st.session_state.firefly_token)

    # Add refresh button
    col1, col2 = st.columns([1, 5])
    with col1:
        if st.button("🔄 Refresh"):
            st.cache_data.clear()
            st.rerun()
    with col2:
        st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Year: {selected_year}")

    st.markdown("---")

    # Cache data fetching
    @st.cache_data(ttl=300)
    def fetch_timeline_data(_client, year):
        """Fetch all budget data for the entire year"""
        start_date, end_date = get_year_date_range(year)

        budgets = _client.get_budgets()

        # Fetch budget limits for each budget
        budget_limits = {}
        for budget in budgets:
            budget_id = budget.get('id')
            limits = _client.get_budget_limits(budget_id, start_date, end_date)
            budget_limits[budget_id] = limits

        # Fetch all transactions for the year
        transactions = _client.get_transactions(start_date=start_date, end_date=end_date)

        return budgets, budget_limits, transactions

    # Fetch data
    with st.spinner("Loading budget timeline data..."):
        budgets_data, budget_limits_data, transactions_data = fetch_timeline_data(
            client, selected_year
        )

        if not budgets_data:
            st.warning("No budgets found. Please create budgets in Firefly III first.")
            st.info("""
            **To create budgets in Firefly III:**
            1. Go to your Firefly III instance
            2. Navigate to **Budgets** in the menu
            3. Click **Create a new budget**
            4. Set budget limits for the desired periods
            """)
            st.stop()

        # Parse transaction data
        if transactions_data:
            df_transactions = client.parse_transaction_data(transactions_data)
        else:
            df_transactions = pd.DataFrame()

        # Calculate monthly budget data
        monthly_df = get_monthly_budget_data(
            budgets_data,
            budget_limits_data,
            df_transactions,
            selected_year
        )

        current_month = datetime.now().month if selected_year == datetime.now().year else 12

        # Calculate summary metrics
        total_budgeted = monthly_df['budgeted'].sum()
        total_spent = monthly_df[monthly_df['month'] <= current_month]['spent'].sum()
        total_remaining = total_budgeted - total_spent
        ytd_months = current_month if selected_year == datetime.now().year else 12
        avg_monthly_budget = total_budgeted / 12
        avg_monthly_spend = total_spent / ytd_months if ytd_months > 0 else 0

        # Projection for rest of year
        months_remaining = 12 - current_month if selected_year == datetime.now().year else 0
        projected_spend = total_spent + (avg_monthly_spend * months_remaining)
        projected_remaining = total_budgeted - projected_spend

        # === SECTION 1: Summary Metrics ===
        st.markdown("### 💰 Annual Budget Summary")

        cols = st.columns(8)
        cols[0].metric("Total Budget", f"€{total_budgeted:,.0f}")
        cols[1].metric("YTD Spent", f"€{total_spent:,.0f}")
        cols[2].metric("Remaining", f"€{total_remaining:,.0f}")
        cols[3].metric("Avg Monthly Budget", f"€{avg_monthly_budget:,.0f}")
        cols[4].metric("Avg Monthly Spend", f"€{avg_monthly_spend:,.0f}")

        if months_remaining > 0:
            cols[5].metric("Projected Total", f"€{projected_spend:,.0f}")
            cols[6].metric("Projected Remaining", f"€{projected_remaining:,.0f}")
            status_emoji = "✅" if projected_remaining >= 0 else "⚠️"
            cols[7].metric("Status", f"{status_emoji}")
        else:
            utilization_pct = (total_spent / total_budgeted * 100) if total_budgeted > 0 else 0
            cols[5].metric("Utilization", f"{utilization_pct:.1f}%")

        st.markdown("---")

        # === SECTION 2: Timeline Visualization ===
        st.markdown("### 📊 Budget Timeline")

        fig_timeline = create_timeline_chart(monthly_df, current_month)
        st.plotly_chart(fig_timeline, use_container_width=True, config={'displayModeBar': False})

        st.markdown("---")

        # === SECTION 3: Analysis Charts ===
        st.markdown("### 📈 Budget Analysis")

        col1, col2 = st.columns(2)

        with col1:
            fig_cumulative = create_cumulative_chart(monthly_df, current_month)
            st.plotly_chart(fig_cumulative, use_container_width=True, config={'displayModeBar': False})

        with col2:
            fig_deviation = create_deviation_chart(monthly_df, current_month)
            st.plotly_chart(fig_deviation, use_container_width=True, config={'displayModeBar': False})

        st.markdown("---")

        # === SECTION 4: Monthly Breakdown Table ===
        st.markdown("### 📋 Monthly Breakdown")

        # Status filter
        col1, col2 = st.columns([2, 4])
        with col1:
            status_filter = st.multiselect(
                "Filter by Status",
                options=['On Track', 'Over Budget', 'Under Budget', 'Future', 'No Budget'],
                default=['On Track', 'Over Budget', 'Under Budget', 'Future']
            )

        # Apply filter
        filtered_df = monthly_df[monthly_df['status'].isin(status_filter)] if status_filter else monthly_df

        # Format and display
        display_df = create_monthly_breakdown_table(filtered_df)

        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                'month_full': 'Month',
                'budgeted': 'Budgeted',
                'spent': 'Spent',
                'remaining': 'Remaining',
                'deviation': 'Deviation',
                'deviation_pct': 'Deviation %',
                'status': 'Status'
            },
            height=450
        )

        # Export option
        csv = monthly_df.to_csv(index=False)
        st.download_button(
            label="📥 Download CSV",
            data=csv,
            file_name=f"budget_timeline_{selected_year}.csv",
            mime="text/csv"
        )

except Exception as e:
    st.error(f"An error occurred: {str(e)}")
    st.exception(e)
