import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import sys
from pathlib import Path
import json
import plotly.graph_objects as go
import plotly.express as px

# Add parent directory to path to import utils
sys.path.append(str(Path(__file__).parent.parent))
from utils.navigation import render_sidebar_navigation
from utils.charts import create_pie_chart
from utils.database import get_database

# Page configuration
st.set_page_config(
    page_title="Savings Forecast - Firefly III",
    page_icon="🚀",
    layout="wide"
)

# Render custom navigation
render_sidebar_navigation()

# Compact CSS styling
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

    /* Canvas container for Three.js */
    #threejs-canvas {
        width: 100%;
        height: 600px;
        border: 1px solid #333;
        border-radius: 8px;
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
    }
</style>
""", unsafe_allow_html=True)

# Initialize database
db = get_database()

# Load savings from database on first run
if 'savings_loaded' not in st.session_state:
    st.session_state.savings_loaded = True
    st.session_state.savings_list = db.get_all_savings()
elif 'force_reload' in st.session_state and st.session_state.force_reload:
    st.session_state.savings_list = db.get_all_savings()
    st.session_state.force_reload = False

# Currency configuration
CURRENCIES = {
    'EUR': {'symbol': '€', 'name': 'Euro', 'position': 'prefix'},
    'INR': {'symbol': '₹', 'name': 'Indian Rupee', 'position': 'prefix'},
    'USD': {'symbol': '$', 'name': 'US Dollar', 'position': 'prefix'},
    'GBP': {'symbol': '£', 'name': 'British Pound', 'position': 'prefix'}
}

def format_currency(amount, currency_code='EUR'):
    """Format amount with appropriate currency symbol"""
    curr = CURRENCIES.get(currency_code, CURRENCIES['EUR'])
    symbol = curr['symbol']
    if curr['position'] == 'prefix':
        return f"{symbol}{amount:,.2f}"
    else:
        return f"{amount:,.2f}{symbol}"

def format_currency_short(amount, currency_code='EUR'):
    """Format amount with appropriate currency symbol (no decimals)"""
    curr = CURRENCIES.get(currency_code, CURRENCIES['EUR'])
    symbol = curr['symbol']
    if curr['position'] == 'prefix':
        return f"{symbol}{amount:,.0f}"
    else:
        return f"{amount:,.0f}{symbol}"

# Color palette for different savings - optimized for dark mode
# Uses colors that have good contrast on dark backgrounds and match the app's color scheme
COLOR_PALETTE = [
    {'name': 'Sky Blue', 'hex': '#60a5fa', 'rgb': [96, 165, 250]},        # Primary blue (matches charts.py)
    {'name': 'Emerald Green', 'hex': '#4ade80', 'rgb': [74, 222, 128]},   # Success green (matches charts.py)
    {'name': 'Amber', 'hex': '#fbbf24', 'rgb': [251, 191, 36]},          # Warning yellow (matches charts.py)
    {'name': 'Rose', 'hex': '#f87171', 'rgb': [248, 113, 113]},          # Alert red (matches charts.py)
    {'name': 'Violet', 'hex': '#a78bfa', 'rgb': [167, 139, 250]},        # Purple accent
    {'name': 'Cyan', 'hex': '#22d3ee', 'rgb': [34, 211, 238]},           # Bright cyan
    {'name': 'Lime', 'hex': '#a3e635', 'rgb': [163, 230, 53]},           # Lime green
    {'name': 'Pink', 'hex': '#f472b6', 'rgb': [244, 114, 182]},          # Pink accent
    {'name': 'Teal', 'hex': '#2dd4bf', 'rgb': [45, 212, 191]},           # Teal
    {'name': 'Orange', 'hex': '#fb923c', 'rgb': [251, 146, 60]},         # Orange
    {'name': 'Indigo', 'hex': '#818cf8', 'rgb': [129, 140, 248]},        # Indigo
    {'name': 'Yellow', 'hex': '#facc15', 'rgb': [250, 204, 21]}          # Bright yellow
]

def get_color_for_saving(index):
    """Get a color from the palette for a saving index"""
    return COLOR_PALETTE[index % len(COLOR_PALETTE)]

def calculate_compound_interest(principal, rate, years, compounding_frequency=1):
    """
    Calculate compound interest

    Args:
        principal: Initial amount
        rate: Annual interest rate (as decimal, e.g., 0.03 for 3%)
        years: Number of years
        compounding_frequency: Times per year (1=annually, 2=semi-annually, 4=quarterly, 12=monthly)

    Returns:
        Final amount after compound interest
    """
    n = compounding_frequency
    t = years
    amount = principal * (1 + rate / n) ** (n * t)
    return round(amount, 2)


def months_between(start_dt: datetime, end_dt: datetime) -> int:
    """Calculate full months between two dates (floor)."""
    if end_dt <= start_dt:
        return 0
    r = relativedelta(end_dt, start_dt)
    return r.years * 12 + r.months + (1 if r.days >= 0 else 0) - 1


def fv_with_monthly_contrib(principal: float, rate: float, start_dt: datetime, end_dt: datetime,
                            compounding_frequency: int = 12, monthly_contribution: float = 0.0) -> float:
    """
    Future value with compound growth and monthly contributions.

    - Converts stated compounding rate to an effective monthly rate when needed.
    - Assumes contributions at end of each month.
    """
    months = months_between(start_dt, end_dt)
    if months <= 0:
        return round(principal, 2)

    # Effective monthly rate derived from nominal rate and compounding frequency
    if compounding_frequency <= 0:
        compounding_frequency = 12
    monthly_rate = (1 + rate / compounding_frequency) ** (compounding_frequency / 12) - 1

    # FV of principal
    fv_principal = principal * ((1 + monthly_rate) ** months)

    # FV of an annuity (end-of-period contributions)
    fv_contrib = 0.0
    if monthly_contribution > 0 and monthly_rate != 0:
        fv_contrib = monthly_contribution * (((1 + monthly_rate) ** months - 1) / monthly_rate)
    elif monthly_contribution > 0 and monthly_rate == 0:
        fv_contrib = monthly_contribution * months

    return round(fv_principal + fv_contrib, 2)

def generate_timeline_data(savings_list, *, rate_shock_pct: float = 0.0, inflation_pct: float = 0.0,
                           real_terms: bool = False):
    """Generate timeline data points for visualization.

    Applies an optional rate shock (in %) to each saving's rate.
    Optionally deflates values by inflation to show in real terms.
    """
    if not savings_list:
        return []

    today = datetime.now()
    timeline_points = []

    # Add current point
    current_total = sum(s['principal'] for s in savings_list)
    timeline_points.append({
        'date': today,
        'total': current_total,
        'breakdown': [{'name': s['name'], 'value': s['principal']} for s in savings_list]
    })

    # Generate monthly points until the furthest maturity date
    max_date = max(s['maturity_date'] for s in savings_list)
    current_date = today

    while current_date <= max_date:
        current_date += relativedelta(months=1)
        total = 0
        breakdown = []

        for saving in savings_list:
            # Adjusted rate for scenario
            adj_rate = max(0.0, saving['rate'] * (1 + rate_shock_pct / 100.0))

            # Time from saving start to this point (cap at maturity)
            start_dt = saving['start_date']
            mature_dt = saving['maturity_date']
            eval_dt = min(current_date, mature_dt)

            # Current value with optional monthly contribution
            current_value = fv_with_monthly_contrib(
                principal=saving['principal'],
                rate=adj_rate,
                start_dt=start_dt,
                end_dt=eval_dt,
                compounding_frequency=saving['compounding_frequency'],
                monthly_contribution=saving.get('monthly_contribution', 0.0)
            ) if eval_dt >= start_dt else saving['principal']

            # Inflation adjustment to show real terms
            if real_terms and inflation_pct > 0:
                years_since_today = max(0.0, (eval_dt - today).days / 365.25)
                deflator = (1 + inflation_pct / 100.0) ** years_since_today
                current_value = current_value / deflator

            total += current_value
            breakdown.append({'name': saving['name'], 'value': round(current_value, 2)})

        timeline_points.append({
            'date': current_date,
            'total': round(total, 2),
            'breakdown': breakdown
        })

    return timeline_points

# Title
st.title("🚀 Savings Forecast & Roadmap")

# Add refresh button - compact
col1, col2 = st.columns([1, 5])
with col1:
    if st.button("🔄 Refresh"):
        st.rerun()
with col2:
    st.caption(f"Track your savings goals and projected returns | Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# Sidebar for adding savings
with st.sidebar:
    st.header("➕ Add New Saving")

    with st.form("add_saving_form", clear_on_submit=True):
        saving_name = st.text_input("Name", placeholder="e.g., Fixed Deposit 2025")

        col_type, col_curr = st.columns(2)
        with col_type:
            saving_type = st.selectbox("Type", ["Fixed Deposit", "Recurring Deposit", "Retirement Account", "Other"])
        with col_curr:
            currency = st.selectbox("Currency", options=list(CURRENCIES.keys()),
                                   format_func=lambda x: f"{CURRENCIES[x]['symbol']} {CURRENCIES[x]['name']}")

        principal = st.number_input(f"Principal Amount ({CURRENCIES[currency]['symbol']})", min_value=0.0, value=1000.0, step=100.0)
        rate = st.number_input("Annual Interest Rate (%)", min_value=0.0, max_value=100.0, value=3.0, step=0.1)

        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("Start Date", value=datetime.now())
        with col2:
            years = st.number_input("Duration (Years)", min_value=0.1, max_value=50.0, value=2.0, step=0.5)

        compounding = st.selectbox(
            "Compounding Frequency",
            options=[1, 2, 4, 12],
            format_func=lambda x: {1: "Annually", 2: "Semi-annually", 4: "Quarterly", 12: "Monthly"}[x],
            index=0
        )

        monthly_contribution = 0.0
        if saving_type == "Recurring Deposit":
            monthly_contribution = st.number_input(
                f"Monthly Contribution ({CURRENCIES[currency]['symbol']})", min_value=0.0, value=0.0, step=50.0,
                help="Additional amount you add every month"
            )

        submit = st.form_submit_button("Add Saving", width="stretch")

        if submit and saving_name:
            start_dt = datetime.combine(start_date, datetime.min.time())
            maturity_date = start_dt + relativedelta(years=int(years), months=int((years % 1) * 12))
            # Compute maturity using monthly contribution-aware FV
            maturity_value = fv_with_monthly_contrib(
                principal=principal,
                rate=rate/100,
                start_dt=start_dt,
                end_dt=maturity_date,
                compounding_frequency=compounding,
                monthly_contribution=monthly_contribution
            )

            # Total contributions over full months
            total_months = months_between(start_dt, maturity_date)
            total_contrib = monthly_contribution * total_months

            # Assign color based on current index
            color_index = len(st.session_state.savings_list)
            assigned_color = get_color_for_saving(color_index)

            # Save to database
            saving_data = {
                'name': saving_name,
                'type': saving_type,
                'principal': principal,
                'rate': rate / 100,  # Convert to decimal
                'start_date': start_dt,
                'maturity_date': maturity_date,
                'compounding_frequency': compounding,
                'monthly_contribution': monthly_contribution,
                'total_contributions': total_contrib,
                'maturity_value': maturity_value,
                'interest_earned': maturity_value - principal - total_contrib,
                'color': assigned_color,
                'color_index': color_index,
                'currency': currency
            }

            saving_id = db.add_saving(saving_data)
            st.success(f"✅ Added {saving_name}!")

            # Reload from database
            st.session_state.force_reload = True
            st.rerun()

# Main content
if st.session_state.savings_list:
    st.markdown("---")

    # Summary metrics - grouped by currency
    st.markdown("### 📊 Portfolio Summary")

    # Group savings by currency
    from collections import defaultdict
    currency_totals = defaultdict(lambda: {'principal': 0, 'maturity': 0, 'contributions': 0,
                                            'monthly_contrib': 0, 'count': 0, 'maturities_12m': 0})

    next_12m = datetime.now() + relativedelta(years=1)

    for s in st.session_state.savings_list:
        curr = s.get('currency', 'EUR')
        currency_totals[curr]['principal'] += s['principal']
        currency_totals[curr]['maturity'] += s['maturity_value']
        currency_totals[curr]['contributions'] += s.get('total_contributions', 0.0)
        currency_totals[curr]['monthly_contrib'] += s.get('monthly_contribution', 0.0)
        currency_totals[curr]['count'] += 1
        if s['maturity_date'] <= next_12m:
            currency_totals[curr]['maturities_12m'] += s['maturity_value']

    # Calculate overall metrics
    num_savings = len(st.session_state.savings_list)
    num_currencies = len(currency_totals)

    # Display per-currency metrics
    if num_currencies == 1:
        # Single currency - show as before
        curr = list(currency_totals.keys())[0]
        totals = currency_totals[curr]
        total_interest = totals['maturity'] - totals['principal'] - totals['contributions']
        avg_return = (total_interest / totals['principal'] * 100) if totals['principal'] > 0 else 0

        col1, col2, col3, col4, col5, col6, col7, col8 = st.columns(8)
        col1.metric("Total Invested", format_currency_short(totals['principal'], curr))
        col2.metric("Monthly Contrib.", format_currency_short(totals['monthly_contrib'], curr))
        col3.metric("Total Contributions", format_currency_short(totals['contributions'], curr))
        col4.metric("Projected Value", format_currency_short(totals['maturity'], curr))
        col5.metric("Total Interest", format_currency_short(total_interest, curr))
        col6.metric("Avg. Return", f"{avg_return:.1f}%")
        col7.metric("12-mo Maturities", format_currency_short(totals['maturities_12m'], curr))
        col8.metric("# Savings", f"{num_savings}")
    else:
        # Multiple currencies - show summary per currency
        st.caption(f"**{num_savings} savings across {num_currencies} currencies**")

        for curr, totals in sorted(currency_totals.items()):
            st.markdown(f"**{CURRENCIES[curr]['symbol']} {CURRENCIES[curr]['name']}:**")
            total_interest = totals['maturity'] - totals['principal'] - totals['contributions']
            avg_return = (total_interest / totals['principal'] * 100) if totals['principal'] > 0 else 0

            col1, col2, col3, col4, col5, col6 = st.columns(6)
            col1.metric("Invested", format_currency_short(totals['principal'], curr))
            col2.metric("Projected", format_currency_short(totals['maturity'], curr))
            col3.metric("Interest", format_currency_short(total_interest, curr))
            col4.metric("Return", f"{avg_return:.1f}%")
            col5.metric("12-mo Mat.", format_currency_short(totals['maturities_12m'], curr))
            col6.metric("Count", f"{totals['count']}")
            st.markdown("")  # Spacing

    st.markdown("---")

    # Key dates section - compact
    st.markdown("### 📅 Key Dates & Milestones")

    # Sort savings by maturity date
    sorted_savings = sorted(st.session_state.savings_list, key=lambda x: x['maturity_date'])

    # Get next 3 upcoming maturities
    upcoming_3 = sorted_savings[:3]

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if upcoming_3:
            next_maturity = upcoming_3[0]
            days_until = (next_maturity['maturity_date'] - datetime.now()).days
            curr = next_maturity.get('currency', 'EUR')
            col1.metric(
                "Next Maturity",
                f"{next_maturity['name'][:15]}...",
                f"{days_until} days | {format_currency_short(next_maturity['maturity_value'], curr)}"
            )
        else:
            col1.metric("Next Maturity", "N/A")

    with col2:
        # Longest duration saving
        longest = max(st.session_state.savings_list, key=lambda x: (x['maturity_date'] - x['start_date']).days)
        duration_years = (longest['maturity_date'] - longest['start_date']).days / 365.25
        col2.metric(
            "Longest Term",
            f"{longest['name'][:15]}...",
            f"{duration_years:.1f}y | {longest['rate']*100:.1f}%"
        )

    with col3:
        # Highest interest earning
        highest_interest = max(st.session_state.savings_list, key=lambda x: x['interest_earned'])
        curr = highest_interest.get('currency', 'EUR')
        col3.metric(
            "Highest Interest",
            f"{highest_interest['name'][:15]}...",
            format_currency_short(highest_interest['interest_earned'], curr)
        )

    with col4:
        # Weighted average rate (across all currencies)
        total_principal_all = sum(s['principal'] for s in st.session_state.savings_list)
        total_weighted = sum(s['principal'] * s['rate'] for s in st.session_state.savings_list)
        weighted_avg_rate = (total_weighted / total_principal_all * 100) if total_principal_all > 0 else 0
        col4.metric(
            "Weighted Avg Rate",
            f"{weighted_avg_rate:.2f}%",
            f"Across {num_savings} accounts"
        )

    st.markdown("---")

    # What-if controls
    with st.expander("🎛️ What-if Settings", expanded=False):
        col_w1, col_w2, col_w3 = st.columns(3)
        with col_w1:
            rate_shock = st.slider("Rate Shock (+/-%):", -5.0, 10.0, 0.0, 0.1,
                                   help="Apply a relative change to all rates for scenario testing")
        with col_w2:
            inflation_rate = st.slider("Inflation (%):", 0.0, 10.0, 0.0, 0.1,
                                       help="Display values in real terms by deflating with inflation")
        with col_w3:
            show_real = st.toggle("Show Real Terms (Inflation-adjusted)", value=False)

    # Generate timeline data (scenario-aware)
    timeline_data = generate_timeline_data(
        st.session_state.savings_list,
        rate_shock_pct=rate_shock,
        inflation_pct=inflation_rate,
        real_terms=show_real
    )

    # Create DataFrame for the projection chart
    chart_data = []
    for point in timeline_data:
        row = {'Date': point['date'], 'Total': point['total']}
        for item in point['breakdown']:
            row[item['name']] = item['value']
        chart_data.append(row)

    df_timeline = pd.DataFrame(chart_data)

    # Currency info and color legend
    if num_currencies > 1:
        st.info(f"💱 **Multi-Currency Portfolio:** Charts show all {num_currencies} currencies combined. Hover over charts to see individual currency values.")

    # Color legend for easy tracking across charts
    st.markdown("**🎨 Savings Color Legend:**")
    legend_cols = st.columns(min(len(st.session_state.savings_list), 6))
    for idx, saving in enumerate(st.session_state.savings_list[:6]):  # Show first 6
        color_obj = saving.get('color', get_color_for_saving(idx))
        with legend_cols[idx]:
            st.markdown(
                f'<div style="display: inline-block; width: 12px; height: 12px; background-color: {color_obj["hex"]}; '
                f'border-radius: 2px; margin-right: 4px;"></div>'
                f'<span style="font-size: 0.75rem;">{saving["name"][:20]}</span>',
                unsafe_allow_html=True
            )

    if len(st.session_state.savings_list) > 6:
        st.caption(f"+ {len(st.session_state.savings_list) - 6} more (see chart legends)")

    st.markdown("---")

    # Create two columns for side-by-side charts
    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown("**📈 Savings Growth Projection**")

        # Create the main projection chart with Plotly
        fig = go.Figure()

        # Add stacked area chart for each saving
        for idx, saving in enumerate(st.session_state.savings_list):
            color_obj = saving.get('color', get_color_for_saving(idx))

            # Convert hex to rgba with reduced opacity for softer appearance
            rgb = color_obj['rgb']
            fill_color = f'rgba({rgb[0]}, {rgb[1]}, {rgb[2]}, 0.6)'  # 60% opacity
            line_color = f'rgba({rgb[0]}, {rgb[1]}, {rgb[2]}, 0.8)'  # 80% opacity

            fig.add_trace(go.Scatter(
                x=df_timeline['Date'],
                y=df_timeline[saving['name']],
                name=saving['name'],
                mode='lines',
                line=dict(width=0.5, color=line_color),
                stackgroup='one',
                fillcolor=fill_color,
                hovertemplate='<b>%{fullData.name}</b><br>' +
                              'Date: %{x|%Y-%m-%d}<br>' +
                              'Value: €%{y:,.2f}<br>' +
                              '<extra></extra>'
            ))

        # Add total portfolio line (bold, on top) with data labels at key points
        # Show labels only at start, end, and every few months to avoid clutter
        label_indices = [0, len(df_timeline) - 1]  # Start and end
        # Add some intermediate points (every ~3 months)
        step = max(1, len(df_timeline) // 4)
        label_indices.extend(range(step, len(df_timeline) - 1, step))

        text_labels = []
        for i in range(len(df_timeline)):
            if i in label_indices:
                text_labels.append(f'€{df_timeline["Total"].iloc[i]:,.0f}')
            else:
                text_labels.append('')

        fig.add_trace(go.Scatter(
            x=df_timeline['Date'],
            y=df_timeline['Total'],
            name='Total Portfolio',
            mode='lines+text',
            line=dict(width=3, color='#fbbf24', dash='solid'),  # Amber/gold color for visibility
            text=text_labels,
            textposition='top center',
            textfont=dict(size=9, color='#fbbf24'),
            hovertemplate='<b>Total Portfolio</b><br>' +
                          'Date: %{x|%Y-%m-%d}<br>' +
                          'Value: €%{y:,.2f}<br>' +
                          '<extra></extra>'
        ))

        # Add confidence bands (±5% around scenario)
        upper_bound = df_timeline['Total'] * 1.05
        lower_bound = df_timeline['Total'] * 0.95

        fig.add_trace(go.Scatter(
            x=df_timeline['Date'],
            y=upper_bound,
            mode='lines',
            name='Upper Bound (+5%)',
            line=dict(width=0),
            showlegend=False,
            hoverinfo='skip'
        ))

        fig.add_trace(go.Scatter(
            x=df_timeline['Date'],
            y=lower_bound,
            mode='lines',
            name='Lower Bound (-5%)',
            line=dict(width=0),
            fillcolor='rgba(251, 191, 36, 0.1)',  # Amber with low opacity
            fill='tonexty',
            showlegend=False,
            hoverinfo='skip'
        ))

        # Add maturity markers and vertical lines using shapes (to avoid datetime issues)
        shapes = []
        annotations = []

        for idx, saving in enumerate(st.session_state.savings_list):
            color_obj = saving.get('color', get_color_for_saving(idx))

            # Add maturity marker (scatter point)
            maturity_point = df_timeline[df_timeline['Date'] == saving['maturity_date']]
            if not maturity_point.empty:
                fig.add_trace(go.Scatter(
                    x=[saving['maturity_date']],
                    y=[maturity_point[saving['name']].values[0]],
                    mode='markers',
                    name=f"{saving['name']} Maturity",
                    marker=dict(
                        size=15,
                        color=color_obj['hex'],
                        symbol='diamond',
                        line=dict(color='white', width=2)
                    ),
                    showlegend=False,
                    hovertemplate=f'<b>{saving["name"]} Matures</b><br>' +
                                  'Date: %{x|%Y-%m-%d}<br>' +
                                  f'Final Value: €{saving["maturity_value"]:,.2f}<br>' +
                                  f'Interest Earned: €{saving["interest_earned"]:,.2f}<br>' +
                                  '<extra></extra>'
                ))

                # Add vertical line as a shape
                shapes.append(dict(
                    type='line',
                    x0=saving['maturity_date'],
                    x1=saving['maturity_date'],
                    y0=0,
                    y1=1,
                    yref='paper',
                    line=dict(
                        color=color_obj['hex'],
                        width=2,
                        dash='dash'
                    ),
                    opacity=0.6
                ))

                # Add annotation for maturity
                annotations.append(dict(
                    x=saving['maturity_date'],
                    y=1,
                    yref='paper',
                    text=f"{saving['name']} Matures",
                    showarrow=False,
                    yanchor='bottom',
                    font=dict(size=10, color=color_obj['hex']),
                    bgcolor='rgba(0,0,0,0.7)',
                    bordercolor=color_obj['hex'],
                    borderwidth=1,
                    borderpad=4
                ))

        # Update layout with shapes and annotations
        fig.update_layout(
            template='plotly_dark',
            hovermode='x unified',
            height=450,
            margin=dict(l=10, r=10, t=10, b=10),
            plot_bgcolor='rgba(10,10,30,0.9)',
            paper_bgcolor='rgba(10,10,30,0.9)',
            xaxis=dict(
                title='Date',
                showgrid=True,
                gridwidth=1,
                gridcolor='rgba(128,128,128,0.2)',
                zeroline=False
            ),
            yaxis=dict(
                title='Value (€)',
                showgrid=True,
                gridwidth=1,
                gridcolor='rgba(128,128,128,0.2)',
                zeroline=False,
                tickformat=',.0f',
                tickprefix='€'
            ),
            legend=dict(
                orientation='h',
                yanchor='bottom',
                y=1.02,
                xanchor='right',
                x=1,
                bgcolor='rgba(0,0,0,0.5)',
                bordercolor='rgba(128,128,128,0.3)',
                borderwidth=1
            ),
            font=dict(family='Segoe UI, Arial', size=12),
            shapes=shapes,
            annotations=annotations
        )

        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown("**💎 Maturity Values**")

        fig_bars = go.Figure()

        savings_names = [s['name'] for s in st.session_state.savings_list]
        principals = [s['principal'] for s in st.session_state.savings_list]
        # Recompute interest if what-if scenario is active (approximate using maturity date)
        interests = []
        for s in st.session_state.savings_list:
            scenario_maturity = fv_with_monthly_contrib(
                principal=s['principal'],
                rate=max(0.0, s['rate'] * (1 + rate_shock / 100.0)),
                start_dt=s['start_date'],
                end_dt=s['maturity_date'],
                compounding_frequency=s['compounding_frequency'],
                monthly_contribution=s.get('monthly_contribution', 0.0)
            )
            interests.append(max(0.0, scenario_maturity - s['principal'] - s.get('total_contributions', 0.0)))

        # Create softer colors with opacity for the bars
        colors_rgba = []
        for i, s in enumerate(st.session_state.savings_list):
            color_obj = s.get('color', get_color_for_saving(i))
            rgb = color_obj['rgb']
            colors_rgba.append(f'rgba({rgb[0]}, {rgb[1]}, {rgb[2]}, 0.7)')  # 70% opacity

        fig_bars.add_trace(go.Bar(
            name='Principal',
            x=savings_names,
            y=principals,
            marker_color='rgba(100,100,100,0.5)',  # Slightly more transparent
            text=[f'€{p:,.0f}' for p in principals],
            textposition='inside',
            textfont=dict(size=9, color='white'),
            hovertemplate='<b>%{x}</b><br>Principal: €%{y:,.2f}<extra></extra>'
        ))

        fig_bars.add_trace(go.Bar(
            name='Interest Earned',
            x=savings_names,
            y=interests,
            marker_color=colors_rgba,  # Use rgba with opacity
            text=[f'€{i:,.0f}' if i > 0 else '' for i in interests],
            textposition='inside',
            textfont=dict(size=9, color='white'),
            hovertemplate='<b>%{x}</b><br>Interest: €%{y:,.2f}<extra></extra>'
        ))

        # Add total value labels on top of stacked bars
        totals = [p + i for p, i in zip(principals, interests)]
        fig_bars.add_trace(go.Scatter(
            x=savings_names,
            y=totals,
            mode='text',
            text=[f'€{t:,.0f}' for t in totals],
            textposition='top center',
            textfont=dict(size=9, color='#fbbf24'),
            showlegend=False,
            hoverinfo='skip'
        ))

        fig_bars.update_layout(
            barmode='stack',
            template='plotly_dark',
            height=450,
            margin=dict(l=10, r=10, t=30, b=10),  # Increased top margin for labels
            plot_bgcolor='rgba(10,10,30,0.9)',
            paper_bgcolor='rgba(10,10,30,0.9)',
            xaxis=dict(
                title='',
                showgrid=False
            ),
            yaxis=dict(
                title='Amount (€)',
                showgrid=True,
                gridwidth=1,
                gridcolor='rgba(128,128,128,0.2)',
                tickformat=',.0f',
                tickprefix='€'
            ),
            legend=dict(
                orientation='h',
                yanchor='bottom',
                y=1.02,
                xanchor='right',
                x=1,
                bgcolor='rgba(0,0,0,0.5)'
            ),
            font=dict(family='Segoe UI, Arial', size=12)
        )

        st.plotly_chart(fig_bars, use_container_width=True)

    st.markdown("---")

    # Additional insights row - more compact
    st.markdown("### 📊 Breakdown & Allocation")

    c1, c2 = st.columns([2, 1])
    with c1:
        st.markdown("**🪜 Maturity Ladder**")
        # Build per-saving principal and interest at maturity (scenario-aware) with individual colors
        ladder_rows = []
        for idx, s in enumerate(st.session_state.savings_list):
            scen_maturity = fv_with_monthly_contrib(
                principal=s['principal'],
                rate=max(0.0, s['rate'] * (1 + rate_shock / 100.0)),
                start_dt=s['start_date'],
                end_dt=s['maturity_date'],
                compounding_frequency=s['compounding_frequency'],
                monthly_contribution=s.get('monthly_contribution', 0.0)
            )

            # Inflation adjustment for maturity value and components (to real terms)
            if show_real and inflation_rate > 0:
                years_to_maturity = max(0.0, (s['maturity_date'] - datetime.now()).days / 365.25)
                deflator = (1 + inflation_rate / 100.0) ** years_to_maturity
            else:
                deflator = 1.0

            principal_comp = (s['principal'] + s.get('total_contributions', 0.0)) / deflator
            interest_comp = max(0.0, scen_maturity / deflator - principal_comp)
            color_obj = s.get('color', get_color_for_saving(idx))

            ladder_rows.append({
                'Saving': s['name'],
                'Maturity Month': s['maturity_date'].strftime('%Y-%m'),
                'Maturity Date': s['maturity_date'],
                'Principal': principal_comp,
                'Interest': interest_comp,
                'Color': color_obj
            })

        ladder_df = pd.DataFrame(ladder_rows)
        if not ladder_df.empty:
            # Sort by maturity date
            ladder_df = ladder_df.sort_values('Maturity Date')

            # Create stacked bar chart
            ladder_fig = go.Figure()

            # Get unique months in order
            unique_months = ladder_df['Maturity Month'].unique()

            # First, add all principal bars (gray) for each saving
            for _, row in ladder_df.iterrows():
                # Only show label if principal is significant enough
                text_label = f'€{row["Principal"]:,.0f}' if row["Principal"] > 100 else ''

                ladder_fig.add_trace(go.Bar(
                    name=f"{row['Saving']} (Principal)",
                    x=[row['Maturity Month']],
                    y=[row['Principal']],
                    marker_color='rgba(100,100,100,0.5)',
                    text=[text_label],
                    textposition='inside',
                    textfont=dict(size=8, color='white'),
                    hovertemplate=f'<b>{row["Saving"]}</b><br>' +
                                  'Principal: €%{y:,.2f}<extra></extra>',
                    showlegend=False,
                    legendgroup=row['Saving']
                ))

            # Then, add all interest bars (individual colors) for each saving
            for _, row in ladder_df.iterrows():
                rgb = row['Color']['rgb']
                color_rgba = f'rgba({rgb[0]}, {rgb[1]}, {rgb[2]}, 0.7)'
                # Only show label if interest is significant enough
                text_label = f'€{row["Interest"]:,.0f}' if row["Interest"] > 50 else ''

                ladder_fig.add_trace(go.Bar(
                    name=row['Saving'],
                    x=[row['Maturity Month']],
                    y=[row['Interest']],
                    marker_color=color_rgba,
                    text=[text_label],
                    textposition='outside',  # Changed to outside
                    textfont=dict(size=8, color=color_rgba),  # Use same color as bar
                    hovertemplate=f'<b>{row["Saving"]}</b><br>' +
                                  'Interest: €%{y:,.2f}<extra></extra>',
                    showlegend=True,
                    legendgroup=row['Saving']
                ))

            # Calculate max value for y-axis range with padding
            max_value = ladder_df.apply(lambda row: row['Principal'] + row['Interest'], axis=1).max()
            y_max = max_value * 1.15  # Add 15% padding at top for labels

            ladder_fig.update_layout(
                barmode='stack',
                template='plotly_dark',
                height=350,  # Further increased height
                margin=dict(t=10, b=30, l=10, r=10),  # Reset top margin, use y-axis range instead
                xaxis_title='',
                yaxis=dict(
                    title='Maturing (€)',
                    tickprefix='€',
                    tickformat=',.0f',
                    range=[0, y_max]  # Set explicit range with padding
                ),
                legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1, font=dict(size=8)),
                font=dict(size=10),
                uniformtext_minsize=8,
                uniformtext_mode='hide'
            )
            st.plotly_chart(ladder_fig, use_container_width=True, config={'displayModeBar': False})
        else:
            st.info("Add savings to see upcoming maturities")

    with c2:
        st.markdown("**📊 Allocation by Type**")
        alloc_rows = []
        for s in st.session_state.savings_list:
            alloc_rows.append({'Type': s['type'], 'Amount': s['principal'] + s.get('total_contributions', 0.0)})
        alloc_df = pd.DataFrame(alloc_rows)
        if not alloc_df.empty:
            alloc_agg = alloc_df.groupby('Type')['Amount'].sum().reset_index()
            pie_fig = create_pie_chart(alloc_agg, labels='Type', values='Amount', title='', hole=0.5)
            pie_fig.update_layout(template='plotly_dark', height=280, margin=dict(t=10, b=10, l=10, r=10), font=dict(size=10))
            st.plotly_chart(pie_fig, use_container_width=True, config={'displayModeBar': False})
        else:
            st.info("No allocation to show yet")

    st.markdown("---")

    # Related dashboards navigation - compact
    st.markdown('<div style="background-color: rgba(49, 51, 63, 0.2); padding: 0.3rem 0.5rem; border-radius: 0.3rem; font-size: 0.75rem;">💡 <b>Related:</b> <a href="/Net_Worth" style="color: #58a6ff;">📊 Net Worth</a> • <a href="/Cash_Flow" style="color: #58a6ff;">📈 Cash Flow</a> • <a href="/Budget" style="color: #58a6ff;">💰 Budget</a></div>', unsafe_allow_html=True)

    st.markdown("---")

    # Savings list table - collapsible for density
    with st.expander("📋 Your Savings Details", expanded=False):
        # Prepare data for table
        table_data = []
        compounding_map = {1: 'Ann.', 2: 'Semi', 4: 'Qtr', 12: 'Mon.'}

        for idx, saving in enumerate(st.session_state.savings_list):
            color = saving.get('color', get_color_for_saving(idx))
            curr = saving.get('currency', 'EUR')
            years_from_now = (saving['maturity_date'] - datetime.now()).days / 365.25

            table_data.append({
                'Color': color['name'],
                'Name': saving['name'],
                'Currency': CURRENCIES[curr]['symbol'],
                'Type': saving['type'],
                'Principal': format_currency_short(saving['principal'], curr),
                'Contrib.': format_currency_short(saving.get('total_contributions', 0.0), curr),
                'Rate': f"{saving['rate']*100:.1f}%",
                'Comp.': compounding_map[saving['compounding_frequency']],
                'Start': saving['start_date'].strftime('%Y-%m-%d'),
                'Maturity': saving['maturity_date'].strftime('%Y-%m-%d'),
                'Years': f"{years_from_now:.1f}y",
                'Final Value': format_currency_short(saving['maturity_value'], curr),
                'Interest': format_currency_short(saving['interest_earned'], curr),
                'Delete': idx
            })

        # Display table with built-in row selection
        if table_data:
            df = pd.DataFrame(table_data)

            # Display dataframe with row selection
            event = st.dataframe(
                df.drop(columns=['Delete']),
                use_container_width=True,
                height=min(350, (len(table_data) + 1) * 35 + 3),
                on_select="rerun",
                selection_mode="multi-row"
            )

            # Delete selected rows
            if event.selection.rows:
                col1, col2 = st.columns([4, 1])
                with col1:
                    st.info(f"✓ Selected {len(event.selection.rows)} saving(s)")
                with col2:
                    if st.button("🗑️ Delete Selected", type="secondary", width="stretch"):
                        # Delete from database
                        for idx in sorted(event.selection.rows, reverse=True):
                            saving_to_delete = st.session_state.savings_list[idx]
                            if 'id' in saving_to_delete:
                                db.delete_saving(saving_to_delete['id'])

                        # Reload from database
                        st.session_state.force_reload = True
                        st.success(f"✅ Deleted {len(event.selection.rows)} saving(s)")
                        st.rerun()

            st.markdown("---")

            # Downloads and clear all - more compact
            col_dl1, col_dl2, col_dl3, col_clr = st.columns([1, 1, 1, 1])
            with col_dl1:
                st.download_button(
                    "⬇️ Savings CSV",
                    data=pd.DataFrame(table_data).drop(columns=['Delete']).to_csv(index=False).encode('utf-8'),
                    file_name=f"savings_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime='text/csv'
                )
            with col_dl2:
                if 'df_timeline' in locals() and not df_timeline.empty:
                    st.download_button(
                        "⬇️ Projection CSV",
                        data=df_timeline.to_csv(index=False).encode('utf-8'),
                        file_name=f"projection_{datetime.now().strftime('%Y%m%d')}.csv",
                        mime='text/csv'
                    )
            with col_dl3:
                # Export as JSON
                savings_json = json.dumps([{
                    'name': s['name'],
                    'type': s['type'],
                    'principal': s['principal'],
                    'rate': s['rate'],
                    'start_date': s['start_date'].isoformat(),
                    'maturity_date': s['maturity_date'].isoformat(),
                    'compounding_frequency': s['compounding_frequency'],
                    'monthly_contribution': s.get('monthly_contribution', 0.0)
                } for s in st.session_state.savings_list], indent=2)

                st.download_button(
                    "⬇️ Export JSON",
                    data=savings_json,
                    file_name=f"savings_{datetime.now().strftime('%Y%m%d')}.json",
                    mime='application/json'
                )
            with col_clr:
                if st.button("🗑️ Clear All", type="secondary"):
                    # Delete all from database
                    count = db.delete_all_savings()

                    # Reload from database
                    st.session_state.force_reload = True
                    st.success(f"✅ Cleared all {count} saving(s)")
                    st.rerun()

else:
    # Empty state - compact
    st.markdown("---")
    st.info("👈 **Get Started:** Add your first saving using the form in the sidebar to visualize your savings growth!")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        **📝 How to use:**

        1. **Add Savings**: Use sidebar form (Fixed Deposits, Retirement, etc.)
        2. **Visualize Growth**: See projected growth over time
        3. **Track Maturity**: View when each saving matures
        4. **What-if Analysis**: Test different rate scenarios
        """)

    with col2:
        st.markdown("""
        **💡 Example:**
        - Principal: €1,000
        - Interest Rate: 3% annually
        - Duration: 2 years
        - Expected Value: €1,060.90
        - Interest Earned: €60.90
        """)
