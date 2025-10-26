# Savings Forecast Dashboard Implementation Plan

**Date:** 2025-01-26
**Status:** 📋 Planned
**Version:** 1.0

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture Decision](#architecture-decision)
3. [Part 1: Current Year Forecast](#part-1-current-year-forecast)
4. [Part 2: Long-term Retirement Calculator](#part-2-long-term-retirement-calculator)
5. [Technical Implementation](#technical-implementation)
6. [Development Phases](#development-phases)
7. [Integration Points](#integration-points)
8. [Sample User Workflows](#sample-user-workflows)
9. [Future Enhancements](#future-enhancements)

---

## Overview

### Purpose

The Savings Forecast Dashboard provides both tactical (current year) and strategic (long-term retirement) financial planning capabilities:

- **Current Year Forecast**: Answer "How much will I save by year-end?" with interactive what-if scenarios
- **Long-term Calculator**: Answer "When can I retire?" and "What will my retirement portfolio look like?" with comprehensive retirement modeling

### Key Objectives

1. **Project year-end savings** based on current trends and adjustable assumptions
2. **Interactive scenario modeling** to understand impact of income/expense changes
3. **Long-term retirement planning** with compound growth, inflation, and tax considerations
4. **Multi-year projections** (20+ years) with Monte Carlo simulation for variable returns
5. **Retirement readiness assessment** with sustainable withdrawal analysis

### Related Documentation

- [Budget Implementation](BUDGET_IMPLEMENTATION.md)
- [Cash Flow Implementation](CASH_FLOW_IMPLEMENTATION.md)
- [Category Implementation](CATEGORY_IMPLEMENTATION.md)
- [Dashboard Roadmap](DASHBOARD_ROADMAP.md)

---

## Architecture Decision

### Nested Approach (Single Page)

**File:** `pages/6_💰_Savings_Forecast.py`

**Layout:**
```
┌─────────────────────────────────────────┐
│  💰 Savings Forecast Dashboard         │
├─────────────────────────────────────────┤
│                                         │
│  [SECTION 1: Current Year Forecast]    │
│  - Summary Metrics                      │
│  - Scenario Builder                     │
│  - Trajectory Chart                     │
│  - Waterfall Chart                      │
│  - Sensitivity Analysis                 │
│  - Key Insights                         │
│                                         │
├─────────────────────────────────────────┤
│                                         │
│  ▼ [Expander: Long-term Retirement]    │
│     - Calculator Inputs                 │
│     - Wealth Accumulation Chart         │
│     - Retirement Scenarios              │
│     - Readiness Gauge                   │
│     - Monte Carlo Analysis              │
│                                         │
└─────────────────────────────────────────┘
```

**Rationale:**
- Main focus on immediate, actionable current year forecast
- Long-term calculator available when needed without cluttering the page
- Maintains context - both use same historical data as baseline
- Consistent with ultra-compact dashboard design philosophy

---

## Part 1: Current Year Forecast

### A. Data Collection & Baseline

#### Data Sources

**From Existing Dashboards:**

1. **Cash Flow Dashboard** (`3_📈_Cash_Flow.py`):
   - Historical transactions (income/expense by month)
   - Current year income total
   - Current year expense total
   - Transaction counts

2. **Budget Dashboard** (`4_💰_Budget.py`):
   - Budget limits by category
   - Budget utilization rates
   - Budget compliance metrics

3. **Categories Dashboard** (`5_🏷️_Categories.py`):
   - Category-level spending totals
   - Top spending categories
   - Category trends

4. **Net Worth Dashboard** (`1_📊_Net_Worth.py`):
   - Current account balances
   - Net worth trend

#### Baseline Calculations

```python
# Year-to-date calculations
ytd_start = f"{current_year}-01-01"
ytd_end = datetime.now().strftime('%Y-%m-%d')
year_end = f"{current_year}-12-31"

# Calculate YTD metrics
ytd_income = transactions[transactions['type'] == 'deposit']['amount'].sum()
ytd_expenses = transactions[transactions['type'] == 'withdrawal']['amount'].sum()
ytd_savings = ytd_income - ytd_expenses

# Calculate averages
days_elapsed = (datetime.now() - datetime(current_year, 1, 1)).days
months_elapsed = max(1, datetime.now().month)
days_remaining = (datetime(current_year, 12, 31) - datetime.now()).days

avg_daily_income = ytd_income / max(1, days_elapsed)
avg_daily_expenses = ytd_expenses / max(1, days_elapsed)
avg_monthly_savings = ytd_savings / max(1, months_elapsed)

# Linear projection
projected_income = ytd_income + (avg_daily_income * days_remaining)
projected_expenses = ytd_expenses + (avg_daily_expenses * days_remaining)
projected_savings = projected_income - projected_expenses

# Savings rate
savings_rate = (ytd_savings / ytd_income * 100) if ytd_income > 0 else 0
```

### B. Summary Metrics (Compact Row)

Display 7 key metrics in a single row using `st.columns(7)`:

1. **YTD Saved**: `€{ytd_savings:,.0f}`
   - Delta: vs. same period last year

2. **Avg Monthly**: `€{avg_monthly_savings:,.0f}`
   - Shows monthly savings pace

3. **Savings Rate**: `{savings_rate:.1f}%`
   - Percentage of income saved

4. **Projected Year-End**: `€{projected_savings:,.0f}`
   - Based on current trend

5. **vs. Last Year**: `€{delta:,.0f}` or `{delta_pct:.1f}%`
   - Comparison to previous full year

6. **Days Left**: `{days_remaining}`
   - Countdown to year-end

7. **Target Gap**: `€{gap:,.0f}` (if goal set)
   - Distance from user-defined goal

**Styling:**
- Use compact CSS from existing dashboards
- Color-code deltas (green for positive, red for negative)
- Tooltips with explanations

### C. Interactive Scenario Builder

#### Sidebar Controls

**Location:** `st.sidebar` (below date range selector)

**Section 1: Income Adjustments**

```python
st.sidebar.header("💵 Income Adjustments")

# Expected salary change
income_change_pct = st.sidebar.slider(
    "Expected Income Change (%)",
    min_value=-20.0,
    max_value=50.0,
    value=0.0,
    step=0.5,
    help="Expected change in regular income (raise, bonus, job change)"
)

# One-time income
one_time_income = st.sidebar.number_input(
    "One-time Income (€)",
    min_value=0,
    value=0,
    step=100,
    help="Expected one-time income (bonus, tax refund, etc.)"
)
```

**Section 2: Expense Adjustments**

```python
st.sidebar.header("💸 Expense Adjustments")

# Overall expense reduction target
expense_change_pct = st.sidebar.slider(
    "Overall Expense Change (%)",
    min_value=-50.0,
    max_value=50.0,
    value=0.0,
    step=1.0,
    help="Target change in total expenses (negative = reduction)"
)

# Budget adherence improvement
if current_over_budget:
    budget_adherence = st.sidebar.slider(
        "Budget Adherence Improvement (%)",
        min_value=0,
        max_value=100,
        value=0,
        step=5,
        help="Percentage improvement in staying within budget limits"
    )

# One-time expenses
one_time_expense = st.sidebar.number_input(
    "One-time Expenses (€)",
    min_value=0,
    value=0,
    step=100,
    help="Expected one-time expenses (vacation, repairs, etc.)"
)

# Category-specific adjustments (optional expander)
with st.sidebar.expander("📊 Category-Specific Adjustments"):
    category_adjustments = {}
    for category in top_5_categories:
        category_adjustments[category] = st.slider(
            f"{category} (%)",
            min_value=-50,
            max_value=50,
            value=0,
            step=5
        )
```

**Section 3: Savings Behavior**

```python
st.sidebar.header("💰 Additional Savings")

additional_savings = st.sidebar.number_input(
    "Extra Monthly Savings (€)",
    min_value=0,
    value=0,
    step=50,
    help="Additional amount to save each month"
)

apply_from = st.sidebar.radio(
    "Apply changes from:",
    options=["Current month", "Next month"],
    help="When to start applying adjustments"
)
```

**Section 4: Scenario Presets**

```python
st.sidebar.header("🎯 Quick Scenarios")

if st.sidebar.button("Reset to Current Trend"):
    # Reset all adjustments to 0
    pass

if st.sidebar.button("Optimistic (+10% income, -10% expenses)"):
    income_change_pct = 10
    expense_change_pct = -10

if st.sidebar.button("Conservative (No income change, +5% expenses)"):
    income_change_pct = 0
    expense_change_pct = 5

if st.sidebar.button("Budget Compliant"):
    # Calculate required changes to meet all budgets
    pass
```

#### Scenario Calculation Logic

```python
def calculate_scenario_projection(
    ytd_income, ytd_expenses, ytd_savings,
    days_elapsed, days_remaining,
    income_change_pct=0,
    expense_change_pct=0,
    one_time_income=0,
    one_time_expense=0,
    additional_savings_monthly=0,
    category_adjustments=None,
    apply_from='current'
):
    """
    Calculate year-end projection based on scenario adjustments.

    Returns:
        dict with projected_income, projected_expenses, projected_savings,
        monthly_breakdown (list of dicts)
    """

    # Base daily rates
    daily_income = ytd_income / max(1, days_elapsed)
    daily_expenses = ytd_expenses / max(1, days_elapsed)

    # Apply income changes
    adjusted_daily_income = daily_income * (1 + income_change_pct / 100)

    # Apply expense changes
    adjusted_daily_expenses = daily_expenses * (1 + expense_change_pct / 100)

    # Calculate future income/expenses
    future_income = (adjusted_daily_income * days_remaining) + one_time_income
    future_expenses = (adjusted_daily_expenses * days_remaining) + one_time_expense

    # Add additional savings (reduce expenses)
    months_remaining = max(1, (12 - datetime.now().month))
    future_expenses -= (additional_savings_monthly * months_remaining)

    # Calculate projections
    projected_income = ytd_income + future_income
    projected_expenses = ytd_expenses + future_expenses
    projected_savings = projected_income - projected_expenses

    # Generate monthly breakdown
    monthly_breakdown = generate_monthly_breakdown(
        ytd_income, ytd_expenses,
        adjusted_daily_income, adjusted_daily_expenses,
        additional_savings_monthly
    )

    return {
        'projected_income': projected_income,
        'projected_expenses': projected_expenses,
        'projected_savings': projected_savings,
        'monthly_breakdown': monthly_breakdown,
        'avg_monthly_savings': projected_savings / 12,
        'savings_rate': (projected_savings / projected_income * 100) if projected_income > 0 else 0
    }
```

### D. Visualizations

#### 1. Savings Trajectory Chart

**Chart Type:** Multi-line chart with area fill
**Library:** Plotly

**Specifications:**

```python
def create_savings_trajectory_chart(
    historical_data,
    baseline_projection,
    scenario_projections,
    target_savings=None,
    height=450
):
    """
    Create savings trajectory chart showing cumulative savings over the year.

    Args:
        historical_data: DataFrame with actual monthly savings (Jan to current)
        baseline_projection: Dict with projected monthly savings (current trend)
        scenario_projections: List of dicts, each representing a scenario
        target_savings: Optional target savings amount
        height: Chart height in pixels
    """

    fig = go.Figure()

    # Historical cumulative savings (solid line)
    fig.add_trace(go.Scatter(
        x=historical_data['month'],
        y=historical_data['cumulative_savings'],
        mode='lines+markers',
        name='Actual',
        line=dict(color='#2E86AB', width=3),
        marker=dict(size=8),
        hovertemplate='<b>%{x}</b><br>Saved: €%{y:,.0f}<extra></extra>'
    ))

    # Baseline projection (dashed line)
    fig.add_trace(go.Scatter(
        x=baseline_projection['months'],
        y=baseline_projection['cumulative_savings'],
        mode='lines+markers',
        name='Current Trend',
        line=dict(color='#A23B72', width=2, dash='dash'),
        marker=dict(size=6),
        hovertemplate='<b>%{x}</b><br>Projected: €%{y:,.0f}<extra></extra>'
    ))

    # Scenario projections (different colors/patterns)
    colors = ['#F18F01', '#C73E1D', '#6A994E']
    for idx, scenario in enumerate(scenario_projections):
        fig.add_trace(go.Scatter(
            x=scenario['months'],
            y=scenario['cumulative_savings'],
            mode='lines+markers',
            name=scenario['name'],
            line=dict(color=colors[idx % len(colors)], width=2, dash='dot'),
            marker=dict(size=6),
            hovertemplate=f"<b>%{{x}}</b><br>{scenario['name']}: €%{{y:,.0f}}<extra></extra>"
        ))

    # Shaded projection area (uncertainty)
    # Add between baseline and best scenario

    # Target line (if set)
    if target_savings:
        fig.add_hline(
            y=target_savings,
            line_dash="solid",
            line_color="green",
            annotation_text=f"Goal: €{target_savings:,.0f}",
            annotation_position="right"
        )

    # Today marker (vertical line)
    current_month = datetime.now().strftime('%b')
    fig.add_vline(
        x=current_month,
        line_dash="solid",
        line_color="gray",
        annotation_text="Today",
        annotation_position="top"
    )

    fig.update_layout(
        title="Savings Trajectory to Year-End",
        xaxis_title="Month",
        yaxis_title="Cumulative Savings (€)",
        height=height,
        margin=dict(t=50, b=50, l=70, r=70),
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
```

#### 2. Monthly Breakdown Chart

**Chart Type:** Stacked bar chart
**Purpose:** Show income, expenses, and savings by month

```python
def create_monthly_breakdown_chart(monthly_data, current_month, height=350):
    """
    Stacked bar chart showing income/expenses/savings per month.
    Historical data uses solid bars, projections use pattern fill.
    """

    fig = go.Figure()

    # Income bars
    fig.add_trace(go.Bar(
        x=monthly_data['month'],
        y=monthly_data['income'],
        name='Income',
        marker_color='#2E86AB',
        text=monthly_data['income'].apply(lambda x: f'€{x:,.0f}'),
        textposition='inside',
        hovertemplate='<b>%{x}</b><br>Income: €%{y:,.0f}<extra></extra>'
    ))

    # Expense bars (negative for visual clarity)
    fig.add_trace(go.Bar(
        x=monthly_data['month'],
        y=-monthly_data['expenses'],
        name='Expenses',
        marker_color='#C73E1D',
        text=monthly_data['expenses'].apply(lambda x: f'€{x:,.0f}'),
        textposition='inside',
        hovertemplate='<b>%{x}</b><br>Expenses: €%{y:,.0f}<extra></extra>'
    ))

    # Savings bars
    fig.add_trace(go.Bar(
        x=monthly_data['month'],
        y=monthly_data['savings'],
        name='Net Savings',
        marker_color='#6A994E',
        text=monthly_data['savings'].apply(lambda x: f'€{x:,.0f}'),
        textposition='outside',
        hovertemplate='<b>%{x}</b><br>Savings: €%{y:,.0f}<extra></extra>'
    ))

    fig.update_layout(
        title="Monthly Income, Expenses & Savings",
        xaxis_title="Month",
        yaxis_title="Amount (€)",
        barmode='relative',
        height=height,
        margin=dict(t=50, b=50, l=70, r=20),
        hovermode='x unified'
    )

    return fig
```

#### 3. Impact Waterfall Chart

**Chart Type:** Waterfall chart
**Purpose:** Show how each adjustment affects year-end savings

```python
def create_impact_waterfall_chart(baseline, adjustments, height=350):
    """
    Waterfall chart showing impact of each scenario adjustment.

    Args:
        baseline: Baseline year-end savings
        adjustments: List of dicts with {'name': str, 'impact': float}

    Example adjustments:
        [
            {'name': 'Baseline', 'impact': 12500},
            {'name': 'Income +5%', 'impact': 1200},
            {'name': 'Expense -10%', 'impact': 800},
            {'name': 'Extra Savings', 'impact': 600},
            {'name': 'New Total', 'impact': 15100}
        ]
    """

    fig = go.Figure(go.Waterfall(
        name="Savings Impact",
        orientation="v",
        measure=["absolute"] + ["relative"] * (len(adjustments) - 2) + ["total"],
        x=[adj['name'] for adj in adjustments],
        textposition="outside",
        text=[f"€{adj['impact']:,.0f}" for adj in adjustments],
        y=[adj['impact'] for adj in adjustments],
        connector={"line": {"color": "rgb(63, 63, 63)"}},
        decreasing={"marker": {"color": "#C73E1D"}},
        increasing={"marker": {"color": "#6A994E"}},
        totals={"marker": {"color": "#2E86AB"}}
    ))

    fig.update_layout(
        title="Impact of Scenario Adjustments",
        yaxis_title="Year-End Savings (€)",
        height=height,
        margin=dict(t=50, b=100, l=70, r=20),
        showlegend=False
    )

    return fig
```

#### 4. Sensitivity Analysis Table

**Purpose:** Show impact of different percentage changes

```python
def create_sensitivity_analysis_table(baseline_income, baseline_expenses):
    """
    Create matrix showing year-end savings for different scenarios.

    Rows: Expense reduction (0%, 5%, 10%, 15%, 20%)
    Columns: Income increase (0%, 5%, 10%)
    """

    expense_reductions = [0, 5, 10, 15, 20]
    income_increases = [0, 5, 10]

    # Calculate matrix
    matrix_data = []
    for exp_red in expense_reductions:
        row = {'Expense Reduction': f"{exp_red}%"}
        for inc_inc in income_increases:
            # Calculate scenario
            scenario_income = baseline_income * (1 + inc_inc / 100)
            scenario_expenses = baseline_expenses * (1 - exp_red / 100)
            savings = scenario_income - scenario_expenses
            row[f"+{inc_inc}% Income"] = f"€{savings:,.0f}"
        matrix_data.append(row)

    df = pd.DataFrame(matrix_data)

    # Display with color coding
    return df
```

### E. Key Insights Engine

**Purpose:** Auto-generate actionable insights based on data

#### Insight Rules

```python
def generate_savings_insights(
    ytd_savings,
    projected_savings,
    last_year_savings,
    savings_rate,
    target_savings=None,
    top_category=None,
    budget_compliance=None
):
    """
    Generate list of insights based on current data and projections.

    Returns:
        List of insight dicts with {'type': str, 'message': str, 'icon': str}
    """

    insights = []

    # Insight 1: Current trajectory
    insights.append({
        'type': 'info',
        'icon': '📊',
        'message': f"At your current rate, you'll save €{projected_savings:,.0f} by year-end"
    })

    # Insight 2: Year-over-year comparison
    if last_year_savings:
        delta = projected_savings - last_year_savings
        delta_pct = (delta / last_year_savings * 100) if last_year_savings > 0 else 0
        if delta > 0:
            insights.append({
                'type': 'success',
                'icon': '✅',
                'message': f"You're on track to save €{delta:,.0f} ({delta_pct:.1f}%) more than last year!"
            })
        else:
            insights.append({
                'type': 'warning',
                'icon': '⚠️',
                'message': f"Currently tracking €{abs(delta):,.0f} ({abs(delta_pct):.1f}%) below last year"
            })

    # Insight 3: Target gap (if goal set)
    if target_savings:
        gap = target_savings - projected_savings
        months_left = 12 - datetime.now().month
        if gap > 0:
            monthly_needed = gap / max(1, months_left)
            insights.append({
                'type': 'info',
                'icon': '🎯',
                'message': f"To reach your goal of €{target_savings:,.0f}, you need €{monthly_needed:,.0f} more per month"
            })
        else:
            insights.append({
                'type': 'success',
                'icon': '🎉',
                'message': f"You're projected to exceed your goal by €{abs(gap):,.0f}!"
            })

    # Insight 4: Top category opportunity
    if top_category:
        category_name = top_category['name']
        category_amount = top_category['amount']
        reduction_impact = category_amount * 0.15  # 15% reduction
        insights.append({
            'type': 'tip',
            'icon': '💡',
            'message': f"Your biggest spending is {category_name} (€{category_amount:,.0f}). Reducing it 15% adds €{reduction_impact:,.0f}"
        })

    # Insight 5: Budget compliance
    if budget_compliance and budget_compliance['utilization'] > 100:
        potential_savings = budget_compliance['over_amount']
        insights.append({
            'type': 'warning',
            'icon': '📊',
            'message': f"Staying on budget would increase year-end savings by €{potential_savings:,.0f}"
        })

    # Insight 6: Savings rate
    if savings_rate < 10:
        insights.append({
            'type': 'warning',
            'icon': '⚠️',
            'message': f"Your savings rate is {savings_rate:.1f}%. Financial experts recommend 15-20%."
        })
    elif savings_rate >= 20:
        insights.append({
            'type': 'success',
            'icon': '🌟',
            'message': f"Excellent! Your {savings_rate:.1f}% savings rate exceeds the 15-20% recommendation."
        })

    return insights
```

### F. Navigation Integration

Add compact navigation links (matching existing dashboards):

```python
# After summary metrics
st.markdown('<div style="background-color: rgba(49, 51, 63, 0.2); padding: 0.3rem 0.5rem; border-radius: 0.3rem; font-size: 0.75rem;">💡 <b>Related:</b> <a href="/Cash_Flow" style="color: #58a6ff;">📈 Cash Flow</a> • <a href="/Budget" style="color: #58a6ff;">💰 Budget</a> • <a href="/Categories" style="color: #58a6ff;">🏷️ Categories</a> for detailed analysis</div>', unsafe_allow_html=True)
```

---

## Part 2: Long-term Retirement Calculator

### A. Calculator Inputs

**Location:** Inside expandable section at bottom of page

```python
with st.expander("📊 Long-term Retirement Projection (20+ years)", expanded=False):
    st.markdown("### 🎯 Retirement Planning Calculator")

    # Two-column layout for inputs
    col_inputs, col_results = st.columns([1, 2])

    with col_inputs:
        # Input sections
        pass
```

#### Input Section 1: Starting Position

```python
st.markdown("**👤 Your Current Situation**")

current_age = st.number_input(
    "Current Age",
    min_value=18,
    max_value=80,
    value=32,
    step=1
)

current_net_worth = st.number_input(
    "Current Net Worth (€)",
    min_value=0,
    value=int(net_worth_from_dashboard),  # Pre-filled
    step=1000,
    help="Total assets minus liabilities"
)

current_annual_income = st.number_input(
    "Current Annual Income (€)",
    min_value=0,
    value=int(ytd_income * (12 / datetime.now().month)),  # Estimated from YTD
    step=1000
)

current_monthly_savings = st.number_input(
    "Current Monthly Savings (€)",
    min_value=0,
    value=int(avg_monthly_savings),  # Pre-filled
    step=100
)
```

#### Input Section 2: Growth & Returns

```python
st.markdown("**📈 Growth Assumptions**")

annual_raise_pct = st.slider(
    "Expected Annual Raise (%)",
    min_value=0.0,
    max_value=10.0,
    value=2.7,
    step=0.1,
    help="Average annual salary increase"
)

investment_return_pct = st.slider(
    "Expected Investment Return (%)",
    min_value=0.0,
    max_value=15.0,
    value=7.0,
    step=0.5,
    help="Historical stock market average is ~7-10%"
)

conservative_return_pct = st.slider(
    "Conservative Case Return (%)",
    min_value=0.0,
    max_value=10.0,
    value=4.0,
    step=0.5
)

optimistic_return_pct = st.slider(
    "Optimistic Case Return (%)",
    min_value=5.0,
    max_value=20.0,
    value=10.0,
    step=0.5
)

inflation_rate_pct = st.slider(
    "Annual Inflation (%)",
    min_value=0.0,
    max_value=10.0,
    value=2.0,
    step=0.1
)
```

#### Input Section 3: Savings Strategy

```python
st.markdown("**💰 Savings Strategy**")

savings_increase_annual = st.number_input(
    "Annual Savings Increase (€)",
    min_value=0,
    value=0,
    step=50,
    help="Increase monthly savings by this amount each year"
)

employer_match_pct = st.slider(
    "Employer Pension Match (%)",
    min_value=0.0,
    max_value=10.0,
    value=0.0,
    step=0.5,
    help="% of salary employer matches"
)

employer_match_cap = st.number_input(
    "Match Cap (€/year)",
    min_value=0,
    value=0,
    step=100,
    help="Maximum employer contribution"
)
```

#### Input Section 4: Retirement Phase

```python
st.markdown("**🏖️ Retirement Planning**")

target_retirement_age = st.slider(
    "Target Retirement Age",
    min_value=current_age + 1,
    max_value=80,
    value=65,
    step=1
)

life_expectancy = st.slider(
    "Life Expectancy",
    min_value=target_retirement_age + 1,
    max_value=100,
    value=90,
    step=1
)

retirement_expenses_annual = st.number_input(
    "Annual Expenses in Retirement (€)",
    min_value=0,
    value=int(ytd_expenses * (12 / datetime.now().month) * 0.8),  # Assume 80% of current
    step=1000,
    help="Apply inflation adjustment automatically"
)

pension_income_annual = st.number_input(
    "Expected Pension/Social Security (€/year)",
    min_value=0,
    value=0,
    step=1000,
    help="Guaranteed income in retirement"
)
```

#### Input Section 5: Tax Considerations

```python
with st.expander("💼 Tax Settings (Advanced)"):

    capital_gains_tax_pct = st.slider(
        "Capital Gains Tax (%)",
        min_value=0.0,
        max_value=50.0,
        value=33.0,
        step=1.0,
        help="Tax on investment gains"
    )

    tax_advantaged_pct = st.slider(
        "Tax-Advantaged Savings (%)",
        min_value=0.0,
        max_value=100.0,
        value=0.0,
        step=5.0,
        help="% of savings in tax-deferred accounts (pension, etc.)"
    )

    employer_pension_contribution = st.number_input(
        "Employer Pension Contribution (€/year)",
        min_value=0,
        value=0,
        step=100
    )
```

#### Input Section 6: Multiple Goals (Optional)

```python
with st.expander("🎯 Multiple Savings Goals (Optional)"):
    st.markdown("Track specific goals alongside retirement savings")

    num_goals = st.number_input("Number of goals", min_value=0, max_value=5, value=0)

    goals = []
    for i in range(num_goals):
        st.markdown(f"**Goal {i+1}**")
        col1, col2, col3 = st.columns(3)
        with col1:
            goal_name = st.text_input(f"Name {i+1}", value=f"Goal {i+1}", key=f"goal_name_{i}")
        with col2:
            goal_amount = st.number_input(f"Amount {i+1}", min_value=0, value=10000, step=1000, key=f"goal_amount_{i}")
        with col3:
            goal_year = st.number_input(f"Target Year {i+1}", min_value=1, max_value=30, value=5, key=f"goal_year_{i}")

        goals.append({
            'name': goal_name,
            'amount': goal_amount,
            'year': goal_year
        })
```

### B. Calculation Engine

#### Core Retirement Projection Function

```python
def calculate_retirement_projection(
    current_age,
    current_net_worth,
    current_annual_income,
    current_monthly_savings,
    annual_raise_pct,
    investment_return_pct,
    inflation_rate_pct,
    savings_increase_annual,
    employer_match_pct,
    employer_match_cap,
    target_retirement_age,
    life_expectancy,
    retirement_expenses_annual,
    pension_income_annual,
    capital_gains_tax_pct,
    tax_advantaged_pct,
    employer_pension_contribution
):
    """
    Calculate year-by-year projection from current age to life expectancy.

    Returns:
        DataFrame with columns:
        - age: Age for each year
        - year: Calendar year
        - annual_income: Gross income
        - savings_contribution: Amount saved
        - employer_contribution: Employer match/pension
        - portfolio_value: Investment portfolio balance
        - portfolio_gains: Investment returns
        - taxes_paid: Taxes on gains
        - retirement_withdrawal: Amount withdrawn (if retired)
        - net_worth: Total net worth
        - real_value: Inflation-adjusted value
    """

    years_to_retirement = target_retirement_age - current_age
    years_in_retirement = life_expectancy - target_retirement_age
    total_years = years_to_retirement + years_in_retirement

    # Initialize tracking
    results = []
    portfolio_balance = current_net_worth
    annual_income = current_annual_income
    monthly_savings = current_monthly_savings

    current_year = datetime.now().year

    for year_num in range(total_years + 1):
        age = current_age + year_num
        calendar_year = current_year + year_num

        is_retired = age >= target_retirement_age

        if not is_retired:
            # Working years - Accumulation phase

            # Income growth
            if year_num > 0:
                annual_income *= (1 + annual_raise_pct / 100)

            # Savings growth
            annual_savings = monthly_savings * 12
            if year_num > 0:
                monthly_savings += savings_increase_annual / 12

            # Employer match
            match_amount = min(
                annual_income * (employer_match_pct / 100),
                employer_match_cap
            )
            employer_contribution = match_amount + employer_pension_contribution

            # Total contributions
            total_contribution = annual_savings + employer_contribution

            # Investment returns (monthly compounding)
            monthly_return = investment_return_pct / 100 / 12

            # Add contributions throughout the year (assume monthly)
            for month in range(12):
                portfolio_balance *= (1 + monthly_return)
                portfolio_balance += (annual_savings / 12) + (employer_contribution / 12)

            # Calculate gains for the year
            beginning_balance = results[-1]['portfolio_value'] if results else current_net_worth
            portfolio_gains = portfolio_balance - beginning_balance - total_contribution

            # Calculate taxes on gains
            # Tax-advantaged portion is tax-deferred
            taxable_portion = portfolio_gains * (1 - tax_advantaged_pct / 100)
            taxes_paid = max(0, taxable_portion * (capital_gains_tax_pct / 100))

            # Apply taxes
            portfolio_balance -= taxes_paid

            withdrawal = 0

        else:
            # Retirement years - Withdrawal phase

            annual_income = pension_income_annual

            # Inflation-adjusted expenses
            inflation_multiplier = (1 + inflation_rate_pct / 100) ** (age - target_retirement_age)
            adjusted_expenses = retirement_expenses_annual * inflation_multiplier

            # Required withdrawal (expenses minus pension)
            required_withdrawal = max(0, adjusted_expenses - pension_income_annual)

            # Investment returns
            monthly_return = investment_return_pct / 100 / 12

            # Calculate monthly with withdrawals
            for month in range(12):
                portfolio_balance *= (1 + monthly_return)
                portfolio_balance -= (required_withdrawal / 12)

            # Portfolio gains/losses
            beginning_balance = results[-1]['portfolio_value'] if results else current_net_worth
            portfolio_gains = portfolio_balance - beginning_balance + required_withdrawal

            # Taxes on withdrawals
            taxable_withdrawal = required_withdrawal * (1 - tax_advantaged_pct / 100)
            taxes_paid = taxable_withdrawal * (capital_gains_tax_pct / 100)
            portfolio_balance -= taxes_paid

            withdrawal = required_withdrawal
            total_contribution = 0
            employer_contribution = 0
            annual_savings = 0

        # Real value (inflation-adjusted to current dollars)
        inflation_multiplier = (1 + inflation_rate_pct / 100) ** year_num
        real_value = portfolio_balance / inflation_multiplier

        results.append({
            'age': age,
            'year': calendar_year,
            'annual_income': annual_income,
            'savings_contribution': annual_savings,
            'employer_contribution': employer_contribution,
            'portfolio_value': portfolio_balance,
            'portfolio_gains': portfolio_gains,
            'taxes_paid': taxes_paid,
            'retirement_withdrawal': withdrawal,
            'net_worth': portfolio_balance,
            'real_value': real_value,
            'is_retired': is_retired
        })

        # Check if portfolio depleted
        if portfolio_balance <= 0:
            break

    return pd.DataFrame(results)
```

#### Monte Carlo Simulation

```python
def run_monte_carlo_simulation(
    base_parameters,
    num_simulations=1000,
    return_std_dev=0.15  # 15% standard deviation
):
    """
    Run Monte Carlo simulation with variable returns.

    Args:
        base_parameters: Dict with all input parameters
        num_simulations: Number of scenarios to simulate
        return_std_dev: Standard deviation for returns (volatility)

    Returns:
        Dict with:
        - percentile_10: 10th percentile projection (pessimistic)
        - percentile_50: 50th percentile (median)
        - percentile_90: 90th percentile (optimistic)
        - success_rate: % of simulations that don't run out of money
        - all_simulations: List of all projection DataFrames
    """

    import numpy as np

    simulations = []
    success_count = 0

    mean_return = base_parameters['investment_return_pct']

    for sim in range(num_simulations):
        # Generate random returns for each year
        years = base_parameters['target_retirement_age'] - base_parameters['current_age']
        years += base_parameters['life_expectancy'] - base_parameters['target_retirement_age']

        # Use normal distribution for returns
        annual_returns = np.random.normal(
            mean_return,
            return_std_dev * 100,  # Convert to percentage
            size=years + 1
        )

        # Run projection with variable returns
        sim_params = base_parameters.copy()
        yearly_results = []

        portfolio_balance = sim_params['current_net_worth']

        for year_idx, return_pct in enumerate(annual_returns):
            sim_params['investment_return_pct'] = max(return_pct, -50)  # Floor at -50%

            # Calculate year (simplified for Monte Carlo)
            # ... (similar logic as calculate_retirement_projection)

            yearly_results.append({
                'year': year_idx,
                'portfolio_value': portfolio_balance,
                'return': return_pct
            })

            if portfolio_balance <= 0:
                break

        df_sim = pd.DataFrame(yearly_results)
        simulations.append(df_sim)

        # Check if money lasted until life expectancy
        if len(df_sim) >= years:
            success_count += 1

    # Calculate percentiles
    # Get final portfolio values
    final_values = [sim['portfolio_value'].iloc[-1] if len(sim) > 0 else 0 for sim in simulations]

    percentile_10 = np.percentile(final_values, 10)
    percentile_50 = np.percentile(final_values, 50)
    percentile_90 = np.percentile(final_values, 90)

    success_rate = (success_count / num_simulations) * 100

    return {
        'percentile_10': percentile_10,
        'percentile_50': percentile_50,
        'percentile_90': percentile_90,
        'success_rate': success_rate,
        'all_simulations': simulations,
        'final_values': final_values
    }
```

#### Safe Withdrawal Rate Calculator

```python
def calculate_safe_withdrawal_rate(
    portfolio_value,
    years_in_retirement,
    investment_return_pct,
    inflation_rate_pct
):
    """
    Calculate sustainable withdrawal rate using the 4% rule and variations.

    Returns:
        Dict with withdrawal amounts for different rates (3%, 4%, 5%)
        and portfolio longevity for each
    """

    withdrawal_rates = [3.0, 3.5, 4.0, 4.5, 5.0]
    results = {}

    for rate in withdrawal_rates:
        annual_withdrawal = portfolio_value * (rate / 100)

        # Simulate portfolio with this withdrawal rate
        balance = portfolio_value
        years_lasted = 0

        for year in range(years_in_retirement):
            # Apply returns
            balance *= (1 + investment_return_pct / 100)

            # Withdraw (inflation-adjusted)
            inflation_multiplier = (1 + inflation_rate_pct / 100) ** year
            adjusted_withdrawal = annual_withdrawal * inflation_multiplier
            balance -= adjusted_withdrawal

            if balance <= 0:
                years_lasted = year
                break

            years_lasted = year + 1

        results[rate] = {
            'annual_withdrawal': annual_withdrawal,
            'monthly_withdrawal': annual_withdrawal / 12,
            'years_lasted': years_lasted,
            'depletes_before_death': years_lasted < years_in_retirement
        }

    return results
```

### C. Results Display

#### Summary Metrics for Retirement

```python
# Display retirement readiness metrics
cols = st.columns(7)

with cols[0]:
    years_to_retirement = target_retirement_age - current_age
    st.metric("Years to Retirement", years_to_retirement)

with cols[1]:
    final_portfolio = projection_df[projection_df['age'] == target_retirement_age]['portfolio_value'].iloc[0]
    st.metric("Portfolio at Retirement", f"€{final_portfolio:,.0f}")

with cols[2]:
    real_value = projection_df[projection_df['age'] == target_retirement_age]['real_value'].iloc[0]
    st.metric("Real Value (Today's €)", f"€{real_value:,.0f}")

with cols[3]:
    monthly_income = final_portfolio * 0.04 / 12  # 4% rule
    st.metric("Sustainable Income/mo", f"€{monthly_income:,.0f}")

with cols[4]:
    last_age = projection_df['age'].iloc[-1]
    portfolio_longevity = last_age - target_retirement_age
    st.metric("Portfolio Lasts", f"{portfolio_longevity} years")

with cols[5]:
    success_pct = monte_carlo_results['success_rate']
    st.metric("Success Rate", f"{success_pct:.0f}%")

with cols[6]:
    readiness_pct = (final_portfolio / target_portfolio_needed) * 100 if target_portfolio_needed else 100
    st.metric("Retirement Readiness", f"{readiness_pct:.0f}%")
```

#### Retirement Age Scenarios Table

```python
st.markdown("### 🎯 Retirement Age Scenarios")

retirement_scenarios = []
for ret_age in [55, 60, 65, 67, 70]:
    if ret_age > current_age:
        # Calculate projection for this retirement age
        scenario = calculate_retirement_projection(
            # ... parameters with target_retirement_age = ret_age
        )

        years_working = ret_age - current_age
        portfolio_at_retirement = scenario[scenario['age'] == ret_age]['portfolio_value'].iloc[0]
        monthly_income = portfolio_at_retirement * 0.04 / 12
        last_age = scenario['age'].iloc[-1]
        longevity = last_age - ret_age

        retirement_scenarios.append({
            'Retirement Age': ret_age,
            'Years Working': years_working,
            'Portfolio Value': f"€{portfolio_at_retirement:,.0f}",
            'Monthly Income': f"€{monthly_income:,.0f}",
            'Portfolio Lasts': f"{longevity} years",
            'Lasts Until Age': int(last_age)
        })

df_scenarios = pd.DataFrame(retirement_scenarios)

st.dataframe(
    df_scenarios,
    use_container_width=True,
    hide_index=True,
    height=250
)
```

### D. Visualizations for Retirement

#### 1. Wealth Accumulation Chart

```python
def create_wealth_accumulation_chart(
    projection_df,
    target_retirement_age,
    conservative_df=None,
    optimistic_df=None,
    monte_carlo_ranges=None,
    goals=None,
    height=500
):
    """
    Chart showing portfolio growth from current age to life expectancy.
    Includes accumulation and drawdown phases, with confidence intervals.
    """

    fig = go.Figure()

    # Base case projection
    fig.add_trace(go.Scatter(
        x=projection_df['age'],
        y=projection_df['portfolio_value'],
        mode='lines',
        name='Base Case',
        line=dict(color='#2E86AB', width=3),
        hovertemplate='<b>Age %{x}</b><br>Portfolio: €%{y:,.0f}<extra></extra>'
    ))

    # Conservative case
    if conservative_df is not None:
        fig.add_trace(go.Scatter(
            x=conservative_df['age'],
            y=conservative_df['portfolio_value'],
            mode='lines',
            name='Conservative',
            line=dict(color='#C73E1D', width=2, dash='dash'),
            hovertemplate='<b>Age %{x}</b><br>Portfolio: €%{y:,.0f}<extra></extra>'
        ))

    # Optimistic case
    if optimistic_df is not None:
        fig.add_trace(go.Scatter(
            x=optimistic_df['age'],
            y=optimistic_df['portfolio_value'],
            mode='lines',
            name='Optimistic',
            line=dict(color='#6A994E', width=2, dash='dash'),
            hovertemplate='<b>Age %{x}</b><br>Portfolio: €%{y:,.0f}<extra></extra>'
        ))

    # Monte Carlo confidence interval (10th-90th percentile)
    if monte_carlo_ranges:
        fig.add_trace(go.Scatter(
            x=projection_df['age'],
            y=monte_carlo_ranges['percentile_90'],
            mode='lines',
            line=dict(width=0),
            showlegend=False,
            hoverinfo='skip'
        ))
        fig.add_trace(go.Scatter(
            x=projection_df['age'],
            y=monte_carlo_ranges['percentile_10'],
            mode='lines',
            line=dict(width=0),
            fillcolor='rgba(46, 134, 171, 0.2)',
            fill='tonexty',
            name='10th-90th Percentile',
            hoverinfo='skip'
        ))

    # Retirement age line
    fig.add_vline(
        x=target_retirement_age,
        line_dash="solid",
        line_color="orange",
        annotation_text="Retirement",
        annotation_position="top"
    )

    # Goal markers (if tracking multiple goals)
    if goals:
        for goal in goals:
            goal_age = projection_df[projection_df['year'] == datetime.now().year + goal['year']]['age'].iloc[0]
            fig.add_hline(
                y=goal['amount'],
                line_dash="dot",
                line_color="purple",
                annotation_text=goal['name'],
                annotation_position="right"
            )

    # Shading for accumulation vs drawdown
    fig.add_vrect(
        x0=projection_df['age'].min(),
        x1=target_retirement_age,
        fillcolor="lightblue",
        opacity=0.1,
        layer="below",
        line_width=0,
        annotation_text="Accumulation",
        annotation_position="top left"
    )

    fig.add_vrect(
        x0=target_retirement_age,
        x1=projection_df['age'].max(),
        fillcolor="lightgreen",
        opacity=0.1,
        layer="below",
        line_width=0,
        annotation_text="Retirement",
        annotation_position="top left"
    )

    fig.update_layout(
        title="Wealth Accumulation & Retirement Drawdown",
        xaxis_title="Age",
        yaxis_title="Portfolio Value (€)",
        height=height,
        margin=dict(t=60, b=50, l=80, r=80),
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
```

#### 2. Contribution Breakdown (Stacked Area)

```python
def create_contribution_breakdown_chart(projection_df, target_retirement_age, height=400):
    """
    Stacked area chart showing:
    - Principal contributions
    - Investment gains
    - Employer contributions
    """

    # Calculate cumulative components
    projection_df['cumulative_contributions'] = projection_df['savings_contribution'].cumsum()
    projection_df['cumulative_employer'] = projection_df['employer_contribution'].cumsum()
    projection_df['cumulative_gains'] = (
        projection_df['portfolio_value']
        - projection_df['cumulative_contributions']
        - projection_df['cumulative_employer']
    )

    # Filter to accumulation phase only
    df_accumulation = projection_df[projection_df['age'] < target_retirement_age]

    fig = go.Figure()

    # Principal contributions
    fig.add_trace(go.Scatter(
        x=df_accumulation['age'],
        y=df_accumulation['cumulative_contributions'],
        mode='lines',
        name='Your Contributions',
        fill='tozeroy',
        line=dict(color='#2E86AB', width=0),
        fillcolor='rgba(46, 134, 171, 0.7)',
        hovertemplate='<b>Age %{x}</b><br>Contributions: €%{y:,.0f}<extra></extra>'
    ))

    # Employer contributions
    fig.add_trace(go.Scatter(
        x=df_accumulation['age'],
        y=df_accumulation['cumulative_contributions'] + df_accumulation['cumulative_employer'],
        mode='lines',
        name='Employer Contributions',
        fill='tonexty',
        line=dict(color='#F18F01', width=0),
        fillcolor='rgba(241, 143, 1, 0.7)',
        hovertemplate='<b>Age %{x}</b><br>Employer: €%{y:,.0f}<extra></extra>'
    ))

    # Investment gains
    fig.add_trace(go.Scatter(
        x=df_accumulation['age'],
        y=df_accumulation['portfolio_value'],
        mode='lines',
        name='Investment Gains',
        fill='tonexty',
        line=dict(color='#6A994E', width=0),
        fillcolor='rgba(106, 153, 78, 0.7)',
        hovertemplate='<b>Age %{x}</b><br>Total: €%{y:,.0f}<extra></extra>'
    ))

    fig.update_layout(
        title="Portfolio Growth Components (Accumulation Phase)",
        xaxis_title="Age",
        yaxis_title="Value (€)",
        height=height,
        margin=dict(t=50, b=50, l=70, r=20),
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
```

#### 3. Safe Withdrawal Analysis

```python
def create_safe_withdrawal_chart(
    withdrawal_scenarios,
    life_expectancy,
    target_retirement_age,
    height=400
):
    """
    Show portfolio balance during retirement for different withdrawal rates.
    """

    fig = go.Figure()

    colors = ['#6A994E', '#2E86AB', '#F18F01', '#C73E1D', '#8B0000']

    for idx, (rate, scenario_data) in enumerate(withdrawal_scenarios.items()):
        # Simulate portfolio for this rate
        # ... (use scenario_data to project)

        fig.add_trace(go.Scatter(
            x=scenario_data['ages'],
            y=scenario_data['portfolio_values'],
            mode='lines',
            name=f"{rate}% Withdrawal",
            line=dict(color=colors[idx], width=2),
            hovertemplate=f'<b>Age %{{x}}</b><br>{rate}% Rate: €%{{y:,.0f}}<extra></extra>'
        ))

    # Life expectancy line
    fig.add_vline(
        x=life_expectancy,
        line_dash="dash",
        line_color="gray",
        annotation_text="Life Expectancy",
        annotation_position="top"
    )

    # Zero line
    fig.add_hline(
        y=0,
        line_dash="solid",
        line_color="red",
        annotation_text="Portfolio Depleted",
        annotation_position="right"
    )

    fig.update_layout(
        title="Portfolio Longevity by Withdrawal Rate",
        xaxis_title="Age",
        yaxis_title="Portfolio Balance (€)",
        height=height,
        margin=dict(t=50, b=50, l=70, r=70),
        hovermode='x unified'
    )

    return fig
```

#### 4. Retirement Readiness Gauge

```python
def create_retirement_readiness_gauge(
    portfolio_at_retirement,
    target_portfolio_needed,
    height=300
):
    """
    Circular gauge showing retirement readiness percentage.

    Green zone: >100% (can retire early)
    Yellow zone: 80-100% (on track)
    Red zone: <80% (need more)
    """

    readiness_pct = (portfolio_at_retirement / target_portfolio_needed * 100) if target_portfolio_needed > 0 else 0

    # Determine color
    if readiness_pct >= 100:
        color = "#6A994E"  # Green
        status = "Ready to Retire!"
    elif readiness_pct >= 80:
        color = "#F18F01"  # Orange
        status = "On Track"
    else:
        color = "#C73E1D"  # Red
        status = "Needs Improvement"

    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=readiness_pct,
        delta={'reference': 100, 'suffix': '%'},
        title={'text': f"Retirement Readiness<br><sub>{status}</sub>"},
        number={'suffix': '%'},
        gauge={
            'axis': {'range': [None, 150], 'ticksuffix': '%'},
            'bar': {'color': color},
            'steps': [
                {'range': [0, 80], 'color': 'rgba(199, 62, 29, 0.2)'},
                {'range': [80, 100], 'color': 'rgba(241, 143, 1, 0.2)'},
                {'range': [100, 150], 'color': 'rgba(106, 153, 78, 0.2)'}
            ],
            'threshold': {
                'line': {'color': "black", 'width': 4},
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
```

#### 5. Monte Carlo Distribution Chart

```python
def create_monte_carlo_distribution_chart(monte_carlo_results, height=350):
    """
    Histogram showing distribution of final portfolio values from simulations.
    """

    final_values = monte_carlo_results['final_values']

    fig = go.Figure()

    fig.add_trace(go.Histogram(
        x=final_values,
        nbinsx=50,
        name='Simulations',
        marker_color='#2E86AB',
        hovertemplate='Portfolio: €%{x:,.0f}<br>Frequency: %{y}<extra></extra>'
    ))

    # Add percentile lines
    p10 = monte_carlo_results['percentile_10']
    p50 = monte_carlo_results['percentile_50']
    p90 = monte_carlo_results['percentile_90']

    fig.add_vline(x=p10, line_dash="dash", line_color="red", annotation_text="10th %ile")
    fig.add_vline(x=p50, line_dash="solid", line_color="green", annotation_text="Median")
    fig.add_vline(x=p90, line_dash="dash", line_color="blue", annotation_text="90th %ile")

    fig.update_layout(
        title=f"Monte Carlo Simulation Results ({len(final_values)} runs)",
        xaxis_title="Final Portfolio Value (€)",
        yaxis_title="Frequency",
        height=height,
        margin=dict(t=50, b=50, l=70, r=20),
        showlegend=False
    )

    return fig
```

### E. Key Insights & Recommendations

#### Retirement Insights Engine

```python
def generate_retirement_insights(
    current_age,
    target_retirement_age,
    portfolio_at_retirement,
    retirement_expenses,
    success_rate,
    monthly_income,
    projection_df
):
    """
    Generate actionable insights for retirement planning.
    """

    insights = []

    # Insight 1: Basic readiness
    years_to_retirement = target_retirement_age - current_age
    insights.append({
        'type': 'info',
        'icon': '📊',
        'message': f"At current savings rate, you can retire at age {target_retirement_age} with €{portfolio_at_retirement:,.0f}"
    })

    # Insight 2: Retirement income
    insights.append({
        'type': 'info',
        'icon': '💰',
        'message': f"Your retirement portfolio will provide €{monthly_income:,.0f}/month (4% rule)"
    })

    # Insight 3: Success rate assessment
    if success_rate >= 90:
        insights.append({
            'type': 'success',
            'icon': '✅',
            'message': f"Excellent! {success_rate:.0f}% chance your money lasts through retirement"
        })
    elif success_rate >= 70:
        insights.append({
            'type': 'warning',
            'icon': '⚠️',
            'message': f"{success_rate:.0f}% success rate. Consider increasing savings or delaying retirement"
        })
    else:
        insights.append({
            'type': 'error',
            'icon': '🚨',
            'message': f"Only {success_rate:.0f}% success rate. Significant adjustments needed"
        })

    # Insight 4: Early retirement possibility
    # Find age when portfolio reaches target
    target_needed = retirement_expenses * 25  # 4% rule inverse
    can_retire_at = None
    for _, row in projection_df.iterrows():
        if row['portfolio_value'] >= target_needed and not row['is_retired']:
            can_retire_at = int(row['age'])
            break

    if can_retire_at and can_retire_at < target_retirement_age:
        years_earlier = target_retirement_age - can_retire_at
        insights.append({
            'type': 'success',
            'icon': '🎉',
            'message': f"You could retire {years_earlier} years earlier (age {can_retire_at}) with current plan!"
        })

    # Insight 5: Savings increase impact
    # Calculate if saving €200 more per month
    additional_savings = 200
    months_to_retirement = years_to_retirement * 12
    simple_addition = additional_savings * months_to_retirement
    # With 7% returns, roughly 1.5x due to compounding
    estimated_impact = simple_addition * 1.5

    insights.append({
        'type': 'tip',
        'icon': '💡',
        'message': f"Saving €{additional_savings} more per month adds ~€{estimated_impact:,.0f} at retirement"
    })

    # Insight 6: Delay retirement impact
    if years_to_retirement > 5:
        # Calculate working 2 more years
        insights.append({
            'type': 'tip',
            'icon': '📅',
            'message': f"Working 2 more years could increase retirement sustainability by ~40%"
        })

    return insights
```

#### Optimization Recommendations

```python
def generate_optimization_recommendations(
    current_monthly_savings,
    employer_match_pct,
    employer_match_cap,
    annual_income,
    projection_df,
    success_rate
):
    """
    Generate specific recommendations for optimization.
    """

    recommendations = []

    # Recommendation 1: Maximize employer match
    if employer_match_pct > 0:
        max_match = min(annual_income * (employer_match_pct / 100), employer_match_cap)
        current_contributions = current_monthly_savings * 12

        if current_contributions < max_match:
            missing_match = max_match - current_contributions
            recommendations.append({
                'priority': 'HIGH',
                'icon': '🎁',
                'title': 'Maximize Employer Match',
                'message': f"You're leaving €{missing_match:,.0f}/year in free money on the table! Increase contributions to maximize match.",
                'action': f"Increase monthly savings by €{missing_match/12:,.0f}"
            })

    # Recommendation 2: Annual savings increases
    recommendations.append({
        'priority': 'MEDIUM',
        'icon': '📈',
        'title': 'Automate Savings Growth',
        'message': "Increase savings by 1% annually with raises. You won't miss it, but it compounds significantly.",
        'action': "Set up automatic annual increase"
    })

    # Recommendation 3: Tax optimization
    recommendations.append({
        'priority': 'MEDIUM',
        'icon': '💼',
        'title': 'Tax-Advantaged Accounts',
        'message': "Maximize pension contributions and tax-deferred accounts to reduce tax burden.",
        'action': "Review pension contribution limits"
    })

    # Recommendation 4: Investment allocation
    recommendations.append({
        'priority': 'LOW',
        'icon': '📊',
        'title': 'Review Asset Allocation',
        'message': "Ensure your investment mix aligns with your risk tolerance and time horizon.",
        'action': "Consider rebalancing portfolio"
    })

    # Recommendation 5: Reduce expenses if success rate low
    if success_rate < 80:
        recommendations.append({
            'priority': 'HIGH',
            'icon': '💸',
            'title': 'Reduce Retirement Expenses',
            'message': f"Success rate is {success_rate:.0f}%. Reducing retirement expenses by 10% significantly improves sustainability.",
            'action': "Plan for lower expenses in retirement"
        })

    return recommendations
```

### F. Interactive What-If Sliders

Add real-time sliders for quick adjustments:

```python
st.markdown("### ⚡ Quick Adjustments")

col1, col2, col3, col4 = st.columns(4)

with col1:
    quick_retirement_age = st.slider(
        "Retirement Age",
        min_value=current_age + 1,
        max_value=75,
        value=target_retirement_age,
        key='quick_retirement_age'
    )

with col2:
    quick_monthly_savings = st.slider(
        "Monthly Savings (€)",
        min_value=0,
        max_value=5000,
        value=int(current_monthly_savings),
        step=100,
        key='quick_monthly_savings'
    )

with col3:
    quick_return = st.slider(
        "Expected Return (%)",
        min_value=0.0,
        max_value=15.0,
        value=investment_return_pct,
        step=0.5,
        key='quick_return'
    )

with col4:
    quick_expenses = st.slider(
        "Retirement Expenses (€/year)",
        min_value=0,
        max_value=100000,
        value=int(retirement_expenses_annual),
        step=1000,
        key='quick_expenses'
    )

# Recalculate and update charts in real-time based on slider changes
```

### G. Export Options

```python
# Export buttons
col1, col2 = st.columns(2)

with col1:
    # CSV export
    csv = projection_df.to_csv(index=False)
    st.download_button(
        label="📥 Download Detailed Projection (CSV)",
        data=csv,
        file_name=f"retirement_projection_{datetime.now().strftime('%Y%m%d')}.csv",
        mime="text/csv"
    )

with col2:
    # PDF export (using reportlab or similar)
    if st.button("📄 Generate PDF Report"):
        # Generate PDF with summary, charts, recommendations
        st.info("PDF generation feature coming soon!")
```

---

## Technical Implementation

### File Structure

```
pythondashboard/
├── pages/
│   └── 6_💰_Savings_Forecast.py          # Main dashboard page
│
├── utils/
│   ├── api_client.py                      # Existing (no changes)
│   ├── config.py                          # Existing (no changes)
│   ├── navigation.py                      # Existing (no changes)
│   │
│   ├── calculations.py                    # ADD new functions
│   │   ├── calculate_year_end_projection()
│   │   ├── calculate_scenario_impact()
│   │   ├── generate_monthly_breakdown()
│   │   ├── calculate_sensitivity_matrix()
│   │
│   ├── charts.py                          # ADD new functions
│   │   ├── create_savings_trajectory_chart()
│   │   ├── create_monthly_breakdown_chart()
│   │   ├── create_impact_waterfall_chart()
│   │   ├── create_wealth_accumulation_chart()
│   │   ├── create_contribution_breakdown_chart()
│   │   ├── create_safe_withdrawal_chart()
│   │   ├── create_retirement_readiness_gauge()
│   │   ├── create_monte_carlo_distribution_chart()
│   │
│   └── retirement_calculator.py           # NEW FILE
│       ├── calculate_retirement_projection()
│       ├── run_monte_carlo_simulation()
│       ├── calculate_safe_withdrawal_rate()
│       ├── generate_retirement_insights()
│       ├── generate_optimization_recommendations()
```

### Dependencies

Add to `requirements.txt`:

```txt
# Existing dependencies remain

# For Monte Carlo simulation
numpy>=1.24.0
scipy>=1.10.0

# For PDF export (optional - Phase 4)
# reportlab>=4.0.0
```

### State Management

```python
# Session state for calculator inputs
if 'retirement_params' not in st.session_state:
    st.session_state.retirement_params = {
        'current_age': 32,
        'target_retirement_age': 65,
        'investment_return_pct': 7.0,
        # ... other defaults
    }

# Session state for scenarios
if 'saved_scenarios' not in st.session_state:
    st.session_state.saved_scenarios = []

# Save/load scenarios
def save_scenario(name, params):
    st.session_state.saved_scenarios.append({
        'name': name,
        'params': params,
        'timestamp': datetime.now()
    })

def load_scenario(name):
    for scenario in st.session_state.saved_scenarios:
        if scenario['name'] == name:
            return scenario['params']
    return None
```

### Caching Strategy

```python
# Cache historical data
@st.cache_data(ttl=300)
def fetch_historical_data(_client, start_date, end_date):
    return _client.get_transactions(start_date=start_date, end_date=end_date)

# Cache expensive calculations
@st.cache_data
def calculate_cached_projection(params_tuple):
    # Convert tuple back to dict
    params = dict(params_tuple)
    return calculate_retirement_projection(**params)

# Cache Monte Carlo results (longer TTL)
@st.cache_data(ttl=3600)
def run_cached_monte_carlo(params_tuple, num_simulations):
    params = dict(params_tuple)
    return run_monte_carlo_simulation(params, num_simulations)
```

---

## Development Phases

### Phase 1: Core Current Year Forecast ⏱️ ~8 hours

**Deliverables:**
- Basic page structure with compact CSS
- Data collection from existing dashboards
- Summary metrics (7 key metrics)
- Simple baseline projection to year-end
- Basic trajectory chart (historical + projection)
- 2-3 preset scenarios (Current Trend, Optimistic, Conservative)

**Acceptance Criteria:**
- Page loads without errors
- Shows YTD data correctly
- Baseline projection calculated accurately
- Chart displays historical and projected data
- Presets apply and update projection

**Files to Create/Modify:**
- `pages/6_💰_Savings_Forecast.py` (new)
- `utils/calculations.py` (add basic functions)
- `utils/charts.py` (add trajectory chart)

### Phase 2: Interactive What-If Scenarios ⏱️ ~6 hours

**Deliverables:**
- Sidebar controls for income/expense adjustments
- Real-time scenario calculation
- Waterfall chart showing impact
- Sensitivity analysis table
- Monthly breakdown chart
- Insights engine (6-8 insights)

**Acceptance Criteria:**
- Sliders update calculations in real-time
- Waterfall chart shows component impacts
- Sensitivity table displays correctly
- Insights are relevant and actionable
- Multiple scenarios can be compared

**Files to Modify:**
- `pages/6_💰_Savings_Forecast.py`
- `utils/calculations.py` (add scenario logic)
- `utils/charts.py` (add waterfall, breakdown charts)

### Phase 3: Long-term Retirement Calculator ⏱️ ~10 hours

**Deliverables:**
- Collapsible expander section
- Input form with all parameters
- Core retirement projection calculation
- Wealth accumulation chart
- Contribution breakdown chart
- Retirement readiness gauge
- Summary metrics for retirement
- Retirement age scenarios table

**Acceptance Criteria:**
- Calculator inputs pre-filled from dashboards
- Projection calculates accurately
  - Compound interest correct
  - Inflation applied properly
  - Tax calculations correct
- Charts display accumulation and drawdown
- Metrics show correct values
- Scenarios table compares different retirement ages

**Files to Create/Modify:**
- `utils/retirement_calculator.py` (new)
- `pages/6_💰_Savings_Forecast.py` (add expander)
- `utils/charts.py` (add retirement charts)

### Phase 4: Advanced Features ⏱️ ~12 hours

**Deliverables:**
- Monte Carlo simulation (1000 runs)
- Monte Carlo distribution chart
- Confidence interval shading on wealth chart
- Safe withdrawal rate analysis
- Safe withdrawal chart
- Multiple goals tracking
- Goal markers on charts
- Tax optimization logic
- Detailed recommendation engine
- Quick adjustment sliders
- Scenario save/load functionality
- CSV/PDF export

**Acceptance Criteria:**
- Monte Carlo completes in <10 seconds
- Success rate calculated accurately
- Safe withdrawal rates compared
- Goals tracked and displayed
- Recommendations are specific and actionable
- Export functions work correctly

**Files to Modify:**
- `utils/retirement_calculator.py` (add Monte Carlo, goals)
- `pages/6_💰_Savings_Forecast.py` (add advanced UI)
- `utils/charts.py` (add Monte Carlo chart)

---

## Integration Points

### Data Dependencies

**From Cash Flow Dashboard:**
```python
# Import or replicate logic
from utils.api_client import FireflyAPIClient
from utils.calculations import calculate_cash_flow

# Fetch YTD transactions
ytd_transactions = client.get_transactions(
    start_date=f"{current_year}-01-01",
    end_date=datetime.now().strftime('%Y-%m-%d')
)

df_transactions = client.parse_transaction_data(ytd_transactions)

# Calculate YTD totals
ytd_income = df_transactions[df_transactions['type'] == 'deposit']['amount'].sum()
ytd_expenses = df_transactions[df_transactions['type'] == 'withdrawal']['amount'].sum()
```

**From Net Worth Dashboard:**
```python
# Get current net worth
accounts = client.get_accounts()
df_accounts = client.parse_account_data(accounts)
current_net_worth = df_accounts[df_accounts['include_net_worth'] == True]['current_balance'].sum()
```

**From Budget Dashboard:**
```python
# Get budget compliance data
budgets = client.get_budgets()
budget_limits = client.get_budget_limits(budget_id, start_date, end_date)
budget_performance = calculate_budget_performance(budgets, budget_limits, df_transactions, start_date, end_date)

# Calculate over-budget amounts
total_over = budget_performance[budget_performance['status'] == 'Over Budget']['remaining'].abs().sum()
```

**From Categories Dashboard:**
```python
# Get top spending categories
category_spending = calculate_category_spending(df_transactions, start_date, end_date)
top_5_categories = category_spending.head(5)['category_name'].tolist()
```

### Navigation Links

**To Savings Forecast from other dashboards:**

Update each dashboard's compact navigation section:

```python
# Cash Flow page
st.markdown('... <a href="/Savings_Forecast" style="color: #58a6ff;">💰 Savings Forecast</a> ...')

# Budget page
st.markdown('... <a href="/Savings_Forecast" style="color: #58a6ff;">💰 Savings Forecast</a> ...')

# Categories page
st.markdown('... <a href="/Savings_Forecast" style="color: #58a6ff;">💰 Savings Forecast</a> ...')

# Net Worth page
st.markdown('... <a href="/Savings_Forecast" style="color: #58a6ff;">💰 Savings Forecast</a> ...')
```

**From Savings Forecast to others:**

```python
st.markdown('<div style="background-color: rgba(49, 51, 63, 0.2); padding: 0.3rem 0.5rem; border-radius: 0.3rem; font-size: 0.75rem;">💡 <b>Related:</b> <a href="/Cash_Flow" style="color: #58a6ff;">📈 Cash Flow</a> • <a href="/Budget" style="color: #58a6ff;">💰 Budget</a> • <a href="/Categories" style="color: #58a6ff;">🏷️ Categories</a> • <a href="/Net_Worth" style="color: #58a6ff;">📊 Net Worth</a></div>', unsafe_allow_html=True)
```

---

## Sample User Workflows

### Workflow 1: "Can I afford a vacation this year?"

1. User opens Savings Forecast page
2. Views baseline projection: €12,500 by year-end
3. Adjusts sidebar: "One-time expense: €2,000" (vacation)
4. Sees updated projection: €10,500
5. Checks if still on track for savings goal
6. Decision: Go on vacation (still above minimum target)

**Expected Time:** 2 minutes

### Workflow 2: "Should I take the new job with higher pay?"

1. User opens Savings Forecast
2. Current projection: €12,500
3. Adjusts "Expected Income Change: +15%"
4. Views waterfall chart showing +€3,200 impact
5. New projection: €15,700
6. Sees sensitivity table: multiple scenarios
7. Decision: Job change significantly improves savings

**Expected Time:** 3 minutes

### Workflow 3: "How can I save more?"

1. User views baseline: €12,500
2. Checks insights section:
   - "Your biggest spending is Dining (€3,200)"
   - "Reducing it 15% adds €480"
3. Adjusts "Dining category: -15%"
4. Views waterfall: +€480
5. Adjusts "Additional savings: €100/month"
6. Views waterfall: +€600 more
7. New projection: €13,580
8. Decision: Reduce dining out, set up automatic savings

**Expected Time:** 4 minutes

### Workflow 4: "When can I retire?"

1. User scrolls to retirement calculator
2. Inputs pre-filled from dashboards:
   - Age: 32
   - Net worth: €45,000
   - Monthly savings: €2,000
3. Sets target retirement age: 65
4. Views projection: €852,000 at retirement
5. Sees monthly income: €2,840 (4% rule)
6. Checks success rate: 87%
7. Adjusts savings to €2,500/month
8. New projection: €1,065,000 (95% success rate)
9. Views retirement scenarios table
10. Sees can retire at 60 with €2,500/month savings
11. Decision: Increase savings to retire 5 years early

**Expected Time:** 8 minutes

### Workflow 5: "Is my retirement plan realistic?"

1. User opens retirement calculator
2. Sets parameters:
   - Retirement age: 55 (early retirement goal)
   - Current savings: €2,000/month
3. Runs Monte Carlo simulation
4. Views success rate: 62% (too low!)
5. Checks recommendations:
   - "Work 2 more years (retire at 57) improves success to 85%"
   - "Reduce retirement expenses 10% adds 5 years portfolio life"
6. Adjusts retirement age: 57
7. New success rate: 85%
8. Views safe withdrawal analysis
9. Sees 3.5% withdrawal rate is sustainable
10. Decision: Retire at 57, plan for modest retirement lifestyle

**Expected Time:** 12 minutes

---

## Future Enhancements

### Phase 5: Goal Tracking Dashboard Integration

**Features:**
- Save specific savings goals (house, car, emergency fund)
- Track progress toward each goal
- Allocate income to multiple goals
- Visual progress bars for each goal
- Timeline showing when each goal will be reached

**Implementation:**
- New table in session state for goals
- Integration with budget categories
- Separate goal allocation logic
- Enhanced charts showing multiple goal trajectories

### Phase 6: Investment Portfolio Optimization

**Features:**
- Asset allocation recommendations based on age/risk tolerance
- Rebalancing suggestions
- Tax-loss harvesting opportunities
- Fee impact analysis (expense ratios)
- Compare target date funds vs DIY allocation

**Implementation:**
- Modern Portfolio Theory calculations
- Risk tolerance questionnaire
- Asset class return assumptions
- Fee comparison engine

### Phase 7: Life Milestone Templates

**Features:**
- Pre-defined templates for major life events:
  - Marriage (combined finances, wedding expenses)
  - Children (childcare, education costs)
  - Home purchase (down payment, mortgage)
  - Career change (income disruption)
  - Retirement (lifestyle changes)
- Apply templates to projection with one click
- Customize template parameters

**Implementation:**
- Template library with default values
- Template selection UI
- Merge template with current projection
- Scenario comparison with/without milestone

### Phase 8: Social Benchmarking

**Features:**
- Compare savings rate to national/international averages
- Age-based benchmarks (e.g., "average net worth at 35")
- Percentile ranking
- Anonymized data sharing (opt-in)

**Implementation:**
- Benchmark data API or static dataset
- Percentile calculations
- Privacy-preserving comparisons
- Visual comparison charts

### Phase 9: AI-Powered Insights

**Features:**
- Natural language queries: "How much more do I need to save to retire at 60?"
- Personalized recommendations based on spending patterns
- Anomaly detection (unusual spending)
- Predictive alerts (projected to miss savings goal)

**Implementation:**
- Integration with LLM API (OpenAI, Claude)
- Prompt engineering for financial queries
- Context injection (user's financial data)
- Safety guardrails for financial advice

### Phase 10: Mobile Responsiveness & PWA

**Features:**
- Optimized layout for mobile devices
- Progressive Web App (PWA) for offline access
- Push notifications for goal milestones
- Quick-entry for on-the-go updates

**Implementation:**
- Responsive CSS breakpoints
- PWA manifest and service worker
- Mobile-optimized charts (touch interactions)
- Simplified mobile UI

---

## Testing Checklist

### Current Year Forecast Tests

- [ ] Baseline projection calculates correctly
- [ ] YTD metrics match source data
- [ ] Trajectory chart displays historical data
- [ ] Trajectory chart shows projection
- [ ] Income adjustment slider updates projection
- [ ] Expense adjustment slider updates projection
- [ ] One-time income/expense applied correctly
- [ ] Category-specific adjustments work
- [ ] Waterfall chart shows correct impacts
- [ ] Sensitivity table calculates all scenarios
- [ ] Preset scenarios apply correctly
- [ ] Insights are relevant and accurate
- [ ] Navigation links work
- [ ] Page loads in <3 seconds

### Retirement Calculator Tests

- [ ] Input pre-fill from dashboards correct
- [ ] Compound interest calculation accurate (verified manually)
- [ ] Inflation applied correctly
- [ ] Tax calculations correct
- [ ] Employer match calculated correctly
- [ ] Wealth accumulation chart displays correctly
- [ ] Accumulation phase calculations correct
- [ ] Retirement phase calculations correct
- [ ] Safe withdrawal rates calculated correctly
- [ ] Portfolio depletion detected correctly
- [ ] Monte Carlo simulation runs without errors
- [ ] Monte Carlo percentiles calculated correctly
- [ ] Success rate accurate
- [ ] Retirement readiness gauge shows correct %
- [ ] Scenario table compares ages correctly
- [ ] Goals tracked and displayed
- [ ] Recommendations are relevant
- [ ] Quick adjustment sliders work
- [ ] CSV export downloads correctly
- [ ] Calculator completes in <5 seconds (without Monte Carlo)
- [ ] Monte Carlo completes in <10 seconds

### Integration Tests

- [ ] Data fetched from Cash Flow correctly
- [ ] Data fetched from Net Worth correctly
- [ ] Data fetched from Budget correctly
- [ ] Data fetched from Categories correctly
- [ ] Navigation between pages works
- [ ] Session state persists across navigation
- [ ] No conflicts with existing dashboards
- [ ] Styling consistent with other dashboards

### Edge Case Tests

- [ ] No historical data (new user)
- [ ] Negative cash flow (spending > income)
- [ ] Zero savings rate
- [ ] Extreme adjustment values (-100%, +1000%)
- [ ] Very short time horizon (retire next year)
- [ ] Very long time horizon (retire in 50 years)
- [ ] Portfolio depletion during retirement
- [ ] Negative investment returns
- [ ] Zero investment returns
- [ ] Multiple currencies (if applicable)

---

## Success Metrics

### User Engagement
- **Page views:** Track visits to Savings Forecast page
- **Time on page:** Average session duration
- **Interaction rate:** % of users who adjust sliders/inputs
- **Scenario creation:** # of custom scenarios created
- **Export usage:** # of CSV/PDF downloads

### Feature Adoption
- **Current year forecast:** % of users who view
- **Retirement calculator:** % of users who open expander
- **Monte Carlo simulation:** % of users who run simulation
- **Goal tracking:** # of goals created
- **Scenario comparison:** # of scenarios compared

### Impact Metrics
- **Savings rate improvement:** Do users increase savings after using dashboard?
- **Budget adherence:** Do users stick to budgets better?
- **Retirement readiness:** Do users feel more prepared?

### Technical Metrics
- **Page load time:** <3 seconds
- **Calculation speed:** <1 second for projections
- **Monte Carlo speed:** <10 seconds for 1000 simulations
- **Error rate:** <1% of sessions
- **Mobile usage:** % of mobile visitors

---

## Documentation Updates Needed

### User Guide

Create `pythondashboard/Docs/SAVINGS_FORECAST_USER_GUIDE.md` with:
- How to use current year forecast
- How to create scenarios
- How to interpret insights
- How to use retirement calculator
- How to run Monte Carlo simulation
- How to optimize savings
- FAQs and troubleshooting

### API Documentation

Update `pythondashboard/Docs/API_REFERENCE.md` with:
- New calculation functions
- New chart functions
- Retirement calculator API
- Input/output specifications

### Dashboard Roadmap

Update `pythondashboard/Docs/DASHBOARD_ROADMAP.md`:
- Add Savings Forecast as Phase 2
- Update completion status
- Link to implementation doc

---

## Appendix

### Financial Formulas Reference

#### Compound Interest (Monthly Compounding)

```
FV = PV × (1 + r/n)^(n×t) + PMT × [((1 + r/n)^(n×t) - 1) / (r/n)]

Where:
- FV = Future Value
- PV = Present Value (starting balance)
- r = Annual interest rate (decimal)
- n = Compounding frequency (12 for monthly)
- t = Time in years
- PMT = Regular payment/contribution
```

#### Safe Withdrawal Rate (4% Rule)

```
Annual Withdrawal = Portfolio Value × 0.04

Monthly Withdrawal = (Portfolio Value × 0.04) / 12

Portfolio Needed = Annual Expenses / 0.04
```

#### Inflation Adjustment

```
Real Value = Nominal Value / (1 + inflation_rate)^years

Future Expenses = Current Expenses × (1 + inflation_rate)^years
```

#### Savings Rate

```
Savings Rate (%) = (Income - Expenses) / Income × 100
```

#### Capital Gains Tax

```
Tax Owed = (Portfolio Gains × Taxable Portion) × Tax Rate

Where:
- Taxable Portion = 1 - (Tax Advantaged %)
```

#### Employer Match

```
Match Amount = min(
    Annual Salary × Match %,
    Match Cap
)
```

### Color Palette

Use consistent colors across all charts:

```python
COLORS = {
    'primary': '#2E86AB',      # Blue (income, baseline)
    'secondary': '#A23B72',    # Purple (projections)
    'success': '#6A994E',      # Green (positive, on track)
    'warning': '#F18F01',      # Orange (warning, moderate)
    'danger': '#C73E1D',       # Red (expenses, over budget)
    'neutral': '#64748B',      # Gray (neutral info)
    'accent': '#8B5CF6',       # Purple (highlights)
}
```

### Icon Legend

- 💰 Savings/Money
- 📊 Charts/Analysis
- 📈 Growth/Increase
- 📉 Decline/Decrease
- 🎯 Goals/Targets
- ✅ Success/Complete
- ⚠️ Warning/Caution
- 🚨 Alert/Danger
- 💡 Tip/Insight
- 📅 Calendar/Timeline
- 🏖️ Retirement
- 💼 Professional/Tax
- 🎉 Celebration/Achievement
- 🔍 Detail/Analysis

---

**End of Implementation Plan**

**Version:** 1.0
**Last Updated:** 2025-01-26
**Status:** 📋 Ready for Implementation

---

## Next Steps

1. **Review this plan** with stakeholders
2. **Prioritize phases** based on business needs
3. **Allocate resources** for development
4. **Set timeline** for each phase
5. **Begin Phase 1 implementation**
6. **Create user guide** alongside development
7. **Set up testing environment**
8. **Plan user testing** for Phase 1
9. **Iterate based on feedback**
10. **Launch Phase 1** to production
