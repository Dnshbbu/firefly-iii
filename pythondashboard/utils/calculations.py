"""Financial calculation utilities for Firefly III Dashboard

Common financial calculations and data aggregations.
"""

import pandas as pd
from typing import Dict, List, Tuple
from datetime import datetime, timedelta


def calculate_net_worth(df: pd.DataFrame) -> Dict[str, float]:
    """
    Calculate net worth by currency.

    Args:
        df: DataFrame with account data (must have 'include_net_worth', 'currency_code', 'current_balance' columns)

    Returns:
        Dictionary mapping currency code to net worth amount
    """
    # Filter accounts that should be included in net worth
    net_worth_accounts = df[df['include_net_worth'] == True]

    # Group by currency and sum balances
    net_worth_by_currency = net_worth_accounts.groupby('currency_code')['current_balance'].sum().to_dict()

    return net_worth_by_currency


def calculate_cash_flow(
    transactions_df: pd.DataFrame,
    period: str = 'ME'
) -> pd.DataFrame:
    """
    Calculate cash flow (income vs expenses) aggregated by period.

    Args:
        transactions_df: DataFrame with transaction data (must have 'date', 'type', 'amount' columns)
        period: Pandas period string ('D' = daily, 'W' = weekly, 'ME' = monthly, 'QE' = quarterly, 'YE' = yearly)

    Returns:
        DataFrame with columns: period, income, expenses, net_flow
    """
    if transactions_df.empty:
        return pd.DataFrame(columns=['period', 'income', 'expenses', 'net_flow'])

    df = transactions_df.copy()

    # Ensure date is datetime
    # Check if date column is datetime and has timezone info
    if pd.api.types.is_datetime64_any_dtype(df['date']):
        if hasattr(df['date'].dt, 'tz') and df['date'].dt.tz is not None:
            # Already datetime with timezone - just remove timezone
            df['date'] = df['date'].dt.tz_localize(None)
    else:
        # Convert date column to datetime if it's not already
        # Use utc=True to handle timezone-aware datetime objects
        df['date'] = pd.to_datetime(df['date'], utc=True)
        # Remove timezone to make resampling work
        df['date'] = df['date'].dt.tz_localize(None)

    # Set date as index for resampling
    df = df.set_index('date')

    # Separate income and expenses
    income_df = df[df['type'] == 'deposit'].copy()
    expense_df = df[df['type'] == 'withdrawal'].copy()

    # Resample and sum by period
    income_by_period = income_df.resample(period)['amount'].sum()
    expenses_by_period = expense_df.resample(period)['amount'].sum()

    # Create result dataframe
    result = pd.DataFrame({
        'income': income_by_period,
        'expenses': -expenses_by_period,  # Make expenses negative for display
        'net_flow': income_by_period - expenses_by_period
    })

    result = result.reset_index()
    result.columns = ['period', 'income', 'expenses', 'net_flow']

    # Fill NaN with 0
    result = result.fillna(0)

    return result


def calculate_category_spending(
    transactions_df: pd.DataFrame,
    start_date: str = None,
    end_date: str = None
) -> pd.DataFrame:
    """
    Calculate spending by category.

    Args:
        transactions_df: DataFrame with transaction data
        start_date: Optional start date filter (YYYY-MM-DD)
        end_date: Optional end date filter (YYYY-MM-DD)

    Returns:
        DataFrame with columns: category_name, total_amount, transaction_count
    """
    if transactions_df.empty:
        return pd.DataFrame(columns=['category_name', 'total_amount', 'transaction_count'])

    df = transactions_df.copy()

    # Ensure date is datetime and handle timezone
    if pd.api.types.is_datetime64_any_dtype(df['date']):
        if hasattr(df['date'].dt, 'tz') and df['date'].dt.tz is not None:
            # Already datetime with timezone - just remove timezone
            df['date'] = df['date'].dt.tz_localize(None)
    else:
        # Convert date column to datetime if it's not already
        # Use utc=True to handle timezone-aware datetime objects
        df['date'] = pd.to_datetime(df['date'], utc=True)
        # Remove timezone to make comparisons work
        df['date'] = df['date'].dt.tz_localize(None)

    # Filter by date range if provided
    if start_date:
        start_dt = pd.to_datetime(start_date)
        df = df[df['date'] >= start_dt]
    if end_date:
        end_dt = pd.to_datetime(end_date)
        df = df[df['date'] <= end_dt]

    # Filter for expenses only (withdrawals)
    expense_df = df[df['type'] == 'withdrawal'].copy()

    # Replace None and empty category names with 'Uncategorized'
    expense_df['category_name'] = expense_df['category_name'].fillna('Uncategorized')
    expense_df['category_name'] = expense_df['category_name'].replace('', 'Uncategorized')

    # Group by category
    category_summary = expense_df.groupby('category_name').agg({
        'amount': ['sum', 'count']
    }).reset_index()

    category_summary.columns = ['category_name', 'total_amount', 'transaction_count']

    # Sort by total amount descending
    category_summary = category_summary.sort_values('total_amount', ascending=False)

    return category_summary


def calculate_income_sources(
    transactions_df: pd.DataFrame,
    start_date: str = None,
    end_date: str = None
) -> pd.DataFrame:
    """
    Calculate income by source.

    Args:
        transactions_df: DataFrame with transaction data
        start_date: Optional start date filter (YYYY-MM-DD)
        end_date: Optional end date filter (YYYY-MM-DD)

    Returns:
        DataFrame with columns: source_name, total_amount, transaction_count
    """
    if transactions_df.empty:
        return pd.DataFrame(columns=['source_name', 'total_amount', 'transaction_count'])

    df = transactions_df.copy()

    # Ensure date is datetime and handle timezone
    if pd.api.types.is_datetime64_any_dtype(df['date']):
        if hasattr(df['date'].dt, 'tz') and df['date'].dt.tz is not None:
            # Already datetime with timezone - just remove timezone
            df['date'] = df['date'].dt.tz_localize(None)
    else:
        # Convert date column to datetime if it's not already
        # Use utc=True to handle timezone-aware datetime objects
        df['date'] = pd.to_datetime(df['date'], utc=True)
        # Remove timezone to make comparisons work
        df['date'] = df['date'].dt.tz_localize(None)

    # Filter by date range if provided
    if start_date:
        start_dt = pd.to_datetime(start_date)
        df = df[df['date'] >= start_dt]
    if end_date:
        end_dt = pd.to_datetime(end_date)
        df = df[df['date'] <= end_dt]

    # Filter for income only (deposits)
    income_df = df[df['type'] == 'deposit'].copy()

    # Replace None and empty source names with 'Unknown'
    income_df['source_name'] = income_df['source_name'].fillna('Unknown')
    income_df['source_name'] = income_df['source_name'].replace('', 'Unknown')

    # Group by source
    source_summary = income_df.groupby('source_name').agg({
        'amount': ['sum', 'count']
    }).reset_index()

    source_summary.columns = ['source_name', 'total_amount', 'transaction_count']

    # Sort by total amount descending
    source_summary = source_summary.sort_values('total_amount', ascending=False)

    return source_summary


def calculate_savings_rate(income: float, expenses: float) -> float:
    """
    Calculate savings rate as percentage.

    Args:
        income: Total income
        expenses: Total expenses

    Returns:
        Savings rate as percentage (0-100)
    """
    if income <= 0:
        return 0.0

    savings = income - expenses
    return (savings / income) * 100


def calculate_period_comparison(
    transactions_df: pd.DataFrame,
    current_start: str,
    current_end: str,
    previous_start: str,
    previous_end: str
) -> Dict[str, Dict[str, float]]:
    """
    Compare financial metrics between two periods.

    Args:
        transactions_df: DataFrame with transaction data
        current_start: Current period start date (YYYY-MM-DD)
        current_end: Current period end date (YYYY-MM-DD)
        previous_start: Previous period start date (YYYY-MM-DD)
        previous_end: Previous period end date (YYYY-MM-DD)

    Returns:
        Dictionary with current, previous, and change metrics
    """
    if transactions_df.empty:
        return {
            'current': {'income': 0, 'expenses': 0, 'net': 0},
            'previous': {'income': 0, 'expenses': 0, 'net': 0},
            'change': {'income': 0, 'expenses': 0, 'net': 0},
            'change_pct': {'income': 0, 'expenses': 0, 'net': 0}
        }

    df = transactions_df.copy()
    # Check if date column is datetime and has timezone info
    if pd.api.types.is_datetime64_any_dtype(df['date']):
        if hasattr(df['date'].dt, 'tz') and df['date'].dt.tz is not None:
            # Already datetime with timezone - just remove timezone
            df['date'] = df['date'].dt.tz_localize(None)
    else:
        # Convert date column to datetime if it's not already
        # Use utc=True to handle timezone-aware datetime objects
        df['date'] = pd.to_datetime(df['date'], utc=True)
        # Remove timezone to make comparisons work
        df['date'] = df['date'].dt.tz_localize(None)

    # Prepare date filters (no timezone needed since we removed it from df['date'])
    current_start_dt = pd.to_datetime(current_start)
    current_end_dt = pd.to_datetime(current_end)
    previous_start_dt = pd.to_datetime(previous_start)
    previous_end_dt = pd.to_datetime(previous_end)

    # Current period
    current_df = df[(df['date'] >= current_start_dt) &
                    (df['date'] <= current_end_dt)]

    current_income = current_df[current_df['type'] == 'deposit']['amount'].sum()
    current_expenses = current_df[current_df['type'] == 'withdrawal']['amount'].sum()
    current_net = current_income - current_expenses

    # Previous period
    previous_df = df[(df['date'] >= previous_start_dt) &
                     (df['date'] <= previous_end_dt)]

    previous_income = previous_df[previous_df['type'] == 'deposit']['amount'].sum()
    previous_expenses = previous_df[previous_df['type'] == 'withdrawal']['amount'].sum()
    previous_net = previous_income - previous_expenses

    # Calculate changes
    income_change = current_income - previous_income
    expenses_change = current_expenses - previous_expenses
    net_change = current_net - previous_net

    # Calculate percentage changes
    income_change_pct = (income_change / previous_income * 100) if previous_income > 0 else 0
    expenses_change_pct = (expenses_change / previous_expenses * 100) if previous_expenses > 0 else 0
    net_change_pct = (net_change / previous_net * 100) if previous_net != 0 else 0

    return {
        'current': {
            'income': current_income,
            'expenses': current_expenses,
            'net': current_net
        },
        'previous': {
            'income': previous_income,
            'expenses': previous_expenses,
            'net': previous_net
        },
        'change': {
            'income': income_change,
            'expenses': expenses_change,
            'net': net_change
        },
        'change_pct': {
            'income': income_change_pct,
            'expenses': expenses_change_pct,
            'net': net_change_pct
        }
    }


def get_date_ranges(period_type: str = 'month') -> Dict[str, Tuple[str, str]]:
    """
    Get common date ranges for analysis.

    Args:
        period_type: Type of period ('month', 'quarter', 'year')

    Returns:
        Dictionary with date ranges (start, end) for current and previous periods
    """
    today = datetime.now()

    if period_type == 'month':
        # Current month
        current_start = today.replace(day=1)
        if today.month == 12:
            current_end = today.replace(day=31)
        else:
            current_end = (today.replace(day=1, month=today.month + 1) - timedelta(days=1))

        # Previous month
        if today.month == 1:
            previous_start = today.replace(year=today.year - 1, month=12, day=1)
            previous_end = today.replace(year=today.year - 1, month=12, day=31)
        else:
            previous_start = today.replace(month=today.month - 1, day=1)
            previous_end = (today.replace(day=1) - timedelta(days=1))

    elif period_type == 'quarter':
        # Current quarter
        current_quarter = (today.month - 1) // 3 + 1
        current_start = today.replace(month=(current_quarter - 1) * 3 + 1, day=1)
        current_end = today

        # Previous quarter
        if current_quarter == 1:
            previous_quarter = 4
            previous_year = today.year - 1
        else:
            previous_quarter = current_quarter - 1
            previous_year = today.year

        previous_start = today.replace(year=previous_year, month=(previous_quarter - 1) * 3 + 1, day=1)
        previous_end_month = previous_quarter * 3
        previous_end = (today.replace(year=previous_year, month=previous_end_month + 1, day=1) - timedelta(days=1))

    elif period_type == 'year':
        # Current year
        current_start = today.replace(month=1, day=1)
        current_end = today

        # Previous year
        previous_start = today.replace(year=today.year - 1, month=1, day=1)
        previous_end = today.replace(year=today.year - 1, month=12, day=31)

    else:
        raise ValueError(f"Unknown period_type: {period_type}")

    return {
        'current': (current_start.strftime('%Y-%m-%d'), current_end.strftime('%Y-%m-%d')),
        'previous': (previous_start.strftime('%Y-%m-%d'), previous_end.strftime('%Y-%m-%d'))
    }


def calculate_budget_performance(
    budgets_data: List[Dict],
    budget_limits_data: Dict[str, List[Dict]],
    transactions_df: pd.DataFrame,
    start_date: str,
    end_date: str
) -> pd.DataFrame:
    """
    Calculate budget performance (budgeted vs. spent vs. remaining).

    Args:
        budgets_data: List of budget dictionaries from API
        budget_limits_data: Dictionary mapping budget_id to list of budget limits
        transactions_df: DataFrame with transaction data
        start_date: Period start date (YYYY-MM-DD)
        end_date: Period end date (YYYY-MM-DD)

    Returns:
        DataFrame with columns: budget_name, budget_id, budgeted, spent, remaining, utilization_pct, status
    """
    if not budgets_data:
        return pd.DataFrame(columns=['budget_name', 'budget_id', 'budgeted', 'spent', 'remaining', 'utilization_pct', 'status'])

    budget_performance = []

    for budget in budgets_data:
        budget_id = budget.get('id')
        budget_name = budget.get('attributes', {}).get('name', 'Unknown')

        # Get budget limit for this period
        limits = budget_limits_data.get(budget_id, [])
        budgeted_amount = 0.0

        for limit in limits:
            limit_attrs = limit.get('attributes', {})
            budgeted_amount += float(limit_attrs.get('amount', 0))

        # Calculate spent amount from transactions
        if not transactions_df.empty:
            budget_transactions = transactions_df[
                (transactions_df['budget_name'] == budget_name) &
                (transactions_df['type'] == 'withdrawal')
            ]
            spent_amount = budget_transactions['amount'].sum()
        else:
            spent_amount = 0.0

        # Calculate remaining and utilization
        remaining = budgeted_amount - spent_amount
        utilization_pct = (spent_amount / budgeted_amount * 100) if budgeted_amount > 0 else 0

        # Determine status
        if utilization_pct >= 100:
            status = 'Over Budget'
        elif utilization_pct >= 80:
            status = 'Warning'
        else:
            status = 'On Track'

        budget_performance.append({
            'budget_name': budget_name,
            'budget_id': budget_id,
            'budgeted': budgeted_amount,
            'spent': spent_amount,
            'remaining': remaining,
            'utilization_pct': utilization_pct,
            'status': status
        })

    df = pd.DataFrame(budget_performance)

    # Sort by utilization percentage descending
    df = df.sort_values('utilization_pct', ascending=False)

    return df


def calculate_budget_burn_rate(
    budgeted: float,
    spent: float,
    start_date: str,
    end_date: str,
    current_date: str = None
) -> Dict[str, float]:
    """
    Calculate budget burn rate and projections.

    Args:
        budgeted: Total budgeted amount
        spent: Amount spent so far
        start_date: Budget period start (YYYY-MM-DD)
        end_date: Budget period end (YYYY-MM-DD)
        current_date: Current date (YYYY-MM-DD), defaults to today

    Returns:
        Dictionary with burn_rate, days_elapsed, days_remaining, projected_spend, projected_over_under
    """
    start = pd.to_datetime(start_date)
    end = pd.to_datetime(end_date)
    today = pd.Timestamp.now()
    
    # Determine the effective "current" date for calculations
    if current_date:
        current = pd.to_datetime(current_date)
    elif end < today:
        # Period has already ended - use the end date
        current = end
    else:
        # Period is ongoing - use today but cap at end date
        current = min(today, end)

    # Calculate days
    total_days = (end - start).days + 1
    days_elapsed = min((current - start).days + 1, total_days)  # Can't exceed total days
    days_remaining = max(0, (end - current).days)

    # Prevent division by zero
    days_elapsed = max(1, days_elapsed)

    # Calculate burn rate (spend per day)
    burn_rate = spent / days_elapsed if days_elapsed > 0 else 0

    # For completed periods, no projection needed
    if end < today:
        projected_spend = spent  # Actual final amount
        projected_over_under = budgeted - spent  # Actual over/under
    else:
        # Project total spend at current burn rate for ongoing periods
        projected_spend = spent + (burn_rate * days_remaining)
        projected_over_under = budgeted - projected_spend

    return {
        'burn_rate': burn_rate,
        'days_elapsed': days_elapsed,
        'days_remaining': days_remaining,
        'total_days': total_days,
        'projected_spend': projected_spend,
        'projected_over_under': projected_over_under
    }


def calculate_daily_budget_pace(
    budgeted: float,
    spent: float,
    start_date: str,
    end_date: str
) -> pd.DataFrame:
    """
    Calculate ideal daily budget pace vs. actual spending.

    Args:
        budgeted: Total budgeted amount
        spent: Amount spent so far
        start_date: Budget period start (YYYY-MM-DD)
        end_date: Budget period end (YYYY-MM-DD)

    Returns:
        DataFrame with columns: day, ideal_cumulative, actual_cumulative (for current day only)
    """
    start = pd.to_datetime(start_date)
    end = pd.to_datetime(end_date)
    today = pd.Timestamp.now()

    # Generate date range
    date_range = pd.date_range(start=start, end=end, freq='D')

    total_days = len(date_range)
    daily_budget = budgeted / total_days if total_days > 0 else 0

    data = []
    for i, date in enumerate(date_range):
        day_number = i + 1
        ideal_cumulative = daily_budget * day_number

        # Only show actual for current day
        actual_cumulative = spent if date.date() == today.date() else None

        data.append({
            'day': day_number,
            'date': date,
            'ideal_cumulative': ideal_cumulative,
            'actual_cumulative': actual_cumulative
        })

    return pd.DataFrame(data)


def calculate_category_trends(
    transactions_df: pd.DataFrame,
    period: str = 'ME'
) -> pd.DataFrame:
    """
    Calculate category spending trends over time.

    Args:
        transactions_df: DataFrame with transaction data
        period: Pandas period string ('ME' = monthly, 'W' = weekly, 'QE' = quarterly)

    Returns:
        DataFrame with date, category_name, and amount columns
    """
    if transactions_df.empty:
        return pd.DataFrame(columns=['date', 'category_name', 'amount'])

    # Filter for expenses only
    df = transactions_df[transactions_df['type'] == 'withdrawal'].copy()

    if df.empty:
        return pd.DataFrame(columns=['date', 'category_name', 'amount'])

    # Replace None/empty categories
    df['category_name'] = df['category_name'].fillna('Uncategorized')
    df['category_name'] = df['category_name'].replace('', 'Uncategorized')

    # Ensure date is datetime
    # Check if date column is datetime and has timezone info
    if pd.api.types.is_datetime64_any_dtype(df['date']):
        if hasattr(df['date'].dt, 'tz') and df['date'].dt.tz is not None:
            # Already datetime with timezone - just remove timezone
            df['date'] = df['date'].dt.tz_localize(None)
    else:
        # Convert date column to datetime if it's not already
        # Use utc=True to handle timezone-aware datetime objects
        df['date'] = pd.to_datetime(df['date'], utc=True)
        # Remove timezone to make grouping work
        df['date'] = df['date'].dt.tz_localize(None)

    # Group by period and category
    df_grouped = df.groupby([pd.Grouper(key='date', freq=period), 'category_name'])['amount'].sum().reset_index()

    return df_grouped


def calculate_category_monthly_comparison(
    transactions_df: pd.DataFrame,
    category_name: str
) -> pd.DataFrame:
    """
    Calculate month-over-month spending for a specific category.

    Args:
        transactions_df: DataFrame with transaction data
        category_name: Name of the category to analyze

    Returns:
        DataFrame with month, amount, and change columns
    """
    if transactions_df.empty:
        return pd.DataFrame(columns=['month', 'amount', 'change', 'change_pct'])

    # Filter for specific category and expenses
    df = transactions_df[
        (transactions_df['category_name'] == category_name) &
        (transactions_df['type'] == 'withdrawal')
    ].copy()

    if df.empty:
        return pd.DataFrame(columns=['month', 'amount', 'change', 'change_pct'])

    # Ensure date is datetime
    # Check if date column is datetime and has timezone info
    if pd.api.types.is_datetime64_any_dtype(df['date']):
        if hasattr(df['date'].dt, 'tz') and df['date'].dt.tz is not None:
            # Already datetime with timezone - just remove timezone
            df['date'] = df['date'].dt.tz_localize(None)
    else:
        # Convert date column to datetime if it's not already
        # Use utc=True to handle timezone-aware datetime objects
        df['date'] = pd.to_datetime(df['date'], utc=True)
        # Remove timezone to make grouping work
        df['date'] = df['date'].dt.tz_localize(None)

    # Group by month
    monthly = df.groupby(pd.Grouper(key='date', freq='ME'))['amount'].sum().reset_index()
    monthly.columns = ['month', 'amount']

    # Calculate month-over-month change
    monthly['change'] = monthly['amount'].diff()
    monthly['change_pct'] = monthly['amount'].pct_change() * 100

    return monthly


def calculate_category_percentage(
    transactions_df: pd.DataFrame,
    start_date: str = None,
    end_date: str = None
) -> pd.DataFrame:
    """
    Calculate category spending as percentage of total expenses.

    Args:
        transactions_df: DataFrame with transaction data
        start_date: Optional start date filter (YYYY-MM-DD)
        end_date: Optional end date filter (YYYY-MM-DD)

    Returns:
        DataFrame with category_name, amount, percentage, and cumulative_pct columns
    """
    if transactions_df.empty:
        return pd.DataFrame(columns=['category_name', 'amount', 'percentage', 'cumulative_pct'])

    df = transactions_df.copy()

    # Ensure date is datetime and handle timezone
    if pd.api.types.is_datetime64_any_dtype(df['date']):
        if hasattr(df['date'].dt, 'tz') and df['date'].dt.tz is not None:
            # Already datetime with timezone - just remove timezone
            df['date'] = df['date'].dt.tz_localize(None)
    else:
        # Convert date column to datetime if it's not already
        # Use utc=True to handle timezone-aware datetime objects
        df['date'] = pd.to_datetime(df['date'], utc=True)
        # Remove timezone to make comparisons work
        df['date'] = df['date'].dt.tz_localize(None)

    # Filter by date range if provided
    if start_date:
        start_dt = pd.to_datetime(start_date)
        df = df[df['date'] >= start_dt]
    if end_date:
        end_dt = pd.to_datetime(end_date)
        df = df[df['date'] <= end_dt]

    # Filter for expenses only
    df = df[df['type'] == 'withdrawal'].copy()

    if df.empty:
        return pd.DataFrame(columns=['category_name', 'amount', 'percentage', 'cumulative_pct'])

    # Replace None/empty categories
    df['category_name'] = df['category_name'].fillna('Uncategorized')
    df['category_name'] = df['category_name'].replace('', 'Uncategorized')

    # Group by category
    category_totals = df.groupby('category_name')['amount'].sum().reset_index()
    category_totals.columns = ['category_name', 'amount']

    # Calculate total expenses
    total_expenses = category_totals['amount'].sum()

    # Calculate percentage
    category_totals['percentage'] = (category_totals['amount'] / total_expenses * 100) if total_expenses > 0 else 0

    # Sort by amount descending
    category_totals = category_totals.sort_values('amount', ascending=False)

    # Calculate cumulative percentage
    category_totals['cumulative_pct'] = category_totals['percentage'].cumsum()

    return category_totals


def get_top_transactions_by_category(
    transactions_df: pd.DataFrame,
    category_name: str,
    limit: int = 10
) -> pd.DataFrame:
    """
    Get top transactions for a specific category.

    Args:
        transactions_df: DataFrame with transaction data
        category_name: Name of the category
        limit: Number of top transactions to return

    Returns:
        DataFrame with top transactions sorted by amount descending
    """
    if transactions_df.empty:
        return pd.DataFrame(columns=['date', 'description', 'amount', 'destination_name'])

    # Filter for specific category
    df = transactions_df[transactions_df['category_name'] == category_name].copy()

    if df.empty:
        return pd.DataFrame(columns=['date', 'description', 'amount', 'destination_name'])

    # Sort by amount descending
    df_sorted = df.sort_values('amount', ascending=False)

    # Select relevant columns and limit
    result = df_sorted[['date', 'description', 'amount', 'destination_name']].head(limit)

    return result


def calculate_category_statistics(
    transactions_df: pd.DataFrame,
    category_name: str
) -> Dict[str, float]:
    """
    Calculate statistical metrics for a category.

    Args:
        transactions_df: DataFrame with transaction data
        category_name: Name of the category

    Returns:
        Dictionary with mean, median, min, max, std, and count
    """
    if transactions_df.empty:
        return {
            'mean': 0,
            'median': 0,
            'min': 0,
            'max': 0,
            'std': 0,
            'count': 0
        }

    # Filter for specific category
    df = transactions_df[transactions_df['category_name'] == category_name].copy()

    if df.empty:
        return {
            'mean': 0,
            'median': 0,
            'min': 0,
            'max': 0,
            'std': 0,
            'count': 0
        }

    return {
        'mean': df['amount'].mean(),
        'median': df['amount'].median(),
        'min': df['amount'].min(),
        'max': df['amount'].max(),
        'std': df['amount'].std(),
        'count': len(df)
    }
