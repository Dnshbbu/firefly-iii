"""Chart utilities for Firefly III Dashboard

Reusable chart creation functions using Plotly.
"""

import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from typing import List, Optional


def create_line_chart(
    df: pd.DataFrame,
    x: str,
    y: str,
    title: str,
    xaxis_title: Optional[str] = None,
    yaxis_title: Optional[str] = None,
    color: Optional[str] = None,
    height: int = 400
) -> go.Figure:
    """
    Create a line chart.

    Args:
        df: DataFrame with data
        x: Column name for x-axis
        y: Column name for y-axis
        title: Chart title
        xaxis_title: X-axis label (defaults to x)
        yaxis_title: Y-axis label (defaults to y)
        color: Color for the line
        height: Chart height in pixels

    Returns:
        Plotly Figure object
    """
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=df[x],
        y=df[y],
        mode='lines+markers',
        line=dict(color=color or '#60a5fa', width=2),
        marker=dict(size=6)
    ))

    fig.update_layout(
        title=title,
        xaxis_title=xaxis_title or x,
        yaxis_title=yaxis_title or y,
        height=height,
        margin=dict(t=50, b=50, l=50, r=20),
        hovermode='x unified'
    )

    return fig


def create_bar_chart(
    df: pd.DataFrame,
    x: str,
    y: str,
    title: str,
    xaxis_title: Optional[str] = None,
    yaxis_title: Optional[str] = None,
    color: Optional[str] = None,
    orientation: str = 'v',
    height: int = 400
) -> go.Figure:
    """
    Create a bar chart.

    Args:
        df: DataFrame with data
        x: Column name for x-axis
        y: Column name for y-axis
        title: Chart title
        xaxis_title: X-axis label
        yaxis_title: Y-axis label
        color: Bar color
        orientation: 'v' for vertical, 'h' for horizontal
        height: Chart height in pixels

    Returns:
        Plotly Figure object
    """
    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=df[x] if orientation == 'v' else df[y],
        y=df[y] if orientation == 'v' else df[x],
        orientation=orientation,
        marker=dict(color=color or '#60a5fa')
    ))

    fig.update_layout(
        title=title,
        xaxis_title=xaxis_title or (x if orientation == 'v' else y),
        yaxis_title=yaxis_title or (y if orientation == 'v' else x),
        height=height,
        margin=dict(t=50, b=50, l=50, r=20)
    )

    return fig


def create_combo_chart(
    df: pd.DataFrame,
    x: str,
    y1: str,
    y2: str,
    title: str,
    y1_name: str = 'Series 1',
    y2_name: str = 'Series 2',
    y1_color: str = '#4ade80',
    y2_color: str = '#f87171',
    height: int = 400
) -> go.Figure:
    """
    Create a combination bar + line chart.

    Args:
        df: DataFrame with data
        x: Column name for x-axis
        y1: Column name for first y-axis (bars)
        y2: Column name for second y-axis (bars)
        title: Chart title
        y1_name: Legend name for first series
        y2_name: Legend name for second series
        y1_color: Color for first series
        y2_color: Color for second series
        height: Chart height in pixels

    Returns:
        Plotly Figure object
    """
    fig = go.Figure()

    # Add first series (bars)
    fig.add_trace(go.Bar(
        x=df[x],
        y=df[y1],
        name=y1_name,
        marker=dict(color=y1_color)
    ))

    # Add second series (bars)
    fig.add_trace(go.Bar(
        x=df[x],
        y=df[y2],
        name=y2_name,
        marker=dict(color=y2_color)
    ))

    fig.update_layout(
        title=title,
        xaxis_title='Date',
        yaxis_title='Amount',
        height=height,
        margin=dict(t=50, b=50, l=50, r=20),
        barmode='group',
        hovermode='x unified'
    )

    return fig


def create_waterfall_chart(
    categories: List[str],
    values: List[float],
    title: str,
    height: int = 400
) -> go.Figure:
    """
    Create a waterfall chart.

    Args:
        categories: List of category names
        values: List of values (positive for increases, negative for decreases)
        title: Chart title
        height: Chart height in pixels

    Returns:
        Plotly Figure object
    """
    # Create measure list: 'relative' for intermediate values, 'total' for first and last
    measure = ['total'] + ['relative'] * (len(values) - 2) + ['total'] if len(values) > 2 else ['total'] * len(values)

    fig = go.Figure(go.Waterfall(
        x=categories,
        y=values,
        measure=measure,
        connector={"line": {"color": "rgb(63, 63, 63)"}},
        increasing={"marker": {"color": "#4ade80"}},
        decreasing={"marker": {"color": "#f87171"}},
        totals={"marker": {"color": "#60a5fa"}},
        text=[f'€{v:,.0f}' if v != 0 else '' for v in values],
        textposition='outside',
        textfont=dict(size=9)
    ))

    # Calculate y-axis range to accommodate outside text labels
    # Add 20% padding on both top and bottom for labels
    if values:
        max_value = max(values)
        min_value = min(values)
        value_range = max_value - min_value
        padding = value_range * 0.20 if value_range > 0 else abs(max(max_value, abs(min_value))) * 0.20
        y_min = min_value - padding
        y_max = max_value + padding
    else:
        y_min = None
        y_max = None

    fig.update_layout(
        title=title,
        height=height,
        margin=dict(t=50, b=50, l=50, r=20),
        showlegend=False,
        yaxis=dict(range=[y_min, y_max]) if y_min is not None else {}
    )

    # Enable automargin to prevent cutoff
    fig.update_xaxes(automargin=True)
    fig.update_yaxes(automargin=True)

    return fig


def create_pie_chart(
    df: pd.DataFrame,
    labels: str,
    values: str,
    title: str,
    colors: Optional[List[str]] = None,
    hole: float = 0.3,
    height: int = 400
) -> go.Figure:
    """
    Create a pie/donut chart.

    Args:
        df: DataFrame with data
        labels: Column name for labels
        values: Column name for values
        title: Chart title
        colors: Optional list of colors
        hole: Size of center hole (0 = pie chart, 0.3 = donut chart)
        height: Chart height in pixels

    Returns:
        Plotly Figure object
    """
    fig = go.Figure(data=[go.Pie(
        labels=df[labels],
        values=df[values],
        hole=hole,
        marker=dict(colors=colors or px.colors.qualitative.Set3)
    )])

    fig.update_layout(
        title=title,
        height=height,
        margin=dict(t=50, b=20, l=20, r=20)
    )

    return fig


def create_stacked_area_chart(
    df: pd.DataFrame,
    x: str,
    y_columns: List[str],
    title: str,
    xaxis_title: Optional[str] = None,
    yaxis_title: Optional[str] = None,
    height: int = 400
) -> go.Figure:
    """
    Create a stacked area chart.

    Args:
        df: DataFrame with data
        x: Column name for x-axis
        y_columns: List of column names for y-axis (will be stacked)
        title: Chart title
        xaxis_title: X-axis label
        yaxis_title: Y-axis label
        height: Chart height in pixels

    Returns:
        Plotly Figure object
    """
    fig = go.Figure()

    for column in y_columns:
        fig.add_trace(go.Scatter(
            x=df[x],
            y=df[column],
            name=column,
            mode='lines',
            stackgroup='one',
            fillcolor=None  # Use default colors
        ))

    fig.update_layout(
        title=title,
        xaxis_title=xaxis_title or x,
        yaxis_title=yaxis_title or 'Amount',
        height=height,
        margin=dict(t=50, b=50, l=50, r=20),
        hovermode='x unified'
    )

    return fig


def create_gauge_chart(
    value: float,
    max_value: float,
    title: str,
    threshold_colors: Optional[List[dict]] = None,
    height: int = 300
) -> go.Figure:
    """
    Create a gauge chart.

    Args:
        value: Current value
        max_value: Maximum value
        title: Chart title
        threshold_colors: Optional list of threshold color dictionaries
        height: Chart height in pixels

    Returns:
        Plotly Figure object
    """
    if threshold_colors is None:
        threshold_colors = [
            {'range': [0, max_value * 0.5], 'color': "#4ade80"},
            {'range': [max_value * 0.5, max_value * 0.8], 'color': "#fbbf24"},
            {'range': [max_value * 0.8, max_value], 'color': "#f87171"}
        ]

    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=value,
        title={'text': title},
        gauge={
            'axis': {'range': [None, max_value]},
            'bar': {'color': "#60a5fa"},
            'steps': threshold_colors,
            'threshold': {
                'line': {'color': "white", 'width': 4},
                'thickness': 0.75,
                'value': value
            }
        }
    ))

    fig.update_layout(
        height=height,
        margin=dict(t=50, b=20, l=20, r=20)
    )

    return fig


def create_net_flow_chart(
    df: pd.DataFrame,
    x: str,
    income_col: str,
    expense_col: str,
    title: str,
    height: int = 400
) -> go.Figure:
    """
    Create a cash flow chart with income, expenses, and net flow line.

    Args:
        df: DataFrame with data
        x: Column name for x-axis (usually date)
        income_col: Column name for income
        expense_col: Column name for expenses
        title: Chart title
        height: Chart height in pixels

    Returns:
        Plotly Figure object
    """
    # Calculate net flow
    df_copy = df.copy()
    df_copy['net_flow'] = df_copy[income_col] + df_copy[expense_col]

    fig = go.Figure()

    # Income bars (green) with data labels
    fig.add_trace(go.Bar(
        x=df_copy[x],
        y=df_copy[income_col],
        name='Income',
        marker=dict(color='#4ade80'),
        text=df_copy[income_col].apply(lambda v: f'€{v:,.0f}' if v != 0 else ''),
        textposition='outside',
        textfont=dict(size=9)
    ))

    # Expense bars (red) - already negative values with data labels
    fig.add_trace(go.Bar(
        x=df_copy[x],
        y=df_copy[expense_col],
        name='Expenses',
        marker=dict(color='#f87171'),
        text=df_copy[expense_col].apply(lambda v: f'€{abs(v):,.0f}' if v != 0 else ''),
        textposition='outside',
        textfont=dict(size=9)
    ))

    # Net flow line (blue) with data labels
    fig.add_trace(go.Scatter(
        x=df_copy[x],
        y=df_copy['net_flow'],
        name='Net Flow',
        mode='lines+markers+text',
        line=dict(color='#60a5fa', width=3),
        marker=dict(size=8),
        text=df_copy['net_flow'].apply(lambda v: f'€{v:,.0f}'),
        textposition='top center',
        textfont=dict(size=9),
        yaxis='y'
    ))

    fig.update_layout(
        title=title,
        xaxis_title='Date',
        yaxis_title='Amount',
        height=height,
        margin=dict(t=50, b=50, l=50, r=20),
        barmode='relative',
        hovermode='x unified',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )

    return fig


def create_budget_vs_actual_chart(
    df: pd.DataFrame,
    budget_col: str = 'budgeted',
    spent_col: str = 'spent',
    remaining_col: str = 'remaining',
    name_col: str = 'budget_name',
    title: str = 'Budget vs. Actual',
    height: int = 400
) -> go.Figure:
    """
    Create a stacked bar chart showing budgeted, spent, and remaining amounts.
    Uses green for under-budget and red for over-budget to make status intuitive.

    Args:
        df: DataFrame with budget data
        budget_col: Column name for budgeted amount
        spent_col: Column name for spent amount
        remaining_col: Column name for remaining amount
        name_col: Column name for budget names
        title: Chart title
        height: Chart height in pixels

    Returns:
        Plotly Figure object
    """
    fig = go.Figure()

    # Separate data into under-budget and over-budget
    df_copy = df.copy()
    df_copy['is_over_budget'] = df_copy[remaining_col] < 0
    
    # For under-budget: show spent (green) + remaining (lighter green)
    under_budget_mask = ~df_copy['is_over_budget']
    if under_budget_mask.any():
        # Spent amount for under-budget items (green)
        fig.add_trace(go.Bar(
            x=df_copy[under_budget_mask][name_col],
            y=df_copy[under_budget_mask][spent_col],
            name='Spent (Under Budget)',
            marker=dict(color='#4ade80'),  # Green
            text=df_copy[under_budget_mask][spent_col].apply(lambda x: f'€{x:,.0f}'),
            textposition='inside',
            legendgroup='under'
        ))

        # Remaining amount for under-budget items (lighter green)
        fig.add_trace(go.Bar(
            x=df_copy[under_budget_mask][name_col],
            y=df_copy[under_budget_mask][remaining_col],
            name='Remaining',
            marker=dict(color='#86efac'),  # Lighter green
            text=df_copy[under_budget_mask][remaining_col].apply(lambda x: f'€{x:,.0f}' if x > 0 else ''),
            textposition='inside',
            legendgroup='under'
        ))
    
    # For over-budget: show budgeted (orange) + overspent (red)
    over_budget_mask = df_copy['is_over_budget']
    if over_budget_mask.any():
        # Budgeted amount for over-budget items (orange/warning)
        fig.add_trace(go.Bar(
            x=df_copy[over_budget_mask][name_col],
            y=df_copy[over_budget_mask][budget_col],
            name='Budgeted Amount',
            marker=dict(color='#fb923c'),  # Orange
            text=df_copy[over_budget_mask][budget_col].apply(lambda x: f'€{x:,.0f}'),
            textposition='inside',
            legendgroup='over'
        ))

        # Over-budget amount (red) - show the excess above budget
        df_copy['overspent'] = df_copy.apply(
            lambda row: row[spent_col] - row[budget_col] if row['is_over_budget'] else 0,
            axis=1
        )
        fig.add_trace(go.Bar(
            x=df_copy[over_budget_mask][name_col],
            y=df_copy[over_budget_mask]['overspent'],
            name='Over Budget',
            marker=dict(color='#ef4444'),  # Red
            text=df_copy[over_budget_mask]['overspent'].apply(lambda x: f'€{x:,.0f}' if x > 0 else ''),
            textposition='inside',
            legendgroup='over'
        ))

    # Add a marker for budget limit (yellow diamond)
    fig.add_trace(go.Scatter(
        x=df[name_col],
        y=df[budget_col],
        name='Budget Limit',
        mode='markers',
        marker=dict(color='#fbbf24', size=10, symbol='diamond'),
        showlegend=True
    ))

    fig.update_layout(
        title=title,
        xaxis_title='Budget',
        yaxis_title='Amount (€)',
        height=height,
        margin=dict(t=50, b=100, l=50, r=20),
        barmode='stack',
        hovermode='x unified',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )

    return fig


def create_budget_utilization_gauges(
    budget_name: str,
    utilization_pct: float,
    height: int = 250,
    total_budgeted: float = None,
    total_spent: float = None,
    avg_spent: float = None
) -> go.Figure:
    """
    Create a gauge chart for budget utilization.

    Args:
        budget_name: Name of the budget
        utilization_pct: Utilization percentage (0-100+)
        height: Chart height in pixels
        total_budgeted: Total budgeted amount (optional)
        total_spent: Total spent amount (optional)
        avg_spent: Average monthly spending (optional)

    Returns:
        Plotly Figure object
    """
    # Determine color based on utilization
    if utilization_pct >= 100:
        bar_color = "#f87171"  # Red
        delta_color = "red"
    elif utilization_pct >= 80:
        bar_color = "#fbbf24"  # Yellow
        delta_color = "orange"
    else:
        bar_color = "#4ade80"  # Green
        delta_color = "green"

    # Build title with optional information
    if avg_spent is not None:
        title_text = f"{budget_name}<br><sub>Avg: €{avg_spent:,.2f}/mo</sub>"
    else:
        title_text = budget_name

    # Build number display with additional information
    if total_spent is not None and total_budgeted is not None:
        # Calculate difference
        difference = round(total_spent - total_budgeted, 2)

        # Format delta text with proper sign and arrow
        if difference > 0:
            arrow = "▲"  # Up arrow for over budget
            delta_text = f"{arrow} +€{abs(difference):,.2f}"
        elif difference < 0:
            arrow = "▼"  # Down arrow for under budget
            delta_text = f"{arrow} -€{abs(difference):,.2f}"
        else:
            arrow = ""
            delta_text = "€0.00"

        # Use mode="gauge+number" without delta to avoid the automatic colored percentage
        # Shift the gauge up by adjusting the domain to make room for annotations below
        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=utilization_pct,
            title={'text': title_text, 'font': {'size': 14}},
            number={'suffix': '%', 'font': {'size': 20}},
            domain={'x': [0, 1], 'y': [0.20, 1]},  # Shift gauge up by starting at 0.20 to create more space below
            gauge={
                'axis': {'range': [None, max(100, utilization_pct)], 'tickfont': {'size': 10}},
                'bar': {'color': bar_color},
                'steps': [
                    {'range': [0, 50], 'color': "rgba(74, 222, 128, 0.2)"},
                    {'range': [50, 80], 'color': "rgba(74, 222, 128, 0.3)"},
                    {'range': [80, 100], 'color': "rgba(251, 191, 36, 0.3)"},
                    {'range': [100, max(100, utilization_pct)], 'color': "rgba(248, 113, 113, 0.3)"}
                ],
                'threshold': {
                    'line': {'color': "white", 'width': 4},
                    'thickness': 0.75,
                    'value': 100
                }
            }
        ))

        # Add annotations for total spent and difference below the gauge with more spacing
        # Position spent amount in the space below the gauge
        fig.add_annotation(
            text=f"€{total_spent:,.2f}",
            xref="paper", yref="paper",
            x=0.5, y=0.12,
            showarrow=False,
            font=dict(size=12),
            xanchor='center',
            yanchor='middle'
        )

        # Position difference at the very bottom with more spacing
        fig.add_annotation(
            text=delta_text,
            xref="paper", yref="paper",
            x=0.5, y=0.04,
            showarrow=False,
            font=dict(size=12, color=delta_color),
            xanchor='center',
            yanchor='middle'
        )
    else:
        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=utilization_pct,
            title={'text': title_text, 'font': {'size': 14}},
            number={'suffix': '%', 'font': {'size': 20}, 'prefix': ''},
            gauge={
                'axis': {'range': [None, max(100, utilization_pct)], 'tickfont': {'size': 10}},
                'bar': {'color': bar_color},
                'steps': [
                    {'range': [0, 50], 'color': "rgba(74, 222, 128, 0.2)"},
                    {'range': [50, 80], 'color': "rgba(74, 222, 128, 0.3)"},
                    {'range': [80, 100], 'color': "rgba(251, 191, 36, 0.3)"},
                    {'range': [100, max(100, utilization_pct)], 'color': "rgba(248, 113, 113, 0.3)"}
                ],
                'threshold': {
                    'line': {'color': "white", 'width': 4},
                    'thickness': 0.75,
                    'value': 100
                }
            }
        ))

    fig.update_layout(
        height=height,
        margin=dict(t=60, b=15, l=30, r=30)
    )

    return fig


def create_burn_rate_chart(
    burn_rate: float,
    daily_budget: float,
    title: str = 'Daily Burn Rate',
    height: int = 300
) -> go.Figure:
    """
    Create a comparison chart of actual burn rate vs. ideal daily budget.

    Args:
        burn_rate: Actual daily spending rate
        daily_budget: Ideal daily budget
        title: Chart title
        height: Chart height in pixels

    Returns:
        Plotly Figure object
    """
    categories = ['Ideal Daily Budget', 'Actual Burn Rate']
    values = [daily_budget, burn_rate]
    colors = ['#60a5fa', '#f87171' if burn_rate > daily_budget else '#4ade80']

    # Calculate y-axis range to accommodate outside text labels
    max_value = max(values)
    y_max = max_value * 1.15  # Add 15% padding for labels

    fig = go.Figure(data=[
        go.Bar(
            x=categories,
            y=values,
            marker=dict(color=colors),
            text=[f'€{v:,.2f}' for v in values],
            textposition='outside'
        )
    ])

    fig.update_layout(
        title=title,
        yaxis=dict(
            title='Amount per Day (€)',
            range=[0, y_max]
        ),
        height=height,
        margin=dict(t=70, b=50, l=50, r=20),
        showlegend=False
    )

    return fig


def create_budget_progress_bars(
    df: pd.DataFrame,
    name_col: str = 'budget_name',
    utilization_col: str = 'utilization_pct',
    height: int = 400
) -> go.Figure:
    """
    Create horizontal progress bars for each budget.

    Args:
        df: DataFrame with budget data
        name_col: Column name for budget names
        utilization_col: Column name for utilization percentage
        height: Chart height in pixels

    Returns:
        Plotly Figure object
    """
    # Sort by utilization descending
    df_sorted = df.sort_values(utilization_col, ascending=True)

    # Determine colors based on utilization
    colors = []
    for pct in df_sorted[utilization_col]:
        if pct >= 100:
            colors.append('#f87171')  # Red
        elif pct >= 80:
            colors.append('#fbbf24')  # Yellow
        else:
            colors.append('#4ade80')  # Green

    fig = go.Figure()

    fig.add_trace(go.Bar(
        y=df_sorted[name_col],
        x=df_sorted[utilization_col],
        orientation='h',
        marker=dict(color=colors),
        text=df_sorted[utilization_col].apply(lambda x: f'{x:.1f}%'),
        textposition='auto'
    ))

    fig.update_layout(
        title='Budget Utilization',
        xaxis_title='Utilization (%)',
        yaxis_title='Budget',
        height=max(height, len(df_sorted) * 40),
        margin=dict(t=50, b=50, l=150, r=20),
        showlegend=False
    )

    # Add vertical line at 100%
    fig.add_vline(x=100, line_dash="dash", line_color="white", opacity=0.5)

    return fig


def create_category_trend_chart(
    df: pd.DataFrame,
    categories: List[str],
    title: str = 'Category Spending Trends',
    height: int = 500
) -> go.Figure:
    """
    Create a multi-line chart showing spending trends for multiple categories.

    Args:
        df: DataFrame with columns: date, category_name, amount
        categories: List of category names to display
        title: Chart title
        height: Chart height in pixels

    Returns:
        Plotly Figure object
    """
    fig = go.Figure()

    for category in categories:
        category_data = df[df['category_name'] == category]

        if not category_data.empty:
            fig.add_trace(go.Scatter(
                x=category_data['date'],
                y=category_data['amount'],
                name=category,
                mode='lines+markers',
                line=dict(width=2),
                marker=dict(size=6)
            ))

    fig.update_layout(
        title=title,
        xaxis_title='Date',
        yaxis_title='Amount (€)',
        height=height,
        margin=dict(t=80, b=50, l=50, r=20),  # Reduced top margin with compact buttons
        hovermode='x unified',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        updatemenus=[
            dict(
                type="buttons",
                direction="down",  # Stack vertically
                buttons=[
                    dict(
                        label="👁",  # Eye icon for Show All
                        method="restyle",
                        args=["visible", True]
                    ),
                    dict(
                        label="⦻",  # Circle with X for Hide All
                        method="restyle",
                        args=["visible", "legendonly"]
                    )
                ],
                pad={"r": 5, "t": 5},
                showactive=False,
                x=1.0,
                xanchor="right",
                y=1.08,  # Positioned closer to chart
                yanchor="top",
                bgcolor="rgba(0,0,0,0.05)",  # Subtle background
                bordercolor="rgba(255,255,255,0.2)",
                borderwidth=1,
                font=dict(size=16)  # Larger icon size
            )
        ]
    )

    return fig


def create_treemap_chart(
    df: pd.DataFrame,
    labels_col: str,
    values_col: str,
    title: str = 'Category Breakdown',
    height: int = 500
) -> go.Figure:
    """
    Create a treemap visualization for hierarchical category data.

    Args:
        df: DataFrame with category data
        labels_col: Column name for labels
        values_col: Column name for values
        title: Chart title
        height: Chart height in pixels

    Returns:
        Plotly Figure object
    """
    fig = go.Figure(go.Treemap(
        labels=df[labels_col],
        parents=[""] * len(df),  # All top-level
        values=df[values_col],
        textinfo="label+value+percent parent",
        marker=dict(
            colorscale='Reds',
            cmid=df[values_col].median()
        )
    ))

    fig.update_layout(
        title=title,
        height=height,
        margin=dict(t=50, b=20, l=20, r=20)
    )

    return fig


def create_pareto_chart(
    df: pd.DataFrame,
    category_col: str = 'category_name',
    amount_col: str = 'amount',
    cumulative_col: str = 'cumulative_pct',
    title: str = 'Pareto Analysis (80/20 Rule)',
    height: int = 500
) -> go.Figure:
    """
    Create a Pareto chart showing category distribution and cumulative percentage.

    Args:
        df: DataFrame with category data (should be pre-sorted by amount descending)
        category_col: Column name for categories
        amount_col: Column name for amounts
        cumulative_col: Column name for cumulative percentage
        title: Chart title
        height: Chart height in pixels

    Returns:
        Plotly Figure object
    """
    fig = go.Figure()

    # Bar chart for amounts
    fig.add_trace(go.Bar(
        x=df[category_col],
        y=df[amount_col],
        name='Amount',
        marker=dict(color='#f87171'),
        yaxis='y'
    ))

    # Line chart for cumulative percentage
    fig.add_trace(go.Scatter(
        x=df[category_col],
        y=df[cumulative_col],
        name='Cumulative %',
        mode='lines+markers',
        line=dict(color='#60a5fa', width=3),
        marker=dict(size=8),
        yaxis='y2'
    ))

    # Add 80% threshold line
    fig.add_hline(
        y=80,
        line_dash="dash",
        line_color="#fbbf24",
        annotation_text="80%",
        annotation_position="right",
        yref='y2'
    )

    fig.update_layout(
        title=title,
        xaxis_title='Category',
        yaxis_title='Amount (€)',
        yaxis2=dict(
            title='Cumulative %',
            overlaying='y',
            side='right',
            range=[0, 105]
        ),
        height=height,
        margin=dict(t=50, b=100, l=50, r=80),
        hovermode='x unified',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )

    return fig


def create_category_comparison_chart(
    df: pd.DataFrame,
    category_name: str,
    title: str = None,
    height: int = 400
) -> go.Figure:
    """
    Create a month-over-month comparison chart for a specific category.

    Args:
        df: DataFrame with columns: month, amount, change, change_pct
        category_name: Name of the category
        title: Chart title (defaults to category name)
        height: Chart height in pixels

    Returns:
        Plotly Figure object
    """
    if title is None:
        title = f'{category_name} - Monthly Trend'

    fig = go.Figure()

    # Bar chart for monthly amounts
    fig.add_trace(go.Bar(
        x=df['month'].dt.strftime('%b %Y'),
        y=df['amount'],
        name='Monthly Spending',
        marker=dict(color='#f87171'),
        text=df['amount'].apply(lambda x: f'€{x:,.0f}'),
        textposition='outside'
    ))

    # Line for month-over-month change percentage
    fig.add_trace(go.Scatter(
        x=df['month'].dt.strftime('%b %Y'),
        y=df['change_pct'],
        name='MoM Change %',
        mode='lines+markers',
        line=dict(color='#60a5fa', width=2),
        marker=dict(size=8),
        yaxis='y2'
    ))

    # Calculate y-axis range to accommodate outside text labels
    max_value = df['amount'].max()
    y_max = max_value * 1.15  # Add 15% padding for labels

    fig.update_layout(
        title=title,
        xaxis_title='Month',
        yaxis=dict(
            title='Amount (€)',
            range=[0, y_max]
        ),
        yaxis2=dict(
            title='Change (%)',
            overlaying='y',
            side='right'
        ),
        height=height,
        margin=dict(t=80, b=50, l=50, r=80),
        hovermode='x unified',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )

    return fig


def create_tag_distribution_chart(
    df: pd.DataFrame,
    title: str = 'Tag Distribution',
    height: int = 400
) -> go.Figure:
    """
    Create a pie chart showing transaction distribution by tags.

    Args:
        df: DataFrame with columns: tag_name, transaction_count
        title: Chart title
        height: Chart height in pixels

    Returns:
        Plotly Figure object
    """
    fig = go.Figure()

    fig.add_trace(go.Pie(
        labels=df['tag_name'],
        values=df['transaction_count'],
        hole=0.3,
        textinfo='label+percent',
        textposition='auto'
    ))

    fig.update_layout(
        title=title,
        height=height,
        margin=dict(t=50, b=20, l=20, r=20),
        showlegend=True,
        legend=dict(
            orientation="v",
            yanchor="middle",
            y=0.5,
            xanchor="left",
            x=1.02
        )
    )

    return fig


def create_tag_timeline_chart(
    df: pd.DataFrame,
    title: str = 'Tag Usage Timeline',
    height: int = 500
) -> go.Figure:
    """
    Create a timeline chart showing tag usage over time.

    Args:
        df: DataFrame with date, tag_name, and transaction_count columns
        title: Chart title
        height: Chart height in pixels

    Returns:
        Plotly Figure object
    """
    fig = go.Figure()

    # Get unique tags
    unique_tags = df['tag_name'].unique()

    for tag in unique_tags:
        tag_data = df[df['tag_name'] == tag]

        fig.add_trace(go.Scatter(
            x=tag_data['date'],
            y=tag_data['transaction_count'],
            name=tag,
            mode='lines+markers',
            line=dict(width=2),
            marker=dict(size=6)
        ))

    fig.update_layout(
        title=title,
        xaxis_title='Date',
        yaxis_title='Transaction Count',
        height=height,
        margin=dict(t=50, b=50, l=50, r=20),
        hovermode='x unified',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )

    return fig


def create_import_batch_chart(
    df: pd.DataFrame,
    title: str = 'Import Batches',
    height: int = 400
) -> go.Figure:
    """
    Create a bar chart showing import batches by date.

    Args:
        df: DataFrame with import_date and transaction_count columns
        title: Chart title
        height: Chart height in pixels

    Returns:
        Plotly Figure object
    """
    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=df['import_date'].astype(str),
        y=df['transaction_count'],
        marker=dict(color='#60a5fa'),
        text=df['transaction_count'],
        textposition='outside',
        hovertemplate='<b>%{x}</b><br>Transactions: %{y}<br><extra></extra>'
    ))

    # Calculate y-axis range to accommodate outside text labels
    max_value = df['transaction_count'].max()
    y_max = max_value * 1.15  # Add 15% padding for labels

    fig.update_layout(
        title=title,
        xaxis_title='Import Date',
        yaxis=dict(
            title='Transaction Count',
            range=[0, y_max]
        ),
        height=height,
        margin=dict(t=50, b=80, l=50, r=20),
        showlegend=False
    )

    return fig


def create_gap_analysis_chart(
    df: pd.DataFrame,
    title: str = 'Import Gap Analysis by Tag',
    height: int = 400
) -> go.Figure:
    """
    Create a bar chart showing average gap between transaction date and import date.

    Args:
        df: DataFrame with tag_name and avg_gap_days columns
        title: Chart title
        height: Chart height in pixels

    Returns:
        Plotly Figure object
    """
    fig = go.Figure()

    # Create color scale based on gap (negative = imported before transaction date)
    colors = ['#f87171' if x < 0 else '#60a5fa' for x in df['avg_gap_days']]

    fig.add_trace(go.Bar(
        x=df['tag_name'],
        y=df['avg_gap_days'],
        marker=dict(color=colors),
        text=df['avg_gap_days'].apply(lambda x: f'{x:.1f}d'),
        textposition='outside',
        hovertemplate='<b>%{x}</b><br>Avg Gap: %{y:.2f} days<br><extra></extra>'
    ))

    fig.update_layout(
        title=title,
        xaxis_title='Tag',
        yaxis_title='Average Gap (days)',
        height=height,
        margin=dict(t=50, b=100, l=50, r=20),
        showlegend=False
    )

    # Add horizontal line at y=0
    fig.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.5)

    return fig


def create_sankey_diagram(
    income_df: pd.DataFrame,
    expense_df: pd.DataFrame,
    income_source_col: str = 'source_name',
    income_amount_col: str = 'total_amount',
    expense_category_col: str = 'category_name',
    expense_amount_col: str = 'total_amount',
    title: str = 'Cash Flow: Income Sources → Total Income → Expenses + Remaining',
    height: int = 600,
    top_n_income: int = 10,
    top_n_expense: int = 15
) -> go.Figure:
    """
    Create a three-tier Sankey diagram showing:
    1. Income sources flowing into Total Income
    2. Total Income splitting into expense categories and remaining amount

    Args:
        income_df: DataFrame with income sources and amounts
        expense_df: DataFrame with expense categories and amounts
        income_source_col: Column name for income source names
        income_amount_col: Column name for income amounts
        expense_category_col: Column name for expense category names
        expense_amount_col: Column name for expense amounts
        title: Chart title
        height: Chart height in pixels
        top_n_income: Number of top income sources to display
        top_n_expense: Number of top expense categories to display

    Returns:
        Plotly Figure object
    """
    # Take top N income sources and expense categories
    top_income = income_df.nlargest(top_n_income, income_amount_col).copy()
    top_expenses = expense_df.nlargest(top_n_expense, expense_amount_col).copy()

    # Create node labels for income sources
    income_labels = top_income[income_source_col].tolist()

    # Add "Other Income" if there are more items
    if len(income_df) > top_n_income:
        other_income_amount = income_df.iloc[top_n_income:][income_amount_col].sum()
        if other_income_amount > 0:
            top_income = pd.concat([
                top_income,
                pd.DataFrame({
                    income_source_col: ['Other Income'],
                    income_amount_col: [other_income_amount]
                })
            ], ignore_index=True)
            income_labels.append('Other Income')

    # Add "Other Expenses" if there are more items
    expense_labels = top_expenses[expense_category_col].tolist()
    if len(expense_df) > top_n_expense:
        other_expense_amount = expense_df.iloc[top_n_expense:][expense_amount_col].sum()
        if other_expense_amount > 0:
            top_expenses = pd.concat([
                top_expenses,
                pd.DataFrame({
                    expense_category_col: ['Other Expenses'],
                    expense_amount_col: [other_expense_amount]
                })
            ], ignore_index=True)
            expense_labels.append('Other Expenses')

    # Calculate totals
    total_income = top_income[income_amount_col].sum()
    total_expenses = top_expenses[expense_amount_col].sum()
    remaining = total_income - total_expenses

    # Build node structure: [Income Sources] + [Total Income] + [Expense Categories] + [Remaining]
    # Layer 0: Income sources (left)
    # Layer 1: Total Income (middle)
    # Layer 2: Expense categories + Remaining (right)

    # Add amounts and percentages to node labels for visibility
    income_labels_with_amounts = [
        f"{label}<br>€{amount:,.0f} ({amount/total_income*100:.1f}%)"
        for label, amount in zip(income_labels, top_income[income_amount_col])
    ]

    total_income_node_label = f"💰 Total Income<br>€{total_income:,.0f} (100%)"

    expense_labels_with_amounts = [
        f"{label}<br>€{amount:,.0f} ({amount/total_income*100:.1f}%)"
        for label, amount in zip(expense_labels, top_expenses[expense_amount_col])
    ]

    remaining_pct = (remaining / total_income * 100) if total_income > 0 else 0
    remaining_node_label = f"💎 Remaining<br>€{remaining:,.0f} ({remaining_pct:.1f}%)"

    all_labels = income_labels_with_amounts + [total_income_node_label] + expense_labels_with_amounts + [remaining_node_label]

    # Calculate node indices
    total_income_idx = len(income_labels)
    first_expense_idx = total_income_idx + 1
    remaining_idx = len(all_labels) - 1

    # Create links
    sources = []
    targets = []
    values = []

    # Phase 1: Income sources → Total Income
    for i, income_row in enumerate(top_income.itertuples()):
        income_amount = getattr(income_row, income_amount_col)
        sources.append(i)  # Income source index
        targets.append(total_income_idx)  # Total Income node
        values.append(income_amount)

    # Phase 2: Total Income → Expense categories
    for i, expense_row in enumerate(top_expenses.itertuples()):
        expense_amount = getattr(expense_row, expense_amount_col)
        sources.append(total_income_idx)  # Total Income node
        targets.append(first_expense_idx + i)  # Expense category index
        values.append(expense_amount)

    # Phase 3: Total Income → Remaining (if positive)
    if remaining > 0:
        sources.append(total_income_idx)  # Total Income node
        targets.append(remaining_idx)  # Remaining node
        values.append(remaining)

    # Create color scheme
    # Layer 0: Income sources (green shades)
    income_colors = ['rgba(74, 222, 128, 0.7)'] * len(income_labels)

    # Layer 1: Total Income (blue)
    total_income_color = ['rgba(59, 130, 246, 0.8)']

    # Layer 2: Expense categories (red shades) + Remaining (bright green)
    expense_colors = ['rgba(248, 113, 113, 0.7)'] * len(expense_labels)
    remaining_color = ['rgba(34, 197, 94, 0.8)'] if remaining > 0 else ['rgba(239, 68, 68, 0.8)']

    node_colors = income_colors + total_income_color + expense_colors + remaining_color

    # Link colors
    # Green for income → total income
    income_link_colors = ['rgba(74, 222, 128, 0.3)'] * len(income_labels)
    # Red for total income → expenses
    expense_link_colors = ['rgba(248, 113, 113, 0.3)'] * len(expense_labels)
    # Green for total income → remaining (if positive)
    remaining_link_color = ['rgba(34, 197, 94, 0.4)'] if remaining > 0 else []

    link_colors = income_link_colors + expense_link_colors + remaining_link_color

    # Create custom data for hover information
    node_customdata = []

    # Income sources
    for val in top_income[income_amount_col].tolist():
        node_customdata.append(f'€{val:,.0f}')

    # Total Income
    node_customdata.append(f'€{total_income:,.0f}')

    # Expense categories
    for val in top_expenses[expense_amount_col].tolist():
        node_customdata.append(f'€{val:,.0f}')

    # Remaining
    node_customdata.append(f'€{remaining:,.0f}')

    fig = go.Figure(data=[go.Sankey(
        arrangement='snap',
        node=dict(
            pad=15,
            thickness=25,
            line=dict(color='white', width=1),
            label=all_labels,
            color=node_colors,
            customdata=node_customdata,
            hovertemplate='%{label}<br>Amount: %{customdata}<extra></extra>'
        ),
        link=dict(
            source=sources,
            target=targets,
            value=values,
            color=link_colors,
            hovertemplate='%{source.label} → %{target.label}<br>Amount: €%{value:,.0f}<extra></extra>'
        )
    )])

    fig.update_layout(
        title=title,
        height=height,
        margin=dict(t=50, b=20, l=20, r=20),
        font=dict(size=11, family='Arial, sans-serif')
    )

    return fig
