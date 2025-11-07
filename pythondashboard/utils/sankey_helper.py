"""
Helper module for creating Sankey diagrams with destination accounts.
This creates a 5-tier cash flow visualization.
"""

import plotly.graph_objects as go
import pandas as pd


def create_sankey_with_destinations(
    income_df: pd.DataFrame,
    destination_df: pd.DataFrame,
    destination_category_mapping_df: pd.DataFrame,
    income_source_col: str = 'source_name',
    income_amount_col: str = 'total_amount',
    destination_account_col: str = 'destination_name',
    destination_amount_col: str = 'total_amount',
    category_col: str = 'category_name',
    mapping_amount_col: str = 'total_amount',
    title: str = 'Complete Cash Flow Visualization',
    height: int = 700,
    top_n_income: int = 10,
    top_n_destination: int = 15,
    top_n_category: int = 15
) -> go.Figure:
    """
    Create 5-tier Sankey: Income Sources → Total Income → (Remaining + Total Expenses) → Destination Accounts → Categories

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
        title: Chart title
        height: Chart height
        top_n_income: Top N income sources
        top_n_destination: Top N destination accounts
        top_n_category: Top N categories

    Returns:
        Plotly Figure
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

    # Build labels with amounts and percentages
    income_labels = [
        f"{name}<br>€{amt:,.0f} ({amt/total_income*100:.1f}%)"
        for name, amt in zip(top_income[income_source_col], top_income[income_amount_col])
    ]

    total_income_label = f"💰 Total Income<br>€{total_income:,.0f} (100%)"

    remaining_pct = (remaining / total_income * 100) if total_income > 0 else 0
    remaining_label = f"💎 Remaining<br>€{remaining:,.0f} ({remaining_pct:.1f}%)"

    total_expenses_pct = (total_expenses / total_income * 100) if total_income > 0 else 0
    total_expenses_label = f"💸 Total Expenses<br>€{total_expenses:,.0f} ({total_expenses_pct:.1f}%)"

    destination_labels = [
        f"{name}<br>€{amt:,.0f} ({amt/total_expenses*100:.1f}%)"
        for name, amt in zip(top_destinations[destination_account_col], top_destinations[destination_amount_col])
    ]

    category_labels = [
        f"{name}<br>€{amt:,.0f} ({amt/total_expenses*100:.1f}%)"
        for name, amt in zip(top_categories[category_col], top_categories['total'])
    ]

    # Combine all labels
    # Structure: Income Sources | Total Income | Remaining + Total Expenses | Destinations | Categories
    all_labels = income_labels + [total_income_label] + [remaining_label, total_expenses_label] + destination_labels + category_labels

    # Calculate indices
    num_income = len(income_labels)
    total_income_idx = num_income
    remaining_idx = num_income + 1
    total_expenses_idx = num_income + 2
    first_dest_idx = num_income + 3
    num_destinations = len(destination_labels)
    first_category_idx = first_dest_idx + num_destinations

    # Build links
    sources = []
    targets = []
    values = []

    # Phase 1: Income sources → Total Income
    for i in range(num_income):
        sources.append(i)
        targets.append(total_income_idx)
        values.append(top_income.iloc[i][income_amount_col])

    # Phase 2: Total Income → Remaining
    if remaining > 0:
        sources.append(total_income_idx)
        targets.append(remaining_idx)
        values.append(remaining)

    # Phase 3: Total Income → Total Expenses
    sources.append(total_income_idx)
    targets.append(total_expenses_idx)
    values.append(total_expenses)

    # Phase 4: Total Expenses → Destination Accounts
    for i in range(num_destinations):
        sources.append(total_expenses_idx)
        targets.append(first_dest_idx + i)
        values.append(top_destinations.iloc[i][destination_amount_col])

    # Phase 5: Destination Accounts → Categories (using mapping)
    # Filter mapping to only include top destinations and top categories
    top_dest_names = set(top_destinations[destination_account_col].tolist())
    top_cat_names = set(top_categories[category_col].tolist())
    dest_index_map = {name: idx for idx, name in enumerate(top_destinations[destination_account_col].tolist())}
    cat_index_map = {name: idx for idx, name in enumerate(top_categories[category_col].tolist())}

    filtered_mapping = destination_category_mapping_df[
        destination_category_mapping_df[destination_account_col].isin(top_dest_names) &
        destination_category_mapping_df[category_col].isin(top_cat_names)
    ].copy()

    # Add links from destinations to categories
    for _, row in filtered_mapping.iterrows():
        dest_name = row[destination_account_col]
        cat_name = row[category_col]
        amount = row[mapping_amount_col]

        # Find indices
        dest_pos = dest_index_map.get(dest_name)
        cat_pos = cat_index_map.get(cat_name)
        if dest_pos is None or cat_pos is None:
            continue
        dest_idx = first_dest_idx + dest_pos
        cat_idx = first_category_idx + cat_pos

        sources.append(dest_idx)
        targets.append(cat_idx)
        values.append(amount)

    # Colors - using higher base opacity for better hover contrast
    income_colors = ['rgba(74, 222, 128, 0.85)'] * num_income
    total_income_color = ['rgba(59, 130, 246, 0.9)']
    remaining_color = ['rgba(34, 197, 94, 0.9)'] if remaining > 0 else ['rgba(239, 68, 68, 0.9)']
    total_expenses_color = ['rgba(251, 146, 60, 0.9)']
    destination_colors = ['rgba(255, 193, 7, 0.85)'] * num_destinations
    category_colors = ['rgba(248, 113, 113, 0.85)'] * len(category_labels)

    node_colors = income_colors + total_income_color + remaining_color + total_expenses_color + destination_colors + category_colors

    # Link colors - slightly more transparent for visual hierarchy
    income_link_colors = ['rgba(74, 222, 128, 0.4)'] * num_income
    remaining_link_color = ['rgba(34, 197, 94, 0.5)'] if remaining > 0 else []
    total_expenses_link_color = ['rgba(251, 146, 60, 0.4)']
    dest_link_colors = ['rgba(255, 193, 7, 0.4)'] * num_destinations
    cat_link_colors = ['rgba(248, 113, 113, 0.4)'] * len(filtered_mapping)

    link_colors = income_link_colors + remaining_link_color + total_expenses_link_color + dest_link_colors + cat_link_colors

    # Positions
    node_x = []
    node_y = []

    # Layer 0: Income (x=0.01)
    for i in range(num_income):
        node_x.append(0.01)
        node_y.append(i / max(1, num_income - 1) if num_income > 1 else 0.5)

    # Layer 1: Total Income (x=0.25)
    node_x.append(0.25)
    node_y.append(0.5)

    # Layer 2: Remaining + Total Expenses (x=0.50)
    node_x.append(0.50)
    node_y.append(0.05)  # Remaining at top
    node_x.append(0.50)
    node_y.append(0.5)   # Total Expenses in middle

    # Layer 3: Destinations (x=0.75)
    for i in range(num_destinations):
        node_x.append(0.75)
        if num_destinations > 1:
            y_pos = 0.2 + (i / (num_destinations - 1)) * 0.75
        else:
            y_pos = 0.5
        node_y.append(y_pos)

    # Layer 4: Categories (x=0.99)
    num_categories = len(category_labels)
    for i in range(num_categories):
        node_x.append(0.99)
        if num_categories > 1:
            y_pos = 0.2 + (i / (num_categories - 1)) * 0.75
        else:
            y_pos = 0.5
        node_y.append(y_pos)

    # Create figure with hover interactions
    fig = go.Figure(data=[go.Sankey(
        arrangement='snap',
        node=dict(
            pad=20,
            thickness=30,
            line=dict(color='white', width=1),
            label=all_labels,
            color=node_colors,
            x=node_x,
            y=node_y,
            hoverinfo='none',
            customdata=list(range(len(all_labels)))
        ),
        link=dict(
            source=sources,
            target=targets,
            value=values,
            color=link_colors,
            hoverinfo='none'
        ),
        textfont=dict(size=10, family='Arial, sans-serif'),
        valueformat='.0f',
        valuesuffix=' EUR'
    )])

    fig.update_layout(
        title=title,
        height=height,
        margin=dict(t=60, b=40, l=40, r=40),
        font=dict(size=11, family='Arial, sans-serif'),
        hoverlabel=dict(
            bgcolor="rgba(255, 255, 255, 0.95)",
            font_size=12,
            font_family="Arial"
        ),
        # This enables better hover interactions
        hovermode='closest'
    )

    return fig
