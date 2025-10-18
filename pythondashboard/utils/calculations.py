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
    period: str = 'M'
) -> pd.DataFrame:
    """
    Calculate cash flow (income vs expenses) aggregated by period.

    Args:
        transactions_df: DataFrame with transaction data (must have 'date', 'type', 'amount' columns)
        period: Pandas period string ('D' = daily, 'W' = weekly, 'M' = monthly, 'Q' = quarterly, 'Y' = yearly)

    Returns:
        DataFrame with columns: period, income, expenses, net_flow
    """
    if transactions_df.empty:
        return pd.DataFrame(columns=['period', 'income', 'expenses', 'net_flow'])

    df = transactions_df.copy()

    # Ensure date is datetime
    df['date'] = pd.to_datetime(df['date'])

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

    # Filter by date range if provided
    if start_date:
        start_dt = pd.to_datetime(start_date)
        # If the date column has timezone info, make start_dt timezone-aware
        if df['date'].dt.tz is not None:
            start_dt = start_dt.tz_localize(df['date'].dt.tz)
        df = df[df['date'] >= start_dt]
    if end_date:
        end_dt = pd.to_datetime(end_date)
        # If the date column has timezone info, make end_dt timezone-aware
        if df['date'].dt.tz is not None:
            end_dt = end_dt.tz_localize(df['date'].dt.tz)
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

    # Filter by date range if provided
    if start_date:
        start_dt = pd.to_datetime(start_date)
        # If the date column has timezone info, make start_dt timezone-aware
        if df['date'].dt.tz is not None:
            start_dt = start_dt.tz_localize(df['date'].dt.tz)
        df = df[df['date'] >= start_dt]
    if end_date:
        end_dt = pd.to_datetime(end_date)
        # If the date column has timezone info, make end_dt timezone-aware
        if df['date'].dt.tz is not None:
            end_dt = end_dt.tz_localize(df['date'].dt.tz)
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
    df['date'] = pd.to_datetime(df['date'])

    # Prepare date filters with timezone awareness
    current_start_dt = pd.to_datetime(current_start)
    current_end_dt = pd.to_datetime(current_end)
    previous_start_dt = pd.to_datetime(previous_start)
    previous_end_dt = pd.to_datetime(previous_end)

    # If the date column has timezone info, make comparison dates timezone-aware
    if df['date'].dt.tz is not None:
        current_start_dt = current_start_dt.tz_localize(df['date'].dt.tz)
        current_end_dt = current_end_dt.tz_localize(df['date'].dt.tz)
        previous_start_dt = previous_start_dt.tz_localize(df['date'].dt.tz)
        previous_end_dt = previous_end_dt.tz_localize(df['date'].dt.tz)

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
