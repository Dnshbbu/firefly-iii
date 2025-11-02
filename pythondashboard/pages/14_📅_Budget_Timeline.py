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
from utils.navigation import render_sidebar_navigation
from utils.config import get_firefly_url, get_firefly_token

# Page configuration
st.set_page_config(
    page_title="Budget Timeline - Firefly III",
    page_icon="📅",
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


def get_year_date_range(year: int) -> tuple[str, str]:
    """Get start and end dates for a year"""
    start_date = f"{year}-01-01"
    end_date = f"{year}-12-31"
    return start_date, end_date


def get_monthly_budget_data(
    budgets_data: List[Dict],
    budget_limits_data: Dict[str, List[Dict]],
    transactions_df: pd.DataFrame,
    start_date_str: str,
    end_date_str: str
) -> pd.DataFrame:
    """
    Calculate monthly budget data across all budgets for a date range.

    Returns DataFrame with columns:
    - month: Month number (1-12)
    - month_name: Month name
    - year_month: YYYY-MM format for unique identification
    - budgeted: Total budgeted amount for the month
    - spent: Total spent amount for the month
    - remaining: Remaining budget
    - deviation: Deviation from budget (negative = over budget)
    - deviation_pct: Deviation as percentage
    - status: Status indicator
    """
    monthly_data = []

    # Parse start and end dates
    range_start = datetime.strptime(start_date_str, '%Y-%m-%d')
    range_end = datetime.strptime(end_date_str, '%Y-%m-%d')

    # Generate list of months in the range
    current = range_start.replace(day=1)
    months_in_range = []

    while current <= range_end:
        months_in_range.append(current)
        # Move to next month
        if current.month == 12:
            current = current.replace(year=current.year + 1, month=1)
        else:
            current = current.replace(month=current.month + 1)

    for month_date in months_in_range:
        year = month_date.year
        month = month_date.month
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
            if not transactions_df.empty and 'date' in transactions_df.columns:
                # Make start_date and end_date timezone-aware if transactions have timezone info
                compare_start = start_date
                compare_end = end_date
                # Check if date column is datetime and has timezone info
                if pd.api.types.is_datetime64_any_dtype(transactions_df['date']):
                    if hasattr(transactions_df['date'].dt, 'tz') and transactions_df['date'].dt.tz is not None:
                        compare_start = pd.Timestamp(start_date).tz_localize(transactions_df['date'].dt.tz)
                        compare_end = pd.Timestamp(end_date).tz_localize(transactions_df['date'].dt.tz)
                else:
                    # Convert date column to datetime if it's not already
                    # Use utc=True to handle timezone-aware datetime objects
                    transactions_df['date'] = pd.to_datetime(transactions_df['date'], utc=True)
                    # Remove timezone to make comparisons work
                    transactions_df['date'] = transactions_df['date'].dt.tz_localize(None)

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

        # Determine status (check if this month is in the future)
        today = datetime.now()
        is_future = month_date.replace(day=1) > today.replace(day=1)

        if is_future:
            status = 'Future'
        elif total_budgeted == 0:
            status = 'No Budget'
        elif deviation_pct > 0:
            status = 'Over Budget'
        elif deviation_pct > -20:
            status = 'On Track'
        else:
            status = 'Under Budget'

        # Create month label (show year if spanning multiple years)
        if range_start.year != range_end.year:
            month_label = f"{calendar.month_abbr[month]} {str(year)[2:]}"
        else:
            month_label = calendar.month_abbr[month]

        monthly_data.append({
            'month': month,
            'month_name': month_label,
            'month_full': calendar.month_name[month],
            'year': year,
            'year_month': f"{year}-{month:02d}",
            'date': month_date,
            'budgeted': total_budgeted,
            'spent': total_spent,
            'remaining': remaining,
            'deviation': deviation,
            'deviation_pct': deviation_pct,
            'status': status
        })

    return pd.DataFrame(monthly_data)


def create_timeline_chart(monthly_df: pd.DataFrame, current_month_index: int) -> go.Figure:
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

    # Add actual spending bars with conditional coloring based on status
    actual_colors = monthly_df.apply(
        lambda row: 'crimson' if row['spent'] > row['budgeted'] and row['budgeted'] > 0
        else 'lightgreen' if row['status'] != 'Future'
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
        title="Budget Timeline: Expected vs Actual Spending",
        xaxis_title="Month",
        yaxis_title="Amount (€)",
        barmode='group',  # Changed from 'overlay' to 'group' for clustered bars
        height=450,
        margin=dict(t=80, b=60, l=80, r=40),
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

    # Enable automargin to prevent cutoff
    fig.update_xaxes(automargin=True)
    fig.update_yaxes(automargin=True)

    # Add vertical line for current month if we can identify it
    if current_month_index > 0 and current_month_index <= len(monthly_df):
        fig.add_vline(
            x=current_month_index - 1,
            line_dash="dash",
            line_color="orange",
            annotation_text="Today",
            annotation_position="top",
            annotation_font_size=9
        )

    return fig


def create_deviation_chart(monthly_df: pd.DataFrame, current_month_index: int) -> go.Figure:
    """Create a chart showing budget deviations by month"""
    # Filter to only show past and current months (not future)
    past_months = monthly_df[monthly_df['status'] != 'Future'].copy()

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
        textfont=dict(size=10),
        showlegend=False
    ))

    # Add zero line
    fig.add_hline(y=0, line_dash="solid", line_color="black", line_width=1)

    # Calculate range to give space for labels
    if not past_months.empty:
        max_val = past_months['deviation'].max()
        min_val = past_months['deviation'].min()
        # Add 15% padding on top and bottom for labels
        padding = max(abs(max_val), abs(min_val)) * 0.15
        y_range = [min_val - padding, max_val + padding]
    else:
        y_range = None

    fig.update_layout(
        title="Budget Deviations (Over/Under Budget)",
        xaxis_title="Month",
        yaxis_title="Deviation (€)",
        height=400,
        margin=dict(t=80, b=80, l=80, r=40),
        font=dict(size=10),
        yaxis=dict(range=y_range) if y_range else {}
    )

    # Enable automargin to prevent cutoff
    fig.update_xaxes(automargin=True)
    fig.update_yaxes(automargin=True)

    return fig


def create_cumulative_chart(monthly_df: pd.DataFrame, current_month_index: int) -> go.Figure:
    """Create a chart showing cumulative budget vs actual over time"""
    # Make a copy to avoid modifying the original
    df = monthly_df.copy()

    # Calculate cumulative values
    df['cumulative_budgeted'] = df['budgeted'].cumsum()
    df['cumulative_spent'] = df['spent'].cumsum()

    fig = go.Figure()

    # Cumulative budgeted line
    fig.add_trace(go.Scatter(
        x=df['month_name'],
        y=df['cumulative_budgeted'],
        mode='lines+markers',
        name='Cumulative Budget',
        line=dict(color='blue', width=2),
        marker=dict(size=6),
        hovertemplate='€%{y:,.2f}<extra></extra>'
    ))

    # Cumulative spent line (only up to current month - exclude future)
    actual_data = df[df['status'] != 'Future'].copy()
    if not actual_data.empty:
        fig.add_trace(go.Scatter(
            x=actual_data['month_name'],
            y=actual_data['cumulative_spent'],
            mode='lines+markers',
            name='Cumulative Spent',
            line=dict(color='red', width=2, dash='dash'),
            marker=dict(size=6),
            hovertemplate='€%{y:,.2f}<extra></extra>'
        ))

        # Projection line (for future months if any)
        future_data = df[df['status'] == 'Future']
        if not future_data.empty:
            # Calculate average monthly spending so far
            avg_monthly_spend = actual_data['spent'].mean()

            # Get last cumulative value
            last_cumulative = actual_data['cumulative_spent'].iloc[-1]

            # Build projection values
            projection_values = [last_cumulative]
            for i in range(len(future_data)):
                projection_values.append(projection_values[-1] + avg_monthly_spend)

            # Combine current month with future months for projection line
            projection_months = [actual_data['month_name'].iloc[-1]] + future_data['month_name'].tolist()

            fig.add_trace(go.Scatter(
                x=projection_months,
                y=projection_values,
                mode='lines+markers',
                name='Projected Spending',
                line=dict(color='orange', width=2, dash='dot'),
                marker=dict(size=5, symbol='diamond'),
                hovertemplate='€%{y:,.2f}<extra></extra>'
            ))

    fig.update_layout(
        title="Cumulative Budget vs Actual Spending",
        xaxis_title="Month",
        yaxis_title="Cumulative Amount (€)",
        height=400,
        margin=dict(t=70, b=50, l=80, r=40),
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

    # Enable automargin to prevent cutoff
    fig.update_xaxes(automargin=True)
    fig.update_yaxes(automargin=True)

    return fig


def create_monthly_breakdown_table(monthly_df: pd.DataFrame) -> pd.DataFrame:
    """Format monthly data for display"""
    df = monthly_df.copy()

    # Return data as-is, formatting will be handled by st.dataframe column_config
    return df[['month_full', 'budgeted', 'spent', 'remaining', 'deviation', 'deviation_pct', 'status']]


def get_per_budget_monthly_data(
    budgets_data: List[Dict],
    budget_limits_data: Dict[str, List[Dict]],
    transactions_df: pd.DataFrame,
    start_date_str: str,
    end_date_str: str
) -> Dict[str, pd.DataFrame]:
    """
    Calculate monthly data for each individual budget for a date range.

    Returns:
        Dictionary mapping budget_name to DataFrame with monthly data
    """
    budget_monthly_data = {}

    # Parse start and end dates
    range_start = datetime.strptime(start_date_str, '%Y-%m-%d')
    range_end = datetime.strptime(end_date_str, '%Y-%m-%d')

    # Generate list of months in the range
    current = range_start.replace(day=1)
    months_in_range = []

    while current <= range_end:
        months_in_range.append(current)
        # Move to next month
        if current.month == 12:
            current = current.replace(year=current.year + 1, month=1)
        else:
            current = current.replace(month=current.month + 1)

    for budget in budgets_data:
        budget_id = budget.get('id')
        budget_name = budget.get('attributes', {}).get('name', 'Unknown')

        monthly_records = []

        for month_date in months_in_range:
            year = month_date.year
            month = month_date.month
            # Get start and end dates for this month
            start_date = datetime(year, month, 1)
            last_day = calendar.monthrange(year, month)[1]
            end_date = datetime(year, month, last_day)

            start_str = start_date.strftime('%Y-%m-%d')
            end_str = end_date.strftime('%Y-%m-%d')

            budgeted_amount = 0.0
            spent_amount = 0.0

            # Get budget limits for this budget and month
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
                        budgeted_amount += prorated_amount

            # Calculate spent amount for this budget in this month
            if not transactions_df.empty and 'date' in transactions_df.columns:
                # Make start_date and end_date timezone-aware if transactions have timezone info
                compare_start = start_date
                compare_end = end_date
                # Check if date column is datetime and has timezone info
                if pd.api.types.is_datetime64_any_dtype(transactions_df['date']):
                    if hasattr(transactions_df['date'].dt, 'tz') and transactions_df['date'].dt.tz is not None:
                        compare_start = pd.Timestamp(start_date).tz_localize(transactions_df['date'].dt.tz)
                        compare_end = pd.Timestamp(end_date).tz_localize(transactions_df['date'].dt.tz)
                else:
                    # Convert date column to datetime if it's not already
                    # Use utc=True to handle timezone-aware datetime objects
                    transactions_df['date'] = pd.to_datetime(transactions_df['date'], utc=True)
                    # Remove timezone to make comparisons work
                    transactions_df['date'] = transactions_df['date'].dt.tz_localize(None)

                budget_transactions = transactions_df[
                    (transactions_df['budget_name'] == budget_name) &
                    (transactions_df['type'] == 'withdrawal') &
                    (transactions_df['date'] >= compare_start) &
                    (transactions_df['date'] <= compare_end)
                ]
                spent_amount = budget_transactions['amount'].sum()

            # Create month label (show year if spanning multiple years)
            if range_start.year != range_end.year:
                month_label = f"{calendar.month_abbr[month]} {str(year)[2:]}"
            else:
                month_label = calendar.month_abbr[month]

            monthly_records.append({
                'month': month,
                'month_name': month_label,
                'budgeted': budgeted_amount,
                'spent': spent_amount
            })

        budget_monthly_data[budget_name] = pd.DataFrame(monthly_records)

    return budget_monthly_data


def create_budget_gauge(budget_name: str, total_budgeted: float, total_spent: float, avg_spent: float) -> go.Figure:
    """Create a gauge chart for a budget showing utilization"""
    # Calculate utilization percentage
    utilization_pct = (total_spent / total_budgeted * 100) if total_budgeted > 0 else 0

    # Calculate difference and round it properly
    difference = round(total_spent - total_budgeted, 2)

    # Determine color based on utilization
    if utilization_pct >= 100:
        color = "red"
        delta_color = "red"
    elif utilization_pct >= 80:
        color = "orange"
        delta_color = "orange"
    else:
        color = "green"
        delta_color = "green"

    # Format delta text with proper sign
    if difference > 0:
        delta_text = f"+€{abs(difference):,.2f}"
    elif difference < 0:
        delta_text = f"-€{abs(difference):,.2f}"
    else:
        delta_text = "€0.00"

    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=total_spent,
        title={'text': f"{budget_name}<br><sub>Avg: €{avg_spent:,.2f}/mo</sub>", 'font': {'size': 14}},
        number={
            'valueformat': '€,.2f',
            'font': {'size': 22},
            'prefix': '',
            'suffix': f'<br><span style="font-size:16px; color:{delta_color};">{delta_text}</span>'
        },
        domain={'x': [0, 1], 'y': [0, 1]},
        gauge={
            'axis': {'range': [None, total_budgeted * 1.2], 'tickformat': '€,.0f', 'tickfont': {'size': 10}},
            'bar': {'color': color},
            'steps': [
                {'range': [0, total_budgeted * 0.8], 'color': 'lightgray'},
                {'range': [total_budgeted * 0.8, total_budgeted], 'color': 'lightyellow'}
            ],
            'threshold': {
                'line': {'color': "blue", 'width': 2},
                'thickness': 0.75,
                'value': total_budgeted
            }
        }
    ))

    fig.update_layout(
        height=270,
        margin=dict(t=65, b=30, l=30, r=30),
        font=dict(size=12)
    )

    return fig


def create_small_budget_chart(budget_name: str, budget_df: pd.DataFrame, current_month: int) -> go.Figure:
    """Create a small chart for an individual budget showing expected, actual, and running average"""
    fig = go.Figure()

    # Expected (budgeted) line
    fig.add_trace(go.Scatter(
        x=budget_df['month_name'],
        y=budget_df['budgeted'],
        mode='lines+markers',
        name='Expected',
        line=dict(color='steelblue', width=2.5),
        marker=dict(size=6),
        showlegend=True
    ))

    # Actual spending line (only up to current month)
    actual_data = budget_df[budget_df['month'] <= current_month].copy()
    total_spent = 0

    if not actual_data.empty:
        fig.add_trace(go.Scatter(
            x=actual_data['month_name'],
            y=actual_data['spent'],
            mode='lines+markers',
            name='Actual',
            line=dict(color='crimson', width=2.5, dash='dash'),
            marker=dict(size=6),
            showlegend=True
        ))

        # Calculate running/cumulative average (average from month 1 up to each month)
        actual_data['running_avg'] = actual_data['spent'].expanding().mean()

        total_spent = actual_data['spent'].sum()

        fig.add_trace(go.Scatter(
            x=actual_data['month_name'],
            y=actual_data['running_avg'],
            mode='lines',
            name='Running Avg',
            line=dict(color='orange', width=2.5, dash='dot'),
            showlegend=True
        ))

    # Calculate total budgeted
    total_budgeted = budget_df['budgeted'].sum()

    fig.update_layout(
        title=dict(
            text=f"{budget_name}<br><sub>Budget: €{total_budgeted:,.0f} | Spent: €{total_spent:,.0f}</sub>",
            font=dict(size=13)
        ),
        xaxis_title="",
        yaxis_title="€",
        height=260,
        margin=dict(t=65, b=50, l=60, r=30),
        legend=dict(
            orientation="h",
            yanchor="top",
            y=-0.2,
            xanchor="center",
            x=0.5,
            font=dict(size=10)
        ),
        font=dict(size=11),
        hovermode='x unified'
    )

    # Customize axes and enable automargin to prevent cutoff
    fig.update_xaxes(tickfont=dict(size=10), automargin=True)
    fig.update_yaxes(tickfont=dict(size=10), automargin=True)

    return fig


# Main app
st.title("📅 Budget Timeline & Roadmap")

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

# Sidebar time period selection
st.sidebar.header("📅 Timeline Period")

period_type = st.sidebar.selectbox(
    "Select Period",
    options=[
        "Last 7 Days", "Last 30 Days", "Last 3 Months", "Last 6 Months", "Last 12 Months",
        "Last Exact 3 Months", "Last Exact 6 Months", "Last Exact 12 Months",
        "Current Month", "Current Quarter", "Current Year", 
        "Last Month", "Last Quarter", "Last Year", "Year to Date", "Custom"
    ],
    index=10  # Default to "Current Year"
)

# Calculate date range based on selection
today = datetime.now()
current_year = today.year
first_day_of_month = datetime(today.year, today.month, 1)

if period_type == "Last 7 Days":
    end_date = today
    start_date = end_date - timedelta(days=7)
    selected_start = start_date.strftime('%Y-%m-%d')
    selected_end = end_date.strftime('%Y-%m-%d')
    period_label = "Last 7 Days"

elif period_type == "Last 30 Days":
    end_date = today
    start_date = end_date - timedelta(days=30)
    selected_start = start_date.strftime('%Y-%m-%d')
    selected_end = end_date.strftime('%Y-%m-%d')
    period_label = "Last 30 Days"

elif period_type == "Last 3 Months":
    end_date = today
    start_date = end_date - timedelta(days=90)
    selected_start = start_date.strftime('%Y-%m-%d')
    selected_end = end_date.strftime('%Y-%m-%d')
    period_label = "Last 3 Months"

elif period_type == "Last 6 Months":
    end_date = today
    start_date = end_date - timedelta(days=180)
    selected_start = start_date.strftime('%Y-%m-%d')
    selected_end = end_date.strftime('%Y-%m-%d')
    period_label = "Last 6 Months"

elif period_type == "Last 12 Months":
    end_date = today
    start_date = end_date - timedelta(days=365)
    selected_start = start_date.strftime('%Y-%m-%d')
    selected_end = end_date.strftime('%Y-%m-%d')
    period_label = "Last 12 Months"

elif period_type == "Last Exact 3 Months":
    # Get complete months only (e.g., if today is Oct 26, show Jul 1 - Sep 30)
    if today.month <= 3:
        start_date = datetime(today.year - 1, today.month + 9, 1)
        end_date = datetime(today.year, today.month - 1, 1) - timedelta(days=1) if today.month > 1 else datetime(today.year - 1, 12, 31)
    else:
        start_date = datetime(today.year, today.month - 3, 1)
        end_date = datetime(today.year, today.month, 1) - timedelta(days=1)
    selected_start = start_date.strftime('%Y-%m-%d')
    selected_end = end_date.strftime('%Y-%m-%d')
    period_label = f"{start_date.strftime('%b')} - {end_date.strftime('%b %Y')}"

elif period_type == "Last Exact 6 Months":
    # Get complete months only
    if today.month <= 6:
        start_date = datetime(today.year - 1, today.month + 6, 1)
        end_date = datetime(today.year, today.month - 1, 1) - timedelta(days=1) if today.month > 1 else datetime(today.year - 1, 12, 31)
    else:
        start_date = datetime(today.year, today.month - 6, 1)
        end_date = datetime(today.year, today.month, 1) - timedelta(days=1)
    selected_start = start_date.strftime('%Y-%m-%d')
    selected_end = end_date.strftime('%Y-%m-%d')
    period_label = f"{start_date.strftime('%b %Y')} - {end_date.strftime('%b %Y')}"

elif period_type == "Last Exact 12 Months":
    # Get complete months only (previous 12 full months)
    start_date = datetime(today.year - 1, today.month, 1)
    end_date = datetime(today.year, today.month, 1) - timedelta(days=1)
    selected_start = start_date.strftime('%Y-%m-%d')
    selected_end = end_date.strftime('%Y-%m-%d')
    period_label = f"{start_date.strftime('%b %Y')} - {end_date.strftime('%b %Y')}"

elif period_type == "Current Month":
    selected_start = first_day_of_month.strftime('%Y-%m-%d')
    selected_end = today.strftime('%Y-%m-%d')
    period_label = f"{today.strftime('%B %Y')}"

elif period_type == "Current Quarter":
    quarter = (today.month - 1) // 3
    start_date = datetime(today.year, quarter * 3 + 1, 1)
    selected_start = start_date.strftime('%Y-%m-%d')
    selected_end = today.strftime('%Y-%m-%d')
    period_label = f"Q{quarter + 1} {today.year}"

elif period_type == "Current Year":
    selected_year = current_year
    selected_start = f"{selected_year}-01-01"
    selected_end = f"{selected_year}-12-31"
    period_label = f"Year {selected_year}"

elif period_type == "Last Month":
    if today.month == 1:
        start_date = datetime(today.year - 1, 12, 1)
        end_date = first_day_of_month - timedelta(days=1)
    else:
        start_date = datetime(today.year, today.month - 1, 1)
        end_date = first_day_of_month - timedelta(days=1)
    selected_start = start_date.strftime('%Y-%m-%d')
    selected_end = end_date.strftime('%Y-%m-%d')
    period_label = start_date.strftime('%B %Y')

elif period_type == "Last Quarter":
    quarter = (today.month - 1) // 3
    if quarter == 0:
        start_date = datetime(today.year - 1, 10, 1)
        end_date = datetime(today.year - 1, 12, 31)
        period_label = f"Q4 {today.year - 1}"
    else:
        start_date = datetime(today.year, (quarter - 1) * 3 + 1, 1)
        end_date = datetime(today.year, quarter * 3, 1) - timedelta(days=1)
        period_label = f"Q{quarter} {today.year}"
    selected_start = start_date.strftime('%Y-%m-%d')
    selected_end = end_date.strftime('%Y-%m-%d')

elif period_type == "Last Year":
    selected_year = current_year - 1
    selected_start = f"{selected_year}-01-01"
    selected_end = f"{selected_year}-12-31"
    period_label = f"Year {selected_year}"

elif period_type == "Year to Date":
    selected_start = f"{current_year}-01-01"
    selected_end = today.strftime('%Y-%m-%d')
    period_label = f"YTD {current_year}"

else:  # Custom
    col1, col2 = st.sidebar.columns(2)
    with col1:
        custom_start = st.date_input(
            "Start Date",
            value=datetime(current_year, 1, 1),
            max_value=today
        )
    with col2:
        custom_end = st.date_input(
            "End Date",
            value=today,
            max_value=today
        )

    selected_start = custom_start.strftime('%Y-%m-%d')
    selected_end = custom_end.strftime('%Y-%m-%d')
    period_label = f"{selected_start} to {selected_end}"

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
        st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Period: {period_label}")

    st.markdown("---")

    # Cache data fetching
    @st.cache_data(ttl=300)
    def fetch_timeline_data(_client, start_date, end_date):
        """Fetch all budget data for the specified date range"""
        budgets = _client.get_budgets()

        # Fetch budget limits for each budget
        budget_limits = {}
        for budget in budgets:
            budget_id = budget.get('id')
            limits = _client.get_budget_limits(budget_id, start_date, end_date)
            budget_limits[budget_id] = limits

        # Fetch all transactions for the period
        transactions = _client.get_transactions(start_date=start_date, end_date=end_date)

        return budgets, budget_limits, transactions

    # Fetch data
    with st.spinner("Loading budget timeline data..."):
        budgets_data, budget_limits_data, transactions_data = fetch_timeline_data(
            client, selected_start, selected_end
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
            selected_start,
            selected_end
        )

        # Determine the current period index for charts
        today = datetime.now()
        if not monthly_df.empty and 'date' in monthly_df.columns:
            # Find the index of the current month in the data
            current_month_mask = monthly_df['date'].apply(
                lambda x: x.year == today.year and x.month == today.month
            )
            if current_month_mask.any():
                current_month_index = current_month_mask.idxmax() + 1
            else:
                # If current month not in range, use the last month
                current_month_index = len(monthly_df)
        else:
            current_month_index = today.month

        # Calculate summary metrics
        total_budgeted = monthly_df['budgeted'].sum()
        # Calculate total spent for past/current months only (exclude future)
        past_months = monthly_df[monthly_df['status'] != 'Future']
        total_spent = past_months['spent'].sum()
        total_remaining = total_budgeted - total_spent

        total_months = len(monthly_df)
        past_months_count = len(past_months)
        avg_monthly_budget = total_budgeted / total_months if total_months > 0 else 0
        avg_monthly_spend = total_spent / past_months_count if past_months_count > 0 else 0

        # Projection for remaining months
        future_months = monthly_df[monthly_df['status'] == 'Future']
        months_remaining = len(future_months)
        projected_spend = total_spent + (avg_monthly_spend * months_remaining)
        projected_remaining = total_budgeted - projected_spend

        # === SECTION 1: Summary Metrics ===
        st.markdown("### 💰 Budget Summary")

        # Single row with visual grouping via subtle background colors
        cols = st.columns(8)

        # Group 1: Period Totals (light blue background)
        with cols[0]:
            st.markdown('<div style="background-color: rgba(173, 216, 230, 0.15); padding: 10px; border-radius: 5px; height: 100%;">', unsafe_allow_html=True)
            st.metric("Total Budget", f"€{total_budgeted:,.0f}")
            st.markdown('</div>', unsafe_allow_html=True)

        with cols[1]:
            st.markdown('<div style="background-color: rgba(173, 216, 230, 0.15); padding: 10px; border-radius: 5px; height: 100%;">', unsafe_allow_html=True)
            st.metric("YTD Spent", f"€{total_spent:,.0f}")
            st.markdown('</div>', unsafe_allow_html=True)

        with cols[2]:
            st.markdown('<div style="background-color: rgba(173, 216, 230, 0.15); padding: 10px; border-radius: 5px; height: 100%;">', unsafe_allow_html=True)
            st.metric("Remaining", f"€{total_remaining:,.0f}")
            st.markdown('</div>', unsafe_allow_html=True)

        # Group 2: Monthly Averages (light green background)
        with cols[3]:
            st.markdown('<div style="background-color: rgba(144, 238, 144, 0.15); padding: 10px; border-radius: 5px; height: 100%;">', unsafe_allow_html=True)
            st.metric("Avg Monthly Budget", f"€{avg_monthly_budget:,.0f}")
            st.markdown('</div>', unsafe_allow_html=True)

        with cols[4]:
            st.markdown('<div style="background-color: rgba(144, 238, 144, 0.15); padding: 10px; border-radius: 5px; height: 100%;">', unsafe_allow_html=True)
            st.metric("Avg Monthly Spend", f"€{avg_monthly_spend:,.0f}")
            st.markdown('</div>', unsafe_allow_html=True)

        # Group 3: Projections (light yellow background)
        if months_remaining > 0:
            with cols[5]:
                st.markdown('<div style="background-color: rgba(255, 255, 224, 0.3); padding: 10px; border-radius: 5px; height: 100%;">', unsafe_allow_html=True)
                st.metric("Projected Total", f"€{projected_spend:,.0f}")
                st.markdown('</div>', unsafe_allow_html=True)

            with cols[6]:
                st.markdown('<div style="background-color: rgba(255, 255, 224, 0.3); padding: 10px; border-radius: 5px; height: 100%;">', unsafe_allow_html=True)
                st.metric("Projected Remaining", f"€{projected_remaining:,.0f}")
                st.markdown('</div>', unsafe_allow_html=True)

            with cols[7]:
                st.markdown('<div style="background-color: rgba(255, 255, 224, 0.3); padding: 10px; border-radius: 5px; height: 100%;">', unsafe_allow_html=True)
                status_emoji = "✅" if projected_remaining >= 0 else "⚠️"
                st.metric("Status", f"{status_emoji}")
                st.markdown('</div>', unsafe_allow_html=True)
        else:
            with cols[5]:
                st.markdown('<div style="background-color: rgba(255, 255, 224, 0.3); padding: 10px; border-radius: 5px; height: 100%;">', unsafe_allow_html=True)
                utilization_pct = (total_spent / total_budgeted * 100) if total_budgeted > 0 else 0
                st.metric("Utilization", f"{utilization_pct:.1f}%")
                st.markdown('</div>', unsafe_allow_html=True)

        # Related dashboards navigation - compact
        st.markdown('<div style="background-color: rgba(49, 51, 63, 0.2); padding: 0.3rem 0.5rem; border-radius: 0.3rem; font-size: 0.75rem;">💡 <b>Related:</b> <a href="/Budget" style="color: #58a6ff;">💰 Budget</a> • <a href="/Cash_Flow" style="color: #58a6ff;">📈 Cash Flow</a> • <a href="/Categories" style="color: #58a6ff;">🏷️ Categories</a></div>', unsafe_allow_html=True)

        st.markdown("---")

        # === SECTION 2: Timeline Visualization ===
        st.markdown("### 📊 Budget Timeline")

        fig_timeline = create_timeline_chart(monthly_df, current_month_index)
        st.plotly_chart(fig_timeline, use_container_width=True, config={'displayModeBar': False})

        st.markdown("---")

        # === SECTION 3: Analysis Charts ===
        st.markdown("### 📈 Budget Analysis")

        col1, col2 = st.columns(2)

        with col1:
            fig_cumulative = create_cumulative_chart(monthly_df, current_month_index)
            st.plotly_chart(fig_cumulative, use_container_width=True, config={'displayModeBar': False})

        with col2:
            fig_deviation = create_deviation_chart(monthly_df, current_month_index)
            st.plotly_chart(fig_deviation, use_container_width=True, config={'displayModeBar': False})

        st.markdown("---")

        # === SECTION 4: Budget Gauges ===
        st.markdown("### 🎯 Budget Utilization Overview")

        # Get per-budget monthly data
        budget_monthly_data = get_per_budget_monthly_data(
            budgets_data,
            budget_limits_data,
            df_transactions,
            selected_start,
            selected_end
        )

        # Filter out budgets with no data
        active_budgets = {name: df for name, df in budget_monthly_data.items()
                         if df['budgeted'].sum() > 0 or df['spent'].sum() > 0}

        if active_budgets:
            # Calculate totals for each budget and create gauges
            budget_names = list(active_budgets.keys())
            gauges_per_row = 3  # 3 gauges per row

            for i in range(0, len(budget_names), gauges_per_row):
                cols = st.columns(gauges_per_row)

                for j in range(gauges_per_row):
                    idx = i + j
                    if idx < len(budget_names):
                        budget_name = budget_names[idx]
                        budget_df = active_budgets[budget_name]

                        # Calculate totals and round to 2 decimal places to avoid floating point precision issues
                        total_budgeted = round(budget_df['budgeted'].sum(), 2)
                        total_spent = round(budget_df['spent'].sum(), 2)

                        # Calculate average monthly spending (only for months with data)
                        months_with_data = len(budget_df[budget_df['spent'] > 0])
                        avg_spent = round(total_spent / months_with_data, 2) if months_with_data > 0 else 0

                        with cols[j]:
                            fig_gauge = create_budget_gauge(budget_name, total_budgeted, total_spent, avg_spent)
                            st.plotly_chart(fig_gauge, use_container_width=True, config={'displayModeBar': False})
        else:
            st.info("No budget data available for the selected period.")

        st.markdown("---")

        # === SECTION 5: Individual Budget Charts ===
        st.markdown("### 📊 Individual Budget Performance")

        # active_budgets already calculated above
        # Filter out budgets with no data (redundant but kept for clarity)
        active_budgets = {name: df for name, df in budget_monthly_data.items()
                         if df['budgeted'].sum() > 0 or df['spent'].sum() > 0}

        if active_budgets:
            # Display charts in a grid (3 per row)
            budget_names = list(active_budgets.keys())
            charts_per_row = 3

            for i in range(0, len(budget_names), charts_per_row):
                cols = st.columns(charts_per_row)

                for j in range(charts_per_row):
                    idx = i + j
                    if idx < len(budget_names):
                        budget_name = budget_names[idx]
                        budget_df = active_budgets[budget_name]

                        with cols[j]:
                            fig = create_small_budget_chart(budget_name, budget_df, today.month)
                            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
        else:
            st.info("No budget data available for the selected period.")

        st.markdown("---")

        # === SECTION 6: Monthly Breakdown Table ===
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
                'budgeted': st.column_config.NumberColumn('Budgeted', format="€%.2f"),
                'spent': st.column_config.NumberColumn('Spent', format="€%.2f"),
                'remaining': st.column_config.NumberColumn('Remaining', format="€%.2f"),
                'deviation': st.column_config.NumberColumn('Deviation', format="€%.2f"),
                'deviation_pct': st.column_config.NumberColumn('Deviation %', format="%.1f%%"),
                'status': 'Status'
            },
            height=450
        )

        # Export option
        csv = monthly_df.to_csv(index=False)
        st.download_button(
            label="📥 Download CSV",
            data=csv,
            file_name=f"budget_timeline_{selected_start}_to_{selected_end}.csv",
            mime="text/csv"
        )

except Exception as e:
    st.error(f"An error occurred: {str(e)}")
    st.exception(e)
