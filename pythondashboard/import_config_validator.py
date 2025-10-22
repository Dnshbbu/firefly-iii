"""
Import Config Validator
Validates CSV files against Firefly III Data Importer configuration files
"""

import json
from pathlib import Path
from typing import Dict, List, Tuple, Optional


class ImportConfigValidator:
    """Validates CSV structure against import configuration expectations"""

    # Map bank types to their recommended import config files
    BANK_CONFIG_MAP = {
        "Revolut": "Revolut_Personal_import_config_v4.json",
        "Revolut Credit Card": "Revolut_CC_import_config_v3.json",
        "T212": "T212_All_import_config_v6.json",
        "AIB": "AIB_import_config_v2.json",
    }

    def __init__(self, config_dir: Path):
        """
        Initialize validator with config directory

        Args:
            config_dir: Path to directory containing import config JSON files
        """
        self.config_dir = config_dir

    def get_config_path(self, bank_type: str) -> Optional[Path]:
        """Get the recommended config file path for a bank type"""
        config_filename = self.BANK_CONFIG_MAP.get(bank_type)
        if not config_filename:
            return None

        config_path = self.config_dir / config_filename
        return config_path if config_path.exists() else None

    def load_config(self, config_path: Path) -> Dict:
        """Load import configuration from JSON file"""
        with open(config_path, 'r') as f:
            return json.load(f)

    def get_expected_column_count(self, config: Dict) -> int:
        """Get expected number of columns from config"""
        return len(config.get('roles', []))

    def get_column_roles(self, config: Dict) -> List[str]:
        """Get the role mapping for each column"""
        return config.get('roles', [])

    def validate_csv_structure(
        self,
        csv_columns: List[str],
        bank_type: str
    ) -> Tuple[bool, Dict]:
        """
        Validate CSV columns against expected import config structure

        Args:
            csv_columns: List of column names from the CSV file
            bank_type: Detected bank type

        Returns:
            Tuple of (is_valid, validation_info)
            validation_info contains:
                - config_file: Name of the import config file
                - config_path: Full path to config file
                - expected_columns: Number of expected columns
                - actual_columns: Number of actual columns
                - column_roles: Role mapping from config
                - is_match: True if column counts match
                - extra_columns: Columns in CSV but not needed
                - missing_columns: Columns needed but not in CSV
        """
        config_path = self.get_config_path(bank_type)

        if not config_path:
            return False, {
                'error': f'No import config found for {bank_type}',
                'config_file': None,
                'expected_columns': None,
                'actual_columns': len(csv_columns),
            }

        config = self.load_config(config_path)
        expected_count = self.get_expected_column_count(config)
        actual_count = len(csv_columns)
        column_roles = self.get_column_roles(config)

        is_match = expected_count == actual_count

        # Determine extra or missing columns
        extra_columns = []
        missing_count = 0

        if actual_count > expected_count:
            # CSV has more columns than expected
            extra_columns = csv_columns[expected_count:]
        elif actual_count < expected_count:
            # CSV has fewer columns than expected
            missing_count = expected_count - actual_count

        validation_info = {
            'config_file': config_path.name,
            'config_path': str(config_path),
            'expected_columns': expected_count,
            'actual_columns': actual_count,
            'column_roles': column_roles,
            'is_match': is_match,
            'extra_columns': extra_columns,
            'missing_count': missing_count,
            'csv_columns': csv_columns,
        }

        return is_match, validation_info

    def get_normalized_columns(
        self,
        csv_columns: List[str],
        bank_type: str
    ) -> Tuple[List[str], str]:
        """
        Get normalized column list based on import config expectations

        Args:
            csv_columns: Original CSV columns
            bank_type: Detected bank type

        Returns:
            Tuple of (normalized_columns, normalization_summary)
        """
        _, validation_info = self.validate_csv_structure(csv_columns, bank_type)

        if validation_info.get('error'):
            return csv_columns, validation_info['error']

        expected_count = validation_info['expected_columns']
        actual_count = validation_info['actual_columns']

        if validation_info['is_match']:
            return csv_columns, "No normalization needed - columns match exactly"

        normalized = csv_columns[:expected_count]  # Take first N columns

        summary_parts = []
        if validation_info['extra_columns']:
            summary_parts.append(
                f"Removed {len(validation_info['extra_columns'])} extra column(s): "
                f"{', '.join(validation_info['extra_columns'])}"
            )

        if validation_info['missing_count'] > 0:
            # Add placeholder columns
            for i in range(validation_info['missing_count']):
                normalized.append(f'_placeholder_{i+1}')
            summary_parts.append(
                f"Added {validation_info['missing_count']} placeholder column(s)"
            )

        return normalized, " | ".join(summary_parts)
