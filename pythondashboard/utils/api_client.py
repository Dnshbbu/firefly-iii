"""Firefly III API Client

This module provides a client for interacting with the Firefly III REST API.
"""

import requests
import pandas as pd
from typing import Dict, List, Optional, Tuple
from datetime import datetime, date


class FireflyAPIClient:
    """Client for interacting with Firefly III API"""

    def __init__(self, base_url: str, api_token: str):
        """
        Initialize the Firefly III API client.

        Args:
            base_url: The base URL of your Firefly III instance (e.g., http://192.168.0.242)
            api_token: Your personal access token from Firefly III
        """
        self.base_url = base_url.rstrip('/')
        self.api_token = api_token
        self.headers = {
            'Authorization': f'Bearer {api_token}',
            'Accept': 'application/vnd.api+json',
            'Content-Type': 'application/json'
        }

    def test_connection(self) -> Tuple[bool, str]:
        """
        Test API connection.

        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            response = requests.get(
                f"{self.base_url}/api/v1/about",
                headers=self.headers,
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                version = data.get('data', {}).get('version', 'unknown')
                return True, f"Connected to Firefly III v{version}"
            else:
                return False, f"Error: {response.status_code} - {response.text}"
        except requests.exceptions.RequestException as e:
            return False, f"Connection failed: {str(e)}"

    def get_accounts(self, account_type: Optional[str] = None) -> List[Dict]:
        """
        Fetch accounts from Firefly III.

        Args:
            account_type: Optional filter by account type (asset, expense, revenue, liability)

        Returns:
            List of account dictionaries
        """
        try:
            url = f"{self.base_url}/api/v1/accounts"
            params = {}
            if account_type:
                params['type'] = account_type

            response = requests.get(
                url,
                headers=self.headers,
                params=params,
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                return data.get('data', [])
            else:
                return []
        except requests.exceptions.RequestException:
            return []

    def get_transactions(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        transaction_type: Optional[str] = None,
        limit: int = 500
    ) -> List[Dict]:
        """
        Fetch transactions from Firefly III.

        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            transaction_type: Filter by type (withdrawal, deposit, transfer)
            limit: Maximum number of transactions per page (default 500)

        Returns:
            List of transaction dictionaries
        """
        try:
            url = f"{self.base_url}/api/v1/transactions"
            params = {'limit': limit}

            if start_date:
                params['start'] = start_date
            if end_date:
                params['end'] = end_date
            if transaction_type:
                params['type'] = transaction_type

            all_transactions = []
            page = 1

            while True:
                params['page'] = page
                response = requests.get(
                    url,
                    headers=self.headers,
                    params=params,
                    timeout=30
                )

                if response.status_code != 200:
                    break

                data = response.json()
                transactions = data.get('data', [])

                if not transactions:
                    break

                all_transactions.extend(transactions)

                # Check if there are more pages
                meta = data.get('meta', {})
                pagination = meta.get('pagination', {})
                current_page = pagination.get('current_page', page)
                total_pages = pagination.get('total_pages', page)

                if current_page >= total_pages:
                    break

                page += 1

            return all_transactions

        except requests.exceptions.RequestException:
            return []

    def get_budgets(self) -> List[Dict]:
        """
        Fetch all budgets.

        Returns:
            List of budget dictionaries
        """
        try:
            url = f"{self.base_url}/api/v1/budgets"
            response = requests.get(
                url,
                headers=self.headers,
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                return data.get('data', [])
            return []
        except requests.exceptions.RequestException:
            return []

    def get_budget_limits(self, budget_id: str, start: str, end: str) -> List[Dict]:
        """
        Fetch budget limits for a specific budget and date range.

        Args:
            budget_id: Budget ID
            start: Start date in YYYY-MM-DD format
            end: End date in YYYY-MM-DD format

        Returns:
            List of budget limit dictionaries
        """
        try:
            url = f"{self.base_url}/api/v1/budgets/{budget_id}/limits"
            params = {'start': start, 'end': end}
            response = requests.get(
                url,
                headers=self.headers,
                params=params,
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                return data.get('data', [])
            return []
        except requests.exceptions.RequestException:
            return []

    def get_categories(self) -> List[Dict]:
        """
        Fetch all categories.

        Returns:
            List of category dictionaries
        """
        try:
            url = f"{self.base_url}/api/v1/categories"
            response = requests.get(
                url,
                headers=self.headers,
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                return data.get('data', [])
            return []
        except requests.exceptions.RequestException:
            return []

    def get_bills(self) -> List[Dict]:
        """
        Fetch all bills.

        Returns:
            List of bill dictionaries
        """
        try:
            url = f"{self.base_url}/api/v1/bills"
            response = requests.get(
                url,
                headers=self.headers,
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                return data.get('data', [])
            return []
        except requests.exceptions.RequestException:
            return []

    def get_piggy_banks(self) -> List[Dict]:
        """
        Fetch all piggy banks.

        Returns:
            List of piggy bank dictionaries
        """
        try:
            url = f"{self.base_url}/api/v1/piggy-banks"
            response = requests.get(
                url,
                headers=self.headers,
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                return data.get('data', [])
            return []
        except requests.exceptions.RequestException:
            return []

    def parse_account_data(self, accounts_data: List[Dict]) -> pd.DataFrame:
        """
        Parse account data into a pandas DataFrame.

        Args:
            accounts_data: List of account dictionaries from API

        Returns:
            DataFrame with parsed account data
        """
        accounts = []

        for account in accounts_data:
            attributes = account.get('attributes', {})

            # Get current balance
            current_balance = attributes.get('current_balance', '0')
            currency_code = attributes.get('currency_code', 'EUR')

            accounts.append({
                'id': account.get('id'),
                'name': attributes.get('name', ''),
                'type': attributes.get('type', ''),
                'account_role': attributes.get('account_role', ''),
                'currency_code': currency_code,
                'current_balance': float(current_balance),
                'iban': attributes.get('iban', ''),
                'active': attributes.get('active', True),
                'include_net_worth': attributes.get('include_net_worth', True)
            })

        return pd.DataFrame(accounts)

    def parse_transaction_data(self, transactions_data: List[Dict]) -> pd.DataFrame:
        """
        Parse transaction data into a pandas DataFrame.

        Args:
            transactions_data: List of transaction dictionaries from API

        Returns:
            DataFrame with parsed transaction data
        """
        transactions = []

        for transaction in transactions_data:
            attributes = transaction.get('attributes', {})

            # Each transaction can have multiple "splits" (for split transactions)
            transaction_splits = attributes.get('transactions', [])

            for split in transaction_splits:
                transactions.append({
                    'id': transaction.get('id'),
                    'date': split.get('date'),
                    'description': split.get('description', ''),
                    'amount': float(split.get('amount', 0)),
                    'currency_code': split.get('currency_code', 'EUR'),
                    'type': split.get('type', ''),
                    'category_name': split.get('category_name', ''),
                    'budget_name': split.get('budget_name', ''),
                    'source_name': split.get('source_name', ''),
                    'destination_name': split.get('destination_name', ''),
                    'notes': split.get('notes', ''),
                })

        df = pd.DataFrame(transactions)

        # Convert date to datetime
        if not df.empty and 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'])

        return df
