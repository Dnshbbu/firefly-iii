# Cash Flow Dashboard Implementation

**Date:** 2025-10-18
**Status:** ✅ Complete
**Version:** 1.0

---

## Overview

The Cash Flow Dashboard has been successfully implemented as part of Phase 1 of the [Dashboard Roadmap](DASHBOARD_ROADMAP.md). This dashboard provides comprehensive visualization and analysis of income vs. expenses over customizable time periods.

---

## What Was Implemented

### 1. **Refactored Shared Utilities** (`utils/`)

Created reusable utility modules that can be shared across all dashboards:

#### `utils/api_client.py`
Enhanced API client with comprehensive methods:
- `test_connection()` - Verify API connectivity
- `get_accounts()` - Fetch accounts with type filtering
- `get_transactions()` - Fetch transactions with pagination support
- `get_budgets()` - Fetch budget data
- `get_budget_limits()` - Fetch budget limits by date range
- `get_categories()` - Fetch categories
- `get_bills()` - Fetch bills
- `get_piggy_banks()` - Fetch piggy banks
- `parse_account_data()` - Parse account data to DataFrame
- `parse_transaction_data()` - Parse transaction data to DataFrame

**Key Features:**
- Automatic pagination for large datasets
- Proper error handling with try-catch blocks
- Type hints for better code documentation
- Date parsing and DataFrame conversion

#### `utils/charts.py`
Reusable chart creation functions using Plotly:
- `create_line_chart()` - Line charts with markers
- `create_bar_chart()` - Vertical/horizontal bar charts
- `create_combo_chart()` - Combined bar charts
- `create_waterfall_chart()` - Waterfall charts for flow visualization
- `create_pie_chart()` - Pie/donut charts
- `create_stacked_area_chart()` - Stacked area charts
- `create_gauge_chart()` - Gauge/indicator charts
- `create_net_flow_chart()` - Specialized cash flow chart (income + expense bars + net line)

**Design Principles:**
- Consistent color scheme (green for positive, red for negative, blue for neutral)
- Dark mode compatible
- Configurable heights and styling
- Hover interactions enabled

#### `utils/calculations.py`
Financial calculation utilities:
- `calculate_net_worth()` - Calculate net worth by currency
- `calculate_cash_flow()` - Aggregate transactions by period (D/W/M/Q/Y)
- `calculate_category_spending()` - Aggregate expenses by category
- `calculate_income_sources()` - Aggregate income by source
- `calculate_savings_rate()` - Calculate savings as % of income
- `calculate_period_comparison()` - Compare two time periods
- `get_date_ranges()` - Generate common date ranges (month, quarter, year)

**Key Features:**
- Pandas-based aggregations for performance
- Support for multiple aggregation periods
- Handles empty data gracefully
- Period-over-period comparison logic

---

### 2. **Cash Flow Dashboard** (`pages/3_📈_Cash_Flow.py`)

A comprehensive dashboard for analyzing cash flow patterns.

#### Key Features

**A. Summary Metrics (Top Section)**
- **Total Income:** Sum of all deposits in date range
- **Total Expenses:** Sum of all withdrawals in date range
- **Net Cash Flow:** Difference between income and expenses
- **Savings Rate:** Percentage of income saved (net / income × 100)
- **Average Monthly Metrics:** Normalized monthly averages

**B. Cash Flow Over Time Chart**
- Combined visualization showing:
  - Income bars (green)
  - Expense bars (red, displayed as negative)
  - Net flow line (blue)
- Supports multiple aggregation periods:
  - Daily
  - Weekly
  - Monthly (default)
  - Quarterly

**C. Category Analysis (Two-Column Layout)**
- **Left Column: Top Expense Categories**
  - Pie chart showing top 10 categories
  - Expandable table with all categories
  - Shows total amount and transaction count per category

- **Right Column: Income Sources**
  - Pie chart showing income breakdown by source
  - Expandable table with all income sources
  - Shows total amount and transaction count per source

**D. Cash Flow Waterfall Chart**
- Visual representation of monthly cash flow progression
- Shows cumulative effect of each month's net flow
- Available for monthly aggregation only

**E. Transaction Details Table**
- Filterable list of all transactions
- Filters available:
  - Transaction type (deposit/withdrawal)
  - Category
  - Minimum amount
- Sortable columns
- Shows: date, description, type, category, amount, currency

**F. Data Export**
- CSV export of filtered transaction data
- Filename includes date range for easy identification

#### User Interface Features

**Sidebar Controls:**
- **API Configuration:** URL and token input (reused from Net Worth)
- **Date Range Presets:**
  - Last 30 Days
  - Last 3 Months
  - Last 6 Months
  - Last Year
  - Year to Date
  - Custom (date picker)
- **Aggregation Period:** Daily/Weekly/Monthly/Quarterly

**Main Content:**
- Refresh button with cache clearing
- Last updated timestamp
- Responsive layout with Streamlit columns
- Expandable sections for detailed data
- Loading spinners during API calls

#### Technical Features

**Performance Optimizations:**
- `@st.cache_data(ttl=300)` - 5-minute cache for API calls
- Pagination support for large transaction datasets
- Efficient DataFrame operations using Pandas

**Error Handling:**
- Connection test before data fetch
- Graceful handling of empty datasets
- User-friendly error messages
- Exception display for debugging

**Dark Mode Styling:**
- Consistent with existing dashboards
- Compact CSS for better space utilization
- Proper contrast ratios for readability

---

## File Structure

```
pythondashboard/
├── Home.py                          # Updated with Cash Flow description
├── pages/
│   ├── 1_📊_Net_Worth.py           # Existing (unchanged)
│   ├── 2_📄_CSV_Preprocessor.py    # Existing (unchanged)
│   └── 3_📈_Cash_Flow.py           # NEW: Cash Flow Dashboard
├── utils/                           # NEW: Shared utilities
│   ├── __init__.py                 # Module initialization
│   ├── api_client.py               # Firefly III API client
│   ├── charts.py                   # Reusable chart functions
│   └── calculations.py             # Financial calculations
├── Docs/
│   ├── DASHBOARD_ROADMAP.md        # Created earlier
│   └── CASH_FLOW_IMPLEMENTATION.md # This file
├── requirements.txt                # No changes needed (all deps present)
└── README.md                        # Existing
```

---

## How to Use

### 1. Start the Application

```bash
cd pythondashboard
streamlit run Home.py
```

The app will open in your browser at `http://localhost:8501`

### 2. Configure API Connection

1. Navigate to the **Cash Flow Dashboard** from the sidebar
2. Enter your Firefly III URL (e.g., `http://192.168.0.242`)
3. Enter your Personal Access Token (from Profile → OAuth in Firefly III)
4. Click **Connect**

### 3. Select Date Range

Choose a preset range or use custom dates:
- **Preset:** Quick selection (Last 30 Days, Last 3 Months, etc.)
- **Custom:** Pick specific start and end dates

### 4. Choose Aggregation Period

Select how to group your data:
- **Daily:** Day-by-day breakdown (useful for short periods)
- **Weekly:** Week-by-week summary
- **Monthly:** Month-by-month analysis (recommended)
- **Quarterly:** Quarter-by-quarter view

### 5. Analyze Your Cash Flow

- **Summary Metrics:** See totals and averages at a glance
- **Charts:** Visualize trends over time
- **Categories:** Understand where your money goes
- **Income Sources:** See where your money comes from
- **Waterfall:** Track cumulative cash flow progression
- **Transactions:** Drill down into individual transactions

### 6. Export Data

Click the **Download Transaction Data (CSV)** button to export filtered transactions for further analysis in Excel or other tools.

---

## API Endpoints Used

The Cash Flow Dashboard uses the following Firefly III API endpoints:

- `GET /api/v1/about` - Connection test
- `GET /api/v1/transactions` - Fetch transactions
  - Query params: `start`, `end`, `limit`, `page`
  - Supports pagination for large datasets

---

## Data Flow

```
User Input (Date Range, Aggregation)
         ↓
API Client (fetch_transactions)
         ↓
Transaction Data (JSON)
         ↓
Parse to DataFrame (parse_transaction_data)
         ↓
Filter by Type (deposits, withdrawals)
         ↓
Calculate Metrics (calculate_cash_flow, calculate_category_spending, etc.)
         ↓
Create Visualizations (create_net_flow_chart, create_pie_chart, etc.)
         ↓
Display in Streamlit
```

---

## Key Calculations

### Net Cash Flow
```python
net_flow = total_income - total_expenses
```

### Savings Rate
```python
savings_rate = (net_flow / total_income) × 100
```

### Average Monthly
```python
avg_monthly = total_amount / (days_in_range / 30)
```

### Cash Flow Aggregation
Uses Pandas `resample()` method:
```python
df.set_index('date').resample(period)['amount'].sum()
```

---

## Future Enhancements

Potential improvements for the Cash Flow Dashboard:

1. **Period-over-Period Comparison**
   - Side-by-side comparison of current vs. previous period
   - Variance analysis with percentage changes
   - Color-coded indicators for increases/decreases

2. **Trend Analysis**
   - Moving averages
   - Linear regression trend lines
   - Forecasting based on historical data

3. **Budget Integration**
   - Overlay budget limits on expense charts
   - Budget vs. actual comparison
   - Budget burn rate indicators

4. **Sub-Category Breakdown**
   - Drill-down into categories to see sub-categories
   - Hierarchical visualization (sunburst or treemap)

5. **Merchant Analysis**
   - Top merchants by spending
   - Merchant frequency analysis
   - Spending patterns by merchant

6. **Custom Filters**
   - Save filter presets
   - Filter by account, tags, notes
   - Advanced search with multiple conditions

7. **Alerts & Insights**
   - Anomaly detection (unusual spending)
   - Pattern recognition (e.g., "You spend more on weekends")
   - Automated recommendations

8. **Export Options**
   - PDF report generation
   - Excel export with formatting
   - Scheduled email reports

---

## Testing Checklist

Before using in production, test the following scenarios:

- [ ] Connection to Firefly III API succeeds
- [ ] Transactions load correctly for various date ranges
- [ ] Charts display properly with data
- [ ] Empty data scenarios show appropriate messages
- [ ] Filters work correctly
- [ ] CSV export includes correct data
- [ ] Pagination works for large transaction datasets (>500 transactions)
- [ ] Cache refreshes when clicking "Refresh Data"
- [ ] Different aggregation periods (D/W/M/Q) calculate correctly
- [ ] Multiple currencies are handled properly (if applicable)
- [ ] Dark mode styling appears correctly
- [ ] Responsive layout works on different screen sizes

---

## Known Limitations

1. **Currency:** Currently assumes single currency (Euro). Multi-currency support would require:
   - Currency conversion logic
   - Per-currency aggregation
   - Exchange rate API integration

2. **Transfers:** Transfer transactions are excluded from cash flow analysis to avoid double-counting. This is by design but may need adjustment for specific use cases.

3. **Performance:** For very large transaction datasets (>10,000 transactions), initial load may take several seconds. Consider:
   - Increasing cache TTL
   - Implementing lazy loading
   - Adding progress indicators

4. **Waterfall Chart:** Only available for monthly aggregation. Could be extended to support other periods with additional logic.

5. **Category Hierarchy:** Currently treats all categories as flat. Doesn't support parent/child category relationships.

---

## Dependencies

All required dependencies are already in `requirements.txt`:

```
streamlit==1.31.0
pandas==2.2.0
requests==2.31.0
plotly==5.18.0
```

No additional installations needed.

---

## Migration Notes

### For Existing Net Worth Dashboard Users

The API client has been refactored into `utils/api_client.py`. If you want to update the Net Worth dashboard to use the shared client:

1. Add import: `from utils.api_client import FireflyAPIClient`
2. Remove the `FireflyAPIClient` class definition from `pages/1_📊_Net_Worth.py`
3. Test that everything still works

This is **optional** - the Net Worth dashboard will continue to work as-is with its embedded client class.

---

## Contributing

If you add new dashboards, please:

1. Use the shared utilities in `utils/`
2. Follow the existing code style and structure
3. Include comprehensive error handling
4. Add caching for API calls
5. Use consistent dark mode styling
6. Update `Home.py` with the new dashboard description
7. Document your implementation in `Docs/`

---

## Support

For issues or questions:
- Check the [Dashboard Roadmap](DASHBOARD_ROADMAP.md) for planned features
- Review the Firefly III API documentation: https://docs.firefly-iii.org/
- Check Streamlit documentation: https://docs.streamlit.io/

---

## Changelog

| Version | Date       | Changes                                          |
|---------|------------|--------------------------------------------------|
| 1.0     | 2025-10-18 | Initial implementation of Cash Flow Dashboard    |

---

**End of Document**
