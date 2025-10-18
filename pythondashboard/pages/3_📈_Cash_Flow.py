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

# Page configuration
st.set_page_config(
    page_title="Cash Flow Dashboard - Firefly III",
    page_icon="📈",
    layout="wide"
)

# Compact CSS styling with dark mode support
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
st.title("📈 Cash Flow Dashboard")

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

    Once connected, your cash flow data will be displayed automatically.
    """)
    st.stop()

# Sidebar date range selection
st.sidebar.header("📅 Date Range")

# Preset date ranges
preset_range = st.sidebar.selectbox(
    "Select Preset",
    ["Last 30 Days", "Last 3 Months", "Last 6 Months", "Last Year", "Year to Date", "Custom"]
)

today = datetime.now()

if preset_range == "Last 30 Days":
    start_date = today - timedelta(days=30)
    end_date = today
elif preset_range == "Last 3 Months":
    start_date = today - timedelta(days=90)
    end_date = today
elif preset_range == "Last 6 Months":
    start_date = today - timedelta(days=180)
    end_date = today
elif preset_range == "Last Year":
    start_date = today - timedelta(days=365)
    end_date = today
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
    "Monthly": "M",
    "Quarterly": "Q"
}

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

            # Filter out transfers (only show income and expenses)
            df_filtered = df[df['type'].isin(['deposit', 'withdrawal'])].copy()

            if df_filtered.empty:
                st.warning("No income or expense transactions found in the selected date range.")
                st.stop()

            # Calculate cash flow by period
            cash_flow_df = calculate_cash_flow(df_filtered, period=aggregation_map[aggregation])

            # Calculate totals
            total_income = df_filtered[df_filtered['type'] == 'deposit']['amount'].sum()
            total_expenses = df_filtered[df_filtered['type'] == 'withdrawal']['amount'].sum()
            net_flow = total_income - total_expenses

            # Calculate average per month (for context)
            days_in_range = (end_date - start_date).days
            months_in_range = max(1, days_in_range / 30)
            avg_monthly_income = total_income / months_in_range
            avg_monthly_expenses = total_expenses / months_in_range
            avg_monthly_net = net_flow / months_in_range

            # Display summary metrics
            st.header("💰 Summary Metrics")

            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric(
                    label="Total Income",
                    value=f"€{total_income:,.2f}",
                    delta=None
                )

            with col2:
                st.metric(
                    label="Total Expenses",
                    value=f"€{total_expenses:,.2f}",
                    delta=None
                )

            with col3:
                delta_color = "normal" if net_flow >= 0 else "inverse"
                st.metric(
                    label="Net Cash Flow",
                    value=f"€{net_flow:,.2f}",
                    delta=None
                )

            with col4:
                savings_rate = (net_flow / total_income * 100) if total_income > 0 else 0
                st.metric(
                    label="Savings Rate",
                    value=f"{savings_rate:.1f}%",
                    delta=None
                )

            st.divider()

            # Display average monthly metrics
            st.subheader("📊 Average Monthly")

            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric(
                    label="Avg. Monthly Income",
                    value=f"€{avg_monthly_income:,.2f}"
                )

            with col2:
                st.metric(
                    label="Avg. Monthly Expenses",
                    value=f"€{avg_monthly_expenses:,.2f}"
                )

            with col3:
                st.metric(
                    label="Avg. Monthly Net",
                    value=f"€{avg_monthly_net:,.2f}"
                )

            st.divider()

            # Cash flow chart
            st.header("📈 Cash Flow Over Time")

            if not cash_flow_df.empty:
                # Format period for display
                if aggregation == "Monthly":
                    cash_flow_df['period_display'] = cash_flow_df['period'].dt.strftime('%b %Y')
                elif aggregation == "Weekly":
                    cash_flow_df['period_display'] = cash_flow_df['period'].dt.strftime('%Y-W%U')
                elif aggregation == "Quarterly":
                    cash_flow_df['period_display'] = cash_flow_df['period'].dt.to_period('Q').astype(str)
                else:  # Daily
                    cash_flow_df['period_display'] = cash_flow_df['period'].dt.strftime('%Y-%m-%d')

                fig = create_net_flow_chart(
                    cash_flow_df,
                    x='period_display',
                    income_col='income',
                    expense_col='expenses',
                    title=f"Income vs. Expenses ({aggregation})",
                    height=500
                )

                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("No data available for the selected period.")

            st.divider()

            # Category spending and income sources
            col1, col2 = st.columns(2)

            with col1:
                st.subheader("💸 Top Expense Categories")

                category_spending = calculate_category_spending(df_filtered, start_date_str, end_date_str)

                if not category_spending.empty:
                    # Show top 10 categories
                    top_categories = category_spending.head(10)

                    # Create pie chart
                    fig_categories = create_pie_chart(
                        top_categories,
                        labels='category_name',
                        values='total_amount',
                        title="Top 10 Expense Categories",
                        height=400
                    )

                    st.plotly_chart(fig_categories, use_container_width=True)

                    # Show table
                    with st.expander("View All Categories"):
                        category_spending_display = category_spending.copy()
                        category_spending_display['total_amount'] = category_spending_display['total_amount'].apply(lambda x: f"€{x:,.2f}")
                        st.dataframe(
                            category_spending_display,
                            use_container_width=True,
                            hide_index=True,
                            column_config={
                                'category_name': 'Category',
                                'total_amount': 'Total Spent',
                                'transaction_count': 'Transactions'
                            }
                        )
                else:
                    st.info("No categorized expenses found.")

            with col2:
                st.subheader("💵 Income Sources")

                income_sources = calculate_income_sources(df_filtered, start_date_str, end_date_str)

                if not income_sources.empty:
                    # Create pie chart
                    fig_income = create_pie_chart(
                        income_sources,
                        labels='source_name',
                        values='total_amount',
                        title="Income by Source",
                        height=400
                    )

                    st.plotly_chart(fig_income, use_container_width=True)

                    # Show table
                    with st.expander("View All Income Sources"):
                        income_sources_display = income_sources.copy()
                        income_sources_display['total_amount'] = income_sources_display['total_amount'].apply(lambda x: f"€{x:,.2f}")
                        st.dataframe(
                            income_sources_display,
                            use_container_width=True,
                            hide_index=True,
                            column_config={
                                'source_name': 'Source',
                                'total_amount': 'Total Income',
                                'transaction_count': 'Transactions'
                            }
                        )
                else:
                    st.info("No income sources found.")

            st.divider()

            # Waterfall chart - Monthly breakdown
            st.header("🌊 Cash Flow Waterfall")

            if aggregation == "Monthly" and not cash_flow_df.empty:
                # Create waterfall data
                waterfall_categories = ['Starting'] + cash_flow_df['period_display'].tolist() + ['Ending']
                waterfall_values = [0] + cash_flow_df['net_flow'].tolist() + [0]

                # Set first value to 0 and last to total
                waterfall_values[0] = 0
                waterfall_values[-1] = net_flow

                fig_waterfall = create_waterfall_chart(
                    waterfall_categories,
                    waterfall_values,
                    title="Monthly Cash Flow Progression",
                    height=400
                )

                st.plotly_chart(fig_waterfall, use_container_width=True)
            else:
                st.info("Waterfall chart is only available for monthly aggregation.")

            st.divider()

            # Transaction details table
            st.header("📋 Transaction Details")

            # Add filters
            col1, col2, col3 = st.columns(3)

            with col1:
                transaction_type_filter = st.multiselect(
                    "Transaction Type",
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
            st.divider()
            csv = df_display.to_csv(index=False)
            st.download_button(
                label="📥 Download Transaction Data (CSV)",
                data=csv,
                file_name=f"firefly_cashflow_{start_date_str}_to_{end_date_str}.csv",
                mime="text/csv"
            )

        else:
            st.warning("No transactions found in the selected date range. Please adjust your date range or check your API connection.")

except Exception as e:
    st.error(f"An error occurred: {str(e)}")
    st.exception(e)
