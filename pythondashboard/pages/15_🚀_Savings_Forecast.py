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

    # 3D Roadmap Visualization with Three.js
    st.subheader("🚀 3D Savings Roadmap")
    st.markdown("**Interactive 3D timeline** - Drag to rotate, scroll to zoom, click Reset to return to default view")

    # Generate timeline data
    timeline_data = generate_timeline_data(st.session_state.savings_list)

    # Prepare data for Three.js
    timeline_json = json.dumps([{
        'date': point['date'].strftime('%Y-%m-%d'),
        'year': point['date'].year,
        'month': point['date'].month,
        'total': point['total'],
        'breakdown': point['breakdown']
    } for point in timeline_data])

    savings_json = json.dumps([{
        'name': s['name'],
        'type': s['type'],
        'principal': s['principal'],
        'maturity_value': s['maturity_value'],
        'maturity_date': s['maturity_date'].strftime('%Y-%m-%d'),
        'maturity_year': s['maturity_date'].year,
        'rate': s['rate'] * 100,
        'color': s.get('color', get_color_for_saving(idx))
    } for idx, s in enumerate(st.session_state.savings_list)])

    # Three.js visualization with clear labels and story
    st.components.v1.html(f"""
    <!DOCTYPE html>
    <html>
    <head>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
        <script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js"></script>
        <style>
            body {{ margin: 0; padding: 0; overflow: hidden; background: #0a0a0a; }}
            #canvas-container {{ width: 100%; height: 700px; position: relative; }}
            #reset-button {{
                position: absolute;
                top: 15px;
                right: 15px;
                background: linear-gradient(135deg, #FFD700 0%, #FFA500 100%);
                color: #000;
                border: none;
                padding: 12px 24px;
                border-radius: 8px;
                font-size: 14px;
                font-weight: bold;
                cursor: pointer;
                z-index: 100;
                box-shadow: 0 4px 15px rgba(255, 215, 0, 0.4);
                transition: all 0.3s ease;
            }}
            #reset-button:hover {{
                transform: translateY(-2px);
                box-shadow: 0 6px 20px rgba(255, 215, 0, 0.6);
            }}
            .label-overlay {{
                position: absolute;
                background: rgba(0, 0, 0, 0.85);
                color: #fff;
                padding: 8px 12px;
                border-radius: 6px;
                font-size: 13px;
                font-family: 'Arial', sans-serif;
                pointer-events: none;
                border: 1px solid rgba(255, 255, 255, 0.2);
                backdrop-filter: blur(10px);
            }}
            .year-label {{
                font-size: 20px;
                font-weight: bold;
                color: #FFD700;
                text-shadow: 0 0 10px rgba(255, 215, 0, 0.5);
            }}
            .value-label {{
                font-size: 16px;
                color: #4CAF50;
                font-weight: bold;
            }}
        </style>
    </head>
    <body>
        <div id="canvas-container">
            <canvas id="threejs-canvas"></canvas>
            <button id="reset-button">🔄 Reset View</button>
        </div>

        <script>
            const timelineData = {timeline_json};
            const savingsData = {savings_json};

            // Scene setup
            const canvas = document.getElementById('threejs-canvas');
            const container = document.getElementById('canvas-container');
            const scene = new THREE.Scene();
            scene.background = new THREE.Color(0x0a0a0a);
            scene.fog = new THREE.Fog(0x0a0a0a, 30, 60);

            const camera = new THREE.PerspectiveCamera(
                60,
                container.clientWidth / container.clientHeight,
                0.1,
                1000
            );

            const renderer = new THREE.WebGLRenderer({{ canvas: canvas, antialias: true }});
            renderer.setSize(container.clientWidth, container.clientHeight);

            // Orbit controls
            const controls = new THREE.OrbitControls(camera, renderer.domElement);
            controls.enableDamping = true;
            controls.dampingFactor = 0.08;
            controls.minDistance = 15;
            controls.maxDistance = 60;
            controls.maxPolarAngle = Math.PI / 2 + 0.3;

            // Enhanced lighting
            const ambientLight = new THREE.AmbientLight(0xffffff, 0.5);
            scene.add(ambientLight);

            const keyLight = new THREE.DirectionalLight(0xffffff, 0.8);
            keyLight.position.set(15, 15, 15);
            scene.add(keyLight);

            const fillLight = new THREE.DirectionalLight(0x4488ff, 0.3);
            fillLight.position.set(-10, 10, -10);
            scene.add(fillLight);

            // Create ground grid for reference
            const gridHelper = new THREE.GridHelper(50, 20, 0x444444, 0x222222);
            gridHelper.position.y = -2;
            scene.add(gridHelper);

            // Calculate timeline layout
            const maxValue = Math.max(...timelineData.map(d => d.total));
            const timelineLength = timelineData.length;
            const startYear = timelineData[0].year;
            const endYear = timelineData[timelineData.length - 1].year;
            const yearSpan = endYear - startYear + 1;

            // Create year markers along the timeline
            const yearsToShow = [];
            for (let year = startYear; year <= endYear; year++) {{
                const yearData = timelineData.find(d => d.year === year && d.month === 1) ||
                                timelineData.find(d => d.year === year);
                if (yearData) {{
                    yearsToShow.push({{
                        year: year,
                        index: timelineData.indexOf(yearData),
                        total: yearData.total
                    }});
                }}
            }}

            // Generate 3D roadmap path
            const roadmapPoints = [];
            timelineData.forEach((point, index) => {{
                const progress = index / (timelineLength - 1);
                const x = progress * 40 - 20;  // Spread along X axis
                const y = (point.total / maxValue) * 15;  // Height = value
                const z = Math.sin(progress * Math.PI) * 8;  // Slight curve for depth
                roadmapPoints.push(new THREE.Vector3(x, y, z));
            }});

            // Create the main timeline path (glowing tube)
            const curve = new THREE.CatmullRomCurve3(roadmapPoints);
            const tubeGeometry = new THREE.TubeGeometry(curve, 200, 0.15, 16, false);
            const tubeMaterial = new THREE.MeshPhongMaterial({{
                color: 0xFFD700,
                emissive: 0x886600,
                shininess: 100,
                transparent: true,
                opacity: 0.9
            }});
            const tubeMesh = new THREE.Mesh(tubeGeometry, tubeMaterial);
            scene.add(tubeMesh);

            // Add individual colored paths for each saving
            savingsData.forEach((saving, savingIndex) => {{
                const savingPoints = [];
                timelineData.forEach((point, timeIndex) => {{
                    const progress = timeIndex / (timelineLength - 1);
                    const x = progress * 40 - 20;

                    const breakdownItem = point.breakdown.find(b => b.name === saving.name);
                    const value = breakdownItem ? breakdownItem.value : saving.principal;
                    const y = (value / maxValue) * 15;
                    const z = Math.sin(progress * Math.PI) * 8 + (savingIndex * 0.5);

                    savingPoints.push(new THREE.Vector3(x, y, z));
                }});

                if (savingPoints.length > 1) {{
                    const savingCurve = new THREE.CatmullRomCurve3(savingPoints);
                    const geometry = new THREE.TubeGeometry(savingCurve, 150, 0.08, 12, false);

                    const rgb = saving.color.rgb;
                    const color = new THREE.Color(`rgb(${{rgb[0]}}, ${{rgb[1]}}, ${{rgb[2]}})`);

                    const material = new THREE.MeshPhongMaterial({{
                        color: color,
                        emissive: color.clone().multiplyScalar(0.3),
                        shininess: 80,
                        transparent: true,
                        opacity: 0.75
                    }});

                    const mesh = new THREE.Mesh(geometry, material);
                    scene.add(mesh);
                }}
            }});

            // Function to create 3D text sprite
            function createTextSprite(text, options = {{}}) {{
                const canvas = document.createElement('canvas');
                const context = canvas.getContext('2d');

                const fontSize = options.fontSize || 48;
                const fontWeight = options.fontWeight || 'bold';
                const color = options.color || '#FFFFFF';
                const bgColor = options.bgColor || 'rgba(0, 0, 0, 0.7)';

                context.font = `${{fontWeight}} ${{fontSize}}px Arial`;
                const metrics = context.measureText(text);
                const textWidth = metrics.width;

                canvas.width = textWidth + 40;
                canvas.height = fontSize + 30;

                // Background
                context.fillStyle = bgColor;
                context.roundRect = function(x, y, w, h, r) {{
                    this.beginPath();
                    this.moveTo(x + r, y);
                    this.lineTo(x + w - r, y);
                    this.quadraticCurveTo(x + w, y, x + w, y + r);
                    this.lineTo(x + w, y + h - r);
                    this.quadraticCurveTo(x + w, y + h, x + w - r, y + h);
                    this.lineTo(x + r, y + h);
                    this.quadraticCurveTo(x, y + h, x, y + h - r);
                    this.lineTo(x, y + r);
                    this.quadraticCurveTo(x, y, x + r, y);
                    this.closePath();
                    this.fill();
                }};
                context.roundRect(5, 5, canvas.width - 10, canvas.height - 10, 10);

                // Text
                context.fillStyle = color;
                context.font = `${{fontWeight}} ${{fontSize}}px Arial`;
                context.textAlign = 'center';
                context.textBaseline = 'middle';
                context.fillText(text, canvas.width / 2, canvas.height / 2);

                const texture = new THREE.CanvasTexture(canvas);
                const spriteMaterial = new THREE.SpriteMaterial({{ map: texture, transparent: true }});
                const sprite = new THREE.Sprite(spriteMaterial);

                const scale = options.scale || 2;
                sprite.scale.set(scale * canvas.width / 100, scale * canvas.height / 100, 1);

                return sprite;
            }}

            // Add year labels along the timeline
            yearsToShow.forEach(yearInfo => {{
                const pos = roadmapPoints[yearInfo.index];
                if (pos) {{
                    // Year label above the timeline
                    const yearLabel = createTextSprite(yearInfo.year.toString(), {{
                        fontSize: 56,
                        color: '#FFD700',
                        bgColor: 'rgba(0, 0, 0, 0.85)',
                        scale: 2.5
                    }});
                    yearLabel.position.set(pos.x, pos.y + 3.5, pos.z);
                    scene.add(yearLabel);

                    // Value label below year
                    const valueLabel = createTextSprite(`€${{Math.round(yearInfo.total).toLocaleString()}}`, {{
                        fontSize: 44,
                        color: '#4CAF50',
                        bgColor: 'rgba(0, 0, 0, 0.75)',
                        scale: 2
                    }});
                    valueLabel.position.set(pos.x, pos.y + 1.5, pos.z);
                    scene.add(valueLabel);

                    // Vertical line from ground to timeline
                    const lineGeometry = new THREE.BufferGeometry().setFromPoints([
                        new THREE.Vector3(pos.x, -1.8, pos.z),
                        new THREE.Vector3(pos.x, pos.y, pos.z)
                    ]);
                    const lineMaterial = new THREE.LineBasicMaterial({{
                        color: 0xFFD700,
                        transparent: true,
                        opacity: 0.3,
                        linewidth: 2
                    }});
                    const line = new THREE.Line(lineGeometry, lineMaterial);
                    scene.add(line);

                    // Glowing orb at year point
                    const orbGeometry = new THREE.SphereGeometry(0.3, 32, 32);
                    const orbMaterial = new THREE.MeshPhongMaterial({{
                        color: 0xFFD700,
                        emissive: 0xFFD700,
                        emissiveIntensity: 0.8,
                        shininess: 100
                    }});
                    const orb = new THREE.Mesh(orbGeometry, orbMaterial);
                    orb.position.copy(pos);
                    scene.add(orb);
                }}
            }});

            // Add maturity markers with names and values
            savingsData.forEach((saving, idx) => {{
                const maturityDate = saving.maturity_date;
                const maturityPoint = timelineData.find(d => d.date === maturityDate);

                if (maturityPoint) {{
                    const maturityIndex = timelineData.indexOf(maturityPoint);
                    const pos = roadmapPoints[maturityIndex];

                    if (pos) {{
                        const rgb = saving.color.rgb;
                        const color = new THREE.Color(`rgb(${{rgb[0]}}, ${{rgb[1]}}, ${{rgb[2]}})`);

                        // Diamond marker
                        const markerGeometry = new THREE.OctahedronGeometry(0.4);
                        const markerMaterial = new THREE.MeshPhongMaterial({{
                            color: color,
                            emissive: color.clone().multiplyScalar(0.5),
                            shininess: 100
                        }});
                        const marker = new THREE.Mesh(markerGeometry, markerMaterial);
                        marker.position.set(pos.x, pos.y + 0.8, pos.z);
                        scene.add(marker);

                        // Saving name label
                        const nameLabel = createTextSprite(saving.name, {{
                            fontSize: 40,
                            color: saving.color.hex,
                            bgColor: 'rgba(0, 0, 0, 0.9)',
                            scale: 1.8
                        }});
                        nameLabel.position.set(pos.x, pos.y + 6, pos.z);
                        scene.add(nameLabel);

                        // Maturity value label
                        const maturityLabel = createTextSprite(`€${{Math.round(saving.maturity_value).toLocaleString()}}`, {{
                            fontSize: 48,
                            color: '#4CAF50',
                            bgColor: 'rgba(0, 0, 0, 0.85)',
                            scale: 2
                        }});
                        maturityLabel.position.set(pos.x, pos.y + 4.5, pos.z);
                        scene.add(maturityLabel);
                    }}
                }}
            }});

            // Initial camera position
            const initialCameraPosition = {{ x: 25, y: 12, z: 25 }};
            const initialTarget = {{ x: 0, y: 5, z: 0 }};

            camera.position.set(initialCameraPosition.x, initialCameraPosition.y, initialCameraPosition.z);
            controls.target.set(initialTarget.x, initialTarget.y, initialTarget.z);
            controls.update();

            // Reset button
            document.getElementById('reset-button').addEventListener('click', () => {{
                const duration = 1000;
                const startTime = Date.now();
                const startPos = {{ x: camera.position.x, y: camera.position.y, z: camera.position.z }};
                const startTarget = {{ x: controls.target.x, y: controls.target.y, z: controls.target.z }};

                function animateReset() {{
                    const elapsed = Date.now() - startTime;
                    const progress = Math.min(elapsed / duration, 1);
                    const eased = progress < 0.5 ? 2 * progress * progress : 1 - Math.pow(-2 * progress + 2, 2) / 2;

                    camera.position.x = startPos.x + (initialCameraPosition.x - startPos.x) * eased;
                    camera.position.y = startPos.y + (initialCameraPosition.y - startPos.y) * eased;
                    camera.position.z = startPos.z + (initialCameraPosition.z - startPos.z) * eased;

                    controls.target.x = startTarget.x + (initialTarget.x - startTarget.x) * eased;
                    controls.target.y = startTarget.y + (initialTarget.y - startTarget.y) * eased;
                    controls.target.z = startTarget.z + (initialTarget.z - startTarget.z) * eased;

                    controls.update();

                    if (progress < 1) requestAnimationFrame(animateReset);
                }}

                animateReset();
            }});

            // Animation loop
            const clock = new THREE.Clock();

            function animate() {{
                requestAnimationFrame(animate);
                controls.update();

                const time = clock.getElapsedTime();

                // Gentle pulsing on markers
                scene.children.forEach(child => {{
                    if (child.geometry && child.geometry.type === 'OctahedronGeometry') {{
                        child.rotation.y = time * 0.5;
                        child.position.y += Math.sin(time * 3) * 0.002;
                    }}
                }});

                renderer.render(scene, camera);
            }}

            animate();

            // Handle resize
            window.addEventListener('resize', () => {{
                camera.aspect = container.clientWidth / container.clientHeight;
                camera.updateProjectionMatrix();
                renderer.setSize(container.clientWidth, container.clientHeight);
            }});
        </script>
    </body>
    </html>
    """, height=720)

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
