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
- `/pythondashboard/pages/5_🏷️_Categories.py` - Line ~700

---