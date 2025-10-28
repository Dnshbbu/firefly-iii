"""Database utilities for Firefly III Dashboard

SQLite database for persisting user data across sessions.
"""

import sqlite3
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Any
import os


class Database:
    """SQLite database manager for dashboard data"""

    def __init__(self, db_path: str = None):
        """Initialize database connection

        Args:
            db_path: Path to SQLite database file. Defaults to pythondashboard/dashboard.db
        """
        if db_path is None:
            # Default to pythondashboard directory
            base_dir = Path(__file__).parent.parent
            db_path = base_dir / "dashboard.db"

        self.db_path = str(db_path)
        self.init_database()

    def get_connection(self):
        """Get database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Enable column access by name
        return conn

    def init_database(self):
        """Initialize database tables"""
        conn = self.get_connection()
        cursor = conn.cursor()

        # Create savings table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS savings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                type TEXT NOT NULL,
                currency TEXT NOT NULL DEFAULT 'EUR',
                principal REAL NOT NULL,
                rate REAL NOT NULL,
                start_date TEXT NOT NULL,
                maturity_date TEXT NOT NULL,
                compounding_frequency INTEGER NOT NULL,
                monthly_contribution REAL DEFAULT 0.0,
                total_contributions REAL DEFAULT 0.0,
                maturity_value REAL NOT NULL,
                interest_earned REAL NOT NULL,
                color_index INTEGER NOT NULL,
                color_data TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)

        # Add new columns if they don't exist (migration)
        try:
            cursor.execute("ALTER TABLE savings ADD COLUMN has_payout INTEGER DEFAULT 0")
        except sqlite3.OperationalError:
            pass  # Column already exists

        try:
            cursor.execute("ALTER TABLE savings ADD COLUMN payout_frequency INTEGER DEFAULT 4")
        except sqlite3.OperationalError:
            pass  # Column already exists

        try:
            cursor.execute("ALTER TABLE savings ADD COLUMN notes TEXT DEFAULT ''")
        except sqlite3.OperationalError:
            pass  # Column already exists

        conn.commit()
        conn.close()

    # ===== SAVINGS CRUD OPERATIONS =====

    def add_saving(self, saving_data: Dict[str, Any]) -> int:
        """Add a new saving to database

        Args:
            saving_data: Dictionary containing saving information

        Returns:
            ID of newly created saving
        """
        conn = self.get_connection()
        cursor = conn.cursor()

        now = datetime.now().isoformat()

        cursor.execute("""
            INSERT INTO savings (
                name, type, currency, principal, rate,
                start_date, maturity_date, compounding_frequency,
                monthly_contribution, total_contributions,
                maturity_value, interest_earned,
                color_index, color_data, has_payout, payout_frequency, notes,
                created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            saving_data['name'],
            saving_data['type'],
            saving_data.get('currency', 'EUR'),
            saving_data['principal'],
            saving_data['rate'],
            saving_data['start_date'].isoformat() if isinstance(saving_data['start_date'], datetime) else saving_data['start_date'],
            saving_data['maturity_date'].isoformat() if isinstance(saving_data['maturity_date'], datetime) else saving_data['maturity_date'],
            saving_data['compounding_frequency'],
            saving_data.get('monthly_contribution', 0.0),
            saving_data.get('total_contributions', 0.0),
            saving_data['maturity_value'],
            saving_data['interest_earned'],
            saving_data.get('color_index', 0),
            json.dumps(saving_data['color']),
            1 if saving_data.get('has_payout', False) else 0,
            saving_data.get('payout_frequency', 4),
            saving_data.get('notes', ''),
            now,
            now
        ))

        saving_id = cursor.lastrowid
        conn.commit()
        conn.close()

        return saving_id

    def get_all_savings(self) -> List[Dict[str, Any]]:
        """Get all savings from database

        Returns:
            List of saving dictionaries
        """
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM savings ORDER BY created_at ASC
        """)

        rows = cursor.fetchall()
        conn.close()

        savings = []
        for row in rows:
            saving = {
                'id': row['id'],
                'name': row['name'],
                'type': row['type'],
                'currency': row['currency'],
                'principal': row['principal'],
                'rate': row['rate'],
                'start_date': datetime.fromisoformat(row['start_date']),
                'maturity_date': datetime.fromisoformat(row['maturity_date']),
                'compounding_frequency': row['compounding_frequency'],
                'monthly_contribution': row['monthly_contribution'],
                'total_contributions': row['total_contributions'],
                'maturity_value': row['maturity_value'],
                'interest_earned': row['interest_earned'],
                'color_index': row['color_index'],
                'color': json.loads(row['color_data']),
                'has_payout': bool(row['has_payout']) if 'has_payout' in row.keys() else False,
                'payout_frequency': row['payout_frequency'] if 'payout_frequency' in row.keys() else 4,
                'notes': row['notes'] if 'notes' in row.keys() else '',
                'created_at': row['created_at'],
                'updated_at': row['updated_at']
            }
            savings.append(saving)

        return savings

    def get_saving_by_id(self, saving_id: int) -> Optional[Dict[str, Any]]:
        """Get a specific saving by ID

        Args:
            saving_id: ID of the saving

        Returns:
            Saving dictionary or None if not found
        """
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM savings WHERE id = ?", (saving_id,))
        row = cursor.fetchone()
        conn.close()

        if row is None:
            return None

        return {
            'id': row['id'],
            'name': row['name'],
            'type': row['type'],
            'currency': row['currency'],
            'principal': row['principal'],
            'rate': row['rate'],
            'start_date': datetime.fromisoformat(row['start_date']),
            'maturity_date': datetime.fromisoformat(row['maturity_date']),
            'compounding_frequency': row['compounding_frequency'],
            'monthly_contribution': row['monthly_contribution'],
            'total_contributions': row['total_contributions'],
            'maturity_value': row['maturity_value'],
            'interest_earned': row['interest_earned'],
            'color_index': row['color_index'],
            'color': json.loads(row['color_data']),
            'has_payout': bool(row['has_payout']) if 'has_payout' in row.keys() else False,
            'payout_frequency': row['payout_frequency'] if 'payout_frequency' in row.keys() else 4,
            'notes': row['notes'] if 'notes' in row.keys() else '',
            'created_at': row['created_at'],
            'updated_at': row['updated_at']
        }

    def update_saving(self, saving_id: int, saving_data: Dict[str, Any]) -> bool:
        """Update an existing saving

        Args:
            saving_id: ID of the saving to update
            saving_data: Dictionary containing updated saving information

        Returns:
            True if update successful, False otherwise
        """
        conn = self.get_connection()
        cursor = conn.cursor()

        now = datetime.now().isoformat()

        cursor.execute("""
            UPDATE savings SET
                name = ?, type = ?, currency = ?, principal = ?, rate = ?,
                start_date = ?, maturity_date = ?, compounding_frequency = ?,
                monthly_contribution = ?, total_contributions = ?,
                maturity_value = ?, interest_earned = ?,
                color_index = ?, color_data = ?, has_payout = ?, payout_frequency = ?, notes = ?,
                updated_at = ?
            WHERE id = ?
        """, (
            saving_data['name'],
            saving_data['type'],
            saving_data.get('currency', 'EUR'),
            saving_data['principal'],
            saving_data['rate'],
            saving_data['start_date'].isoformat() if isinstance(saving_data['start_date'], datetime) else saving_data['start_date'],
            saving_data['maturity_date'].isoformat() if isinstance(saving_data['maturity_date'], datetime) else saving_data['maturity_date'],
            saving_data['compounding_frequency'],
            saving_data.get('monthly_contribution', 0.0),
            saving_data.get('total_contributions', 0.0),
            saving_data['maturity_value'],
            saving_data['interest_earned'],
            saving_data.get('color_index', 0),
            json.dumps(saving_data['color']),
            1 if saving_data.get('has_payout', False) else 0,
            saving_data.get('payout_frequency', 4),
            saving_data.get('notes', ''),
            now,
            saving_id
        ))

        success = cursor.rowcount > 0
        conn.commit()
        conn.close()

        return success

    def delete_saving(self, saving_id: int) -> bool:
        """Delete a saving from database

        Args:
            saving_id: ID of the saving to delete

        Returns:
            True if delete successful, False otherwise
        """
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("DELETE FROM savings WHERE id = ?", (saving_id,))

        success = cursor.rowcount > 0
        conn.commit()
        conn.close()

        return success

    def delete_all_savings(self) -> int:
        """Delete all savings from database

        Returns:
            Number of savings deleted
        """
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("DELETE FROM savings")

        count = cursor.rowcount
        conn.commit()
        conn.close()

        return count

    def get_savings_count(self) -> int:
        """Get total count of savings

        Returns:
            Number of savings in database
        """
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) as count FROM savings")
        result = cursor.fetchone()
        conn.close()

        return result['count']


# Singleton instance
_db_instance = None


def get_database() -> Database:
    """Get singleton database instance"""
    global _db_instance
    if _db_instance is None:
        _db_instance = Database()
    return _db_instance
