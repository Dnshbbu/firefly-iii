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

# Currency configuration - Using INR only
CURRENCY_SYMBOL = '₹'

def format_currency(amount):
    """Format amount with INR currency symbol"""
    return f"{CURRENCY_SYMBOL}{amount:,.2f}"

def format_currency_short(amount):
    """Format amount with INR currency symbol (no decimals)"""
    return f"{CURRENCY_SYMBOL}{amount:,.0f}"

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

# Sidebar for adding/editing savings
with st.sidebar:
    # Add mode selector at the top
    if 'editing_index' not in st.session_state or st.session_state.editing_index is None:
        st.markdown("### Entry Mode")
        entry_mode = st.radio(
            "Choose entry mode:",
            ["Calculator", "Manual"],
            help="Calculator: Auto-calculates interest | Manual: Enter all values directly",
            horizontal=True
        )
        st.markdown("---")

    # Check if we're in edit mode
    if 'editing_index' in st.session_state and st.session_state.editing_index is not None:
        # Edit mode
        st.header("✏️ Edit Saving")
        editing_saving = st.session_state.savings_list[st.session_state.editing_index]

        # Calculate current duration
        duration_delta = relativedelta(editing_saving['maturity_date'], editing_saving['start_date'])

        with st.form("edit_saving_form"):
            saving_name = st.text_input("Name", value=editing_saving['name'])
            saving_type = st.selectbox(
                "Type",
                ["Fixed Deposit", "Recurring Deposit", "Retirement Account", "Other"],
                index=["Fixed Deposit", "Recurring Deposit", "Retirement Account", "Other"].index(editing_saving['type'])
            )

            principal = st.number_input(f"Principal Amount ({CURRENCY_SYMBOL})", min_value=0.0, value=float(editing_saving['principal']), step=1000.0)
            rate = st.number_input("Annual Interest Rate (%)", min_value=0.0, max_value=100.0, value=float(editing_saving['rate']*100), step=0.1)

            start_date = st.date_input("Start Date", value=editing_saving['start_date'].date(), min_value=None, max_value=None)

            st.markdown("**Duration:**")
            col1, col2, col3 = st.columns(3)
            with col1:
                duration_years = st.number_input("Years", min_value=0, max_value=50, value=duration_delta.years, step=1)
            with col2:
                duration_months = st.number_input("Months", min_value=0, max_value=11, value=duration_delta.months, step=1)
            with col3:
                duration_days = st.number_input("Days", min_value=0, max_value=31, value=duration_delta.days, step=1)

            # Interest payout option
            has_payout = st.checkbox(
                "Interest Payout (Non-cumulative FD)",
                value=editing_saving.get('has_payout', False),
                help="Check if interest is paid out periodically instead of being compounded"
            )

            # Show compounding frequency only for cumulative FDs
            compounding = 1
            payout_frequency = 1
            if has_payout:
                st.info("ℹ️ For payout FDs, maturity value = Principal + Contributions (interest paid separately)")
                current_payout_freq = editing_saving.get('payout_frequency', 4)
                payout_frequency = st.selectbox(
                    "Payout Frequency",
                    options=[1, 2, 4, 12],
                    format_func=lambda x: {1: "Annually", 2: "Semi-annually", 4: "Quarterly", 12: "Monthly"}[x],
                    index=[1, 2, 4, 12].index(current_payout_freq) if current_payout_freq in [1, 2, 4, 12] else 2,
                    help="How often interest is paid out"
                )
            else:
                compounding = st.selectbox(
                    "Compounding Frequency",
                    options=[1, 2, 4, 12],
                    format_func=lambda x: {1: "Annually", 2: "Semi-annually", 4: "Quarterly", 12: "Monthly"}[x],
                    index=[1, 2, 4, 12].index(editing_saving['compounding_frequency']) if editing_saving['compounding_frequency'] in [1, 2, 4, 12] else 0,
                    help="How often interest is compounded"
                )

            monthly_contribution = 0.0
            if saving_type == "Recurring Deposit":
                monthly_contribution = st.number_input(
                    f"Monthly Contribution ({CURRENCY_SYMBOL})",
                    min_value=0.0,
                    value=float(editing_saving.get('monthly_contribution', 0.0)),
                    step=500.0,
                    help="Additional amount you add every month"
                )

            # Notes field
            notes = st.text_area(
                "Notes (Optional)",
                value=editing_saving.get('notes', ''),
                max_chars=500,
                height=80,
                help="Add any notes or comments about this saving"
            )

            col_submit, col_cancel = st.columns(2)
            with col_submit:
                submit = st.form_submit_button("💾 Update", width="stretch")
            with col_cancel:
                cancel = st.form_submit_button("❌ Cancel", width="stretch")

            if cancel:
                del st.session_state.editing_index
                st.rerun()

            if submit and saving_name:
                start_dt = datetime.combine(start_date, datetime.min.time())
                maturity_date = start_dt + relativedelta(years=duration_years, months=duration_months, days=duration_days)

                # Total contributions over full months
                total_months = months_between(start_dt, maturity_date)
                total_contrib = monthly_contribution * total_months

                # Calculate maturity value based on payout type
                if has_payout:
                    # Non-cumulative FD - interest is paid out periodically
                    years = (maturity_date - start_dt).days / 365.25
                    total_interest = principal * (rate / 100) * years
                    maturity_value = principal + total_contrib  # Principal + contributions returned at maturity
                else:
                    # Cumulative FD - interest compounds
                    maturity_value = fv_with_monthly_contrib(
                        principal=principal,
                        rate=rate/100,
                        start_dt=start_dt,
                        end_dt=maturity_date,
                        compounding_frequency=compounding,
                        monthly_contribution=monthly_contribution
                    )
                    total_interest = maturity_value - principal - total_contrib

                # Update saving in database
                saving_data = {
                    'name': saving_name,
                    'type': saving_type,
                    'principal': principal,
                    'rate': rate / 100,
                    'start_date': start_dt,
                    'maturity_date': maturity_date,
                    'compounding_frequency': 0 if has_payout else compounding,
                    'monthly_contribution': monthly_contribution,
                    'total_contributions': total_contrib,
                    'maturity_value': maturity_value,
                    'interest_earned': total_interest,
                    'has_payout': has_payout,
                    'payout_frequency': payout_frequency if has_payout else 0,
                    'notes': notes,
                    'color': editing_saving['color'],  # Keep existing color
                    'color_index': editing_saving['color_index'],
                    'currency': 'INR'
                }

                # Update in database
                if 'id' in editing_saving:
                    db.update_saving(editing_saving['id'], saving_data)
                    st.success(f"✅ Updated {saving_name}!")

                    # Clear editing state and reload
                    del st.session_state.editing_index
                    st.session_state.force_reload = True
                    st.rerun()
    else:
        # Add mode - check which mode is selected
        if entry_mode == "Calculator":
            # Calculator mode - existing functionality
            st.header("➕ Add New Saving (Calculator)")

            saving_name = st.text_input("Name", placeholder="e.g., Fixed Deposit 2025", key="calc_name")

            saving_type = st.selectbox("Type", ["Fixed Deposit", "Recurring Deposit", "Retirement Account", "Other"], key="calc_type")

            principal = st.number_input(f"Principal Amount ({CURRENCY_SYMBOL})", min_value=0.0, value=10000.0, step=1000.0, key="calc_principal")
            rate = st.number_input("Annual Interest Rate (%)", min_value=0.0, max_value=100.0, value=6.5, step=0.1, key="calc_rate")

            start_date = st.date_input("Start Date", value=datetime.now(), min_value=None, max_value=None, key="calc_start")

            st.markdown("**Duration:**")
            col1, col2, col3 = st.columns(3)
            with col1:
                duration_years = st.number_input("Years", min_value=0, max_value=50, value=2, step=1, key="calc_years")
            with col2:
                duration_months = st.number_input("Months", min_value=0, max_value=11, value=0, step=1, key="calc_months")
            with col3:
                duration_days = st.number_input("Days", min_value=0, max_value=31, value=0, step=1, key="calc_days")

            # Interest payout option
            has_payout = st.checkbox(
                "Interest Payout (Non-cumulative FD)",
                value=False,
                help="Check if interest is paid out periodically instead of being compounded",
                key="calc_payout"
            )

            # Show compounding frequency only for cumulative FDs
            compounding = 1
            payout_frequency = 1
            if has_payout:
                st.info("ℹ️ For payout FDs, maturity value = Principal + Contributions (interest paid separately)")
                payout_frequency = st.selectbox(
                    "Payout Frequency",
                    options=[1, 2, 4, 12],
                    format_func=lambda x: {1: "Annually", 2: "Semi-annually", 4: "Quarterly", 12: "Monthly"}[x],
                    index=2,  # Default to Quarterly
                    help="How often interest is paid out",
                    key="calc_payout_freq"
                )
            else:
                compounding = st.selectbox(
                    "Compounding Frequency",
                    options=[1, 2, 4, 12],
                    format_func=lambda x: {1: "Annually", 2: "Semi-annually", 4: "Quarterly", 12: "Monthly"}[x],
                    index=0,
                    help="How often interest is compounded",
                    key="calc_compounding"
                )

            monthly_contribution = 0.0
            if saving_type == "Recurring Deposit":
                monthly_contribution = st.number_input(
                    f"Monthly Contribution ({CURRENCY_SYMBOL})", min_value=0.0, value=0.0, step=500.0,
                    help="Additional amount you add every month",
                    key="calc_monthly"
                )

            # Notes field
            notes = st.text_area(
                "Notes (Optional)",
                max_chars=500,
                height=80,
                help="Add any notes or comments about this saving",
                key="calc_notes"
            )

            submit = st.button("Add Saving", type="primary", use_container_width=True, key="calc_submit")

            if submit and saving_name:
                start_dt = datetime.combine(start_date, datetime.min.time())
                maturity_date = start_dt + relativedelta(years=duration_years, months=duration_months, days=duration_days)

                # Total contributions over full months
                total_months = months_between(start_dt, maturity_date)
                total_contrib = monthly_contribution * total_months

                # Calculate maturity value based on payout type
                if has_payout:
                    # Non-cumulative FD - interest is paid out periodically, principal remains same
                    # Calculate total interest that will be paid out
                    years = (maturity_date - start_dt).days / 365.25
                    total_interest = principal * (rate / 100) * years
                    maturity_value = principal + total_contrib  # Principal + contributions returned at maturity
                    # Note: total_interest represents payouts received during the period
                else:
                    # Cumulative FD - interest compounds
                    maturity_value = fv_with_monthly_contrib(
                        principal=principal,
                        rate=rate/100,
                        start_dt=start_dt,
                        end_dt=maturity_date,
                        compounding_frequency=compounding,
                        monthly_contribution=monthly_contribution
                    )
                    total_interest = maturity_value - principal - total_contrib

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
                    'compounding_frequency': 0 if has_payout else compounding,
                    'monthly_contribution': monthly_contribution,
                    'total_contributions': total_contrib,
                    'maturity_value': maturity_value,
                    'interest_earned': total_interest,
                    'has_payout': has_payout,
                    'payout_frequency': payout_frequency if has_payout else 0,
                    'notes': notes,
                    'color': assigned_color,
                    'color_index': color_index,
                    'currency': 'INR'  # Always INR
                }

                saving_id = db.add_saving(saving_data)
                st.success(f"✅ Added {saving_name}!")

                # Reload from database
                st.session_state.force_reload = True
                st.rerun()

        else:
            # Manual mode - direct input of all values
            st.header("➕ Add New Saving (Manual)")

            saving_name = st.text_input("Name", placeholder="e.g., Fixed Deposit 2025", key="manual_name")

            saving_type = st.selectbox("Type", ["Fixed Deposit", "Recurring Deposit", "Retirement Account", "Other"], key="manual_type")

            # Manual inputs
            principal = st.number_input(f"Principal Amount ({CURRENCY_SYMBOL})", min_value=0.0, value=10000.0, step=1000.0, key="manual_principal")

            start_date = st.date_input("Start Date", value=datetime.now(), min_value=None, max_value=None, key="manual_start")
            maturity_date_input = st.date_input("Maturity Date", value=datetime.now() + relativedelta(years=2), min_value=None, max_value=None, key="manual_maturity")

            maturity_value = st.number_input(
                f"Maturity Value ({CURRENCY_SYMBOL})",
                min_value=0.0,
                value=12000.0,
                step=1000.0,
                help="Total amount you'll receive at maturity (principal only for payout FDs)",
                key="manual_maturity_value"
            )

            # Interest payout option
            has_payout = st.checkbox(
                "Interest Payout (Non-cumulative FD)",
                value=False,
                help="Check if interest is paid out periodically instead of being compounded",
                key="manual_payout"
            )

            # Show compounding frequency only for cumulative FDs, payout frequency for payout FDs
            total_interest_payout = 0.0
            payout_frequency = 1
            compounding = 1
            if has_payout:
                total_interest_payout = st.number_input(
                    f"Total Interest Paid Out ({CURRENCY_SYMBOL})",
                    min_value=0.0,
                    value=0.0,
                    step=100.0,
                    help="Total interest you received as payouts during the period",
                    key="manual_interest_payout"
                )

                payout_frequency = st.selectbox(
                    "Payout Frequency",
                    options=[1, 2, 4, 12],
                    format_func=lambda x: {1: "Annually", 2: "Semi-annually", 4: "Quarterly", 12: "Monthly"}[x],
                    index=2,  # Default to Quarterly
                    help="How often interest was paid out",
                    key="manual_payout_freq"
                )
            else:
                compounding = st.selectbox(
                    "Compounding Frequency",
                    options=[1, 2, 4, 12],
                    format_func=lambda x: {1: "Annually", 2: "Semi-annually", 4: "Quarterly", 12: "Monthly"}[x],
                    index=0,
                    help="How often interest is compounded",
                    key="manual_compounding"
                )

            # Optional fields
            with st.expander("📝 Optional Details", expanded=False):
                rate = st.number_input(
                    "Interest Rate (%) - Optional",
                    min_value=0.0,
                    max_value=100.0,
                    value=0.0,
                    step=0.1,
                    help="For display purposes only",
                    key="manual_rate"
                )

                monthly_contribution = st.number_input(
                    f"Monthly Contribution ({CURRENCY_SYMBOL}) - Optional",
                    min_value=0.0,
                    value=0.0,
                    step=500.0,
                    help="For display purposes only",
                    key="manual_monthly"
                )

            # Notes field
            notes = st.text_area(
                "Notes (Optional)",
                max_chars=500,
                height=80,
                help="Add any notes or comments about this saving",
                key="manual_notes"
            )

            submit = st.button("Add Saving", type="primary", use_container_width=True, key="manual_submit")

            if submit and saving_name:
                start_dt = datetime.combine(start_date, datetime.min.time())
                maturity_dt = datetime.combine(maturity_date_input, datetime.min.time())

                # Validate that maturity is after start
                if maturity_dt <= start_dt:
                    st.error("❌ Maturity date must be after start date!")
                else:
                    # Calculate interest earned and total contributions
                    total_months = months_between(start_dt, maturity_dt)
                    total_contrib = monthly_contribution * total_months

                    # Calculate interest based on payout type
                    if has_payout:
                        # For payout FDs, interest_earned is the total interest paid out
                        interest_earned = total_interest_payout
                    else:
                        # For cumulative FDs, calculate from maturity value
                        interest_earned = maturity_value - principal - total_contrib

                    # Assign color based on current index
                    color_index = len(st.session_state.savings_list)
                    assigned_color = get_color_for_saving(color_index)

                    # Save to database with manual values
                    saving_data = {
                        'name': saving_name,
                        'type': saving_type,
                        'principal': principal,
                        'rate': rate / 100 if rate > 0 else 0.0,  # Convert to decimal
                        'start_date': start_dt,
                        'maturity_date': maturity_dt,
                        'compounding_frequency': 0 if has_payout else compounding,
                        'monthly_contribution': monthly_contribution,
                        'total_contributions': total_contrib,
                        'maturity_value': maturity_value,
                        'interest_earned': interest_earned,
                        'has_payout': has_payout,
                        'payout_frequency': payout_frequency if has_payout else 0,
                        'notes': notes,
                        'color': assigned_color,
                        'color_index': color_index,
                        'currency': 'INR'
                    }

                    saving_id = db.add_saving(saving_data)
                    st.success(f"✅ Added {saving_name}!")

                    # Reload from database
                    st.session_state.force_reload = True
                    st.rerun()

# Main content
if st.session_state.savings_list:
    st.markdown("---")

    # Summary metrics
    st.markdown("### 📊 Portfolio Summary")

    # Calculate totals
    total_principal = sum(s['principal'] for s in st.session_state.savings_list)
    total_maturity = sum(s['maturity_value'] for s in st.session_state.savings_list)
    total_contributions = sum(s.get('total_contributions', 0.0) for s in st.session_state.savings_list)
    total_monthly_contrib = sum(s.get('monthly_contribution', 0.0) for s in st.session_state.savings_list)
    # Use interest_earned from each saving (handles both cumulative and payout FDs correctly)
    total_interest = sum(s.get('interest_earned', 0.0) for s in st.session_state.savings_list)
    avg_return = (total_interest / total_principal * 100) if total_principal > 0 else 0
    num_savings = len(st.session_state.savings_list)

    # Maturities in next 12 months
    next_12m = datetime.now() + relativedelta(years=1)
    maturities_12m = sum(s['maturity_value'] for s in st.session_state.savings_list if s['maturity_date'] <= next_12m)

    col1, col2, col3, col4, col5, col6, col7, col8 = st.columns(8)
    col1.metric("Total Invested", format_currency_short(total_principal))
    col2.metric("Monthly Contrib.", format_currency_short(total_monthly_contrib))
    col3.metric("Total Contributions", format_currency_short(total_contributions))
    col4.metric("Projected Value", format_currency_short(total_maturity))
    col5.metric("Total Interest", format_currency_short(total_interest))
    col6.metric("Avg. Return", f"{avg_return:.1f}%")
    col7.metric("12-mo Maturities", format_currency_short(maturities_12m))
    col8.metric("# Savings", f"{num_savings}")

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
            col1.metric(
                "Next Maturity",
                f"{next_maturity['name'][:15]}...",
                f"{days_until} days | {format_currency_short(next_maturity['maturity_value'])}"
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
        col3.metric(
            "Highest Interest",
            f"{highest_interest['name'][:15]}...",
            format_currency_short(highest_interest['interest_earned'])
        )

    with col4:
        # Weighted average rate
        total_weighted = sum(s['principal'] * s['rate'] for s in st.session_state.savings_list)
        weighted_avg_rate = (total_weighted / total_principal * 100) if total_principal > 0 else 0
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
                              'Value: ₹%{y:,.2f}<br>' +
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
                text_labels.append(f'₹{df_timeline["Total"].iloc[i]:,.0f}')
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
                          'Value: ₹%{y:,.2f}<br>' +
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
                                  f'Final Value: ₹{saving["maturity_value"]:,.2f}<br>' +
                                  f'Interest Earned: ₹{saving["interest_earned"]:,.2f}<br>' +
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

        # Add yellow dotted line for today's date
        today = datetime.now()
        shapes.append(dict(
            type='line',
            x0=today,
            x1=today,
            y0=0,
            y1=1,
            yref='paper',
            line=dict(
                color='#fbbf24',  # Yellow/amber color
                width=2,
                dash='dot'
            ),
            opacity=0.8
        ))

        annotations.append(dict(
            x=today,
            y=1.05,
            yref='paper',
            text="Today",
            showarrow=False,
            yanchor='bottom',
            font=dict(size=10, color='#fbbf24'),
            bgcolor='rgba(251, 191, 36, 0.2)',
            bordercolor='#fbbf24',
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
                title='Value (₹)',
                showgrid=True,
                gridwidth=1,
                gridcolor='rgba(128,128,128,0.2)',
                zeroline=False,
                tickformat=',.0f',
                tickprefix='₹'
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
            text=[f'₹{p:,.0f}' for p in principals],
            textposition='inside',
            textfont=dict(size=9, color='white'),
            hovertemplate='<b>%{x}</b><br>Principal: ₹%{y:,.2f}<extra></extra>'
        ))

        fig_bars.add_trace(go.Bar(
            name='Interest Earned',
            x=savings_names,
            y=interests,
            marker_color=colors_rgba,  # Use rgba with opacity
            text=[f'₹{i:,.0f}' if i > 0 else '' for i in interests],
            textposition='inside',
            textfont=dict(size=9, color='white'),
            hovertemplate='<b>%{x}</b><br>Interest: ₹%{y:,.2f}<extra></extra>'
        ))

        # Add total value labels on top of stacked bars
        totals = [p + i for p, i in zip(principals, interests)]
        fig_bars.add_trace(go.Scatter(
            x=savings_names,
            y=totals,
            mode='text',
            text=[f'₹{t:,.0f}' for t in totals],
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
                title='Amount (₹)',
                showgrid=True,
                gridwidth=1,
                gridcolor='rgba(128,128,128,0.2)',
                tickformat=',.0f',
                tickprefix='₹'
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
                'Start Month': s['start_date'].strftime('%Y-%m'),
                'Start Date': s['start_date'],
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

            # Add timeline lines from start to maturity for each saving
            # These lines rise from 0, plateau at total value height, then drop back to 0
            for _, row in ladder_df.iterrows():
                rgb = row['Color']['rgb']
                line_color = f'rgba({rgb[0]}, {rgb[1]}, {rgb[2]}, 0.8)'
                principal_height = row['Principal']
                total_height = row['Principal'] + row['Interest']

                # Create a path: start at 0, rise to total height, maintain, then drop to 0
                x_points = [
                    row['Start Month'],      # Start point
                    row['Start Month'],      # Rise point (same x, creates vertical rise)
                    row['Maturity Month'],   # Plateau end (same x as maturity)
                    row['Maturity Month']    # Drop point (same x, creates vertical drop)
                ]
                y_points = [
                    0,                       # Start at baseline
                    total_height,            # Rise to total value (principal + interest)
                    total_height,            # Maintain height
                    0                        # Drop back to baseline
                ]

                # First, add principal layer (gray fill) - drawn first so it's at the bottom
                principal_x_points = [
                    row['Start Month'],
                    row['Start Month'],
                    row['Maturity Month'],
                    row['Maturity Month']
                ]
                principal_y_points = [
                    0,
                    principal_height,
                    principal_height,
                    0
                ]

                ladder_fig.add_trace(go.Scatter(
                    x=principal_x_points,
                    y=principal_y_points,
                    mode='lines',
                    line=dict(color='rgba(180,180,180,0.8)', width=2, dash='solid'),
                    name=f'{row["Saving"]} (Principal)',
                    showlegend=False,
                    hovertemplate=f'<b>{row["Saving"]} Principal</b><br>₹{principal_height:,.0f}<extra></extra>',
                    fill='tozeroy',
                    fillcolor='rgba(120,120,120,0.5)'  # Darker gray fill with 50% opacity for principal
                ))

                # Then, add the interest layer (colored fill) - on top of principal
                # This only fills the area ABOVE the principal
                interest_x_points = [
                    row['Start Month'],
                    row['Start Month'],
                    row['Maturity Month'],
                    row['Maturity Month']
                ]
                interest_y_points = [
                    principal_height,        # Start from principal height
                    total_height,            # Rise to total value
                    total_height,            # Maintain height
                    principal_height         # Drop back to principal height
                ]

                ladder_fig.add_trace(go.Scatter(
                    x=interest_x_points,
                    y=interest_y_points,
                    mode='lines',
                    line=dict(color=line_color, width=2, shape='linear'),
                    name=f'{row["Saving"]} (Interest)',
                    showlegend=False,
                    hovertemplate=f'<b>{row["Saving"]} Interest</b><br>₹{row["Interest"]:,.0f}<extra></extra>',
                    fill='tonexty',  # Fill to next y (fills the interest portion)
                    fillcolor=f'rgba({rgb[0]}, {rgb[1]}, {rgb[2]}, 0.4)'  # Colored fill for interest
                ))

                # Add the main outline with markers
                ladder_fig.add_trace(go.Scatter(
                    x=x_points,
                    y=y_points,
                    mode='lines+markers',
                    line=dict(color=line_color, width=3, shape='linear'),
                    marker=dict(
                        size=[10, 0, 0, 14],  # Show markers only at start and end
                        color=line_color,
                        symbol=['circle', 'circle', 'circle', 'diamond']
                    ),
                    name=row['Saving'],
                    showlegend=True,
                    hovertemplate=f'<b>{row["Saving"]}</b><br>' +
                                  f'Start: {row["Start Date"].strftime("%d-%b-%Y")}<br>' +
                                  f'Maturity: {row["Maturity Date"].strftime("%d-%b-%Y")}<br>' +
                                  f'Principal: ₹{row["Principal"]:,.0f}<br>' +
                                  f'Interest: ₹{row["Interest"]:,.0f}<br>' +
                                  f'Total: ₹{total_height:,.0f}<br>' +
                                  '<extra></extra>'
                ))

                # Add separate text annotations for total value labels at maturity
                ladder_fig.add_trace(go.Scatter(
                    x=[row['Maturity Month']],
                    y=[total_height],
                    mode='text',
                    text=[f'₹{total_height:,.0f}'],
                    textposition='top left',  # Position text above and to the left (ends at maturity point)
                    textfont=dict(size=11, color=line_color),
                    showlegend=False,
                    hoverinfo='skip'
                ))

            # Calculate max value for y-axis range with padding
            max_value = ladder_df.apply(lambda row: row['Principal'] + row['Interest'], axis=1).max()
            y_max = max_value * 1.3  # Add 30% padding at top for labels

            # Add yellow dotted line for today's date
            today_month = datetime.now().strftime('%Y-%m')
            ladder_fig.add_shape(
                type='line',
                x0=today_month,
                x1=today_month,
                y0=0,
                y1=y_max,
                line=dict(
                    color='#fbbf24',  # Yellow/amber color
                    width=2,
                    dash='dot'
                ),
                opacity=0.8
            )

            ladder_fig.add_annotation(
                x=today_month,
                y=y_max,
                text="Today",
                showarrow=False,
                yanchor='bottom',
                font=dict(size=10, color='#fbbf24'),
                bgcolor='rgba(251, 191, 36, 0.2)',
                bordercolor='#fbbf24',
                borderwidth=1,
                borderpad=4
            )

            ladder_fig.update_layout(
                template='plotly_dark',
                height=350,  # Further increased height
                margin=dict(t=10, b=30, l=10, r=10),  # Reset top margin, use y-axis range instead
                xaxis_title='',
                yaxis=dict(
                    title='Maturing (₹)',
                    tickprefix='₹',
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
        frequency_map = {1: 'Ann.', 2: 'Semi', 4: 'Qtr', 12: 'Mon.'}

        for idx, saving in enumerate(st.session_state.savings_list):
            # Calculate actual duration of the saving (from start to maturity)
            duration_delta = relativedelta(saving['maturity_date'], saving['start_date'])
            duration_str = []
            if duration_delta.years > 0:
                duration_str.append(f"{duration_delta.years}y")
            if duration_delta.months > 0:
                duration_str.append(f"{duration_delta.months}m")
            if duration_delta.days > 0:
                duration_str.append(f"{duration_delta.days}d")
            duration_display = " ".join(duration_str) if duration_str else "0d"

            # Determine payout type and frequency
            has_payout = saving.get('has_payout', False)
            if has_payout:
                payout_freq = saving.get('payout_frequency', 4)
                payout_freq_map = {1: 'Annual', 2: 'Semi-annual', 4: 'Quarterly', 12: 'Monthly'}
                payout_type = f"Payout ({payout_freq_map.get(payout_freq, 'Quarterly')})"
                # For payout FDs, show payout frequency
                frequency_display = frequency_map.get(payout_freq, 'Qtr')
            else:
                payout_type = "Cumulative"
                # For cumulative FDs, show compounding frequency
                frequency_display = frequency_map.get(saving['compounding_frequency'], 'Ann.')

            # Get notes (truncate if too long for display)
            notes = saving.get('notes', '')
            notes_display = notes[:50] + '...' if len(notes) > 50 else notes

            table_data.append({
                'Name': saving['name'],
                'Type': saving['type'],
                'Payout Type': payout_type,
                'Principal': format_currency_short(saving['principal']),
                'Contrib.': format_currency_short(saving.get('total_contributions', 0.0)),
                'Rate': f"{saving['rate']*100:.2f}%",
                'Freq.': frequency_display,
                'Start': saving['start_date'].strftime('%Y-%m-%d'),
                'Maturity': saving['maturity_date'].strftime('%Y-%m-%d'),
                'Duration': duration_display,
                'Final Value': format_currency_short(saving['maturity_value']),
                'Interest': format_currency_short(saving['interest_earned']),
                'Notes': notes_display,
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

            # Edit or Delete selected rows
            if event.selection.rows:
                if len(event.selection.rows) == 1:
                    # Single selection - allow edit or delete
                    col1, col2, col3 = st.columns([3, 1, 1])
                    with col1:
                        st.info(f"✓ Selected 1 saving")
                    with col2:
                        if st.button("✏️ Edit", type="primary", width="stretch"):
                            st.session_state.editing_index = event.selection.rows[0]
                            st.rerun()
                    with col3:
                        if st.button("🗑️ Delete", type="secondary", width="stretch"):
                            # Delete from database
                            saving_to_delete = st.session_state.savings_list[event.selection.rows[0]]
                            if 'id' in saving_to_delete:
                                db.delete_saving(saving_to_delete['id'])

                            # Reload from database
                            st.session_state.force_reload = True
                            st.success(f"✅ Deleted saving")
                            st.rerun()
                else:
                    # Multiple selection - only allow delete
                    col1, col2 = st.columns([4, 1])
                    with col1:
                        st.info(f"✓ Selected {len(event.selection.rows)} savings")
                    with col2:
                        if st.button("🗑️ Delete Selected", type="secondary", width="stretch"):
                            # Delete from database
                            for idx in sorted(event.selection.rows, reverse=True):
                                saving_to_delete = st.session_state.savings_list[idx]
                                if 'id' in saving_to_delete:
                                    db.delete_saving(saving_to_delete['id'])

                            # Reload from database
                            st.session_state.force_reload = True
                            st.success(f"✅ Deleted {len(event.selection.rows)} savings")
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
        - Principal: ₹1,00,000
        - Interest Rate: 6.5% annually
        - Duration: 2 years
        - Expected Value: ₹1,13,422
        - Interest Earned: ₹13,422
        """)
