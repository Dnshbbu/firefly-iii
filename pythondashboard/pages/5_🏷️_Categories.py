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
from utils.navigation import render_sidebar_navigation
from utils.config import get_firefly_url, get_firefly_token

# Page configuration
st.set_page_config(
    page_title="Category Analysis - Firefly III",
    page_icon="🏷️",
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
st.title("🏷️ Category Spending Analysis")

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
                # Pie chart - compact with click interactivity
                fig_pie = create_pie_chart(
                    category_spending.head(10),
                    labels='category_name',
                    values='total_amount',
                    title="Top 10 Categories by Spending (Click to drill down)",
                    height=300
                )

                # Display chart with click events
                from streamlit_plotly_events import plotly_events

                selected_points_pie = plotly_events(
                    fig_pie,
                    click_event=True,
                    hover_event=False,
                    select_event=False,
                    override_height=300,
                    override_width="100%",
                    key="category_overview_pie"
                )

                # Show category details when clicked
                if selected_points_pie and len(selected_points_pie) > 0:
                    # Get the clicked point data
                    point_data = selected_points_pie[0]

                    # Try to get category name from different possible keys
                    selected_category_name = None
                    if 'pointNumber' in point_data:
                        point_index = point_data['pointNumber']
                        selected_category_name = category_spending.head(10).iloc[point_index]['category_name']
                    elif 'pointIndex' in point_data:
                        point_index = point_data['pointIndex']
                        selected_category_name = category_spending.head(10).iloc[point_index]['category_name']
                    elif 'label' in point_data:
                        selected_category_name = point_data['label']
                    elif 'x' in point_data:
                        selected_category_name = point_data['x']

                    if selected_category_name and selected_category_name in category_spending['category_name'].values:
                        st.markdown(f"#### 🔍 Quick View: {selected_category_name}")

                        # Get transactions for this category
                        cat_txns = df_expenses[df_expenses['category_name'] == selected_category_name].copy()

                        if not cat_txns.empty:
                            # Statistics
                            cols_stats = st.columns(5)
                            cols_stats[0].metric("Count", len(cat_txns))
                            cols_stats[1].metric("Total", f"€{cat_txns['amount'].sum():,.0f}")
                            cols_stats[2].metric("Avg", f"€{cat_txns['amount'].mean():,.0f}")
                            cols_stats[3].metric("Min", f"€{cat_txns['amount'].min():,.0f}")
                            cols_stats[4].metric("Max", f"€{cat_txns['amount'].max():,.0f}")

                            # Transaction table
                            st.caption("📋 All Transactions:")

                            # Show all transactions sorted by date
                            all_txns = cat_txns.sort_values('date', ascending=False)[['date', 'description', 'destination_name', 'amount']].copy()
                            all_txns['date'] = pd.to_datetime(all_txns['date']).dt.strftime('%Y-%m-%d')
                            all_txns['amount'] = all_txns['amount'].apply(lambda x: f"€{x:,.2f}")

                            st.dataframe(
                                all_txns,
                                use_container_width=True,
                                hide_index=True,
                                column_config={
                                    'date': 'Date',
                                    'description': 'Description',
                                    'destination_name': 'Merchant',
                                    'amount': 'Amount'
                                },
                                height=400
                            )

            with col2:
                # Vertical Timeline of Transactions
                if selected_points_pie and len(selected_points_pie) > 0:
                    # Use the same category from pie chart click
                    point_data = selected_points_pie[0]
                    timeline_category = None
                    if 'pointNumber' in point_data:
                        point_index = point_data['pointNumber']
                        timeline_category = category_spending.head(10).iloc[point_index]['category_name']

                    if timeline_category and timeline_category in category_spending['category_name'].values:
                        st.markdown(f"**📅 Transaction Timeline - {timeline_category}**")

                        # Get transactions and group by month
                        timeline_txns = df_expenses[df_expenses['category_name'] == timeline_category].copy()
                        # Remove timezone before converting to period to avoid warning
                        # Note: to_period() still uses 'M' (not 'ME' like resample)
                        timeline_txns['month'] = pd.to_datetime(timeline_txns['date']).dt.tz_localize(None).dt.to_period('M')

                        # Group by month and calculate statistics
                        monthly_data = timeline_txns.groupby('month').agg({
                            'amount': ['sum', 'count', 'mean'],
                            'date': 'max'
                        }).reset_index()

                        # Flatten column names
                        monthly_data.columns = ['month', 'total_amount', 'transaction_count', 'avg_amount', 'last_date']

                        # Sort by month for timeline (descending - newest first)
                        monthly_data_timeline = monthly_data.sort_values('month', ascending=False)

                        # Sort by month for bar chart (ascending - oldest first)
                        monthly_data_chart = monthly_data.sort_values('month', ascending=True)

                        # Create vertical timeline using components
                        import streamlit.components.v1 as components

                        # Create simple vertical timeline with proper styling
                        timeline_html = """
<!DOCTYPE html>
<html>
<head>
<style>
body {
    background-color: #0e1117;
    margin: 0;
    padding: 10px;
    font-family: "Source Sans Pro", sans-serif;
}
.timeline-container {
    position: relative;
    height: 450px;
    overflow-y: auto;
    padding-left: 10px;
    padding-bottom: 20px;
}
/* Custom scrollbar for timeline */
.timeline-container::-webkit-scrollbar {
    width: 6px;
}
.timeline-container::-webkit-scrollbar-track {
    background: #1e293b;
    border-radius: 10px;
}
.timeline-container::-webkit-scrollbar-thumb {
    background: #475569;
    border-radius: 10px;
}
.timeline-container::-webkit-scrollbar-thumb:hover {
    background: #64748b;
}
.timeline {
    position: relative;
    padding: 5px 0;
    margin: 0;
}
/* Timeline line - drawn using border on timeline itself */
.timeline::before {
    content: '';
    position: absolute;
    left: 20px;
    top: 0;
    bottom: 20px;
    width: 3px;
    background: linear-gradient(to bottom, #60a5fa, #f87171);
    box-shadow: 0 0 8px rgba(96, 165, 250, 0.3);
    z-index: 0;
}
.timeline-item {
    position: relative;
    padding: 6px 0 6px 55px;
    margin-bottom: 12px;
    background: rgba(38, 39, 48, 0.4);
    border-radius: 6px;
    padding-left: 50px;
    padding-right: 10px;
    padding-top: 6px;
    padding-bottom: 6px;
    transition: all 0.3s ease;
}
.timeline-item:hover {
    background: rgba(38, 39, 48, 0.7);
    transform: translateX(3px);
}
.timeline-item::before {
    content: '';
    position: absolute;
    left: -37px;
    top: 12px;
    width: 12px;
    height: 12px;
    border-radius: 50%;
    background: #60a5fa;
    border: 3px solid #0e1117;
    box-shadow: 0 0 0 2px #60a5fa;
    z-index: 1;
}
.timeline-date {
    font-size: 0.65rem;
    color: #94a3b8;
    font-weight: 600;
    margin-bottom: 1px;
    letter-spacing: 0.3px;
}
.timeline-month {
    font-size: 0.85rem;
    color: #60a5fa;
    font-weight: 700;
    margin-bottom: 3px;
    text-transform: uppercase;
    letter-spacing: 0.8px;
}
.timeline-amount {
    font-size: 1rem;
    color: #f87171;
    font-weight: 700;
    margin-bottom: 3px;
    text-shadow: 0 0 8px rgba(248, 113, 113, 0.3);
}
.timeline-description {
    font-size: 0.7rem;
    color: #94a3b8;
    line-height: 1.3;
}
</style>
</head>
<body>
<div class="timeline-container">
    <div class="timeline">
"""

                        for _, row in monthly_data_timeline.iterrows():
                            year_str = row['month'].strftime('%Y')
                            month_name = row['month'].strftime('%B').upper()
                            total_str = f"€{row['total_amount']:,.2f}"
                            count = int(row['transaction_count'])
                            avg_str = f"€{row['avg_amount']:,.2f}"

                            timeline_html += f"""
<div class="timeline-item">
    <div class="timeline-date">{year_str}</div>
    <div class="timeline-month">{month_name}</div>
    <div class="timeline-amount">{total_str}</div>
    <div class="timeline-description">{count} transaction{'s' if count != 1 else ''} • Avg: {avg_str}</div>
</div>
"""

                        timeline_html += """
    </div>
</div>
</body>
</html>
"""

                        # Display timeline using iframe component
                        components.html(timeline_html, height=470, scrolling=False)

                        # Add monthly bar chart below timeline
                        st.markdown("**📊 Monthly Spending Trend**")

                        # Create monthly bar chart
                        import plotly.graph_objects as go

                        # Calculate y-axis range to accommodate labels
                        max_value = monthly_data_chart['total_amount'].max()
                        y_max = max_value * 1.2  # Add 20% padding for outside labels

                        fig_monthly_bar = go.Figure()

                        fig_monthly_bar.add_trace(go.Bar(
                            x=monthly_data_chart['month'].dt.strftime('%b %Y'),
                            y=monthly_data_chart['total_amount'],
                            marker=dict(color='#f87171'),
                            text=monthly_data_chart['total_amount'].apply(lambda x: f'€{x:,.0f}'),
                            textposition='outside',
                            textfont=dict(size=9),
                            hovertemplate='<b>%{x}</b><br>Amount: €%{y:,.2f}<br><extra></extra>'
                        ))

                        fig_monthly_bar.update_layout(
                            title=f"Monthly Spending - {timeline_category}",
                            xaxis_title='Month',
                            yaxis=dict(
                                title='Amount (€)',
                                range=[0, y_max]
                            ),
                            height=280,
                            margin=dict(t=40, b=40, l=50, r=20),
                            showlegend=False,
                            plot_bgcolor='rgba(0,0,0,0)',
                            paper_bgcolor='rgba(0,0,0,0)',
                            font=dict(color='#e2e8f0')
                        )

                        st.plotly_chart(fig_monthly_bar, use_container_width=True, config={'displayModeBar': False})
                else:
                    # Show placeholder when nothing is selected
                    st.info("👈 Click on a category in the pie chart to view transaction timeline")

            # Pareto chart - compact with category filter
            st.markdown("**Pareto Analysis (80/20 Rule)**")

            # Category multiselect for filtering
            all_categories = category_percentage.head(15)['category_name'].tolist()

            # Initialize session state for selected categories if not exists
            if 'pareto_selected_categories' not in st.session_state:
                st.session_state.pareto_selected_categories = all_categories

            col_filter, col_reset = st.columns([4, 1])
            with col_filter:
                selected_for_pareto = st.multiselect(
                    "Select categories to include:",
                    options=all_categories,
                    default=st.session_state.pareto_selected_categories,
                    key='pareto_category_filter'
                )
            with col_reset:
                st.write("")  # Spacing
                if st.button("Reset All", key='pareto_reset'):
                    st.session_state.pareto_selected_categories = all_categories
                    st.rerun()

            # Update session state
            st.session_state.pareto_selected_categories = selected_for_pareto

            if selected_for_pareto:
                # Filter data based on selection
                filtered_data = category_percentage[category_percentage['category_name'].isin(selected_for_pareto)].copy()

                # Recalculate cumulative percentage for filtered data
                filtered_data = filtered_data.sort_values('amount', ascending=False)
                filtered_data['percentage'] = (filtered_data['amount'] / filtered_data['amount'].sum()) * 100
                filtered_data['cumulative_pct'] = filtered_data['percentage'].cumsum()

                # Create Pareto chart with recalculated data
                fig_pareto = create_pareto_chart(
                    filtered_data,
                    title=f"Pareto Analysis - {len(selected_for_pareto)} Categories",
                    height=350
                )
                st.plotly_chart(fig_pareto, use_container_width=True, config={'displayModeBar': False})

                # Find 80% threshold
                categories_80 = filtered_data[filtered_data['cumulative_pct'] <= 80]
                if len(categories_80) > 0:
                    st.markdown(f"📌 **Insight:** {len(categories_80)} out of {len(selected_for_pareto)} selected categories account for 80% of spending")
                else:
                    st.markdown(f"📌 **Insight:** Analyzing {len(selected_for_pareto)} categories")
            else:
                st.info("Please select at least one category to display the Pareto analysis")

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
