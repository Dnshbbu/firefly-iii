import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import sys
from pathlib import Path

# Add parent directory to path to import utils
sys.path.append(str(Path(__file__).parent.parent))

from utils.api_client import FireflyAPIClient
from utils.charts import (
    create_pie_chart,
    create_category_trend_chart,
    create_treemap_chart,
    create_pareto_chart,
    create_category_comparison_chart
)
from utils.calculations import (
    calculate_category_spending,
    calculate_category_trends,
    calculate_category_percentage,
    calculate_category_monthly_comparison,
    get_top_transactions_by_category,
    calculate_category_statistics
)

# Page configuration
st.set_page_config(
    page_title="Category Analysis - Firefly III",
    page_icon="🏷️",
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

# Main app
st.title("🏷️ Category Spending Analysis")

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

    Once connected, your category data will be displayed automatically.
    """)
    st.stop()

# Sidebar date range selection
st.sidebar.header("📅 Date Range")

preset_range = st.sidebar.selectbox(
    "Select Preset",
    ["Last 3 Months", "Last 6 Months", "Last Year", "Year to Date", "Custom"]
)

today = datetime.now()

if preset_range == "Last 3 Months":
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
        category_percentage = calculate_category_percentage(df_expenses, start_date_str, end_date_str)

        # Calculate summary metrics
        total_expenses = category_spending['total_amount'].sum()
        num_categories = len(category_spending)
        top_category = category_spending.iloc[0] if not category_spending.empty else None
        avg_per_category = total_expenses / num_categories if num_categories > 0 else 0
        num_transactions = category_spending['transaction_count'].sum()

        # Display all metrics in single compact section
        st.markdown("### 📊 Category Overview")

        # Single row with all metrics
        cols = st.columns(6)
        cols[0].metric("Total Expenses", f"€{total_expenses:,.0f}")
        cols[1].metric("Categories", num_categories)
        cols[2].metric("Transactions", f"{int(num_transactions)}")
        cols[3].metric("Avg/Category", f"€{avg_per_category:,.0f}")
        if top_category is not None:
            cols[4].metric("Top Category", top_category['category_name'])
            cols[5].metric("Top Spending", f"€{top_category['total_amount']:,.0f}")

        st.markdown("---")

        # Visualization tabs
        tab1, tab2, tab3 = st.tabs(["📊 Overview", "📈 Trends", "🔍 Deep Dive"])

        with tab1:
            st.markdown("**Category Distribution**")

            col1, col2 = st.columns(2)

            with col1:
                # Pie chart - compact
                fig_pie = create_pie_chart(
                    category_spending.head(10),
                    labels='category_name',
                    values='total_amount',
                    title="Top 10 Categories by Spending",
                    height=300
                )
                st.plotly_chart(fig_pie, use_container_width=True, config={'displayModeBar': False})

            with col2:
                # Treemap - compact
                fig_treemap = create_treemap_chart(
                    category_spending.head(15),
                    labels_col='category_name',
                    values_col='total_amount',
                    title="Category Spending Treemap",
                    height=300
                )
                st.plotly_chart(fig_treemap, use_container_width=True, config={'displayModeBar': False})

            # Pareto chart - compact
            st.markdown("**Pareto Analysis (80/20 Rule)**")

            fig_pareto = create_pareto_chart(
                category_percentage.head(15),
                title="Category Spending - Pareto Analysis",
                height=350
            )
            st.plotly_chart(fig_pareto, use_container_width=True, config={'displayModeBar': False})

            # Find 80% threshold
            categories_80 = category_percentage[category_percentage['cumulative_pct'] <= 80]
            st.markdown(f"📌 **Insight:** {len(categories_80)} categories account for 80% of your total spending ({len(categories_80) / len(category_percentage) * 100:.1f}% of all categories)")

        with tab2:
            st.markdown("**Category Spending Trends**")

            # Calculate trends
            category_trends = calculate_category_trends(df_expenses, period='ME')

            # Select categories to display
            top_5_categories = category_spending.head(5)['category_name'].tolist()

            selected_categories = st.multiselect(
                "Select categories to display (max 10)",
                options=category_spending['category_name'].tolist(),
                default=top_5_categories
            )

            if selected_categories:
                if len(selected_categories) > 10:
                    st.caption("Showing first 10 selected categories")
                    selected_categories = selected_categories[:10]

                fig_trends = create_category_trend_chart(
                    category_trends,
                    categories=selected_categories,
                    title="Monthly Spending Trends by Category",
                    height=400
                )
                st.plotly_chart(fig_trends, use_container_width=True, config={'displayModeBar': False})
            else:
                st.info("Please select at least one category to display trends")

        with tab3:
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
                top_transactions = get_top_transactions_by_category(df_expenses, selected_category, limit=10)

                # Display statistics - compact row
                cols = st.columns(5)
                cols[0].metric("Transactions", f"{int(stats['count'])}")
                cols[1].metric("Average", f"€{stats['mean']:,.0f}")
                cols[2].metric("Median", f"€{stats['median']:,.0f}")
                cols[3].metric("Min", f"€{stats['min']:,.0f}")
                cols[4].metric("Max", f"€{stats['max']:,.0f}")

                # Monthly comparison chart - compact
                if not monthly_data.empty:
                    st.markdown("**Monthly Trend**")

                    fig_comparison = create_category_comparison_chart(
                        monthly_data,
                        selected_category,
                        height=300
                    )
                    st.plotly_chart(fig_comparison, use_container_width=True, config={'displayModeBar': False})

                # Top transactions - collapsible
                with st.expander("📋 Top 10 Transactions", expanded=False):
                    if not top_transactions.empty:
                        top_transactions_display = top_transactions.copy()
                        top_transactions_display['date'] = pd.to_datetime(top_transactions_display['date']).dt.strftime('%Y-%m-%d')
                        top_transactions_display['amount'] = top_transactions_display['amount'].apply(lambda x: f"€{x:,.2f}")

                        st.dataframe(
                            top_transactions_display,
                            use_container_width=True,
                            hide_index=True,
                            column_config={
                                'date': 'Date',
                                'description': 'Description',
                                'amount': 'Amount',
                                'destination_name': 'Merchant'
                            },
                            height=300
                        )
                    else:
                        st.info("No transactions found for this category")

        st.markdown("---")

        # Category breakdown table - collapsible
        with st.expander("📋 All Categories", expanded=False):
            # Format for display
            category_display = category_percentage.copy()
            category_display['amount'] = category_display['amount'].apply(lambda x: f"€{x:,.2f}")
            category_display['percentage'] = category_display['percentage'].apply(lambda x: f"{x:.1f}%")
            category_display['cumulative_pct'] = category_display['cumulative_pct'].apply(lambda x: f"{x:.1f}%")

            st.dataframe(
                category_display,
                use_container_width=True,
                hide_index=True,
                column_config={
                    'category_name': 'Category',
                    'amount': 'Total Spent',
                    'percentage': '% of Total',
                    'cumulative_pct': 'Cumulative %'
                },
                height=400
            )

            # Export option
            csv = category_percentage.to_csv(index=False)
            st.download_button(
                label="📥 Download CSV",
                data=csv,
                file_name=f"firefly_categories_{start_date_str}_to_{end_date_str}.csv",
                mime="text/csv"
            )

except Exception as e:
    st.error(f"An error occurred: {str(e)}")
    st.exception(e)
