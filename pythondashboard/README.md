# Firefly III Dashboard

A comprehensive Streamlit-based dashboard for managing and visualizing your Firefly III personal finance data.

This directory provides two main tools:
1. **Net Worth Dashboard** - Real-time visualization of your financial position via Firefly III API
2. **CSV Preprocessor** - Clean and prepare bank statement CSV files for import

All CSV preprocessing tools, bank statement files, and import configurations are consolidated in one place for easy management.

## Features

### 📊 Net Worth Dashboard (NEW!)
- **Real-time API Integration** - Connect directly to your Firefly III instance
- **Net Worth Calculation** - Automatic calculation by currency
- **Interactive Charts** - Visual breakdown by account type and individual accounts
- **Account Overview** - Detailed table of all asset and liability accounts
- **Export Capabilities** - Download account data as CSV
- **Filtering Options** - Filter by account type, active status, and balance

### 📄 CSV Preprocessing
- Upload CSV files from your bank statements
- Automatically detect bank type (currently supports Revolut, Revolut Credit Card, T212, and AIB)
- Apply preprocessing rules to clean up data:
  - Remove duplicate/internal transactions
  - Filter out unwanted transaction types
  - Format dates to match Firefly III import configurations
  - Clean data for easier import
- Download processed CSV files ready for Firefly III Data Importer

## Installation

1. Install dependencies:
```bash
cd pythondashboard
pip install -r requirements.txt
```

## Usage

### Starting the Dashboard

1. Start the Streamlit application:
```bash
cd pythondashboard
streamlit run Home.py
```

2. Open your browser to the URL shown (usually `http://localhost:8501`)

3. Use the sidebar to navigate between:
   - **📊 Net Worth** - View your financial dashboard
   - **📄 CSV Preprocessor** - Prepare CSV files for import

### Using the Net Worth Dashboard

1. **Generate API Token** in Firefly III:
   - Go to your Firefly III instance (e.g., `http://192.168.0.242`)
   - Navigate to **Profile → OAuth → Personal Access Tokens**
   - Click **Create New Token**
   - Give it a name (e.g., "Streamlit Dashboard")
   - Copy the generated token

2. **Configure Connection** in the sidebar:
   - Enter your Firefly III URL (e.g., `http://192.168.0.242`)
   - Paste the API token
   - Click **Connect**

3. **View Your Data**:
   - Net worth summary by currency
   - Account type breakdown (pie chart)
   - Individual account balances (bar chart)
   - Detailed account table with filters
   - Export data to CSV

### Preprocessing CSV Files

1. Navigate to the **CSV Preprocessor** page using the sidebar

2. Upload a CSV file from the `statements/<BankName>/` folder

3. Review the detected bank type and preprocessing rules

5. Toggle rules on/off as needed

6. Download the processed CSV file

7. Import the processed file into Firefly III using the Data Importer with the matching configuration from `import-configs/`

### Importing into Firefly III

1. Open Firefly III Data Importer at `http://localhost:81`
2. Upload the processed CSV file
3. Upload the corresponding import configuration from `import-configs/` (e.g., `Revolut_CC_import_config_v1.json`)
4. Review mappings and confirm import

## Supported Banks

### Revolut (Current Account)
**CSV Format:** Contains columns `Type`, `Product`, `Started Date`, `Completed Date`, `Description`, `Amount`, `Currency`

**Preprocessing rules:**
- Removes transactions with Description='Saving vault topup prefunding wallet'
- Removes internal transfers where Product='Deposit' AND Description='To Flexible Cash Funds'
- Removes all transactions where Product='Savings'
- Converts 'Started Date' and 'Completed Date' from `YYYY-MM-DD HH:MM:SS` to `m/d/Y` format (e.g., 9/13/2025)

These rules remove duplicate internal accounting entries and savings account movements that are tracked separately, and format dates correctly for Firefly III import.

### Revolut Credit Card
**CSV Format:** Contains columns `Type`, `Started Date`, `Completed Date`, `Description`, `Amount`, `Fee`, `Balance`

**Preprocessing rules:**
- Converts 'Started Date' and 'Completed Date' from `YYYY-MM-DD HH:MM:SS` to `m/d/Y` format (e.g., 9/13/2025)

The Revolut Credit Card export has a different structure than the current account export (no Product/Currency columns, includes Fee/Balance instead). The date formatting ensures compatibility with Firefly III import configurations.

### Trading 212 (T212)
**CSV Format:** Contains columns `Action`, `Time`, `ID`, `Total`, `Currency (Total)`

**Preprocessing rules:**
- Ensures 'Time' column is in `m/d/Y` format (e.g., 9/13/2025)

T212 exports typically already have the correct date format, but this ensures consistency.

### AIB (Allied Irish Banks)
**CSV Format:** Contains columns `Posted Account`, `Posted Transactions Date`, `Debit Amount`, `Credit Amount`

**Preprocessing rules:**
- Converts 'Posted Transactions Date' from `dd/mm/yyyy` to `d/m/Y` format (e.g., 13/9/2025)

This removes leading zeros from dates to match the format expected by Firefly III import configurations.

## Design Principles

### Compact UI Design

The Streamlit app follows a **compact design philosophy** to maximize information density and minimize scrolling:

**Implementation:**
- Custom CSS reduces padding, margins, and spacing throughout the app
- Dataframes have fixed heights with scrolling for better space utilization
- Collapsible expanders for secondary information (Applied Rules, Removed Rows)
- Concise labels and messaging
- Smaller font sizes for headers and data tables

**Why Compact Design:**
- See more data rows at once without scrolling
- Better overview of preprocessing results
- Faster review and validation workflow
- Professional, dashboard-like appearance
- Efficient use of screen real estate

**When Extending the App:**
When adding new features or bank types, maintain the compact design by:
- Using `st.markdown("**Title**")` instead of `st.subheader()` for minor sections
- Adding `height` parameter to dataframes (e.g., `height=400`)
- Putting detailed information in `st.expander()` components
- Using short, clear metric labels
- Following the existing CSS styling patterns

## Adding New Bank Rules

To add preprocessing rules for a new bank:

1. Open `app.py`
2. Add bank detection logic based on CSV column names (around line 130)
3. Add preprocessing rules similar to existing bank examples
4. Follow the compact design patterns (see Design Principles above)
5. Test with sample CSV files

## Project Structure

```
pythondashboard/
├── app.py                    # Main Streamlit application
├── requirements.txt          # Python dependencies
├── README.md                 # This file
├── statements/               # Bank statement CSV files (organized by bank)
│   ├── AIB/                  # AIB bank statements
│   ├── Revolut/              # Revolut current account exports
│   ├── Revolut_CC/           # Revolut Credit Card exports
│   └── T212/                 # Trading 212 transaction history
└── import-configs/           # Firefly III Data Importer configurations
    ├── AIB_import_config_v1.json
    ├── Revolut_import_config_v1.json
    ├── Revolut_import_config_v2.json
    ├── Revolut_CC_import_config_v1.json
    ├── T212_import_config_v3.json
    ├── T212_import_config_v4.json
    ├── T212_import_config_v5_OK.json
    └── T212_import_config_v6.json
```

### Import Configurations

The `import-configs/` directory contains JSON configuration files for the Firefly III Data Importer. These files define:
- CSV column mappings to Firefly III transaction fields
- Date formats and delimiters
- Default accounts for imports
- Duplicate detection methods
- Custom tags for imported transactions

**Configuration Structure:**
- `roles` - Maps CSV columns to transaction fields (e.g., `date_transaction`, `description`, `amount`)
- `default_account` - Account ID to import transactions into
- `delimiter` - CSV delimiter (comma, semicolon, tab)
- `date` - Date format string
- `custom_tag` - Tag to add to all imported transactions
- `duplicate_detection_method` - How to detect duplicates (none, cell, row)

### Bank Statements

The `statements/` directory is organized by bank/service for easy file management:
- Export CSV files from your bank/service
- Save to the appropriate `statements/<BankName>/` subdirectory
- Use the Streamlit preprocessor to clean the files
- Processed files are typically named with `_processed.csv` suffix

## Future Development

The dashboard is designed to be extensible. Future tabs will include:
- Firefly III API integration
- Real-time budget tracking
- Spending analytics
- Custom reports and visualizations
