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
        margin=dict(t=100, b=50, l=50, r=20),  # Increased top margin for buttons
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
                direction="left",
                buttons=[
                    dict(
                        label="Show All",
                        method="restyle",
                        args=["visible", True]
                    ),
                    dict(
                        label="Hide All",
                        method="restyle",
                        args=["visible", "legendonly"]
                    )
                ],
                pad={"r": 10, "t": 10},
                showactive=False,
                x=0.0,
                xanchor="left",
                y=1.15,
                yanchor="top"
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
