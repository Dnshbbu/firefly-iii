"""
Helper module for creating D3-Sankey diagrams with destination accounts.
This creates a 5-tier cash flow visualization using D3.js.
"""

import pandas as pd
import json


def prepare_sankey_data(
    income_df: pd.DataFrame,
    destination_df: pd.DataFrame,
    destination_category_mapping_df: pd.DataFrame,
    income_source_col: str = 'source_name',
    income_amount_col: str = 'total_amount',
    destination_account_col: str = 'destination_name',
    destination_amount_col: str = 'total_amount',
    category_col: str = 'category_name',
    mapping_amount_col: str = 'total_amount',
    top_n_income: int = 10,
    top_n_destination: int = 15,
    top_n_category: int = 15
) -> dict:
    """
    Prepare data for D3 Sankey diagram: Income Sources → Total Income → (Remaining + Total Expenses) → Destination Accounts → Categories

    Args:
        income_df: Income sources with amounts
        destination_df: Destination accounts with total amounts
        destination_category_mapping_df: Mapping of destination→category with amounts (3 columns)
        income_source_col: Column name for income sources
        income_amount_col: Column for income amounts
        destination_account_col: Column for destination accounts
        destination_amount_col: Column for destination amounts
        category_col: Column for category names
        mapping_amount_col: Column for mapping amounts
        top_n_income: Top N income sources
        top_n_destination: Top N destination accounts
        top_n_category: Top N categories

    Returns:
        Dictionary with nodes and links for D3 Sankey
    """
    # Top income sources
    top_income = income_df.nlargest(top_n_income, income_amount_col).copy()
    if len(income_df) > top_n_income:
        other_income = income_df.iloc[top_n_income:][income_amount_col].sum()
        if other_income > 0:
            top_income = pd.concat([top_income, pd.DataFrame({
                income_source_col: ['Other Income'],
                income_amount_col: [other_income]
            })], ignore_index=True)
    top_income = top_income.reset_index(drop=True)

    # Top destination accounts
    top_destinations = destination_df.nlargest(top_n_destination, destination_amount_col).copy()
    if len(destination_df) > top_n_destination:
        other_dest = destination_df.iloc[top_n_destination:][destination_amount_col].sum()
        if other_dest > 0:
            top_destinations = pd.concat([top_destinations, pd.DataFrame({
                destination_account_col: ['Other Destinations'],
                destination_amount_col: [other_dest]
            })], ignore_index=True)
    top_destinations = top_destinations.reset_index(drop=True)

    # Top categories from mapping
    category_totals = destination_category_mapping_df.groupby(category_col)[mapping_amount_col].sum().reset_index()
    category_totals.columns = [category_col, 'total']
    top_categories = category_totals.nlargest(top_n_category, 'total').copy()
    if len(category_totals) > top_n_category:
        other_cat = category_totals.iloc[top_n_category:]['total'].sum()
        if other_cat > 0:
            top_categories = pd.concat([top_categories, pd.DataFrame({
                category_col: ['Other Categories'],
                'total': [other_cat]
            })], ignore_index=True)
    top_categories = top_categories.reset_index(drop=True)

    # Calculate totals
    total_income = top_income[income_amount_col].sum()
    total_expenses = top_destinations[destination_amount_col].sum()
    remaining = total_income - total_expenses

    # Build nodes array
    nodes = []
    node_index_map = {}

    # Layer 0: Income sources
    for idx, row in top_income.iterrows():
        name = row[income_source_col]
        amount = row[income_amount_col]
        pct = (amount / total_income * 100) if total_income > 0 else 0
        node_index_map[f"income_{name}"] = len(nodes)
        nodes.append({
            "name": name,
            "amount": float(amount),
            "percentage": float(pct),
            "layer": 0,
            "type": "income"
        })

    # Layer 1: Total Income
    node_index_map["total_income"] = len(nodes)
    nodes.append({
        "name": "💰 Total Income",
        "amount": float(total_income),
        "percentage": 100.0,
        "layer": 1,
        "type": "total_income"
    })

    # Layer 2: Remaining + Total Expenses
    if remaining > 0:
        remaining_pct = (remaining / total_income * 100) if total_income > 0 else 0
        node_index_map["remaining"] = len(nodes)
        nodes.append({
            "name": "💎 Remaining",
            "amount": float(remaining),
            "percentage": float(remaining_pct),
            "layer": 2,
            "type": "remaining"
        })

    total_expenses_pct = (total_expenses / total_income * 100) if total_income > 0 else 0
    node_index_map["total_expenses"] = len(nodes)
    nodes.append({
        "name": "💸 Total Expenses",
        "amount": float(total_expenses),
        "percentage": float(total_expenses_pct),
        "layer": 2,
        "type": "total_expenses"
    })

    # Layer 3: Destination accounts
    for idx, row in top_destinations.iterrows():
        name = row[destination_account_col]
        amount = row[destination_amount_col]
        pct = (amount / total_expenses * 100) if total_expenses > 0 else 0
        node_index_map[f"dest_{name}"] = len(nodes)
        nodes.append({
            "name": name,
            "amount": float(amount),
            "percentage": float(pct),
            "layer": 3,
            "type": "destination"
        })

    # Layer 4: Categories
    for idx, row in top_categories.iterrows():
        name = row[category_col]
        amount = row['total']
        pct = (amount / total_expenses * 100) if total_expenses > 0 else 0
        node_index_map[f"cat_{name}"] = len(nodes)
        nodes.append({
            "name": name,
            "amount": float(amount),
            "percentage": float(pct),
            "layer": 4,
            "type": "category"
        })

    # Build links array
    links = []

    # Phase 1: Income sources → Total Income
    for idx, row in top_income.iterrows():
        name = row[income_source_col]
        amount = row[income_amount_col]
        links.append({
            "source": node_index_map[f"income_{name}"],
            "target": node_index_map["total_income"],
            "value": float(amount)
        })

    # Phase 2: Total Income → Remaining
    if remaining > 0:
        links.append({
            "source": node_index_map["total_income"],
            "target": node_index_map["remaining"],
            "value": float(remaining)
        })

    # Phase 3: Total Income → Total Expenses
    links.append({
        "source": node_index_map["total_income"],
        "target": node_index_map["total_expenses"],
        "value": float(total_expenses)
    })

    # Phase 4: Total Expenses → Destination Accounts
    for idx, row in top_destinations.iterrows():
        name = row[destination_account_col]
        amount = row[destination_amount_col]
        links.append({
            "source": node_index_map["total_expenses"],
            "target": node_index_map[f"dest_{name}"],
            "value": float(amount)
        })

    # Phase 5: Destination Accounts → Categories (using mapping)
    top_dest_names = set(top_destinations[destination_account_col].tolist())
    top_cat_names = set(top_categories[category_col].tolist())

    filtered_mapping = destination_category_mapping_df[
        destination_category_mapping_df[destination_account_col].isin(top_dest_names) &
        destination_category_mapping_df[category_col].isin(top_cat_names)
    ].copy()

    for _, row in filtered_mapping.iterrows():
        dest_name = row[destination_account_col]
        cat_name = row[category_col]
        amount = row[mapping_amount_col]

        source_idx = node_index_map.get(f"dest_{dest_name}")
        target_idx = node_index_map.get(f"cat_{cat_name}")

        if source_idx is not None and target_idx is not None:
            links.append({
                "source": source_idx,
                "target": target_idx,
                "value": float(amount)
            })

    return {
        "nodes": nodes,
        "links": links,
        "totals": {
            "total_income": float(total_income),
            "total_expenses": float(total_expenses),
            "remaining": float(remaining)
        }
    }


def generate_d3_sankey_html(data: dict, title: str, height: int = 700) -> str:
    """
    Generate complete HTML with D3 Sankey diagram.

    Args:
        data: Dictionary with nodes and links from prepare_sankey_data()
        title: Chart title
        height: Chart height in pixels

    Returns:
        Complete HTML string with embedded D3 visualization
    """

    data_json = json.dumps(data, indent=2)

    html = f'''
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>{title}</title>
    <script src="https://d3js.org/d3.v7.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/d3-sankey@0.12.3/dist/d3-sankey.min.js"></script>
    <style>
        body {{
            margin: 0;
            padding: 20px;
            font-family: Arial, sans-serif;
            background-color: transparent;
            overflow: hidden;
        }}

        #chart {{
            width: 100%;
            height: {height}px;
        }}

        .node rect {{
            cursor: pointer;
            stroke: #fff;
            stroke-width: 2px;
        }}

        .node text {{
            pointer-events: none;
            font-size: 11px;
            fill: rgba(250, 250, 250, 0.95);
            text-shadow: 0 1px 2px rgba(0,0,0,0.3);
        }}

        .link {{
            fill: none;
            stroke-opacity: 0.4;
            cursor: pointer;
        }}

        .link:hover {{
            stroke-opacity: 0.6;
        }}

        .link.highlighted {{
            stroke-opacity: 0.7 !important;
        }}

        .link.dimmed {{
            stroke-opacity: 0.1 !important;
        }}

        .node.highlighted rect {{
            stroke-width: 3px;
            filter: brightness(1.2);
        }}

        .node.dimmed rect {{
            opacity: 0.2;
        }}

        .node.dimmed text {{
            opacity: 0.2;
        }}

        #tooltip {{
            position: absolute;
            padding: 10px;
            background: rgba(30, 30, 30, 0.95);
            border: 1px solid rgba(255, 255, 255, 0.2);
            border-radius: 4px;
            pointer-events: none;
            font-size: 12px;
            color: #fff;
            display: none;
            z-index: 1000;
            box-shadow: 0 4px 6px rgba(0,0,0,0.3);
        }}

        #tooltip .label {{
            font-weight: bold;
            margin-bottom: 4px;
            font-size: 13px;
        }}

        #tooltip .value {{
            color: #4ade80;
        }}

        h2 {{
            margin: 0 0 10px 0;
            color: rgba(250, 250, 250, 0.9);
            font-size: 1.3rem;
        }}
    </style>
</head>
<body>
    <h2>{title}</h2>
    <div id="tooltip"></div>
    <div id="chart"></div>

    <script>
        const data = {data_json};

        // Color scheme
        const colors = {{
            income: '#4ade80',        // Green
            total_income: '#3b82f6',  // Blue
            remaining: '#22c55e',     // Dark green
            total_expenses: '#fb923c',// Orange
            destination: '#ffc107',   // Yellow
            category: '#f87171'       // Red
        }};

        // Setup
        const margin = {{top: 10, right: 10, bottom: 10, left: 10}};
        const width = document.getElementById('chart').clientWidth - margin.left - margin.right;
        const height = {height} - margin.top - margin.bottom;

        const svg = d3.select("#chart")
            .append("svg")
            .attr("width", width + margin.left + margin.right)
            .attr("height", height + margin.top + margin.bottom)
            .append("g")
            .attr("transform", `translate(${{margin.left}},${{margin.top}})`);

        // Create Sankey generator
        const sankey = d3.sankey()
            .nodeWidth(30)
            .nodePadding(20)
            .extent([[1, 1], [width - 1, height - 1]])
            .nodeId(d => d.index)
            .nodeAlign(d3.sankeyLeft);

        // Add index to nodes
        data.nodes.forEach((node, i) => {{
            node.index = i;
        }});

        // Generate Sankey layout
        const {{nodes, links}} = sankey({{
            nodes: data.nodes.map(d => Object.assign({{}}, d)),
            links: data.links.map(d => Object.assign({{}}, d))
        }});

        // Color scale
        const color = d => colors[d.type] || '#999';

        // Add links
        const link = svg.append("g")
            .attr("class", "links")
            .selectAll("path")
            .data(links)
            .enter()
            .append("path")
            .attr("class", "link")
            .attr("d", d3.sankeyLinkHorizontal())
            .attr("stroke", d => color(d.source))
            .attr("stroke-width", d => Math.max(1, d.width));

        // Add nodes
        const node = svg.append("g")
            .attr("class", "nodes")
            .selectAll("g")
            .data(nodes)
            .enter()
            .append("g")
            .attr("class", "node");

        node.append("rect")
            .attr("x", d => d.x0)
            .attr("y", d => d.y0)
            .attr("height", d => d.y1 - d.y0)
            .attr("width", d => d.x1 - d.x0)
            .attr("fill", d => color(d));

        // Add labels
        node.append("text")
            .attr("x", d => d.x0 < width / 2 ? d.x1 + 6 : d.x0 - 6)
            .attr("y", d => (d.y1 + d.y0) / 2)
            .attr("dy", "0.35em")
            .attr("text-anchor", d => d.x0 < width / 2 ? "start" : "end")
            .text(d => d.name)
            .append("tspan")
            .attr("x", d => d.x0 < width / 2 ? d.x1 + 6 : d.x0 - 6)
            .attr("dy", "1.2em")
            .attr("fill-opacity", 0.8)
            .style("font-size", "10px")
            .text(d => `€${{d.amount.toLocaleString('en-IE', {{maximumFractionDigits: 0}})}} (${{d.percentage.toFixed(1)}}%)`);

        // Tooltip
        const tooltip = d3.select("#tooltip");

        // Hover interactions
        function highlightConnected(d, isNode) {{
            const connectedNodes = new Set();
            const connectedLinks = new Set();

            if (isNode) {{
                connectedNodes.add(d.index);

                // Find all connected links and nodes
                links.forEach(link => {{
                    if (link.source.index === d.index) {{
                        connectedLinks.add(link);
                        connectedNodes.add(link.target.index);
                    }}
                    if (link.target.index === d.index) {{
                        connectedLinks.add(link);
                        connectedNodes.add(link.source.index);
                    }}
                }});
            }} else {{
                connectedLinks.add(d);
                connectedNodes.add(d.source.index);
                connectedNodes.add(d.target.index);
            }}

            // Apply highlighting
            node.classed("highlighted", n => connectedNodes.has(n.index))
                .classed("dimmed", n => !connectedNodes.has(n.index));

            link.classed("highlighted", l => connectedLinks.has(l))
                .classed("dimmed", l => !connectedLinks.has(l));
        }}

        function resetHighlight() {{
            node.classed("highlighted", false).classed("dimmed", false);
            link.classed("highlighted", false).classed("dimmed", false);
        }}

        // Node hover
        node
            .on("mouseover", function(event, d) {{
                highlightConnected(d, true);

                tooltip
                    .style("display", "block")
                    .html(`
                        <div class="label">${{d.name}}</div>
                        <div><span class="value">€${{d.amount.toLocaleString('en-IE', {{maximumFractionDigits: 2}})}}</span></div>
                        <div>${{d.percentage.toFixed(1)}}% of ${{d.type === 'income' || d.type === 'total_income' ? 'income' : 'expenses'}}</div>
                    `);
            }})
            .on("mousemove", function(event) {{
                tooltip
                    .style("left", (event.pageX + 10) + "px")
                    .style("top", (event.pageY - 10) + "px");
            }})
            .on("mouseout", function() {{
                resetHighlight();
                tooltip.style("display", "none");
            }});

        // Link hover
        link
            .on("mouseover", function(event, d) {{
                highlightConnected(d, false);

                tooltip
                    .style("display", "block")
                    .html(`
                        <div class="label">${{d.source.name}} → ${{d.target.name}}</div>
                        <div><span class="value">€${{d.value.toLocaleString('en-IE', {{maximumFractionDigits: 2}})}}</span></div>
                    `);
            }})
            .on("mousemove", function(event) {{
                tooltip
                    .style("left", (event.pageX + 10) + "px")
                    .style("top", (event.pageY - 10) + "px");
            }})
            .on("mouseout", function() {{
                resetHighlight();
                tooltip.style("display", "none");
            }});
    </script>
</body>
</html>
'''

    return html
