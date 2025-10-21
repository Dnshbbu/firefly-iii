"""
Firefly III API Client Module
Handles all API interactions with Firefly III instance
"""

import requests
import json
from typing import Dict, List, Optional, Tuple
from datetime import datetime


class FireflyAPIClient:
    """Client for interacting with Firefly III API"""

    def __init__(self, base_url: str, access_token: str):
        """
        Initialize Firefly III API client

        Args:
            base_url: Base URL of Firefly III instance (e.g., http://localhost)
            access_token: Personal Access Token from Firefly III
        """
        self.base_url = base_url.rstrip('/')
        self.access_token = access_token
        self.headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }

    def test_connection(self) -> Tuple[bool, str]:
        """
        Test API connection

        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            response = requests.get(
                f'{self.base_url}/api/v1/about',
                headers=self.headers,
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                version = data.get('data', {}).get('version', 'unknown')
                return True, f"Connected successfully! Firefly III version: {version}"
            else:
                return False, f"Connection failed: {response.status_code} - {response.text}"
        except requests.exceptions.RequestException as e:
            return False, f"Connection error: {str(e)}"

    def get_rules(self, page: int = 1, limit: int = 50) -> Tuple[bool, Optional[List[Dict]], str]:
        """
        Get all rules from Firefly III

        Args:
            page: Page number for pagination
            limit: Number of rules per page

        Returns:
            Tuple of (success: bool, rules: List[Dict] or None, message: str)
        """
        try:
            response = requests.get(
                f'{self.base_url}/api/v1/rules',
                headers=self.headers,
                params={'page': page, 'limit': limit},
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                rules = data.get('data', [])
                return True, rules, f"Retrieved {len(rules)} rules"
            else:
                return False, None, f"Failed to get rules: {response.status_code} - {response.text}"
        except requests.exceptions.RequestException as e:
            return False, None, f"Error retrieving rules: {str(e)}"

    def get_all_rules(self) -> Tuple[bool, Optional[List[Dict]], str]:
        """
        Get ALL rules from Firefly III (handles pagination automatically)

        Returns:
            Tuple of (success: bool, rules: List[Dict] or None, message: str)
        """
        all_rules = []
        page = 1

        try:
            while True:
                response = requests.get(
                    f'{self.base_url}/api/v1/rules',
                    headers=self.headers,
                    params={'page': page},
                    timeout=10
                )

                if response.status_code != 200:
                    return False, None, f"Failed to get rules: {response.status_code} - {response.text}"

                data = response.json()
                rules = data.get('data', [])

                if not rules:
                    break

                all_rules.extend(rules)

                # Check if there's a next page
                meta = data.get('meta', {})
                pagination = meta.get('pagination', {})
                current_page = pagination.get('current_page', page)
                total_pages = pagination.get('total_pages', 1)

                if current_page >= total_pages:
                    break

                page += 1

            return True, all_rules, f"Retrieved {len(all_rules)} rules"
        except requests.exceptions.RequestException as e:
            return False, None, f"Error retrieving rules: {str(e)}"

    def delete_rule(self, rule_id: int) -> Tuple[bool, str]:
        """
        Delete a rule by ID

        Args:
            rule_id: ID of the rule to delete

        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            response = requests.delete(
                f'{self.base_url}/api/v1/rules/{rule_id}',
                headers=self.headers,
                timeout=10
            )

            if response.status_code == 204:
                return True, f"Rule {rule_id} deleted successfully"
            else:
                return False, f"Failed to delete rule: {response.status_code} - {response.text}"
        except requests.exceptions.RequestException as e:
            return False, f"Error deleting rule: {str(e)}"

    def create_rule(self, rule_data: Dict) -> Tuple[bool, Optional[Dict], str]:
        """
        Create a new rule

        Args:
            rule_data: Rule data dictionary (should contain title, triggers, actions, etc.)

        Returns:
            Tuple of (success: bool, created_rule: Dict or None, message: str)
        """
        try:
            # The API expects the data in a specific format
            # If rule_data doesn't have the required fields, wrap it properly
            if 'title' in rule_data:
                # Data is already in the correct format (attributes directly)
                payload = rule_data
            else:
                # Data might be wrapped in attributes
                payload = rule_data.get('attributes', rule_data)

            response = requests.post(
                f'{self.base_url}/api/v1/rules',
                headers=self.headers,
                json=payload,
                timeout=10
            )

            if response.status_code == 200 or response.status_code == 201:
                data = response.json()
                created_rule = data.get('data', {})
                rule_id = created_rule.get('id', 'unknown')
                return True, created_rule, f"Rule created successfully (ID: {rule_id})"
            else:
                # Include more detailed error information
                error_detail = response.text
                try:
                    error_json = response.json()
                    if 'errors' in error_json:
                        # Format validation errors nicely
                        errors = error_json['errors']
                        error_msgs = []
                        for field, messages in errors.items():
                            error_msgs.append(f"{field}: {', '.join(messages)}")
                        error_detail = '; '.join(error_msgs)
                    elif 'message' in error_json:
                        error_detail = error_json['message']
                except:
                    pass
                return False, None, f"Failed to create rule: {response.status_code} - {error_detail}"
        except requests.exceptions.RequestException as e:
            return False, None, f"Error creating rule: {str(e)}"

    def export_rules_to_json(self, rules: List[Dict], filepath: str) -> Tuple[bool, str]:
        """
        Export rules to JSON file

        Args:
            rules: List of rule dictionaries
            filepath: Path to save the JSON file

        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            export_data = {
                'export_date': datetime.now().isoformat(),
                'firefly_iii_rules_export': True,
                'total_rules': len(rules),
                'rules': rules
            }

            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)

            return True, f"Exported {len(rules)} rules to {filepath}"
        except Exception as e:
            return False, f"Error exporting rules: {str(e)}"

    def import_rules_from_json(self, filepath: str) -> Tuple[bool, Optional[List[Dict]], str]:
        """
        Import rules from JSON file

        Args:
            filepath: Path to the JSON file

        Returns:
            Tuple of (success: bool, rules: List[Dict] or None, message: str)
        """
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Validate the file structure
            if not isinstance(data, dict) or 'rules' not in data:
                return False, None, "Invalid JSON file format. Expected 'rules' key."

            rules = data.get('rules', [])
            if not isinstance(rules, list):
                return False, None, "Invalid rules format. Expected a list."

            return True, rules, f"Loaded {len(rules)} rules from file"
        except json.JSONDecodeError as e:
            return False, None, f"Invalid JSON file: {str(e)}"
        except Exception as e:
            return False, None, f"Error reading file: {str(e)}"

    # ========== CATEGORY MANAGEMENT METHODS ==========

    def get_categories(self, page: int = 1, limit: int = 50) -> Tuple[bool, Optional[List[Dict]], str]:
        """
        Get categories from Firefly III

        Args:
            page: Page number for pagination
            limit: Number of categories per page

        Returns:
            Tuple of (success: bool, categories: List[Dict] or None, message: str)
        """
        try:
            response = requests.get(
                f'{self.base_url}/api/v1/categories',
                headers=self.headers,
                params={'page': page, 'limit': limit},
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                categories = data.get('data', [])
                return True, categories, f"Retrieved {len(categories)} categories"
            else:
                return False, None, f"Failed to get categories: {response.status_code} - {response.text}"
        except requests.exceptions.RequestException as e:
            return False, None, f"Error retrieving categories: {str(e)}"

    def get_all_categories(self) -> Tuple[bool, Optional[List[Dict]], str]:
        """
        Get ALL categories from Firefly III (handles pagination automatically)

        Returns:
            Tuple of (success: bool, categories: List[Dict] or None, message: str)
        """
        all_categories = []
        page = 1

        try:
            while True:
                response = requests.get(
                    f'{self.base_url}/api/v1/categories',
                    headers=self.headers,
                    params={'page': page},
                    timeout=10
                )

                if response.status_code != 200:
                    return False, None, f"Failed to get categories: {response.status_code} - {response.text}"

                data = response.json()
                categories = data.get('data', [])

                if not categories:
                    break

                all_categories.extend(categories)

                # Check if there's a next page
                meta = data.get('meta', {})
                pagination = meta.get('pagination', {})
                current_page = pagination.get('current_page', page)
                total_pages = pagination.get('total_pages', 1)

                if current_page >= total_pages:
                    break

                page += 1

            return True, all_categories, f"Retrieved {len(all_categories)} categories"
        except requests.exceptions.RequestException as e:
            return False, None, f"Error retrieving categories: {str(e)}"

    def delete_category(self, category_id: int) -> Tuple[bool, str]:
        """
        Delete a category by ID

        Args:
            category_id: ID of the category to delete

        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            response = requests.delete(
                f'{self.base_url}/api/v1/categories/{category_id}',
                headers=self.headers,
                timeout=10
            )

            if response.status_code == 204:
                return True, f"Category {category_id} deleted successfully"
            else:
                return False, f"Failed to delete category: {response.status_code} - {response.text}"
        except requests.exceptions.RequestException as e:
            return False, f"Error deleting category: {str(e)}"

    def create_category(self, category_data: Dict) -> Tuple[bool, Optional[Dict], str]:
        """
        Create a new category

        Args:
            category_data: Category data dictionary (should contain name, and optionally notes)

        Returns:
            Tuple of (success: bool, created_category: Dict or None, message: str)
        """
        try:
            # The API expects the data in a specific format
            if 'name' in category_data:
                # Data is already in the correct format
                payload = category_data
            else:
                # Data might be wrapped in attributes
                payload = category_data.get('attributes', category_data)

            response = requests.post(
                f'{self.base_url}/api/v1/categories',
                headers=self.headers,
                json=payload,
                timeout=10
            )

            if response.status_code == 200 or response.status_code == 201:
                data = response.json()
                created_category = data.get('data', {})
                category_id = created_category.get('id', 'unknown')
                return True, created_category, f"Category created successfully (ID: {category_id})"
            else:
                # Include more detailed error information
                error_detail = response.text
                try:
                    error_json = response.json()
                    if 'errors' in error_json:
                        # Format validation errors nicely
                        errors = error_json['errors']
                        error_msgs = []
                        for field, messages in errors.items():
                            error_msgs.append(f"{field}: {', '.join(messages)}")
                        error_detail = '; '.join(error_msgs)
                    elif 'message' in error_json:
                        error_detail = error_json['message']
                except:
                    pass
                return False, None, f"Failed to create category: {response.status_code} - {error_detail}"
        except requests.exceptions.RequestException as e:
            return False, None, f"Error creating category: {str(e)}"

    def update_category(self, category_id: int, category_data: Dict) -> Tuple[bool, Optional[Dict], str]:
        """
        Update an existing category

        Args:
            category_id: ID of the category to update
            category_data: Category data dictionary (should contain name, and optionally notes)

        Returns:
            Tuple of (success: bool, updated_category: Dict or None, message: str)
        """
        try:
            # The API expects the data in a specific format
            if 'name' in category_data:
                # Data is already in the correct format
                payload = category_data
            else:
                # Data might be wrapped in attributes
                payload = category_data.get('attributes', category_data)

            response = requests.put(
                f'{self.base_url}/api/v1/categories/{category_id}',
                headers=self.headers,
                json=payload,
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                updated_category = data.get('data', {})
                return True, updated_category, f"Category updated successfully (ID: {category_id})"
            else:
                # Include more detailed error information
                error_detail = response.text
                try:
                    error_json = response.json()
                    if 'errors' in error_json:
                        # Format validation errors nicely
                        errors = error_json['errors']
                        error_msgs = []
                        for field, messages in errors.items():
                            error_msgs.append(f"{field}: {', '.join(messages)}")
                        error_detail = '; '.join(error_msgs)
                    elif 'message' in error_json:
                        error_detail = error_json['message']
                except:
                    pass
                return False, None, f"Failed to update category: {response.status_code} - {error_detail}"
        except requests.exceptions.RequestException as e:
            return False, None, f"Error updating category: {str(e)}"

    def export_categories_to_json(self, categories: List[Dict], filepath: str) -> Tuple[bool, str]:
        """
        Export categories to JSON file

        Args:
            categories: List of category dictionaries
            filepath: Path to save the JSON file

        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            export_data = {
                'export_date': datetime.now().isoformat(),
                'firefly_iii_categories_export': True,
                'total_categories': len(categories),
                'categories': categories
            }

            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)

            return True, f"Exported {len(categories)} categories to {filepath}"
        except Exception as e:
            return False, f"Error exporting categories: {str(e)}"

    def import_categories_from_json(self, filepath: str) -> Tuple[bool, Optional[List[Dict]], str]:
        """
        Import categories from JSON file

        Args:
            filepath: Path to the JSON file

        Returns:
            Tuple of (success: bool, categories: List[Dict] or None, message: str)
        """
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Validate the file structure
            if not isinstance(data, dict) or 'categories' not in data:
                return False, None, "Invalid JSON file format. Expected 'categories' key."

            categories = data.get('categories', [])
            if not isinstance(categories, list):
                return False, None, "Invalid categories format. Expected a list."

            return True, categories, f"Loaded {len(categories)} categories from file"
        except json.JSONDecodeError as e:
            return False, None, f"Invalid JSON file: {str(e)}"
        except Exception as e:
            return False, None, f"Error reading file: {str(e)}"

    # ========== ACCOUNT MANAGEMENT METHODS ==========

    def get_accounts(self, account_type: Optional[str] = None, page: int = 1, limit: int = 50) -> Tuple[bool, Optional[List[Dict]], str]:
        """
        Get accounts from Firefly III

        Args:
            account_type: Optional filter by account type (asset, expense, revenue, liability, etc.)
            page: Page number for pagination
            limit: Number of accounts per page

        Returns:
            Tuple of (success: bool, accounts: List[Dict] or None, message: str)
        """
        try:
            params = {'page': page, 'limit': limit}
            if account_type:
                params['type'] = account_type

            response = requests.get(
                f'{self.base_url}/api/v1/accounts',
                headers=self.headers,
                params=params,
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                accounts = data.get('data', [])
                return True, accounts, f"Retrieved {len(accounts)} accounts"
            else:
                return False, None, f"Failed to get accounts: {response.status_code} - {response.text}"
        except requests.exceptions.RequestException as e:
            return False, None, f"Error retrieving accounts: {str(e)}"

    def get_all_accounts(self, account_type: Optional[str] = None) -> Tuple[bool, Optional[List[Dict]], str]:
        """
        Get ALL accounts from Firefly III (handles pagination automatically)

        Args:
            account_type: Optional filter by account type (asset, expense, revenue, liability, etc.)

        Returns:
            Tuple of (success: bool, accounts: List[Dict] or None, message: str)
        """
        all_accounts = []
        page = 1

        try:
            while True:
                params = {'page': page}
                if account_type:
                    params['type'] = account_type

                response = requests.get(
                    f'{self.base_url}/api/v1/accounts',
                    headers=self.headers,
                    params=params,
                    timeout=10
                )

                if response.status_code != 200:
                    return False, None, f"Failed to get accounts: {response.status_code} - {response.text}"

                data = response.json()
                accounts = data.get('data', [])

                if not accounts:
                    break

                all_accounts.extend(accounts)

                # Check if there's a next page
                meta = data.get('meta', {})
                pagination = meta.get('pagination', {})
                current_page = pagination.get('current_page', page)
                total_pages = pagination.get('total_pages', 1)

                if current_page >= total_pages:
                    break

                page += 1

            return True, all_accounts, f"Retrieved {len(all_accounts)} accounts"
        except requests.exceptions.RequestException as e:
            return False, None, f"Error retrieving accounts: {str(e)}"

    def delete_account(self, account_id: int) -> Tuple[bool, str]:
        """
        Delete an account by ID

        Args:
            account_id: ID of the account to delete

        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            response = requests.delete(
                f'{self.base_url}/api/v1/accounts/{account_id}',
                headers=self.headers,
                timeout=10
            )

            if response.status_code == 204:
                return True, f"Account {account_id} deleted successfully"
            else:
                return False, f"Failed to delete account: {response.status_code} - {response.text}"
        except requests.exceptions.RequestException as e:
            return False, f"Error deleting account: {str(e)}"

    def create_account(self, account_data: Dict) -> Tuple[bool, Optional[Dict], str]:
        """
        Create a new account

        Args:
            account_data: Account data dictionary (should contain name, type, and other optional fields)

        Returns:
            Tuple of (success: bool, created_account: Dict or None, message: str)
        """
        try:
            # The API expects the data in a specific format
            if 'name' in account_data:
                # Data is already in the correct format
                payload = account_data
            else:
                # Data might be wrapped in attributes
                payload = account_data.get('attributes', account_data)

            response = requests.post(
                f'{self.base_url}/api/v1/accounts',
                headers=self.headers,
                json=payload,
                timeout=10
            )

            if response.status_code == 200 or response.status_code == 201:
                data = response.json()
                created_account = data.get('data', {})
                account_id = created_account.get('id', 'unknown')
                return True, created_account, f"Account created successfully (ID: {account_id})"
            else:
                # Include more detailed error information
                error_detail = response.text
                try:
                    error_json = response.json()
                    if 'errors' in error_json:
                        # Format validation errors nicely
                        errors = error_json['errors']
                        error_msgs = []
                        for field, messages in errors.items():
                            error_msgs.append(f"{field}: {', '.join(messages)}")
                        error_detail = '; '.join(error_msgs)
                    elif 'message' in error_json:
                        error_detail = error_json['message']
                except:
                    pass
                return False, None, f"Failed to create account: {response.status_code} - {error_detail}"
        except requests.exceptions.RequestException as e:
            return False, None, f"Error creating account: {str(e)}"

    def update_account(self, account_id: int, account_data: Dict) -> Tuple[bool, Optional[Dict], str]:
        """
        Update an existing account

        Args:
            account_id: ID of the account to update
            account_data: Account data dictionary (should contain name, type, and other optional fields)

        Returns:
            Tuple of (success: bool, updated_account: Dict or None, message: str)
        """
        try:
            # The API expects the data in a specific format
            if 'name' in account_data:
                # Data is already in the correct format
                payload = account_data
            else:
                # Data might be wrapped in attributes
                payload = account_data.get('attributes', account_data)

            response = requests.put(
                f'{self.base_url}/api/v1/accounts/{account_id}',
                headers=self.headers,
                json=payload,
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                updated_account = data.get('data', {})
                return True, updated_account, f"Account updated successfully (ID: {account_id})"
            else:
                # Include more detailed error information
                error_detail = response.text
                try:
                    error_json = response.json()
                    if 'errors' in error_json:
                        # Format validation errors nicely
                        errors = error_json['errors']
                        error_msgs = []
                        for field, messages in errors.items():
                            error_msgs.append(f"{field}: {', '.join(messages)}")
                        error_detail = '; '.join(error_msgs)
                    elif 'message' in error_json:
                        error_detail = error_json['message']
                except:
                    pass
                return False, None, f"Failed to update account: {response.status_code} - {error_detail}"
        except requests.exceptions.RequestException as e:
            return False, None, f"Error updating account: {str(e)}"

    def export_accounts_to_json(self, accounts: List[Dict], filepath: str, account_type: str = "accounts") -> Tuple[bool, str]:
        """
        Export accounts to JSON file

        Args:
            accounts: List of account dictionaries
            filepath: Path to save the JSON file
            account_type: Type descriptor for the export (e.g., "asset_accounts", "expense_accounts")

        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            export_data = {
                'export_date': datetime.now().isoformat(),
                'firefly_iii_accounts_export': True,
                'account_type': account_type,
                'total_accounts': len(accounts),
                'accounts': accounts
            }

            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)

            return True, f"Exported {len(accounts)} accounts to {filepath}"
        except Exception as e:
            return False, f"Error exporting accounts: {str(e)}"

    def import_accounts_from_json(self, filepath: str) -> Tuple[bool, Optional[List[Dict]], str]:
        """
        Import accounts from JSON file

        Args:
            filepath: Path to the JSON file

        Returns:
            Tuple of (success: bool, accounts: List[Dict] or None, message: str)
        """
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Validate the file structure
            if not isinstance(data, dict) or 'accounts' not in data:
                return False, None, "Invalid JSON file format. Expected 'accounts' key."

            accounts = data.get('accounts', [])
            if not isinstance(accounts, list):
                return False, None, "Invalid accounts format. Expected a list."

            return True, accounts, f"Loaded {len(accounts)} accounts from file"
        except json.JSONDecodeError as e:
            return False, None, f"Invalid JSON file: {str(e)}"
        except Exception as e:
            return False, None, f"Error reading file: {str(e)}"

    # ========== BUDGET MANAGEMENT METHODS ==========

    def get_budgets(self, page: int = 1, limit: int = 50) -> Tuple[bool, Optional[List[Dict]], str]:
        """
        Get budgets from Firefly III

        Args:
            page: Page number for pagination
            limit: Number of budgets per page

        Returns:
            Tuple of (success: bool, budgets: List[Dict] or None, message: str)
        """
        try:
            response = requests.get(
                f'{self.base_url}/api/v1/budgets',
                headers=self.headers,
                params={'page': page, 'limit': limit},
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                budgets = data.get('data', [])
                return True, budgets, f"Retrieved {len(budgets)} budgets"
            else:
                return False, None, f"Failed to get budgets: {response.status_code} - {response.text}"
        except requests.exceptions.RequestException as e:
            return False, None, f"Error retrieving budgets: {str(e)}"

    def get_all_budgets(self) -> Tuple[bool, Optional[List[Dict]], str]:
        """
        Get ALL budgets from Firefly III (handles pagination automatically)

        Returns:
            Tuple of (success: bool, budgets: List[Dict] or None, message: str)
        """
        all_budgets = []
        page = 1

        try:
            while True:
                response = requests.get(
                    f'{self.base_url}/api/v1/budgets',
                    headers=self.headers,
                    params={'page': page},
                    timeout=10
                )

                if response.status_code != 200:
                    return False, None, f"Failed to get budgets: {response.status_code} - {response.text}"

                data = response.json()
                budgets = data.get('data', [])

                if not budgets:
                    break

                all_budgets.extend(budgets)

                # Check if there's a next page
                meta = data.get('meta', {})
                pagination = meta.get('pagination', {})
                current_page = pagination.get('current_page', page)
                total_pages = pagination.get('total_pages', 1)

                if current_page >= total_pages:
                    break

                page += 1

            return True, all_budgets, f"Retrieved {len(all_budgets)} budgets"
        except requests.exceptions.RequestException as e:
            return False, None, f"Error retrieving budgets: {str(e)}"

    def delete_budget(self, budget_id: int) -> Tuple[bool, str]:
        """
        Delete a budget by ID

        Args:
            budget_id: ID of the budget to delete

        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            response = requests.delete(
                f'{self.base_url}/api/v1/budgets/{budget_id}',
                headers=self.headers,
                timeout=10
            )

            if response.status_code == 204:
                return True, f"Budget {budget_id} deleted successfully"
            else:
                return False, f"Failed to delete budget: {response.status_code} - {response.text}"
        except requests.exceptions.RequestException as e:
            return False, f"Error deleting budget: {str(e)}"

    def create_budget(self, budget_data: Dict) -> Tuple[bool, Optional[Dict], str]:
        """
        Create a new budget

        Args:
            budget_data: Budget data dictionary (should contain name, and optionally auto_budget settings)

        Returns:
            Tuple of (success: bool, created_budget: Dict or None, message: str)
        """
        try:
            if 'name' in budget_data:
                payload = budget_data
            else:
                payload = budget_data.get('attributes', budget_data)

            response = requests.post(
                f'{self.base_url}/api/v1/budgets',
                headers=self.headers,
                json=payload,
                timeout=10
            )

            if response.status_code == 200 or response.status_code == 201:
                data = response.json()
                created_budget = data.get('data', {})
                budget_id = created_budget.get('id', 'unknown')
                return True, created_budget, f"Budget created successfully (ID: {budget_id})"
            else:
                error_detail = response.text
                try:
                    error_json = response.json()
                    if 'errors' in error_json:
                        errors = error_json['errors']
                        error_msgs = []
                        for field, messages in errors.items():
                            error_msgs.append(f"{field}: {', '.join(messages)}")
                        error_detail = '; '.join(error_msgs)
                    elif 'message' in error_json:
                        error_detail = error_json['message']
                except:
                    pass
                return False, None, f"Failed to create budget: {response.status_code} - {error_detail}"
        except requests.exceptions.RequestException as e:
            return False, None, f"Error creating budget: {str(e)}"

    def update_budget(self, budget_id: int, budget_data: Dict) -> Tuple[bool, Optional[Dict], str]:
        """
        Update an existing budget

        Args:
            budget_id: ID of the budget to update
            budget_data: Budget data dictionary

        Returns:
            Tuple of (success: bool, updated_budget: Dict or None, message: str)
        """
        try:
            if 'name' in budget_data:
                payload = budget_data
            else:
                payload = budget_data.get('attributes', budget_data)

            response = requests.put(
                f'{self.base_url}/api/v1/budgets/{budget_id}',
                headers=self.headers,
                json=payload,
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                updated_budget = data.get('data', {})
                return True, updated_budget, f"Budget updated successfully (ID: {budget_id})"
            else:
                error_detail = response.text
                try:
                    error_json = response.json()
                    if 'errors' in error_json:
                        errors = error_json['errors']
                        error_msgs = []
                        for field, messages in errors.items():
                            error_msgs.append(f"{field}: {', '.join(messages)}")
                        error_detail = '; '.join(error_msgs)
                    elif 'message' in error_json:
                        error_detail = error_json['message']
                except:
                    pass
                return False, None, f"Failed to update budget: {response.status_code} - {error_detail}"
        except requests.exceptions.RequestException as e:
            return False, None, f"Error updating budget: {str(e)}"

    # ========== BILL/SUBSCRIPTION MANAGEMENT METHODS ==========

    def get_bills(self, page: int = 1, limit: int = 50) -> Tuple[bool, Optional[List[Dict]], str]:
        """
        Get bills from Firefly III

        Args:
            page: Page number for pagination
            limit: Number of bills per page

        Returns:
            Tuple of (success: bool, bills: List[Dict] or None, message: str)
        """
        try:
            response = requests.get(
                f'{self.base_url}/api/v1/bills',
                headers=self.headers,
                params={'page': page, 'limit': limit},
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                bills = data.get('data', [])
                return True, bills, f"Retrieved {len(bills)} bills"
            else:
                return False, None, f"Failed to get bills: {response.status_code} - {response.text}"
        except requests.exceptions.RequestException as e:
            return False, None, f"Error retrieving bills: {str(e)}"

    def get_all_bills(self) -> Tuple[bool, Optional[List[Dict]], str]:
        """
        Get ALL bills from Firefly III (handles pagination automatically)

        Returns:
            Tuple of (success: bool, bills: List[Dict] or None, message: str)
        """
        all_bills = []
        page = 1

        try:
            while True:
                response = requests.get(
                    f'{self.base_url}/api/v1/bills',
                    headers=self.headers,
                    params={'page': page},
                    timeout=10
                )

                if response.status_code != 200:
                    return False, None, f"Failed to get bills: {response.status_code} - {response.text}"

                data = response.json()
                bills = data.get('data', [])

                if not bills:
                    break

                all_bills.extend(bills)

                # Check if there's a next page
                meta = data.get('meta', {})
                pagination = meta.get('pagination', {})
                current_page = pagination.get('current_page', page)
                total_pages = pagination.get('total_pages', 1)

                if current_page >= total_pages:
                    break

                page += 1

            return True, all_bills, f"Retrieved {len(all_bills)} bills"
        except requests.exceptions.RequestException as e:
            return False, None, f"Error retrieving bills: {str(e)}"

    def delete_bill(self, bill_id: int) -> Tuple[bool, str]:
        """
        Delete a bill by ID

        Args:
            bill_id: ID of the bill to delete

        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            response = requests.delete(
                f'{self.base_url}/api/v1/bills/{bill_id}',
                headers=self.headers,
                timeout=10
            )

            if response.status_code == 204:
                return True, f"Bill {bill_id} deleted successfully"
            else:
                return False, f"Failed to delete bill: {response.status_code} - {response.text}"
        except requests.exceptions.RequestException as e:
            return False, f"Error deleting bill: {str(e)}"

    def create_bill(self, bill_data: Dict) -> Tuple[bool, Optional[Dict], str]:
        """
        Create a new bill

        Args:
            bill_data: Bill data dictionary

        Returns:
            Tuple of (success: bool, created_bill: Dict or None, message: str)
        """
        try:
            if 'name' in bill_data:
                payload = bill_data
            else:
                payload = bill_data.get('attributes', bill_data)

            response = requests.post(
                f'{self.base_url}/api/v1/bills',
                headers=self.headers,
                json=payload,
                timeout=10
            )

            if response.status_code == 200 or response.status_code == 201:
                data = response.json()
                created_bill = data.get('data', {})
                bill_id = created_bill.get('id', 'unknown')
                return True, created_bill, f"Bill created successfully (ID: {bill_id})"
            else:
                error_detail = response.text
                try:
                    error_json = response.json()
                    if 'errors' in error_json:
                        errors = error_json['errors']
                        error_msgs = []
                        for field, messages in errors.items():
                            error_msgs.append(f"{field}: {', '.join(messages)}")
                        error_detail = '; '.join(error_msgs)
                    elif 'message' in error_json:
                        error_detail = error_json['message']
                except:
                    pass
                return False, None, f"Failed to create bill: {response.status_code} - {error_detail}"
        except requests.exceptions.RequestException as e:
            return False, None, f"Error creating bill: {str(e)}"

    def update_bill(self, bill_id: int, bill_data: Dict) -> Tuple[bool, Optional[Dict], str]:
        """
        Update an existing bill

        Args:
            bill_id: ID of the bill to update
            bill_data: Bill data dictionary

        Returns:
            Tuple of (success: bool, updated_bill: Dict or None, message: str)
        """
        try:
            if 'name' in bill_data:
                payload = bill_data
            else:
                payload = bill_data.get('attributes', bill_data)

            response = requests.put(
                f'{self.base_url}/api/v1/bills/{bill_id}',
                headers=self.headers,
                json=payload,
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                updated_bill = data.get('data', {})
                return True, updated_bill, f"Bill updated successfully (ID: {bill_id})"
            else:
                error_detail = response.text
                try:
                    error_json = response.json()
                    if 'errors' in error_json:
                        errors = error_json['errors']
                        error_msgs = []
                        for field, messages in errors.items():
                            error_msgs.append(f"{field}: {', '.join(messages)}")
                        error_detail = '; '.join(error_msgs)
                    elif 'message' in error_json:
                        error_detail = error_json['message']
                except:
                    pass
                return False, None, f"Failed to update bill: {response.status_code} - {error_detail}"
        except requests.exceptions.RequestException as e:
            return False, None, f"Error updating bill: {str(e)}"

    # ========== PIGGY BANK MANAGEMENT METHODS ==========

    def get_piggy_banks(self, page: int = 1, limit: int = 50) -> Tuple[bool, Optional[List[Dict]], str]:
        """
        Get piggy banks from Firefly III

        Args:
            page: Page number for pagination
            limit: Number of piggy banks per page

        Returns:
            Tuple of (success: bool, piggy_banks: List[Dict] or None, message: str)
        """
        try:
            response = requests.get(
                f'{self.base_url}/api/v1/piggy-banks',
                headers=self.headers,
                params={'page': page, 'limit': limit},
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                piggy_banks = data.get('data', [])
                return True, piggy_banks, f"Retrieved {len(piggy_banks)} piggy banks"
            else:
                return False, None, f"Failed to get piggy banks: {response.status_code} - {response.text}"
        except requests.exceptions.RequestException as e:
            return False, None, f"Error retrieving piggy banks: {str(e)}"

    def get_all_piggy_banks(self) -> Tuple[bool, Optional[List[Dict]], str]:
        """
        Get ALL piggy banks from Firefly III (handles pagination automatically)

        Returns:
            Tuple of (success: bool, piggy_banks: List[Dict] or None, message: str)
        """
        all_piggy_banks = []
        page = 1

        try:
            while True:
                response = requests.get(
                    f'{self.base_url}/api/v1/piggy-banks',
                    headers=self.headers,
                    params={'page': page},
                    timeout=10
                )

                if response.status_code != 200:
                    return False, None, f"Failed to get piggy banks: {response.status_code} - {response.text}"

                data = response.json()
                piggy_banks = data.get('data', [])

                if not piggy_banks:
                    break

                all_piggy_banks.extend(piggy_banks)

                # Check if there's a next page
                meta = data.get('meta', {})
                pagination = meta.get('pagination', {})
                current_page = pagination.get('current_page', page)
                total_pages = pagination.get('total_pages', 1)

                if current_page >= total_pages:
                    break

                page += 1

            return True, all_piggy_banks, f"Retrieved {len(all_piggy_banks)} piggy banks"
        except requests.exceptions.RequestException as e:
            return False, None, f"Error retrieving piggy banks: {str(e)}"

    def delete_piggy_bank(self, piggy_bank_id: int) -> Tuple[bool, str]:
        """
        Delete a piggy bank by ID

        Args:
            piggy_bank_id: ID of the piggy bank to delete

        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            response = requests.delete(
                f'{self.base_url}/api/v1/piggy-banks/{piggy_bank_id}',
                headers=self.headers,
                timeout=10
            )

            if response.status_code == 204:
                return True, f"Piggy bank {piggy_bank_id} deleted successfully"
            else:
                return False, f"Failed to delete piggy bank: {response.status_code} - {response.text}"
        except requests.exceptions.RequestException as e:
            return False, f"Error deleting piggy bank: {str(e)}"

    def create_piggy_bank(self, piggy_bank_data: Dict) -> Tuple[bool, Optional[Dict], str]:
        """
        Create a new piggy bank

        Args:
            piggy_bank_data: Piggy bank data dictionary

        Returns:
            Tuple of (success: bool, created_piggy_bank: Dict or None, message: str)
        """
        try:
            if 'name' in piggy_bank_data:
                payload = piggy_bank_data
            else:
                payload = piggy_bank_data.get('attributes', piggy_bank_data)

            response = requests.post(
                f'{self.base_url}/api/v1/piggy-banks',
                headers=self.headers,
                json=payload,
                timeout=10
            )

            if response.status_code == 200 or response.status_code == 201:
                data = response.json()
                created_piggy_bank = data.get('data', {})
                piggy_bank_id = created_piggy_bank.get('id', 'unknown')
                return True, created_piggy_bank, f"Piggy bank created successfully (ID: {piggy_bank_id})"
            else:
                error_detail = response.text
                try:
                    error_json = response.json()
                    if 'errors' in error_json:
                        errors = error_json['errors']
                        error_msgs = []
                        for field, messages in errors.items():
                            error_msgs.append(f"{field}: {', '.join(messages)}")
                        error_detail = '; '.join(error_msgs)
                    elif 'message' in error_json:
                        error_detail = error_json['message']
                except:
                    pass
                return False, None, f"Failed to create piggy bank: {response.status_code} - {error_detail}"
        except requests.exceptions.RequestException as e:
            return False, None, f"Error creating piggy bank: {str(e)}"

    def update_piggy_bank(self, piggy_bank_id: int, piggy_bank_data: Dict) -> Tuple[bool, Optional[Dict], str]:
        """
        Update an existing piggy bank

        Args:
            piggy_bank_id: ID of the piggy bank to update
            piggy_bank_data: Piggy bank data dictionary

        Returns:
            Tuple of (success: bool, updated_piggy_bank: Dict or None, message: str)
        """
        try:
            if 'name' in piggy_bank_data:
                payload = piggy_bank_data
            else:
                payload = piggy_bank_data.get('attributes', piggy_bank_data)

            response = requests.put(
                f'{self.base_url}/api/v1/piggy-banks/{piggy_bank_id}',
                headers=self.headers,
                json=payload,
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                updated_piggy_bank = data.get('data', {})
                return True, updated_piggy_bank, f"Piggy bank updated successfully (ID: {piggy_bank_id})"
            else:
                error_detail = response.text
                try:
                    error_json = response.json()
                    if 'errors' in error_json:
                        errors = error_json['errors']
                        error_msgs = []
                        for field, messages in errors.items():
                            error_msgs.append(f"{field}: {', '.join(messages)}")
                        error_detail = '; '.join(error_msgs)
                    elif 'message' in error_json:
                        error_detail = error_json['message']
                except:
                    pass
                return False, None, f"Failed to update piggy bank: {response.status_code} - {error_detail}"
        except requests.exceptions.RequestException as e:
            return False, None, f"Error updating piggy bank: {str(e)}"
