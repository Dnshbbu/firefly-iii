# Dashboard Development Lessons Learned

This document captures important lessons, gotchas, and best practices discovered during dashboard development.

---

## Date & Time Calculations

### Monthly Average Calculation: Calendar Months vs Time Duration

**Issue:** When calculating monthly averages for recurring transactions (like rent), using time-based duration calculations produces incorrect results.

**Example Problem:**
- Date range: May 1, 2025 to September 30, 2025
- Rent: €1,750/month (paid 5 times)
- Total: €8,750
- **Expected average:** €1,750/month
- **Incorrect result:** €1,761.74/month

**Root Cause:**

❌ **INCORRECT: Using `relativedelta` for duration**
```python
from dateutil.relativedelta import relativedelta
months_diff = relativedelta(end_date, start_date)
total_months = months_diff.years * 12 + months_diff.months + (months_diff.days / 30.0)
# Result: 4 months + 29 days = 4.97 months
# Average: 8750 ÷ 4.97 = €1,761.74 ❌
```

This calculates the **time difference** between dates (4 months and 29 days), not the number of calendar months spanned.

✅ **CORRECT: Count calendar months spanned (inclusive)**
```python
# Count how many calendar months are touched by the date range
total_months = (end_date.year - start_date.year) * 12 + (end_date.month - start_date.month) + 1
# Result: (2025-2025)*12 + (9-5) + 1 = 5 months
# Average: 8750 ÷ 5 = €1,750.00 ✅
```

This counts the **calendar months spanned**: May, June, July, August, September = 5 months.

**When to Use Each Method:**

| Use Case | Method | Example |
|----------|--------|---------|
| Monthly averages for recurring transactions | Calendar months (inclusive) | Rent, subscriptions, salary |
| Age/duration calculations | Time duration (`relativedelta`) | "2 months and 15 days old" |
| Precise time intervals | Time duration | Scientific calculations, precise timing |
| Budget periods, reporting | Calendar months | Monthly reports, budget analysis |

**Rule of Thumb:**
- If you're dividing by months for **averages/rates**, use **calendar month counting**
- If you need **precise duration**, use **`relativedelta`** or similar

**Code Pattern to Remember:**
```python
# For monthly averages in financial analysis
total_months = (end_date.year - start_date.year) * 12 + (end_date.month - start_date.month) + 1
monthly_average = total_amount / max(total_months, 1)  # Avoid division by zero
```

**Related Files:**
- `/pythondashboard/pages/5_🏷️_Categories.py` - Line ~700 (monthly average in category table)
- `/pythondashboard/pages/16_🚀_Savings_Forecast.py` - Line ~159 (`months_between` function for monthly contributions)

**Additional Examples:**

**Savings Contributions:**
If you're contributing €100/month to a savings goal from May 1 to September 30:
- ❌ Old calculation: 4 months × €100 = €400
- ✅ Fixed calculation: 5 months × €100 = €500

**Budget Averages (Budget_Timeline.py - CORRECT):**
Budget_Timeline.py doesn't have this issue because it builds a dataframe with one row per calendar month, then uses `len(monthly_df)` to count months. This approach is naturally correct as long as the dataframe is built properly.

---

## Streamlit DataFrames & Tables

### Numeric Column Sorting: String Formatting vs NumberColumn

**Issue:** When displaying numeric columns in Streamlit dataframes, converting numbers to formatted strings causes incorrect sorting behavior (alphabetical instead of numerical).

**Example Problem:**
- Amount column with values: 9.00, 80.00, 750.00
- When sorted descending, order shows: 9.00, 80.00, 750.00 ❌
- **Expected order:** 750.00, 80.00, 9.00 ✅

**Root Cause:**

❌ **INCORRECT: Pre-formatting numbers as strings**
```python
# Converting to formatted string before display
df_display['amount'] = df_display['amount'].apply(lambda x: f"€{x:,.2f}")

st.dataframe(
    df_display,
    column_config={
        'amount': 'Amount'  # This is now a string column!
    }
)
```

This converts numeric values to strings like "€9.00", "€80.00", "€750.00", which sort alphabetically:
- "€750.00" comes before "€80.00" (because '7' < '8')
- "€80.00" comes before "€9.00" (because '8' < '9')
- Result: Descending sort gives 9, 80, 750 ❌

✅ **CORRECT: Use Streamlit's NumberColumn for formatting**
```python
# Keep amount as numeric, use column_config for formatting
st.dataframe(
    df_display,  # amount column stays as float/int
    column_config={
        'amount': st.column_config.NumberColumn('Amount', format="€%.2f")
    }
)
```

This preserves the numeric data type while applying visual formatting:
- Data remains as numbers: 9.00, 80.00, 750.00
- Sorting works numerically: 750.00 > 80.00 > 9.00 ✅
- Display shows formatted: €9.00, €80.00, €750.00

**Benefits of NumberColumn:**

1. **Correct sorting** - Numeric sorting instead of alphabetical
2. **Alignment** - Right-aligned by default (better for numbers)
3. **Flexibility** - Easy to change format without modifying dataframe
4. **Performance** - No need to copy dataframe just for formatting

**Format String Options:**

```python
# Currency with 2 decimals and comma separators
format="€%.2f"  # €1,234.56

# Plain number with commas (Streamlit adds them automatically)
format="%.2f"   # 1,234.56

# No decimals
format="%.0f"   # 1,235

# Percentage
format="%.1f%%"  # 45.5%
```

**Code Pattern to Remember:**

```python
# ❌ DON'T format before display
df_display['amount'] = df_display['amount'].apply(lambda x: f"€{x:,.2f}")

# ✅ DO use NumberColumn config
st.dataframe(
    df,  # Keep numeric columns as-is
    column_config={
        'amount': st.column_config.NumberColumn('Amount', format="€%.2f"),
        'price': st.column_config.NumberColumn('Price', format="%.2f"),
        'count': st.column_config.NumberColumn('Count', format="%.0f")
    }
)
```

**Related Files:**
- `/pythondashboard/pages/3_📈_Cash_Flow.py` - Fixed in all tables:
  - Line ~420-442: Category transaction details table
  - Line ~497-508: Category spending table
  - Line ~530-541: Income sources table
  - Line ~590-616: Main transaction details table
  - Line ~640-667: Transfers table

**Similar Issues in Other Streamlit Components:**

This pattern applies to all Streamlit data display components:
- `st.dataframe()` - Interactive table with sorting
- `st.data_editor()` - Editable table
- `st.table()` - Static table (no sorting, but still better UX)

**Date Column Similar Issue:**

Note: Dates should be kept as datetime objects (not strings) for proper sorting, but can be formatted for display using strftime only when displaying, not when storing in the dataframe for sorting purposes. However, Streamlit's dataframe automatically handles datetime sorting even when displayed as strings via strftime.

---

## Streamlit API Deprecations

### Container Width & Chart Configuration: Fixing Deprecation Warnings

**Issue:** Streamlit introduced deprecation warnings for outdated parameter usage in dataframes and plotly charts, warning that these will be removed after December 31, 2025.

**Two Types of Warnings Encountered:**

1. **Dataframe `use_container_width` deprecation:**
   ```
   Please replace `use_container_width` with `width`.
   `use_container_width` will be removed after 2025-12-31.
   For `use_container_width=True`, use `width='stretch'`.
   For `use_container_width=False`, use `width='content'`.
   ```

2. **Plotly chart keyword arguments deprecation:**
   ```
   The keyword arguments have been deprecated and will be removed in a future release.
   Use `config` instead to specify Plotly configuration options.
   ```

**Root Causes:**

**Dataframes:**
Streamlit is migrating from the boolean `use_container_width` parameter to a more flexible `width` parameter that accepts multiple values.

**Plotly Charts:**
Streamlit now requires that all configuration options (including responsive behavior) be passed within the `config` dictionary rather than as separate keyword arguments.

---

### Solution 1: Dataframes - Use `width='stretch'`

❌ **INCORRECT: Using deprecated `use_container_width`**
```python
st.dataframe(
    df,
    use_container_width=True,  # ❌ Deprecated!
    hide_index=True,
    height=400
)
```

✅ **CORRECT: Use new `width` parameter**
```python
st.dataframe(
    df,
    width='stretch',  # ✅ New API
    hide_index=True,
    height=400
)
```

**Width Parameter Options:**
- `width='stretch'` - Spans full container width (replaces `use_container_width=True`)
- `width='content'` - Fits to content width (replaces `use_container_width=False`)
- You can also specify numeric pixel values: `width=800`

---

### Solution 2: Plotly Charts - Remove `use_container_width`, Use `config` Only

❌ **INCORRECT: Using `use_container_width` with plotly charts**
```python
st.plotly_chart(
    fig,
    config={'displayModeBar': False},
    use_container_width=True  # ❌ Deprecated!
)
```

✅ **CORRECT: Use only `config` with `responsive: True`**
```python
st.plotly_chart(
    fig,
    config={'displayModeBar': False, 'responsive': True}  # ✅ New API
)
```

**Key Points:**
1. **Remove `use_container_width` entirely** from `st.plotly_chart()` calls
2. **Add `'responsive': True`** to the config dictionary to enable responsive behavior
3. The `responsive` option makes the chart adapt to container size automatically

**Common Config Options:**
```python
config={
    'displayModeBar': False,    # Hide plotly toolbar
    'responsive': True,          # Enable responsive resizing
    'staticPlot': False,         # Allow interactions
    'displaylogo': False         # Hide plotly logo
}
```

---

### Complete Before/After Examples

**Example 1: Currency Distribution Chart**

❌ **BEFORE (Deprecated):**
```python
currency_chart = create_currency_distribution_chart(df)
st.plotly_chart(currency_chart, config={'displayModeBar': False}, use_container_width=True)
```

✅ **AFTER (Fixed):**
```python
currency_chart = create_currency_distribution_chart(df)
st.plotly_chart(currency_chart, config={'displayModeBar': False, 'responsive': True})
```

**Example 2: Account Data Table**

❌ **BEFORE (Deprecated):**
```python
st.dataframe(
    health_data,
    use_container_width=True,
    hide_index=True,
    height=210
)
```

✅ **AFTER (Fixed):**
```python
st.dataframe(
    health_data,
    width='stretch',
    hide_index=True,
    height=210
)
```

**Example 3: Detailed Account Table with Column Config**

❌ **BEFORE (Deprecated):**
```python
st.dataframe(
    df_display_formatted,
    use_container_width=True,
    hide_index=True,
    height=400,
    column_config={
        'current_balance': st.column_config.NumberColumn('Balance', format="%.2f")
    }
)
```

✅ **AFTER (Fixed):**
```python
st.dataframe(
    df_display_formatted,
    width='stretch',
    hide_index=True,
    height=400,
    column_config={
        'current_balance': st.column_config.NumberColumn('Balance', format="%.2f")
    }
)
```

---

### Code Pattern to Remember

**For all st.dataframe() calls:**
```python
# Search for: use_container_width=True
# Replace with: width='stretch'

st.dataframe(df, width='stretch', hide_index=True)
```

**For all st.plotly_chart() calls:**
```python
# Remove: use_container_width=True
# Ensure config has: 'responsive': True

st.plotly_chart(fig, config={'displayModeBar': False, 'responsive': True})
```

---

### Related Files Fixed

**Net Worth Dashboard:**
- `/pythondashboard/pages/1_📊_Net_Worth.py`
  - Line 514: Currency distribution chart
  - Line 564: Account health dataframe
  - Line 587, 590, 593: Per-currency breakdown charts
  - Line 635: Detailed account table

**Budget Timeline Dashboard (Reference Example):**
- `/pythondashboard/pages/14_📅_Budget_Timeline.py`
  - Line 1057: Timeline chart
  - Line 1068, 1072: Analysis charts
  - Line 1126: Budget utilization gauges
  - Line 1156: Individual budget charts
  - Line 1182: Monthly breakdown table

---

### Quick Checklist for Fixing Deprecation Warnings

When you encounter these warnings in other dashboard pages:

- [ ] **Search for `use_container_width=True` in dataframes** → Replace with `width='stretch'`
- [ ] **Search for `use_container_width=True` in plotly charts** → Remove it entirely
- [ ] **Verify all `st.plotly_chart()` calls have `'responsive': True`** in their config dictionary
- [ ] **Test that charts and tables still span full width** after changes
- [ ] **Verify that sorting and interactivity still work** in dataframes

---

### Migration Timeline

- **Current:** Both old and new APIs work (with deprecation warnings)
- **After December 31, 2025:** Old `use_container_width` parameter will be removed
- **Action Required:** Update all dashboards before the deadline to avoid breaking changes

---