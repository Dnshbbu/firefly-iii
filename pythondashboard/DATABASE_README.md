# Database Documentation

## Overview

The Firefly III Dashboard now uses SQLite for persistent data storage. This means your savings data is automatically saved and will persist across sessions.

## Database Location

The database file is stored at:
```
pythondashboard/dashboard.db
```

## Features

### Automatic Persistence
- All savings are automatically saved to the database
- Data persists across app restarts
- No manual save button needed

### CRUD Operations
- **Create**: Add new savings via the sidebar form
- **Read**: Automatically loads all savings on page load
- **Update**: Changes are saved automatically (future feature)
- **Delete**: Remove individual savings or clear all

## Database Schema

### Savings Table

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key (auto-increment) |
| name | TEXT | Saving name |
| type | TEXT | Type (Fixed Deposit, Recurring, etc.) |
| currency | TEXT | Currency code (EUR, INR, USD, GBP) |
| principal | REAL | Initial investment amount |
| rate | REAL | Annual interest rate (decimal) |
| start_date | TEXT | Start date (ISO format) |
| maturity_date | TEXT | Maturity date (ISO format) |
| compounding_frequency | INTEGER | Compounding frequency (1=Annual, 2=Semi, 4=Quarterly, 12=Monthly) |
| monthly_contribution | REAL | Monthly contribution amount |
| total_contributions | REAL | Total contributions over period |
| maturity_value | REAL | Projected maturity value |
| interest_earned | REAL | Total interest earned |
| color_index | INTEGER | Index for color assignment |
| color_data | TEXT | JSON color data |
| created_at | TEXT | Creation timestamp |
| updated_at | TEXT | Last update timestamp |

## Usage

### In Code

```python
from utils.database import get_database

# Get database instance
db = get_database()

# Add a saving
saving_id = db.add_saving(saving_data)

# Get all savings
savings = db.get_all_savings()

# Delete a saving
db.delete_saving(saving_id)

# Clear all savings
count = db.delete_all_savings()

# Get count
count = db.get_savings_count()
```

## Database Management

### Backup
Simply copy the `dashboard.db` file to create a backup:
```bash
cp pythondashboard/dashboard.db pythondashboard/dashboard_backup.db
```

### Reset
To reset all data, delete the database file:
```bash
rm pythondashboard/dashboard.db
```
The database will be automatically recreated on next run.

### Export
Use the built-in export features in the UI:
- **CSV Export**: Download savings as CSV
- **JSON Export**: Download savings as JSON

### Import
To import existing data, use the sidebar form to add savings individually.

## Technical Details

### Connection Management
- Database uses singleton pattern for connection management
- Row factory enabled for dict-like access to results
- Automatic table creation on first run

### Thread Safety
SQLite in Python is generally thread-safe with default settings. Each connection is created per operation and closed after use.

### Performance
- SQLite is highly efficient for this use case (< 1000 records)
- Indexed by primary key for fast lookups
- All queries use parameterized statements for security

## Migration Notes

### From Session State to Database

The migration from session state to database storage includes:

1. **Automatic Loading**: Savings load from database on page start
2. **Database ID**: Each saving now has a unique `id` field
3. **Timestamps**: Each saving tracks creation and update times
4. **Persistence**: Data survives page refreshes and app restarts

### Backward Compatibility

Old savings data in session state is not migrated. Users will need to re-add their savings after the update.

## Troubleshooting

### Database Locked Error
If you see "database is locked" errors:
- Close other connections to the database
- Restart the Streamlit app

### Missing Database File
If the database file is missing, it will be automatically recreated with an empty schema.

### Corrupt Database
If the database becomes corrupt:
1. Backup your data (export to JSON/CSV if possible)
2. Delete `dashboard.db`
3. Restart the app
4. Re-import your data

## Future Enhancements

Potential future improvements:
- [ ] Edit existing savings functionality
- [ ] Import from CSV/JSON
- [ ] Database version migration system
- [ ] Backup/restore functionality in UI
- [ ] Multi-user support with user tables
- [ ] Data encryption for sensitive information
