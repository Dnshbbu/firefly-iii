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
