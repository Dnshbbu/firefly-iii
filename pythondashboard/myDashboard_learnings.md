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