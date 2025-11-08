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
    node_filters: dict[str, dict] = {}

    def _node_key(node_type: str, name: str) -> str:
        return f"{node_type}::{name}"

    # Helper to register node drilldown metadata
    def register_node(
        node_type: str,
        name: str,
        *,
        filter_field: str | None,
        filter_values: list[str] | None,
        type_filter: str | None = None,
        is_virtual: bool = False,
        description: str | None = None
    ) -> None:
        node_filters[_node_key(node_type, name)] = {
            "type": node_type,
            "name": name,
            "filter_field": filter_field,
            "filter_values": filter_values or [],
            "type_filter": type_filter,
            "is_virtual": is_virtual,
            "description": description or "",
        }

    # Top income sources - sorted descending by amount and track members
    income_sorted = income_df.sort_values(income_amount_col, ascending=False).reset_index(drop=True)
    top_income = income_sorted.head(top_n_income).copy()
    other_income_members: list[str] = []
    if len(income_sorted) > top_n_income:
        remaining_income_df = income_sorted.iloc[top_n_income:]
        other_income = remaining_income_df[income_amount_col].sum()
        other_income_members = remaining_income_df[income_source_col].tolist()
        if other_income > 0:
            top_income = pd.concat([top_income, pd.DataFrame({
                income_source_col: ['Other Income'],
                income_amount_col: [other_income]
            })], ignore_index=True)
    top_income = top_income.reset_index(drop=True)
    income_member_map = {
        row[income_source_col]: (
            other_income_members if row[income_source_col] == 'Other Income' and other_income_members else [row[income_source_col]]
        ) for _, row in top_income.iterrows()
    }

    # Top destination accounts - sorted descending by amount and track members
    destination_sorted = destination_df.sort_values(destination_amount_col, ascending=False).reset_index(drop=True)
    top_destinations = destination_sorted.head(top_n_destination).copy()
    other_destination_members: list[str] = []
    if len(destination_sorted) > top_n_destination:
        remaining_dest_df = destination_sorted.iloc[top_n_destination:]
        other_dest = remaining_dest_df[destination_amount_col].sum()
        other_destination_members = remaining_dest_df[destination_account_col].tolist()
        if other_dest > 0:
            top_destinations = pd.concat([top_destinations, pd.DataFrame({
                destination_account_col: ['Other Destinations'],
                destination_amount_col: [other_dest]
            })], ignore_index=True)
    top_destinations = top_destinations.reset_index(drop=True)
    destination_member_map = {
        row[destination_account_col]: (
            other_destination_members if row[destination_account_col] == 'Other Destinations' and other_destination_members else [row[destination_account_col]]
        ) for _, row in top_destinations.iterrows()
    }

    # Top categories from mapping - sorted descending by amount and track members
    category_totals = destination_category_mapping_df.groupby(category_col)[mapping_amount_col].sum().reset_index()
    category_totals.columns = [category_col, 'total']
    category_sorted = category_totals.sort_values('total', ascending=False).reset_index(drop=True)
    top_categories = category_sorted.head(top_n_category).copy()
    other_category_members: list[str] = []
    if len(category_sorted) > top_n_category:
        remaining_cat_df = category_sorted.iloc[top_n_category:]
        other_cat = remaining_cat_df['total'].sum()
        other_category_members = remaining_cat_df[category_col].tolist()
        if other_cat > 0:
            top_categories = pd.concat([top_categories, pd.DataFrame({
                category_col: ['Other Categories'],
                'total': [other_cat]
            })], ignore_index=True)
    top_categories = top_categories.reset_index(drop=True)
    category_member_map = {
        row[category_col]: (
            other_category_members if row[category_col] == 'Other Categories' and other_category_members else [row[category_col]]
        ) for _, row in top_categories.iterrows()
    }

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
        register_node(
            "income",
            name,
            filter_field=income_source_col,
            filter_values=income_member_map.get(name, [name]),
            type_filter="deposit",
        )

    # Layer 1: Total Income
    node_index_map["total_income"] = len(nodes)
    nodes.append({
        "name": "💰 Total Income",
        "amount": float(total_income),
        "percentage": 100.0,
        "layer": 1,
        "type": "total_income"
    })
    register_node(
        "total_income",
        "💰 Total Income",
        filter_field="type",
        filter_values=["deposit"],
        type_filter="deposit",
    )

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
        register_node(
            "remaining",
            "💎 Remaining",
            filter_field=None,
            filter_values=None,
            description="Remaining is derived from total income minus expenses.",
            is_virtual=True,
        )

    total_expenses_pct = (total_expenses / total_income * 100) if total_income > 0 else 0
    node_index_map["total_expenses"] = len(nodes)
    nodes.append({
        "name": "💸 Total Expenses",
        "amount": float(total_expenses),
        "percentage": float(total_expenses_pct),
        "layer": 2,
        "type": "total_expenses"
    })
    register_node(
        "total_expenses",
        "💸 Total Expenses",
        filter_field="type",
        filter_values=["withdrawal"],
        type_filter="withdrawal",
    )

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
        register_node(
            "destination",
            name,
            filter_field=destination_account_col,
            filter_values=destination_member_map.get(name, [name]),
            type_filter="withdrawal",
        )

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
        register_node(
            "category",
            name,
            filter_field=category_col,
            filter_values=category_member_map.get(name, [name]),
            type_filter="withdrawal",
        )

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
        },
        "node_filters": node_filters
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
            overflow: auto;
        }}

        #chart {{
            width: 100%;
            height: {height}px;
            overflow: visible;
            position: relative;
        }}

        .node rect {{
            cursor: pointer;
            stroke: rgba(0, 0, 0, 0.3);
            stroke-width: 2px;
        }}

        .node text {{
            pointer-events: none;
            font-size: 11px;
            fill: rgba(255, 255, 255, 0.95);
            text-shadow: 0 1px 3px rgba(0,0,0,0.8);
            font-weight: 500;
        }}

        .link {{
            fill: none;
            stroke-opacity: 0.6;
            cursor: pointer;
        }}

        .link:hover {{
            stroke-opacity: 0.8;
        }}

        .link.highlighted {{
            stroke-opacity: 0.9 !important;
        }}

        .link.dimmed {{
            stroke-opacity: 0.2 !important;
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

        h2 {{
            margin: 0 0 10px 0;
            color: rgba(250, 250, 250, 0.9);
            font-size: 1.3rem;
        }}

        #zoom-controls {{
            position: absolute;
            top: 50px;
            right: 20px;
            display: flex;
            flex-direction: column;
            gap: 5px;
            z-index: 1001;
        }}

        .zoom-btn {{
            width: 35px;
            height: 35px;
            background: rgba(30, 30, 30, 0.95);
            border: 1px solid rgba(255, 255, 255, 0.2);
            border-radius: 4px;
            color: #fff;
            font-size: 18px;
            font-weight: bold;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: all 0.2s;
        }}

        .zoom-btn:hover {{
            background: rgba(60, 60, 60, 0.95);
            border-color: rgba(255, 255, 255, 0.4);
        }}

        .zoom-btn:active {{
            transform: scale(0.95);
        }}

        #chart-container {{
            position: relative;
        }}

        #details-panel {{
            margin-top: 20px;
            padding: 0;
            color: #f8fafc;
        }}

        .panel-grid {{
            display: flex;
            flex-wrap: wrap;
            gap: 16px;
        }}

        .panel-grid > * {{
            flex: 1 1 420px;
        }}

        .details-content {{
            background: rgba(15, 23, 42, 0.55);
            border: 1px solid rgba(148, 163, 184, 0.2);
            border-radius: 8px;
            padding: 12px 16px;
            min-height: 120px;
        }}

        .selection-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 12px;
            margin-bottom: 10px;
        }}

        .selection-header .label {{
            font-size: 0.8rem;
            color: #a5b4fc;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }}

        .selection-header .value {{
            font-size: 1.2rem;
            font-weight: 600;
            color: #7dd3fc;
        }}

        .selection-metrics {{
            display: flex;
            gap: 16px;
            font-size: 0.85rem;
        }}

        .selection-metrics span {{
            display: block;
            color: #cbd5f5;
        }}

        .selection-metrics strong {{
            font-size: 1rem;
            color: #f8fafc;
        }}

        .group-note {{
            font-size: 0.85rem;
            color: #cbd5f5;
            margin-bottom: 8px;
        }}

        .table-wrapper {{
            max-height: 360px;
            overflow-y: auto;
            border-radius: 6px;
            border: 1px solid rgba(148, 163, 184, 0.2);
        }}

        .transactions-table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 0.85rem;
        }}

        .transactions-table thead {{
            position: sticky;
            top: 0;
            background: rgba(15, 23, 42, 0.95);
            z-index: 1;
        }}

        .transactions-table th,
        .transactions-table td {{
            padding: 8px 10px;
            text-align: left;
            border-bottom: 1px solid rgba(148, 163, 184, 0.15);
        }}

        .transactions-table th {{
            font-size: 0.75rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: #94a3b8;
        }}

        .transactions-table td.amount,
        .transactions-table th.amount {{
            text-align: right;
            white-space: nowrap;
        }}

        .transactions-table tbody tr:hover {{
            background: rgba(59, 130, 246, 0.08);
        }}

        .table-footer {{
            margin-top: 8px;
            font-size: 0.8rem;
            color: #94a3b8;
        }}

        .empty-state {{
            text-align: center;
            padding: 20px;
            color: #cbd5f5;
        }}

        .empty-state .state-title {{
            font-size: 1rem;
            font-weight: 600;
            margin-bottom: 6px;
            color: #f8fafc;
        }}

        .trend-panel {{
            padding: 12px 16px;
            background: rgba(8, 25, 48, 0.65);
            border: 1px solid rgba(148, 163, 184, 0.2);
            border-radius: 8px;
            min-height: 120px;
        }}

        .trend-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 12px;
            margin-bottom: 10px;
        }}

        .trend-header .label {{
            font-size: 0.8rem;
            color: #a5b4fc;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }}

        .trend-header .value {{
            font-size: 1rem;
            color: #7dd3fc;
        }}

        .trend-metrics {{
            display: flex;
            gap: 16px;
            font-size: 0.85rem;
        }}

        .trend-metrics span {{
            display: block;
            color: #cbd5f5;
        }}

        .trend-metrics strong {{
            font-size: 1rem;
            color: #f8fafc;
        }}

        .trend-chart {{
            width: 100%;
            min-height: 260px;
        }}

        .trend-chart svg {{
            width: 100%;
            height: 260px;
        }}

        .trend-chart .bar {{
            fill: rgba(56, 189, 248, 0.85);
        }}

        .trend-chart .bar:hover {{
            fill: rgba(56, 189, 248, 1);
        }}

        .trend-chart .axis text {{
            fill: #cbd5f5;
            font-size: 11px;
        }}

        .trend-chart .axis path,
        .trend-chart .axis line {{
            stroke: rgba(148, 163, 184, 0.4);
        }}

        #chart-container:fullscreen {{
            background-color: #0e1117;
            padding: 20px;
            width: 100vw;
            height: 100vh;
            overflow: auto;
        }}

        #chart-container:-webkit-full-screen {{
            background-color: #0e1117;
            padding: 20px;
            width: 100vw;
            height: 100vh;
            overflow: auto;
        }}

        #chart-container:-moz-full-screen {{
            background-color: #0e1117;
            padding: 20px;
            width: 100vw;
            height: 100vh;
            overflow: auto;
        }}

        #chart-container:fullscreen #chart {{
            height: calc(100vh - 100px);
        }}

        #chart-container:-webkit-full-screen #chart {{
            height: calc(100vh - 100px);
        }}

        #chart-container:-moz-full-screen #chart {{
            height: calc(100vh - 100px);
        }}
    </style>
</head>
<body>
    <div id="chart-container">
        <h2>{title}</h2>
        <div id="zoom-controls">
            <button class="zoom-btn" id="zoom-in" title="Zoom In">+</button>
            <button class="zoom-btn" id="zoom-out" title="Zoom Out">−</button>
            <button class="zoom-btn" id="zoom-reset" title="Reset Zoom">⟲</button>
            <button class="zoom-btn" id="fullscreen-toggle" title="Toggle Fullscreen">⛶</button>
        </div>
        <div id="chart"></div>
    </div>

    <div id="details-panel">
        <div class="panel-grid">
            <div id="details-content" class="details-content">
                <div class="empty-state">
                    <div class="state-title">Transactions</div>
                    <p>Select a node in the Sankey diagram to view detailed transactions.</p>
                </div>
            </div>
            <div id="trend-panel" class="trend-panel">
                <div class="empty-state">
                    <div class="state-title">Trend insights</div>
                    <p>Pick a node and the chart will visualize its monthly totals for the selected trend range.</p>
                </div>
            </div>
        </div>
    </div>

    <script>
        const data = {data_json};
        const transactions = data.transactions || [];
        const trendTransactions = data.trend_transactions || [];
        const nodeFilters = data.node_filters || {{}};
        const trendRange = data.trend_range || null;
        const MAX_ROWS = 150;
        const MONTH_NAMES = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];

        // Color scheme
        const colors = {{
            income: '#4ade80',        // Green
            total_income: '#3b82f6',  // Blue
            remaining: '#22c55e',     // Dark green
            total_expenses: '#fb923c',// Orange
            destination: '#ffc107',   // Yellow
            category: '#f87171'       // Red
        }};

        // Much darker color scheme for links (more suitable for dark mode)
        const linkColors = {{
            income: '#0f7a3a',        // Much darker green
            total_income: '#1e3a8a',  // Much darker blue
            remaining: '#0d6e30',     // Much darker green
            total_expenses: '#9a3412', // Much darker orange
            destination: '#a16207',   // Much darker yellow
            category: '#991b1b'       // Much darker red
        }};

        const margin = {{top: 10, right: 10, bottom: 10, left: 10}};
        let svg, g, zoom, sankey, link, node;

        const escapeHtml = (value) => {{
            if (value === undefined || value === null) return '';
            return String(value)
                .replace(/&/g, '&amp;')
                .replace(/</g, '&lt;')
                .replace(/>/g, '&gt;')
                .replace(/"/g, '&quot;')
                .replace(/'/g, '&#39;');
        }};

        const formatCurrency = (value) => {{
            const amount = Number(value || 0);
            return new Intl.NumberFormat('en-IE', {{
                style: 'currency',
                currency: 'EUR',
                maximumFractionDigits: 0
            }}).format(amount);
        }};

        const formatAxisCurrency = (value) => {{
            const amount = Number(value || 0);
            const absAmount = Math.abs(amount);
            if (absAmount >= 1000000) {{
                return `€${{(amount / 1000000).toFixed(1)}}M`;
            }}
            if (absAmount >= 1000) {{
                return `€${{(amount / 1000).toFixed(1)}}k`;
            }}
            return `€${{Math.round(amount)}}`;
        }};

        const getNodeKey = (node) => `${{node.type}}::${{node.name}}`;

        function filterTransactions(meta, dataset = transactions) {{
            if (!dataset.length) return [];
            let results = dataset.slice();

            if (meta.type_filter) {{
                results = results.filter(txn => txn.type === meta.type_filter);
            }}

            if (
                meta.filter_field &&
                Array.isArray(meta.filter_values) &&
                meta.filter_values.length > 0
            ) {{
                const allowed = new Set(meta.filter_values.map(v => (v ?? '')));
                results = results.filter(txn => allowed.has((txn[meta.filter_field] ?? '')));
            }}

            return results;
        }}

        function renderTransactions(node, meta) {{
            const container = document.getElementById('details-content');
            if (!container) return;

            if (meta.is_virtual) {{
                container.innerHTML = `
                    <div class="empty-state">
                        <div class="state-title">${{escapeHtml(node.name)}}</div>
                        <p>${{escapeHtml(meta.description || 'This node represents a derived metric.')}}</p>
                    </div>
                `;
                return;
            }}

            const nodeTransactions = filterTransactions(meta);

            if (!nodeTransactions.length) {{
                container.innerHTML = `
                    <div class="empty-state">
                        <div class="state-title">${{escapeHtml(node.name)}}</div>
                        <p>No transactions found for this node in the selected period.</p>
                    </div>
                `;
                return;
            }}

            const total = nodeTransactions.reduce((acc, txn) => acc + Math.abs(Number(txn.amount || 0)), 0);
            const avg = total / nodeTransactions.length;
            const limited = nodeTransactions.slice(0, MAX_ROWS);
            const clipped = nodeTransactions.length > MAX_ROWS;

            const tableRows = limited.map(txn => `
                <tr>
                    <td>${{escapeHtml(txn.date || '')}}</td>
                    <td>${{escapeHtml(txn.description || '')}}</td>
                    <td>${{escapeHtml(txn.source_name || '')}}</td>
                    <td>${{escapeHtml(txn.destination_name || '')}}</td>
                    <td>${{escapeHtml(txn.category_name || '')}}</td>
                    <td class="amount">${{formatCurrency(Math.abs(Number(txn.amount || 0)))}}</td>
                </tr>
            `).join('');

            const groupNote = meta.filter_values && meta.filter_values.length > 1
                ? `<div class="group-note">Includes ${{meta.filter_values.length}} grouped entries.</div>`
                : '';

            container.innerHTML = `
                <div class="selection-header">
                    <div>
                        <div class="label">Selected Node</div>
                        <div class="value">${{escapeHtml(node.name)}}</div>
                    </div>
                    <div class="selection-metrics">
                        <div><span>Transactions</span><strong>${{nodeTransactions.length}}</strong></div>
                        <div><span>Total</span><strong>${{formatCurrency(total)}}</strong></div>
                        <div><span>Average</span><strong>${{formatCurrency(avg)}}</strong></div>
                    </div>
                </div>
                ${{groupNote}}
                <div class="table-wrapper">
                    <table class="transactions-table">
                        <thead>
                            <tr>
                                <th>Date</th>
                                <th>Description</th>
                                <th>Source</th>
                                <th>Destination</th>
                                <th>Category</th>
                                <th class="amount">Amount</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${{tableRows}}
                        </tbody>
                    </table>
                </div>
                ${{clipped ? `<div class="table-footer">Showing ${{limited.length}} of ${{nodeTransactions.length}} transactions. Narrow your date range for the full list.</div>` : ''}}
            `;
        }}

        function renderTrendChart(node, meta) {{
            const container = document.getElementById('trend-panel');
            if (!container) return;

            const rangeLabel = trendRange
                ? `${{trendRange.label}} • ${{trendRange.start}} → ${{trendRange.end}}`
                : 'Selected trend range';

            if (meta.is_virtual) {{
                container.innerHTML = `
                    <div class="empty-state">
                        <div class="state-title">${{escapeHtml(node.name)}}</div>
                        <p>${{escapeHtml(meta.description || 'Derived nodes do not contain individual transactions.')}}</p>
                    </div>
                `;
                return;
            }}

            if (!trendTransactions.length) {{
                container.innerHTML = `
                    <div class="empty-state">
                        <div class="state-title">${{escapeHtml(node.name)}}</div>
                        <p>No trend data is available for the selected range.</p>
                    </div>
                `;
                return;
            }}

            const nodeTrendTxns = filterTransactions(meta, trendTransactions);

            if (!nodeTrendTxns.length) {{
                container.innerHTML = `
                    <div class="empty-state">
                        <div class="state-title">${{escapeHtml(node.name)}}</div>
                        <p>No transactions found for this node in the trend period (${{rangeLabel}}).</p>
                    </div>
                `;
                return;
            }}

            const monthlyMap = new Map();
            nodeTrendTxns.forEach(txn => {{
                if (!txn.date) {{
                    return;
                }}
                const parsed = new Date(txn.date);
                if (Number.isNaN(parsed.getTime())) {{
                    return;
                }}
                const key = `${{parsed.getFullYear()}}-${{parsed.getMonth()}}`;
                const value = Math.abs(Number(txn.amount || 0));
                monthlyMap.set(key, (monthlyMap.get(key) || 0) + value);
            }});

            if (monthlyMap.size === 0) {{
                container.innerHTML = `
                    <div class="empty-state">
                        <div class="state-title">${{escapeHtml(node.name)}}</div>
                        <p>No valid monthly data available for trend visualization.</p>
                    </div>
                `;
                return;
            }}

            const dataPoints = Array.from(monthlyMap.entries()).map(([key, value]) => {{
                const [yearStr, monthStr] = key.split('-');
                const year = Number(yearStr);
                const monthIndex = Number(monthStr);
                const date = new Date(year, monthIndex, 1);
                const label = `${{MONTH_NAMES[monthIndex]}} ${{String(year).slice(-2)}}`;
                return {{ key, value, date, label }};
            }}).sort((a, b) => a.date - b.date);

            const total = dataPoints.reduce((acc, item) => acc + item.value, 0);
            const avg = total / dataPoints.length;

            container.innerHTML = `
                <div class="trend-header">
                    <div>
                        <div class="label">Trend Range</div>
                        <div class="value">${{escapeHtml(rangeLabel)}}</div>
                    </div>
                    <div class="trend-metrics">
                        <div><span>Total</span><strong>${{formatCurrency(total)}}</strong></div>
                        <div><span>Avg / Month</span><strong>${{formatCurrency(avg)}}</strong></div>
                    </div>
                </div>
                <div id="trend-chart" class="trend-chart"></div>
            `;

            const chartContainer = document.getElementById('trend-chart');
            if (!chartContainer) return;

            const chartMargin = {{ top: 10, right: 10, bottom: 40, left: 60 }};
            const containerWidth = chartContainer.clientWidth || 720;
            const containerHeight = 260;
            const innerWidth = containerWidth - chartMargin.left - chartMargin.right;
            const innerHeight = containerHeight - chartMargin.top - chartMargin.bottom;

            const svg = d3.select(chartContainer)
                .append('svg')
                .attr('width', containerWidth)
                .attr('height', containerHeight);

            const chartGroup = svg.append('g')
                .attr('transform', `translate(${{chartMargin.left}}, ${{chartMargin.top}})`);

            const x = d3.scaleBand()
                .domain(dataPoints.map(d => d.label))
                .range([0, innerWidth])
                .padding(0.25);

            const maxValue = d3.max(dataPoints, d => d.value) || 0;
            const y = d3.scaleLinear()
                .domain([0, maxValue * 1.1 || 1])
                .range([innerHeight, 0])
                .nice();

            const xAxis = d3.axisBottom(x);
            chartGroup.append('g')
                .attr('class', 'axis axis-x')
                .attr('transform', `translate(0, ${{innerHeight}})`)
                .call(xAxis)
                .selectAll('text')
                .attr('transform', 'rotate(-35)')
                .style('text-anchor', 'end');

            const yAxis = d3.axisLeft(y).ticks(5).tickFormat(formatAxisCurrency);
            chartGroup.append('g')
                .attr('class', 'axis axis-y')
                .call(yAxis);

            chartGroup.selectAll('.bar')
                .data(dataPoints)
                .enter()
                .append('rect')
                .attr('class', 'bar')
                .attr('x', d => x(d.label))
                .attr('width', x.bandwidth())
                .attr('y', d => y(d.value))
                .attr('height', d => innerHeight - y(d.value));

            chartGroup.selectAll('.bar-label')
                .data(dataPoints)
                .enter()
                .append('text')
                .attr('class', 'bar-label')
                .attr('x', d => x(d.label) + x.bandwidth() / 2)
                .attr('y', d => Math.min(y(d.value) - 6, innerHeight - 4))
                .attr('text-anchor', 'middle')
                .attr('fill', '#f8fafc')
                .attr('font-size', '10px')
                .text(d => formatCurrency(d.value));
        }}

        function handleNodeClick(nodeData) {{
            const meta = nodeFilters[getNodeKey(nodeData)];
            if (!meta) {{
                const container = document.getElementById('details-content');
                if (container) {{
                    container.innerHTML = `
                        <div class="empty-state">
                            <div class="state-title">${{escapeHtml(nodeData.name)}}</div>
                            <p>No drilldown data is available for this node.</p>
                        </div>
                    `;
                }}
                const trendContainer = document.getElementById('trend-panel');
                if (trendContainer) {{
                    trendContainer.innerHTML = `
                        <div class="empty-state">
                            <div class="state-title">${{escapeHtml(nodeData.name)}}</div>
                            <p>Trend data is unavailable for this node.</p>
                        </div>
                    `;
                }}
                return;
            }}
            renderTransactions(nodeData, meta);
            renderTrendChart(nodeData, meta);
        }}

        function drawChart() {{
            // Clear existing chart
            d3.select("#chart").selectAll("*").remove();

            // Get current dimensions
            const chartElement = document.getElementById('chart');
            const width = chartElement.clientWidth - margin.left - margin.right;
            const height = chartElement.clientHeight - margin.top - margin.bottom;

            // Setup SVG
            svg = d3.select("#chart")
                .append("svg")
                .attr("width", width + margin.left + margin.right)
                .attr("height", height + margin.top + margin.bottom);

            // Create a group for zoom/pan transformations
            g = svg.append("g")
                .attr("transform", `translate(${{margin.left}},${{margin.top}})`);

            // Setup zoom behavior
            zoom = d3.zoom()
                .scaleExtent([0.1, 4])  // Allow zoom from 10% to 400%
                .on("zoom", (event) => {{
                    g.attr("transform", event.transform);
                }});

            svg.call(zoom);

            // Set initial zoom to be slightly zoomed out (90% scale)
            const initialTransform = d3.zoomIdentity
                .translate(margin.left, margin.top)
                .scale(0.90);
            svg.call(zoom.transform, initialTransform);

            // Zoom control functions
            d3.select("#zoom-in").on("click", () => {{
                svg.transition().duration(300).call(zoom.scaleBy, 1.3);
            }});

            d3.select("#zoom-out").on("click", () => {{
                svg.transition().duration(300).call(zoom.scaleBy, 0.7);
            }});

            d3.select("#zoom-reset").on("click", () => {{
                svg.transition().duration(300).call(zoom.transform, initialTransform);
            }});

            // Create Sankey generator
            sankey = d3.sankey()
                .nodeWidth(30)
                .nodePadding(20)
                .extent([[1, 1], [width - 1, height - 1]])
                .nodeId(d => d.index)
                .nodeAlign(d3.sankeyLeft)
                .nodeSort((a, b) => {{
                    // Sort nodes by amount descending (highest at top)
                    // This preserves the order we set in the data
                    return b.amount - a.amount;
                }});

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
            const linkColor = d => linkColors[d.type] || '#666';

            // Add links
            link = g.append("g")
                .attr("class", "links")
                .selectAll("path")
                .data(links)
                .enter()
                .append("path")
                .attr("class", "link")
                .attr("d", d3.sankeyLinkHorizontal())
                .attr("stroke", d => linkColor(d.source))
                .attr("stroke-width", d => Math.max(1, d.width));

            // Add nodes
            node = g.append("g")
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
                .style("fill", "#f3f4f6")
                .style("font-weight", "600")
                .text(d => d.name)
                .append("tspan")
                .attr("x", d => d.x0 < width / 2 ? d.x1 + 6 : d.x0 - 6)
                .attr("dy", "1.2em")
                .style("fill", "#7dd3fc")
                .style("font-size", "10px")
                .style("font-weight", "500")
                .style("font-family", "'Segoe UI', 'Roboto', 'Helvetica Neue', sans-serif")
                .text(d => `€${{d.amount.toLocaleString('en-IE', {{maximumFractionDigits: 0}})}} (${{d.percentage.toFixed(1)}}%)`);

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
                }})
                .on("mouseout", function() {{
                    resetHighlight();
                }})
                .on("click", function(event, d) {{
                    handleNodeClick(d);
                }});

            // Link hover
            link
                .on("mouseover", function(event, d) {{
                    highlightConnected(d, false);
                }})
                .on("mouseout", function() {{
                    resetHighlight();
                }});
        }}

        // Fullscreen functionality
        const chartContainer = document.getElementById('chart-container');
        const fullscreenBtn = document.getElementById('fullscreen-toggle');

        fullscreenBtn.addEventListener('click', () => {{
            if (!document.fullscreenElement) {{
                // Enter fullscreen
                if (chartContainer.requestFullscreen) {{
                    chartContainer.requestFullscreen();
                }} else if (chartContainer.webkitRequestFullscreen) {{
                    chartContainer.webkitRequestFullscreen();
                }} else if (chartContainer.mozRequestFullScreen) {{
                    chartContainer.mozRequestFullScreen();
                }} else if (chartContainer.msRequestFullscreen) {{
                    chartContainer.msRequestFullscreen();
                }}
            }} else {{
                // Exit fullscreen
                if (document.exitFullscreen) {{
                    document.exitFullscreen();
                }} else if (document.webkitExitFullscreen) {{
                    document.webkitExitFullscreen();
                }} else if (document.mozCancelFullScreen) {{
                    document.mozCancelFullScreen();
                }} else if (document.msExitFullscreen) {{
                    document.msExitFullscreen();
                }}
            }}
        }});

        // Update button icon and redraw chart on fullscreen state change
        document.addEventListener('fullscreenchange', handleFullscreenChange);
        document.addEventListener('webkitfullscreenchange', handleFullscreenChange);
        document.addEventListener('mozfullscreenchange', handleFullscreenChange);
        document.addEventListener('MSFullscreenChange', handleFullscreenChange);

        function handleFullscreenChange() {{
            if (document.fullscreenElement || document.webkitFullscreenElement ||
                document.mozFullScreenElement || document.msFullscreenElement) {{
                fullscreenBtn.textContent = '⛶';  // Exit fullscreen icon
                fullscreenBtn.title = 'Exit Fullscreen';
            }} else {{
                fullscreenBtn.textContent = '⛶';  // Enter fullscreen icon
                fullscreenBtn.title = 'Toggle Fullscreen';
            }}

            // Redraw chart after a short delay to allow CSS transitions
            setTimeout(() => {{
                drawChart();
            }}, 100);
        }}

        // Initial draw
        drawChart();
    </script>
</body>
</html>
'''

    return html
