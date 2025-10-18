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
    fig = go.Figure(go.Waterfall(
        x=categories,
        y=values,
        connector={"line": {"color": "rgb(63, 63, 63)"}},
        increasing={"marker": {"color": "#4ade80"}},
        decreasing={"marker": {"color": "#f87171"}},
        totals={"marker": {"color": "#60a5fa"}}
    ))

    fig.update_layout(
        title=title,
        height=height,
        margin=dict(t=50, b=50, l=50, r=20),
        showlegend=False
    )

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

    # Income bars (green)
    fig.add_trace(go.Bar(
        x=df_copy[x],
        y=df_copy[income_col],
        name='Income',
        marker=dict(color='#4ade80')
    ))

    # Expense bars (red) - already negative values
    fig.add_trace(go.Bar(
        x=df_copy[x],
        y=df_copy[expense_col],
        name='Expenses',
        marker=dict(color='#f87171')
    ))

    # Net flow line (blue)
    fig.add_trace(go.Scatter(
        x=df_copy[x],
        y=df_copy['net_flow'],
        name='Net Flow',
        mode='lines+markers',
        line=dict(color='#60a5fa', width=3),
        marker=dict(size=8),
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

    # Spent amount (red)
    fig.add_trace(go.Bar(
        x=df[name_col],
        y=df[spent_col],
        name='Spent',
        marker=dict(color='#f87171'),
        text=df[spent_col].apply(lambda x: f'€{x:,.0f}'),
        textposition='inside'
    ))

    # Remaining amount (green)
    fig.add_trace(go.Bar(
        x=df[name_col],
        y=df[remaining_col],
        name='Remaining',
        marker=dict(color='#4ade80'),
        text=df[remaining_col].apply(lambda x: f'€{x:,.0f}' if x > 0 else ''),
        textposition='inside'
    ))

    # Add a line for budget limit
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
    height: int = 250
) -> go.Figure:
    """
    Create a gauge chart for budget utilization.

    Args:
        budget_name: Name of the budget
        utilization_pct: Utilization percentage (0-100+)
        height: Chart height in pixels

    Returns:
        Plotly Figure object
    """
    # Determine color based on utilization
    if utilization_pct >= 100:
        bar_color = "#f87171"  # Red
    elif utilization_pct >= 80:
        bar_color = "#fbbf24"  # Yellow
    else:
        bar_color = "#4ade80"  # Green

    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=utilization_pct,
        title={'text': budget_name, 'font': {'size': 16}},
        number={'suffix': '%', 'font': {'size': 20}},
        gauge={
            'axis': {'range': [None, max(100, utilization_pct)]},
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
        margin=dict(t=50, b=20, l=20, r=20)
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
        yaxis_title='Amount per Day (€)',
        height=height,
        margin=dict(t=50, b=50, l=50, r=20),
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
