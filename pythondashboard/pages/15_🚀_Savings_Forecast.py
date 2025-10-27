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

        submit = st.form_submit_button("Add Saving", use_container_width=True)

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

    # 2D Roadmap Visualization
    st.subheader("🛣️ Savings Roadmap")
    st.markdown("**Your journey to financial goals**")

    # Generate timeline data
    timeline_data = generate_timeline_data(st.session_state.savings_list)

    # Prepare milestones (years + savings maturity)
    milestones = []

    # Add year milestones
    years_seen = set()
    for point in timeline_data:
        year = point['date'].year
        if year not in years_seen:
            years_seen.add(year)
            milestones.append({
                'date': point['date'],
                'year': year,
                'type': 'year',
                'title': str(year),
                'value': point['total'],
                'description': f"Total Portfolio: €{point['total']:,.0f}"
            })

    # Add savings maturity milestones
    for idx, saving in enumerate(st.session_state.savings_list):
        color = saving.get('color', get_color_for_saving(idx))
        milestones.append({
            'date': saving['maturity_date'],
            'year': saving['maturity_date'].year,
            'type': 'saving',
            'title': saving['name'],
            'value': saving['maturity_value'],
            'description': f"€{saving['maturity_value']:,.0f}",
            'color': color['hex'],
            'saving_data': saving
        })

    # Sort milestones by date
    milestones.sort(key=lambda x: x['date'])

    # Create milestones JSON for JavaScript
    milestones_json = json.dumps(milestones, default=str)

    # 2D Roadmap visualization
    st.components.v1.html(f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{
                margin: 0;
                padding: 0;
                background: linear-gradient(135deg, #0a0a0a 0%, #1a1a2e 100%);
                font-family: 'Segoe UI', Arial, sans-serif;
                overflow: hidden;
            }}
            .roadmap-container {{
                position: relative;
                width: 100%;
                height: 700px;
                overflow: hidden;
                cursor: grab;
            }}
            .roadmap-container:active {{
                cursor: grabbing;
            }}
            .roadmap-content {{
                position: absolute;
                width: 2000px;
                height: 1000px;
                left: 50%;
                top: 50%;
                transform-origin: center center;
            }}
            .zoom-controls {{
                position: absolute;
                top: 20px;
                right: 20px;
                z-index: 100;
                display: flex;
                flex-direction: column;
                gap: 10px;
            }}
            .zoom-btn {{
                width: 50px;
                height: 50px;
                background: rgba(0, 0, 0, 0.8);
                border: 2px solid #FFD700;
                border-radius: 8px;
                color: #FFD700;
                font-size: 24px;
                font-weight: bold;
                cursor: pointer;
                display: flex;
                align-items: center;
                justify-content: center;
                transition: all 0.3s ease;
            }}
            .zoom-btn:hover {{
                background: #FFD700;
                color: #000;
                transform: scale(1.1);
            }}
            .zoom-level {{
                position: absolute;
                bottom: 20px;
                right: 20px;
                background: rgba(0, 0, 0, 0.8);
                color: #FFD700;
                padding: 10px 15px;
                border-radius: 8px;
                font-size: 14px;
                font-weight: bold;
                border: 2px solid #FFD700;
                z-index: 100;
            }}
            .road-path {{
                position: absolute;
                width: 100%;
                height: 100%;
                z-index: 1;
            }}
            .milestone {{
                position: absolute;
                display: flex;
                flex-direction: column;
                align-items: center;
                z-index: 10;
                cursor: pointer;
                transition: transform 0.3s ease;
            }}
            .milestone:hover {{
                transform: scale(1.1);
            }}
            .milestone-marker {{
                width: 80px;
                height: 80px;
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 24px;
                font-weight: bold;
                color: white;
                box-shadow: 0 4px 15px rgba(0,0,0,0.5);
                position: relative;
            }}
            .milestone-marker.year {{
                background: linear-gradient(135deg, #FFD700 0%, #FFA500 100%);
            }}
            .milestone-marker.saving {{
                background: linear-gradient(135deg, var(--color-start) 0%, var(--color-end) 100%);
            }}
            .milestone-label {{
                background: rgba(0,0,0,0.9);
                color: white;
                padding: 12px 20px;
                border-radius: 8px;
                margin-top: 15px;
                text-align: center;
                min-width: 150px;
                box-shadow: 0 4px 12px rgba(0,0,0,0.6);
                border: 2px solid rgba(255,255,255,0.1);
            }}
            .milestone-title {{
                font-size: 18px;
                font-weight: bold;
                margin-bottom: 5px;
            }}
            .milestone-description {{
                font-size: 14px;
                color: #4CAF50;
                font-weight: bold;
            }}
            .road-segment {{
                position: absolute;
                height: 60px;
                background: linear-gradient(180deg, #333 0%, #222 50%, #333 100%);
                border: 2px solid #555;
                border-radius: 30px;
                box-shadow: 0 4px 10px rgba(0,0,0,0.5);
            }}
            .road-stripe {{
                position: absolute;
                height: 4px;
                background: #FFD700;
                top: 50%;
                transform: translateY(-50%);
                border-radius: 2px;
            }}
        </style>
    </head>
    <body>
        <div class="roadmap-container" id="roadmap">
            <div class="roadmap-content" id="content">
                <svg class="road-path" id="road-svg"></svg>
            </div>
        </div>

        <div class="zoom-controls">
            <button class="zoom-btn" id="zoom-in">+</button>
            <button class="zoom-btn" id="zoom-out">−</button>
            <button class="zoom-btn" id="zoom-reset" style="font-size: 18px;">⟲</button>
        </div>
        <div class="zoom-level" id="zoom-level">100%</div>

        <script>
            const milestones = {milestones_json};
            console.log('Milestones:', milestones);

            const container = document.getElementById('roadmap');
            const content = document.getElementById('content');
            const svg = document.getElementById('road-svg');

            // Zoom and pan state
            const defaultScale = 0.5;  // Start zoomed out to fit everything
            let scale = defaultScale;
            let translateX = 0;
            let translateY = 0;
            let isDragging = false;
            let startX, startY;

            function updateTransform() {{
                content.style.transform = `translate(${{translateX}}px, ${{translateY}}px) translate(-50%, -50%) scale(${{scale}})`;
                document.getElementById('zoom-level').textContent = Math.round(scale * 100) + '%';
            }}

            // Zoom controls
            document.getElementById('zoom-in').addEventListener('click', () => {{
                scale = Math.min(scale * 1.2, 3);
                updateTransform();
            }});

            document.getElementById('zoom-out').addEventListener('click', () => {{
                scale = Math.max(scale / 1.2, 0.3);
                updateTransform();
            }});

            document.getElementById('zoom-reset').addEventListener('click', () => {{
                scale = defaultScale;
                translateX = 0;
                translateY = 0;
                updateTransform();
            }});

            // Mouse wheel zoom
            container.addEventListener('wheel', (e) => {{
                e.preventDefault();
                const delta = e.deltaY > 0 ? 0.9 : 1.1;
                scale = Math.max(0.3, Math.min(3, scale * delta));
                updateTransform();
            }});

            // Pan (drag)
            container.addEventListener('mousedown', (e) => {{
                isDragging = true;
                startX = e.clientX - translateX;
                startY = e.clientY - translateY;
            }});

            container.addEventListener('mousemove', (e) => {{
                if (isDragging) {{
                    translateX = e.clientX - startX;
                    translateY = e.clientY - startY;
                    updateTransform();
                }}
            }});

            container.addEventListener('mouseup', () => {{
                isDragging = false;
            }});

            container.addEventListener('mouseleave', () => {{
                isDragging = false;
            }});

            // Calculate road path (S-curve)
            const contentWidth = 1800;
            const contentHeight = 600;
            const roadStartX = 100;
            const roadStartY = contentHeight / 2;

            // Calculate initial positions for all milestones
            const milestonePositions = milestones.map((milestone, index) => {{
                const progress = index / (milestones.length - 1);
                const x = roadStartX + progress * contentWidth;
                const y = roadStartY + Math.sin(progress * Math.PI * 2) * 150;
                return {{ x, y, milestone, index }};
            }});

            // Detect and resolve overlaps
            const minDistance = 200; // Minimum horizontal distance between milestones
            const verticalOffset = 180; // Vertical offset for overlapping milestones

            for (let i = 0; i < milestonePositions.length; i++) {{
                for (let j = i + 1; j < milestonePositions.length; j++) {{
                    const pos1 = milestonePositions[i];
                    const pos2 = milestonePositions[j];

                    const distance = Math.abs(pos2.x - pos1.x);

                    // If milestones are too close horizontally
                    if (distance < minDistance) {{
                        // Alternate above and below the road
                        if (j % 2 === 0) {{
                            pos2.y -= verticalOffset;
                            pos2.offset = 'above';
                        }} else {{
                            pos2.y += verticalOffset;
                            pos2.offset = 'below';
                        }}
                    }}
                }}
            }}

            // Position milestones along curved path
            milestonePositions.forEach(({{ x, y, milestone, index, offset }}) => {{
                // Create milestone element
                const milestoneEl = document.createElement('div');
                milestoneEl.className = 'milestone';
                milestoneEl.style.left = x + 'px';
                milestoneEl.style.top = y + 'px';

                // If milestone is offset, draw a connector line to the road
                if (offset) {{
                    const roadY = roadStartY + Math.sin((index / (milestones.length - 1)) * Math.PI * 2) * 150;
                    const connector = document.createElementNS('http://www.w3.org/2000/svg', 'line');
                    connector.setAttribute('x1', x);
                    connector.setAttribute('y1', y);
                    connector.setAttribute('x2', x);
                    connector.setAttribute('y2', roadY);
                    connector.setAttribute('stroke', milestone.color || '#FFD700');
                    connector.setAttribute('stroke-width', '3');
                    connector.setAttribute('stroke-dasharray', '5,5');
                    connector.setAttribute('opacity', '0.6');
                    svg.appendChild(connector);
                }}

                // Create marker
                const marker = document.createElement('div');
                marker.className = `milestone-marker ${{milestone.type}}`;

                if (milestone.type === 'year') {{
                    marker.textContent = milestone.title;
                }} else {{
                    marker.textContent = (index + 1);
                    const colorHex = milestone.color || '#4CAF50';
                    marker.style.setProperty('--color-start', colorHex);
                    marker.style.setProperty('--color-end', colorHex + 'CC');
                }}

                // Create label
                const label = document.createElement('div');
                label.className = 'milestone-label';
                label.innerHTML = `
                    <div class="milestone-title">${{milestone.title}}</div>
                    <div class="milestone-description">${{milestone.description}}</div>
                `;

                milestoneEl.appendChild(marker);
                milestoneEl.appendChild(label);
                content.appendChild(milestoneEl);
            }});

            // Draw road path using SVG
            let pathData = '';
            for (let i = 0; i < milestones.length - 1; i++) {{
                const progress1 = i / (milestones.length - 1);
                const progress2 = (i + 1) / (milestones.length - 1);

                const x1 = roadStartX + progress1 * contentWidth;
                const y1 = roadStartY + Math.sin(progress1 * Math.PI * 2) * 150;
                const x2 = roadStartX + progress2 * contentWidth;
                const y2 = roadStartY + Math.sin(progress2 * Math.PI * 2) * 150;

                if (i === 0) {{
                    pathData += `M ${{x1}} ${{y1}} `;
                }}

                // Control points for smooth curve
                const cpx1 = x1 + (x2 - x1) * 0.5;
                const cpy1 = y1;
                const cpx2 = x1 + (x2 - x1) * 0.5;
                const cpy2 = y2;

                pathData += `C ${{cpx1}} ${{cpy1}}, ${{cpx2}} ${{cpy2}}, ${{x2}} ${{y2}} `;
            }}

            // Create SVG path for road
            const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
            path.setAttribute('d', pathData);
            path.setAttribute('stroke', '#555');
            path.setAttribute('stroke-width', '60');
            path.setAttribute('fill', 'none');
            path.setAttribute('stroke-linecap', 'round');
            svg.appendChild(path);

            // Create center stripe
            const stripePath = document.createElementNS('http://www.w3.org/2000/svg', 'path');
            stripePath.setAttribute('d', pathData);
            stripePath.setAttribute('stroke', '#FFD700');
            stripePath.setAttribute('stroke-width', '4');
            stripePath.setAttribute('fill', 'none');
            stripePath.setAttribute('stroke-dasharray', '20,15');
            stripePath.setAttribute('stroke-linecap', 'round');
            svg.appendChild(stripePath);

            // Set initial transform
            updateTransform();
        </script>
    </body>
    </html>
    """, height=700)

    st.divider()

    # Savings list table with delete buttons
    st.subheader("📋 Your Savings")

    # Display each saving with a delete button and color indicator
    for idx, saving in enumerate(st.session_state.savings_list):
        # Get or assign color
        color = saving.get('color', get_color_for_saving(idx))
        color_hex = color['hex']

        # Create colored header with emoji
        with st.expander(f"💎 {saving['name']} - €{saving['maturity_value']:,.2f}", expanded=False):
            # Color indicator bar
            st.markdown(f"""
            <div style="
                background: linear-gradient(90deg, {color_hex} 0%, transparent 100%);
                height: 4px;
                border-radius: 2px;
                margin-bottom: 10px;
            "></div>
            """, unsafe_allow_html=True)

            col1, col2, col3 = st.columns([2, 2, 1])

            with col1:
                compounding_map = {1: 'Annually', 2: 'Semi-annually', 4: 'Quarterly', 12: 'Monthly'}
                compounding_text = compounding_map[saving['compounding_frequency']]
                st.markdown(f"""
                <div style="color: {color_hex}; font-weight: bold; margin-bottom: 8px;">
                    ● {color['name']}
                </div>
                **Type:** {saving['type']}
                **Principal:** €{saving['principal']:,.2f}
                **Interest Rate:** {saving['rate']*100:.2f}%
                **Compounding:** {compounding_text}
                """, unsafe_allow_html=True)

            with col2:
                st.markdown(f"""
                **Start Date:** {saving['start_date'].strftime('%Y-%m-%d')}
                **Maturity Date:** {saving['maturity_date'].strftime('%Y-%m-%d')}
                **Maturity Value:** €{saving['maturity_value']:,.2f}
                **Interest Earned:** €{saving['interest_earned']:,.2f}
                """)

            with col3:
                if st.button("🗑️ Delete", key=f"delete_{idx}", type="secondary", use_container_width=True):
                    st.session_state.savings_list.pop(idx)
                    st.rerun()

    st.divider()

    # Clear all button
    col1, col2 = st.columns([3, 1])
    with col2:
        if st.button("🗑️ Clear All Savings", type="secondary", use_container_width=True):
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
