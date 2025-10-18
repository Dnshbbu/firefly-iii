# Firefly III Dashboard Roadmap

**Version:** 1.0
**Last Updated:** 2025-10-18
**Status:** Planning Phase

---

## Table of Contents

1. [Overview](#overview)
2. [Current State](#current-state)
3. [Planned Dashboards](#planned-dashboards)
4. [Implementation Priority](#implementation-priority)
5. [Technical Architecture](#technical-architecture)
6. [API Endpoints Required](#api-endpoints-required)
7. [Design Principles](#design-principles)
8. [Development Phases](#development-phases)

---

## Overview

This document outlines the comprehensive roadmap for building a custom Firefly III dashboard using Streamlit and the Firefly III REST API. The goal is to create an intuitive, actionable personal finance management interface that provides insights beyond the default Firefly III web interface.

**Tech Stack:**
- **Frontend:** Streamlit (Python)
- **Visualization:** Plotly, Chart.js (via gridstack.js)
- **Layout:** gridstack.js for draggable/resizable widgets
- **API:** Firefly III REST API v1
- **Data Processing:** Pandas

---

## Current State

### Implemented Features

1. **Net Worth Dashboard** (`pages/1_📊_Net_Worth.py`)
   - Total net worth calculation by currency
   - Asset breakdown by account type (pie chart)
   - Individual account balances (horizontal bar chart)
   - Account details table with filtering
   - Gridstack.js draggable layout support
   - Dark mode compatible styling

2. **CSV Preprocessor** (`pages/2_📄_CSV_Preprocessor.py`)
   - Automatic bank detection (Revolut, AIB, T212, Revolut CC)
   - Data cleaning and standardization
   - Duplicate/internal transaction removal
   - Date format conversion

### Existing Infrastructure

- **API Client:** `FireflyAPIClient` class with authentication and basic account fetching
- **Styling:** Compact dark mode CSS
- **Session Management:** API credentials stored in session state
- **Gridstack Integration:** Reusable widget framework

---

## Planned Dashboards

### 1. 💰 Budget Dashboard

**Purpose:** Track budget performance and spending against allocated budgets.

**Key Features:**
- Budget vs. actual spending by category (current period)
- Budget burn rate indicator (daily spending rate)
- Top over-budget categories (red flag alerts)
- Budget utilization gauge charts (0-100%)
- Spending forecast based on current burn rate
- Historical budget performance trends
- Budget limit timeline (when will budget run out)

**Visualizations:**
- Stacked bar chart: Budgeted vs. Actual vs. Remaining
- Gauge charts: Budget utilization percentage
- Line chart: Daily spend rate with projected end-of-month
- Table: Category breakdown with variance analysis
- Heat map: Budget performance across categories and time

**API Endpoints:**
- `GET /api/v1/budgets` - List all budgets
- `GET /api/v1/budget-limits` - Get budget limits by period
- `GET /api/v1/budgets/{id}/limits` - Specific budget limits
- `GET /api/v1/budgets/{id}/transactions` - Transactions per budget

**Metrics:**
- Total budgeted amount (current period)
- Total spent amount
- Total remaining
- Average daily spend rate
- Projected end-of-period balance
- Number of over-budget categories

---

### 2. 📈 Cash Flow Dashboard

**Purpose:** Visualize income vs. expenses and understand cash flow patterns.

**Key Features:**
- Income vs. expenses over time (month/quarter/year)
- Monthly net cash flow (income - expenses)
- Income sources breakdown
- Expense categories breakdown
- Cash flow trend analysis (increasing/decreasing)
- Weekly/monthly/quarterly aggregations
- Running balance over time

**Visualizations:**
- Combo chart: Income (green bars) + Expenses (red bars) + Net (line)
- Waterfall chart: Cash flow breakdown
- Area chart: Cumulative cash flow
- Pie/Donut charts: Income sources & expense categories
- Sparklines: Quick trend indicators

**API Endpoints:**
- `GET /api/v1/transactions` - All transactions with date filters
- `GET /api/v1/summary/basic` - Income/expense summary

**Metrics:**
- Total income (period)
- Total expenses (period)
- Net cash flow
- Average monthly income
- Average monthly expenses
- Income-to-expense ratio

---

### 3. 🏷️ Category Spending Analysis

**Purpose:** Deep dive into spending patterns by category.

**Key Features:**
- Spending by category over time (trend analysis)
- Top spending categories (ranked)
- Category spending trends with sparklines
- Month-over-month category comparison
- Average spending per category
- Category percentage of total spending
- Subcategory breakdown (if available)

**Visualizations:**
- Treemap: Hierarchical category spending
- Sunburst chart: Category/subcategory relationships
- Horizontal bar: Top 10 categories
- Line chart: Category trends over time
- Small multiples: Sparklines for each category
- Table: Detailed category breakdown with sorting

**API Endpoints:**
- `GET /api/v1/categories` - List all categories
- `GET /api/v1/categories/{id}/transactions` - Transactions per category
- `GET /api/v1/transactions` - Filter by category

**Metrics:**
- Total number of categories
- Top spending category
- Average spend per category
- Category with highest growth
- Uncategorized transaction count

---

### 4. 📊 Transaction Analytics

**Purpose:** Detailed transaction analysis and search.

**Key Features:**
- Recent transactions table (sortable, filterable, searchable)
- Transaction volume over time (daily/weekly/monthly)
- Average transaction amount by category
- Top merchants/payees
- Transaction type distribution (withdrawal/deposit/transfer)
- Transaction search with advanced filters
- Export filtered results

**Visualizations:**
- Data table: Recent transactions with inline search
- Histogram: Transaction amounts distribution
- Bar chart: Transaction volume by day of week
- Bar chart: Top merchants/payees
- Heatmap: Transactions by day of week × hour (if time data available)
- Timeline: Transaction history

**API Endpoints:**
- `GET /api/v1/transactions` - Paginated transactions
- `GET /api/v1/search/transactions` - Search transactions

**Metrics:**
- Total transaction count (period)
- Average transaction amount
- Largest expense
- Largest income
- Most frequent merchant
- Transaction frequency (transactions per day)

---

### 5. 💳 Liability & Debt Tracking

**Purpose:** Monitor debt, loans, and credit obligations.

**Key Features:**
- Total debt overview (all liability accounts)
- Debt paydown progress over time
- Credit card utilization rates
- Debt-to-asset ratio
- Individual liability account tracking
- Projected payoff dates (based on payment trends)
- Interest accrual tracking

**Visualizations:**
- Area chart: Total debt over time (decreasing trend)
- Progress bars: Individual debt payoff progress
- Gauge: Debt-to-asset ratio
- Bar chart: Liability accounts by balance
- Line chart: Debt reduction rate

**API Endpoints:**
- `GET /api/v1/accounts?type=liabilities` - Liability accounts
- `GET /api/v1/accounts/{id}/transactions` - Liability transactions

**Metrics:**
- Total debt
- Total assets
- Debt-to-asset ratio
- Debt-to-income ratio
- Average monthly payment
- Projected debt-free date

---

### 6. 🐷 Savings Goals (Piggy Banks)

**Purpose:** Track savings goals and progress.

**Key Features:**
- Progress bars for each savings goal
- Target vs. actual savings
- Savings rate over time
- Goal completion timeline
- Total saved vs. total goal amount
- Goal prioritization
- Projected completion dates

**Visualizations:**
- Progress bars: Individual goal progress
- Stacked bar: All goals overview
- Line chart: Savings accumulation over time
- Gauge: Overall savings goal completion
- Timeline: Goal milestones

**API Endpoints:**
- `GET /api/v1/piggy-banks` - All piggy banks
- `GET /api/v1/piggy-banks/{id}` - Specific piggy bank details
- `GET /api/v1/piggy-banks/{id}/events` - Savings events

**Metrics:**
- Total saved across all goals
- Total target amount
- Overall completion percentage
- Closest goal to completion
- Average monthly savings rate

---

### 7. 📅 Bills & Recurring Transactions

**Purpose:** Track bills and manage recurring payments.

**Key Features:**
- Upcoming bills calendar view
- Bill payment history (paid/unpaid status)
- Recurring transaction summary
- Bills paid vs. unpaid this month
- Average monthly bill amount trends
- Bill payment alerts (overdue/upcoming)
- Recurring transaction patterns

**Visualizations:**
- Calendar: Upcoming bill due dates
- Table: Bills with payment status
- Bar chart: Monthly bill amounts over time
- Pie chart: Bill distribution by category
- Timeline: Payment history

**API Endpoints:**
- `GET /api/v1/bills` - List all bills
- `GET /api/v1/bills/{id}` - Bill details
- `GET /api/v1/recurrences` - Recurring transactions
- `GET /api/v1/recurrences/{id}/transactions` - Transactions from recurrence

**Metrics:**
- Total bills this month
- Bills paid this month
- Bills unpaid this month
- Average monthly bill amount
- Next bill due date
- Total recurring monthly expenses

---

### 8. 📉 Net Worth Trends (Enhancement)

**Purpose:** Extend current net worth dashboard with historical trends.

**Key Features:**
- Historical net worth over time (line chart)
- Asset allocation changes over time (area chart)
- Month-over-month growth
- Year-over-year growth
- Net worth growth rate (percentage)
- Milestone tracker (when you reached certain amounts)
- Asset class performance comparison

**Visualizations:**
- Line chart: Net worth over time
- Stacked area: Asset allocation evolution
- Bar chart: MoM/YoY growth
- Milestone markers: Key net worth achievements
- Waterfall: Net worth changes breakdown

**API Endpoints:**
- `GET /api/v1/charts/account/overview` - Account balances over time
- `GET /api/v1/insight/total/asset` - Historical asset data
- `GET /api/v1/insight/total/liability` - Historical liability data

**Metrics:**
- Current net worth
- Net worth 1 month ago
- Net worth 1 year ago
- MoM growth (absolute + percentage)
- YoY growth (absolute + percentage)
- Average monthly growth rate
- Annualized growth rate

---

### 9. 📍 Financial Health Score

**Purpose:** Provide a composite view of financial health.

**Key Features:**
- Emergency fund ratio (liquid assets / monthly expenses)
- Debt-to-income ratio
- Savings rate (savings / income)
- Financial health composite score (0-100)
- Recommendations based on metrics
- Benchmark comparisons (optional)
- Financial health trends

**Visualizations:**
- Gauge: Overall financial health score
- Radar chart: Multi-dimensional health metrics
- Progress bars: Individual metric scores
- Traffic light indicators: Red/yellow/green status
- Trend line: Score changes over time

**Calculations:**
- Emergency fund ratio = Liquid assets / (Monthly expenses × 3)
- Debt-to-income = Monthly debt payments / Monthly income
- Savings rate = Monthly savings / Monthly income
- Health score = Weighted average of all metrics

**Metrics:**
- Financial health score (0-100)
- Emergency fund months
- Debt-to-income ratio
- Savings rate percentage
- Net worth trend (positive/negative)

---

### 10. 🔍 Smart Insights

**Purpose:** Automated insights and anomaly detection.

**Key Features:**
- Unusual spending alerts (statistical anomalies)
- Spending pattern insights (e.g., "You spend 30% more on weekends")
- Month-end projections
- Largest expense changes month-over-month
- Rule effectiveness tracking
- Category spending trends (increasing/decreasing)
- Actionable recommendations

**Visualizations:**
- Alert cards: Highlighted insights
- Comparison charts: This month vs. average
- Anomaly markers: Unusual transactions
- Trend arrows: Increasing/decreasing indicators

**Analysis Methods:**
- Statistical anomaly detection (z-score, IQR)
- Time series pattern recognition
- Moving averages for trend detection
- Percentage change calculations

**Insights Examples:**
- "Groceries spending is 25% higher than usual this month"
- "You've made 15 transactions at Coffee Shop X this month"
- "Projected to be $200 under budget for Dining Out"
- "Net worth increased by €500 this month"

---

### 11. 📆 Period Comparison

**Purpose:** Compare financial metrics across different time periods.

**Key Features:**
- Side-by-side month comparison
- Year-over-year comparison
- Custom date range comparisons
- Seasonal spending patterns
- Period-over-period growth rates
- Multi-period trend analysis

**Visualizations:**
- Side-by-side bar charts: Period comparisons
- Line chart: Multi-period trends
- Table: Detailed metric comparisons with variance
- Heat map: Seasonal patterns across years

**Comparison Types:**
- This month vs. last month
- This month vs. same month last year
- This quarter vs. last quarter
- Custom period A vs. custom period B

**Metrics:**
- Absolute change (€)
- Percentage change (%)
- Variance explanation (category breakdown)

---

### 12. 🎯 Goals & Projections

**Purpose:** Financial forecasting and scenario planning.

**Key Features:**
- Retirement savings projection
- Savings goal timeline
- What-if scenarios (e.g., "What if I save $500 more per month?")
- Break-even analysis for budgets
- Investment growth projections
- Debt payoff simulations

**Visualizations:**
- Projection line chart: Future scenarios
- Comparison chart: Different scenarios side-by-side
- Timeline: Goal achievement dates
- Slider controls: Interactive scenario parameters

**Calculations:**
- Linear regression for trend projections
- Compound growth calculations
- Debt amortization schedules
- Goal achievement date calculations

**Scenarios:**
- Conservative (current savings rate)
- Moderate (10% increase in savings)
- Aggressive (20% increase in savings)
- Custom (user-defined parameters)

---

## Implementation Priority

### Phase 1: Foundation (Immediate Priority)

**Recommended First Implementations:**

1. **Cash Flow Dashboard** ⭐⭐⭐ ✅ **COMPLETED**
   - **Why:** Most actionable insights for daily financial management
   - **Complexity:** Medium (requires transaction aggregation)
   - **Impact:** High (shows where money is going)
   - **Dependencies:** Transaction API endpoint
   - **Estimated Effort:** 1-2 days
   - **Status:** Implemented 2025-10-18
   - **Location:** `pages/3_📈_Cash_Flow.py`

2. **Budget Dashboard** ⭐⭐⭐ ✅ **COMPLETED**
   - **Why:** Complements net worth, enables proactive financial management
   - **Complexity:** Medium (budget API + transaction correlation)
   - **Impact:** High (helps control spending)
   - **Dependencies:** Budget API, transaction API
   - **Estimated Effort:** 2-3 days
   - **Status:** Implemented 2025-10-18
   - **Location:** `pages/4_💰_Budget.py`

3. **Category Spending Analysis** ⭐⭐ 🔄 **NEXT UP**
   - **Why:** Deep dive into spending habits
   - **Complexity:** Medium (requires category aggregation)
   - **Impact:** High (identifies spending patterns)
   - **Dependencies:** Category API, transaction API
   - **Estimated Effort:** 1-2 days

### Phase 2: Enhanced Insights (Next Priority)

4. **Net Worth Trends** ⭐⭐⭐
   - **Why:** Extends existing dashboard with historical context
   - **Complexity:** Low-Medium (time series data)
   - **Impact:** High (shows financial progress)
   - **Dependencies:** Chart API endpoints
   - **Estimated Effort:** 1 day

5. **Transaction Analytics** ⭐⭐
   - **Why:** Detailed transaction exploration
   - **Complexity:** Low (mostly UI work)
   - **Impact:** Medium (useful for research/auditing)
   - **Dependencies:** Transaction API
   - **Estimated Effort:** 1-2 days

6. **Bills & Recurring Transactions** ⭐⭐
   - **Why:** Helps manage regular payments
   - **Complexity:** Medium (calendar integration)
   - **Impact:** Medium-High (prevents missed payments)
   - **Dependencies:** Bills API, recurrence API
   - **Estimated Effort:** 2 days

### Phase 3: Advanced Features (Later Priority)

7. **Liability & Debt Tracking** ⭐
   - **Why:** Important for debt management (if applicable)
   - **Complexity:** Medium (projection calculations)
   - **Impact:** High (if user has debt), Low (if debt-free)
   - **Dependencies:** Account API, transaction API
   - **Estimated Effort:** 1-2 days

8. **Savings Goals (Piggy Banks)** ⭐
   - **Why:** Track specific savings objectives
   - **Complexity:** Low-Medium
   - **Impact:** Medium (motivational tool)
   - **Dependencies:** Piggy bank API
   - **Estimated Effort:** 1 day

9. **Financial Health Score** ⭐⭐
   - **Why:** Composite health indicator
   - **Complexity:** High (calculation logic + multiple data sources)
   - **Impact:** Medium (informational, not actionable)
   - **Dependencies:** Multiple APIs, custom calculations
   - **Estimated Effort:** 2-3 days

### Phase 4: Intelligence & Optimization (Future)

10. **Smart Insights** ⭐⭐⭐
    - **Why:** Proactive recommendations and anomaly detection
    - **Complexity:** Very High (ML/statistics)
    - **Impact:** Very High (actionable intelligence)
    - **Dependencies:** All transaction data, statistical libraries
    - **Estimated Effort:** 3-5 days

11. **Period Comparison** ⭐
    - **Why:** Comparative analysis
    - **Complexity:** Medium (data aggregation across periods)
    - **Impact:** Medium (analytical tool)
    - **Dependencies:** Transaction API, date range handling
    - **Estimated Effort:** 1-2 days

12. **Goals & Projections** ⭐⭐
    - **Why:** Future planning and scenario modeling
    - **Complexity:** High (projection algorithms)
    - **Impact:** High (long-term planning)
    - **Dependencies:** Historical data, mathematical modeling
    - **Estimated Effort:** 3-4 days

---

## Technical Architecture

### File Structure

```
pythondashboard/
├── Home.py                          # Main landing page (updated)
├── pages/
│   ├── 1_📊_Net_Worth.py           # Existing: Net worth dashboard
│   ├── 2_📄_CSV_Preprocessor.py    # Existing: CSV preprocessing
│   ├── 3_📈_Cash_Flow.py           # ✅ DONE: Cash flow dashboard
│   ├── 4_💰_Budget.py              # ✅ DONE: Budget dashboard
│   ├── 5_🏷️_Categories.py         # TODO: Category analysis
│   ├── 6_📊_Transactions.py        # New: Transaction analytics
│   ├── 7_💳_Liabilities.py         # New: Debt tracking
│   ├── 8_🐷_Savings_Goals.py       # New: Piggy banks
│   ├── 9_📅_Bills.py               # New: Bills & recurring
│   ├── 10_📉_Net_Worth_Trends.py   # New: Historical net worth
│   ├── 11_📍_Financial_Health.py   # New: Health score
│   ├── 12_🔍_Insights.py           # New: Smart insights
│   ├── 13_📆_Compare.py            # New: Period comparison
│   └── 14_🎯_Projections.py        # New: Goals & forecasting
├── utils/                           # ✅ Shared utilities created
│   ├── __init__.py                 # ✅ Module initialization
│   ├── api_client.py               # ✅ FireflyAPIClient with budget methods
│   ├── charts.py                   # ✅ 12+ chart functions (including budget charts)
│   ├── calculations.py             # ✅ Financial calcs (cash flow + budget functions)
│   ├── gridstack.py                # TODO: Gridstack widget utilities
│   ├── insights.py                 # TODO: Insight generation logic
│   └── formatters.py               # TODO: Data formatting utilities
├── config/
│   ├── __init__.py
│   └── settings.py                 # App configuration
├── requirements.txt
├── README.md
└── Docs/
    ├── DASHBOARD_ROADMAP.md        # This file
    ├── API_ENDPOINTS.md            # API reference
    └── DESIGN_GUIDELINES.md        # UI/UX guidelines
```

### Shared Components

**API Client (`utils/api_client.py`):**
```python
class FireflyAPIClient:
    def __init__(self, base_url: str, api_token: str)
    def test_connection(self) -> tuple[bool, str]
    def get_accounts(self, account_type: str = None) -> List[Dict]
    def get_transactions(self, start_date: str = None, end_date: str = None, type: str = None) -> List[Dict]
    def get_budgets(self) -> List[Dict]
    def get_budget_limits(self, budget_id: str, start: str, end: str) -> List[Dict]
    def get_categories(self) -> List[Dict]
    def get_bills(self) -> List[Dict]
    def get_piggy_banks(self) -> List[Dict]
    def get_recurrences(self) -> List[Dict]
    def search_transactions(self, query: str) -> List[Dict]
    # ... more methods as needed
```

**Chart Utilities (`utils/charts.py`):**
```python
def create_line_chart(df: pd.DataFrame, x: str, y: str, title: str) -> go.Figure
def create_bar_chart(df: pd.DataFrame, x: str, y: str, title: str) -> go.Figure
def create_pie_chart(df: pd.DataFrame, labels: str, values: str, title: str) -> go.Figure
def create_stacked_area_chart(df: pd.DataFrame, x: str, y_columns: List[str], title: str) -> go.Figure
def create_waterfall_chart(categories: List[str], values: List[float], title: str) -> go.Figure
def create_gauge_chart(value: float, max_value: float, title: str) -> go.Figure
# ... more chart types
```

**Gridstack Utilities (`utils/gridstack.py`):**
```python
def create_gridstack_dashboard(widgets_html: str, height: int = 800) -> None
def create_widget(title: str, content: str, x: int, y: int, w: int, h: int, widget_id: str = "") -> str
def create_metric_widget(label: str, value: str, delta: str = None) -> str
def create_chart_widget(fig: go.Figure) -> str
def create_table_widget(df: pd.DataFrame) -> str
```

**Financial Calculations (`utils/calculations.py`):**
```python
def calculate_net_worth(df: pd.DataFrame) -> Dict[str, float]
def calculate_cash_flow(transactions_df: pd.DataFrame, period: str = 'monthly') -> pd.DataFrame
def calculate_savings_rate(income: float, expenses: float) -> float
def calculate_debt_to_income(debt_payments: float, income: float) -> float
def calculate_emergency_fund_ratio(liquid_assets: float, monthly_expenses: float) -> float
def project_savings_goal(current: float, target: float, monthly_contribution: float) -> date
def detect_anomalies(values: List[float], threshold: float = 2.0) -> List[int]
# ... more calculations
```

### Session State Management

```python
# In each dashboard page, initialize session state
if 'firefly_url' not in st.session_state:
    st.session_state.firefly_url = "http://192.168.0.242"
if 'firefly_token' not in st.session_state:
    st.session_state.firefly_token = ""
if 'api_connected' not in st.session_state:
    st.session_state.api_connected = False

# Cache API calls to reduce redundant requests
@st.cache_data(ttl=300)  # 5-minute cache
def fetch_transactions(_client: FireflyAPIClient, start_date: str, end_date: str):
    return _client.get_transactions(start_date, end_date)
```

### Dark Mode Styling

All dashboards should use consistent dark mode styling:

```python
st.markdown("""
<style>
    .block-container {
        padding-top: 1rem;
        padding-bottom: 0rem;
        padding-left: 2rem;
        padding-right: 2rem;
    }
    /* ... rest of compact dark mode CSS */
</style>
""", unsafe_allow_html=True)
```

---

## API Endpoints Required

### Core Endpoints (Already Used)

- `GET /api/v1/about` - API version and connection test
- `GET /api/v1/accounts` - List accounts (with type filter)
- `GET /api/v1/accounts/{id}` - Get specific account
- `GET /api/v1/accounts/{id}/transactions` - Transactions for an account

### Transaction Endpoints

- `GET /api/v1/transactions` - List all transactions (paginated)
  - Query params: `start`, `end`, `type` (withdrawal/deposit/transfer)
- `GET /api/v1/transactions/{id}` - Get specific transaction
- `GET /api/v1/search/transactions` - Search transactions
  - Query params: `query`, `field`

### Budget Endpoints

- `GET /api/v1/budgets` - List all budgets
- `GET /api/v1/budgets/{id}` - Get specific budget
- `GET /api/v1/budgets/{id}/limits` - Budget limits for a budget
- `GET /api/v1/budgets/{id}/transactions` - Transactions for a budget
- `GET /api/v1/budget-limits` - List all budget limits
- `GET /api/v1/available-budgets` - Available budget amounts

### Category Endpoints

- `GET /api/v1/categories` - List all categories
- `GET /api/v1/categories/{id}` - Get specific category
- `GET /api/v1/categories/{id}/transactions` - Transactions for a category

### Bill Endpoints

- `GET /api/v1/bills` - List all bills
- `GET /api/v1/bills/{id}` - Get specific bill
- `GET /api/v1/bills/{id}/transactions` - Transactions for a bill

### Recurring Transaction Endpoints

- `GET /api/v1/recurrences` - List all recurring transactions
- `GET /api/v1/recurrences/{id}` - Get specific recurrence
- `GET /api/v1/recurrences/{id}/transactions` - Transactions from recurrence

### Piggy Bank Endpoints

- `GET /api/v1/piggy-banks` - List all piggy banks
- `GET /api/v1/piggy-banks/{id}` - Get specific piggy bank
- `GET /api/v1/piggy-banks/{id}/events` - Savings events for piggy bank

### Chart/Insight Endpoints

- `GET /api/v1/charts/account/overview` - Account balance over time
- `GET /api/v1/insight/income/total` - Total income insights
- `GET /api/v1/insight/expense/total` - Total expense insights
- `GET /api/v1/insight/total/asset` - Total asset insights
- `GET /api/v1/insight/total/liability` - Total liability insights
- `GET /api/v1/summary/basic` - Basic financial summary

### User Preferences (Optional)

- `GET /api/v1/preferences` - User preferences
- `GET /api/v1/currencies` - Available currencies

---

## Design Principles

### 1. Consistency

- **Color Scheme:** Use consistent colors across all dashboards
  - Green (#4ade80) for positive values (income, gains)
  - Red (#f87171) for negative values (expenses, losses)
  - Blue (#60a5fa) for neutral values (transfers)
  - Gray (#b0b0b0) for secondary text

- **Typography:** Maintain font sizes and weights
  - Headers: 2rem (h1), 1.5rem (h2), 1.2rem (h3)
  - Body: 0.95rem
  - Metrics: 1.5rem (value), 0.85rem (label)

- **Spacing:** Use compact spacing as established in existing dashboards

### 2. Dark Mode First

- All dashboards must be designed for dark mode (#0e1117 background)
- Widget backgrounds: #262730
- Border color: rgba(250, 250, 250, 0.1)
- Text color: #fafafa (primary), #e0e0e0 (secondary), #b0b0b0 (tertiary)

### 3. Gridstack Integration

- All dashboards should support optional gridstack layout
- Provide both traditional Streamlit layout and gridstack layout
- Use checkbox toggle: "🎨 Use Draggable Dashboard Layout"

### 4. Performance

- Cache API calls with `@st.cache_data(ttl=300)` (5-minute TTL)
- Paginate large datasets
- Use lazy loading for heavy computations
- Show loading spinners: `with st.spinner("Loading data...")`

### 5. User Experience

- **Clear Metrics:** Display key metrics prominently at the top
- **Filters:** Provide date range, account type, category filters
- **Export:** Always include CSV export option
- **Refresh:** Include "🔄 Refresh Data" button
- **Help Text:** Use `help` parameter in widgets for explanations
- **Error Handling:** Graceful error messages with `st.error()` and `st.exception()`

### 6. Responsiveness

- Use `use_container_width=True` for charts and tables
- Responsive column layouts: `st.columns([1, 1, 4])`
- Mobile-friendly gridstack widgets

### 7. Accessibility

- Descriptive titles and labels
- Alt text for visualizations (Plotly built-in)
- High contrast colors (WCAG AA compliant)

---

## Development Phases

### Phase 1: Foundation (Weeks 1-2)

**Goal:** Implement core dashboards with highest impact.

**Tasks:**
1. Refactor `FireflyAPIClient` into `utils/api_client.py`
2. Create shared chart utilities in `utils/charts.py`
3. Implement **Cash Flow Dashboard**
4. Implement **Budget Dashboard**
5. Implement **Category Spending Analysis**

**Deliverables:**
- 3 new functional dashboards
- Refactored codebase with shared utilities
- Documentation for API client usage

### Phase 2: Enhanced Insights (Weeks 3-4)

**Goal:** Add historical trends and detailed analytics.

**Tasks:**
1. Enhance **Net Worth Dashboard** with historical trends
2. Implement **Transaction Analytics**
3. Implement **Bills & Recurring Transactions**

**Deliverables:**
- 3 additional dashboards
- Enhanced net worth dashboard
- Bill/recurring transaction tracking

### Phase 3: Advanced Features (Weeks 5-6)

**Goal:** Add specialized tracking for debt and savings goals.

**Tasks:**
1. Implement **Liability & Debt Tracking**
2. Implement **Savings Goals (Piggy Banks)**
3. Implement **Financial Health Score**

**Deliverables:**
- 3 specialized dashboards
- Financial health composite metric
- Debt management tools

### Phase 4: Intelligence & Optimization (Weeks 7-8)

**Goal:** Add intelligent insights and forecasting.

**Tasks:**
1. Implement **Smart Insights** (anomaly detection)
2. Implement **Period Comparison**
3. Implement **Goals & Projections**
4. Optimize performance across all dashboards

**Deliverables:**
- 3 advanced analytical dashboards
- Automated insight generation
- Performance optimizations

### Phase 5: Polish & Documentation (Week 9)

**Goal:** Finalize product and create comprehensive documentation.

**Tasks:**
1. UI/UX refinements across all dashboards
2. Comprehensive testing (manual + automated)
3. Documentation updates (README, API docs, user guide)
4. Demo video/screenshots
5. Deployment guide

**Deliverables:**
- Production-ready application
- Complete documentation
- Demo materials

---

## Success Metrics

### Technical Metrics

- **Page Load Time:** < 2 seconds for all dashboards
- **API Response Time:** < 1 second for cached data
- **Error Rate:** < 1% of API calls
- **Code Coverage:** > 80% (if tests are written)

### User Experience Metrics

- **Dashboard Completeness:** All 12+ dashboards implemented
- **Feature Parity:** Gridstack support on all dashboards
- **Export Capability:** CSV export on all relevant dashboards
- **Mobile Support:** Responsive design on all dashboards

### Functional Metrics

- **Data Accuracy:** 100% match with Firefly III web interface
- **Date Range Support:** All dashboards support custom date ranges
- **Filter Options:** All relevant filters implemented
- **Chart Variety:** 10+ chart types utilized across dashboards

---

## Future Enhancements (Beyond Roadmap)

1. **Multi-Currency Support:**
   - Currency conversion for unified reporting
   - Exchange rate tracking
   - Multi-currency net worth calculation

2. **Goal Setting UI:**
   - Interactive goal creation
   - Goal templates (emergency fund, retirement, vacation)
   - Goal progress notifications

3. **Reporting:**
   - PDF report generation
   - Email scheduled reports
   - Custom report builder

4. **Collaboration:**
   - Shared dashboards (for household finance)
   - Comments/notes on transactions
   - Approval workflows

5. **Mobile App:**
   - Native mobile interface
   - Push notifications
   - Quick transaction entry

6. **Machine Learning:**
   - Spending category prediction
   - Budget recommendation engine
   - Fraud detection
   - Expense forecasting

7. **Integrations:**
   - Direct bank API integration (Open Banking)
   - Investment portfolio tracking
   - Cryptocurrency tracking
   - Venmo/PayPal integration

8. **Gamification:**
   - Achievement badges
   - Savings challenges
   - Leaderboards (if multi-user)

---

## References

- **Firefly III API Docs:** https://docs.firefly-iii.org/
- **Streamlit Docs:** https://docs.streamlit.io/
- **Plotly Python Docs:** https://plotly.com/python/
- **Gridstack.js Docs:** https://gridstackjs.com/
- **Pandas Docs:** https://pandas.pydata.org/docs/

---

## Changelog

| Version | Date       | Author | Changes                          |
|---------|------------|--------|----------------------------------|
| 1.0     | 2025-10-18 | Claude | Initial roadmap creation         |

---

## Contributors

- **Project Owner:** [Your Name]
- **Development:** Claude Code (AI Assistant)

---

**End of Document**
