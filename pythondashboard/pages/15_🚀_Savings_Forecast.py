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

# Initialize session state for savings
if 'savings_list' not in st.session_state:
    st.session_state.savings_list = []

# Color palette for different savings (vibrant, modern colors)
COLOR_PALETTE = [
    {'name': 'Ocean Blue', 'hex': '#00D4FF', 'rgb': [0, 212, 255]},
    {'name': 'Neon Purple', 'hex': '#B24BF3', 'rgb': [178, 75, 243]},
    {'name': 'Sunset Orange', 'hex': '#FF6B35', 'rgb': [255, 107, 53]},
    {'name': 'Electric Green', 'hex': '#39FF14', 'rgb': [57, 255, 20]},
    {'name': 'Hot Pink', 'hex': '#FF1493', 'rgb': [255, 20, 147]},
    {'name': 'Golden Yellow', 'hex': '#FFD700', 'rgb': [255, 215, 0]},
    {'name': 'Aqua Mint', 'hex': '#7FFFD4', 'rgb': [127, 255, 212]},
    {'name': 'Ruby Red', 'hex': '#FF073A', 'rgb': [255, 7, 58]},
    {'name': 'Lime Zest', 'hex': '#CCFF00', 'rgb': [204, 255, 0]},
    {'name': 'Lavender', 'hex': '#E6E6FA', 'rgb': [230, 230, 250]}
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

def generate_timeline_data(savings_list):
    """Generate timeline data points for visualization"""
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
            # Calculate elapsed time
            elapsed = (current_date - today).days / 365.25
            total_years = (saving['maturity_date'] - today).days / 365.25

            if current_date <= saving['maturity_date']:
                # Calculate current value
                current_value = calculate_compound_interest(
                    saving['principal'],
                    saving['rate'],
                    min(elapsed, total_years),
                    saving['compounding_frequency']
                )
            else:
                # Matured - use final value
                current_value = saving['maturity_value']

            total += current_value
            breakdown.append({
                'name': saving['name'],
                'value': round(current_value, 2)
            })

        timeline_points.append({
            'date': current_date,
            'total': round(total, 2),
            'breakdown': breakdown
        })

    return timeline_points

# Title
st.title("🚀 Savings Forecast & Roadmap")

st.markdown("""
Visualize your savings growth over time with interactive 3D timeline.
Add your fixed deposits, recurring deposits, retirement accounts, and other savings to see projected outcomes.
""")

# Sidebar for adding savings
with st.sidebar:
    st.header("➕ Add New Saving")

    with st.form("add_saving_form", clear_on_submit=True):
        saving_name = st.text_input("Name", placeholder="e.g., Fixed Deposit 2025")
        saving_type = st.selectbox("Type", ["Fixed Deposit", "Recurring Deposit", "Retirement Account", "Other"])
        principal = st.number_input("Principal Amount (€)", min_value=0.0, value=1000.0, step=100.0)
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

        submit = st.form_submit_button("Add Saving", width="stretch")

        if submit and saving_name:
            start_dt = datetime.combine(start_date, datetime.min.time())
            maturity_date = start_dt + relativedelta(years=int(years), months=int((years % 1) * 12))
            maturity_value = calculate_compound_interest(principal, rate/100, years, compounding)

            # Assign color based on current index
            color_index = len(st.session_state.savings_list)
            assigned_color = get_color_for_saving(color_index)

            st.session_state.savings_list.append({
                'name': saving_name,
                'type': saving_type,
                'principal': principal,
                'rate': rate / 100,  # Convert to decimal
                'start_date': start_dt,
                'maturity_date': maturity_date,
                'compounding_frequency': compounding,
                'maturity_value': maturity_value,
                'interest_earned': maturity_value - principal,
                'color': assigned_color
            })
            st.success(f"Added {saving_name}!")
            st.rerun()

# Main content
if st.session_state.savings_list:
    # Summary metrics
    st.subheader("📊 Portfolio Summary")

    total_principal = sum(s['principal'] for s in st.session_state.savings_list)
    total_maturity = sum(s['maturity_value'] for s in st.session_state.savings_list)
    total_interest = total_maturity - total_principal
    avg_return = (total_interest / total_principal * 100) if total_principal > 0 else 0

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Invested", f"€{total_principal:,.2f}")
    col2.metric("Projected Value", f"€{total_maturity:,.2f}")
    col3.metric("Total Interest", f"€{total_interest:,.2f}")
    col4.metric("Avg. Return", f"{avg_return:.2f}%")

    st.divider()

    # Generate timeline data
    timeline_data = generate_timeline_data(st.session_state.savings_list)

    # Create DataFrame for the projection chart
    chart_data = []
    for point in timeline_data:
        row = {'Date': point['date'], 'Total': point['total']}
        for item in point['breakdown']:
            row[item['name']] = item['value']
        chart_data.append(row)

    df_timeline = pd.DataFrame(chart_data)

    # Create two columns for side-by-side charts
    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("📈 Savings Growth Projection")

        # Create the main projection chart with Plotly
        fig = go.Figure()

        # Add stacked area chart for each saving
        for idx, saving in enumerate(st.session_state.savings_list):
            color_obj = saving.get('color', get_color_for_saving(idx))

            fig.add_trace(go.Scatter(
                x=df_timeline['Date'],
                y=df_timeline[saving['name']],
                name=saving['name'],
                mode='lines',
                line=dict(width=0.5, color=color_obj['hex']),
                stackgroup='one',
                fillcolor=color_obj['hex'],
                hovertemplate='<b>%{fullData.name}</b><br>' +
                              'Date: %{x|%Y-%m-%d}<br>' +
                              'Value: €%{y:,.2f}<br>' +
                              '<extra></extra>'
            ))

        # Add total portfolio line (bold, on top)
        fig.add_trace(go.Scatter(
            x=df_timeline['Date'],
            y=df_timeline['Total'],
            name='Total Portfolio',
            mode='lines',
            line=dict(width=3, color='#FFD700', dash='solid'),
            hovertemplate='<b>Total Portfolio</b><br>' +
                          'Date: %{x|%Y-%m-%d}<br>' +
                          'Value: €%{y:,.2f}<br>' +
                          '<extra></extra>'
        ))

        # Add confidence bands (±5% for illustration)
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
            fillcolor='rgba(255, 215, 0, 0.1)',
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
            height=600,
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
        st.subheader("💎 Maturity Values")

        fig_bars = go.Figure()

        savings_names = [s['name'] for s in st.session_state.savings_list]
        principals = [s['principal'] for s in st.session_state.savings_list]
        interests = [s['interest_earned'] for s in st.session_state.savings_list]
        colors = [s.get('color', get_color_for_saving(i))['hex'] for i, s in enumerate(st.session_state.savings_list)]

        fig_bars.add_trace(go.Bar(
            name='Principal',
            x=savings_names,
            y=principals,
            marker_color='rgba(100,100,100,0.6)',
            hovertemplate='<b>%{x}</b><br>Principal: €%{y:,.2f}<extra></extra>'
        ))

        fig_bars.add_trace(go.Bar(
            name='Interest Earned',
            x=savings_names,
            y=interests,
            marker_color=colors,
            hovertemplate='<b>%{x}</b><br>Interest: €%{y:,.2f}<extra></extra>'
        ))

        fig_bars.update_layout(
            barmode='stack',
            template='plotly_dark',
            height=600,
            margin=dict(l=10, r=10, t=10, b=10),
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

    st.divider()

    # Savings list table
    st.subheader("📋 Your Savings")

    # Prepare data for table
    table_data = []
    compounding_map = {1: 'Annually', 2: 'Semi-annually', 4: 'Quarterly', 12: 'Monthly'}

    for idx, saving in enumerate(st.session_state.savings_list):
        color = saving.get('color', get_color_for_saving(idx))
        years_from_now = (saving['maturity_date'] - datetime.now()).days / 365.25

        table_data.append({
            'Color': color['name'],
            'Name': saving['name'],
            'Type': saving['type'],
            'Principal': f"€{saving['principal']:,.2f}",
            'Rate': f"{saving['rate']*100:.2f}%",
            'Compounding': compounding_map[saving['compounding_frequency']],
            'Start Date': saving['start_date'].strftime('%Y-%m-%d'),
            'Maturity Date': saving['maturity_date'].strftime('%Y-%m-%d'),
            'Years': f"{years_from_now:.1f}y",
            'Maturity Value': f"€{saving['maturity_value']:,.2f}",
            'Interest': f"€{saving['interest_earned']:,.2f}",
            'Delete': idx
        })

    # Display table with built-in row selection
    if table_data:
        df = pd.DataFrame(table_data)

        # Display dataframe with row selection
        event = st.dataframe(
            df.drop(columns=['Delete']),
            width="stretch",
            height=min(400, (len(table_data) + 1) * 35 + 3),
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
                    # Sort indices in reverse to delete from end to start
                    for idx in sorted(event.selection.rows, reverse=True):
                        st.session_state.savings_list.pop(idx)
                    st.rerun()

        st.divider()

        # Clear all button
        if st.button("🗑️ Clear All Savings", type="secondary"):
            st.session_state.savings_list = []
            st.rerun()

else:
    # Empty state
    st.info("👈 Add your first saving using the form in the sidebar to visualize your savings growth!")

    st.markdown("""
    ### How to use:

    1. **Add Savings**: Use the sidebar form to add savings accounts (Fixed Deposits, Retirement, etc.)
    2. **Visualize Growth**: See your savings grow over time in an interactive 3D timeline
    3. **Track Maturity**: Golden markers show when each savings matures
    4. **Hover for Details**: Mouse over points to see detailed information

    ### Example:
    - **Principal**: €1,000
    - **Interest Rate**: 3% annually
    - **Duration**: 2 years
    - **Expected Value**: €1,060.90
    """)
