# Firefly III Dashboard

A comprehensive Streamlit-based dashboard for managing and visualizing your Firefly III personal finance data.

This directory provides 20+ interactive dashboard pages for complete financial management:

**Overview & Analytics:**
- 📊 Net Worth Dashboard - Real-time visualization of your financial position
- 📈 Cash Flow Analysis - Track income and expenses over time
- 🌊 Cash Flow Sankey - Interactive D3-based flow visualization

**Budget & Spending:**
- 💰 Budget Overview - Monitor budget usage and limits
- 💵 Budget Management - Create and configure budgets
- 📅 Budget Timeline - Timeline visualization of budget performance

**Categories & Transactions:**
- 🏷️ Categories Overview - Analyze spending by category
- 🔧 Category Management - Create and manage categories
- 🔍 Category Details - Detailed category breakdowns
- 🏷️ Transaction Tags - Tag-based transaction filtering

**Accounts:**
- 🏦 Asset Accounts - Track bank accounts, investments, and assets
- 💰 Revenue Accounts - Monitor income sources
- 💸 Expense Accounts - Analyze expense destinations

**Bills & Recurring:**
- 📅 Bills Management - Track and forecast recurring bills
- 📋 Rules Management - Export, view, delete, and import transaction rules

**Savings & Goals:**
- 🐷 Piggy Banks - Manage savings goals
- 🚀 Savings Forecast - Project future savings and goals

**Data Tools:**
- 📄 CSV Preprocessor - Clean and prepare bank statement CSV files
- 📄 PDF Table Extractor - Extract tables from PDF bank statements
- 📄 CSV Combiner - Merge multiple CSV files

All CSV preprocessing tools, bank statement files, and import configurations are consolidated in one place for easy management.

## Features

### 📊 Net Worth Dashboard
- **Real-time API Integration** - Connect directly to your Firefly III instance
- **Net Worth Calculation** - Automatic calculation by currency
- **Interactive Charts** - Visual breakdown by account type and individual accounts
- **Account Overview** - Detailed table of all asset and liability accounts
- **Export Capabilities** - Download account data as CSV
- **Filtering Options** - Filter by account type, active status, and balance

### 📋 Rules Management
- **Export Rules** - Download all rules as JSON for backup or migration
- **View Rules** - Browse all rules with filtering and search capabilities
- **Delete Rules** - Remove multiple rules with confirmation safeguards
- **Import Rules** - Upload JSON files to bulk import rules
- **Duplicate Detection** - Skip importing rules with matching titles
- **Detailed View** - Inspect triggers, actions, and raw JSON for each rule
- **Batch Operations** - Handle multiple rules at once

### 💵 Budget Management
- **Create Budgets** - Set up new budgets with auto-limits
- **Configure Limits** - Set monthly, quarterly, or yearly budget limits
- **Edit/Delete** - Modify or remove existing budgets
- **Auto-limit Calculation** - Automatically calculate limits from historical spending

### 🔧 Category Management
- **Create Categories** - Add new spending categories
- **Edit Categories** - Update category names and details
- **Delete Categories** - Remove unused categories
- **Category Overview** - View all categories with transaction counts

### 🏦 Account Views
- **Asset Accounts** - Bank accounts, cash, investments overview
- **Revenue Accounts** - Income source tracking and analysis
- **Expense Accounts** - Spending destination tracking
- **Account Balances** - Current balances and account details
- **Interactive Charts** - Visual account breakdowns

### 📅 Bills Management
- **Track Bills** - Monitor recurring bills and payments
- **Bill Forecasting** - Predict upcoming bill payments
- **Payment History** - View past bill payment records
- **Bill Analytics** - Analyze bill payment patterns

### 🐷 Piggy Banks
- **Savings Goals** - Create and track savings targets
- **Progress Tracking** - Monitor savings goal progress
- **Add/Remove Money** - Update piggy bank balances
- **Goal Analytics** - Visualize savings achievements

### 🚀 Savings Forecast
- **Future Projections** - Forecast savings based on current trends
- **Goal Achievement** - Estimate when savings goals will be met
- **Scenario Analysis** - Test different savings scenarios
- **Visual Forecasts** - Interactive charts showing projections

### 📄 PDF Table Extractor
- **Extract Tables** - Pull transaction tables from PDF bank statements
- **Auto-detection** - Automatically detect table structures
- **Export CSV** - Convert extracted tables to CSV format
- **Preview Tables** - Review extracted data before export

### 📄 CSV Combiner
- **Merge Files** - Combine multiple CSV files into one
- **Format Handling** - Smart handling of different CSV formats
- **Deduplication** - Remove duplicate transactions
- **Export Combined** - Download merged CSV file

### 🌊 Cash Flow Sankey
- **D3 Visualization** - Interactive Sankey diagrams for cash flow
- **Income to Expense** - Visual flow from revenue to spending
- **Category Flows** - See money movement between categories
- **Customizable** - Filter by date range and account types

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

1. Create and activate a Python virtual environment:

**Windows (PowerShell):**
```powershell
cd C:\Users\StdUser\Desktop\MyProjects\firefly-iii\pythondashboard
python -m venv venv
.\venv\Scripts\activate.ps1
```

**Linux/macOS/WSL:**
```bash
cd /mnt/c/Users/StdUser/Desktop/MyProjects/firefly-iii/pythondashboard
python3 -m venv venv
source venv/bin/activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure environment (optional):
```bash
# Copy the example environment file
cp .env.example .env

# Edit .env and add your Firefly III credentials
# FIREFLY_URL=http://your-firefly-instance
# FIREFLY_TOKEN=your-personal-access-token
```

**Note:** You can also configure API credentials directly in the dashboard sidebar instead of using `.env`

## Usage

### Starting the Dashboard

**Windows (PowerShell):**
```powershell
cd C:\Users\StdUser\Desktop\MyProjects\firefly-iii\pythondashboard
.\venv\Scripts\activate.ps1
streamlit run .\Home.py
```

**Linux/macOS/WSL:**
```bash
cd /mnt/c/Users/StdUser/Desktop/MyProjects/firefly-iii/pythondashboard
source venv/bin/activate
streamlit run Home.py
```

The dashboard will open in your browser at `http://localhost:8501`

### Navigation

Use the collapsible sidebar to navigate between dashboard pages organized by category:
- **Overview & Analytics** - Net Worth, Cash Flow, Sankey diagrams
- **Budget & Spending** - Budget tracking, management, and timelines
- **Categories & Transactions** - Category analysis, management, and transaction tags
- **Accounts** - Asset, Revenue, and Expense account views
- **Bills & Recurring** - Bills management and transaction rules
- **Savings & Goals** - Piggy banks and savings forecasts
- **Data Tools** - CSV preprocessing, PDF extraction, and file combining

### Using the Rules Management Page

1. **Generate API Token** in Firefly III:
   - Go to your Firefly III instance
   - Navigate to **Options → Profile → OAuth**
   - Under **Personal Access Tokens**, click **Create New Token**
   - Give it a name (e.g., "Streamlit Rules Manager")
   - Copy the generated token (shown only once!)

2. **Connect to Firefly III**:
   - Enter your Firefly III URL in the sidebar (e.g., `http://localhost` or `http://app:8080` for Docker)
   - Paste your Personal Access Token
   - Click **Connect to Firefly III**

3. **Export Rules**:
   - Go to the **View & Export Rules** tab
   - Click **Refresh Rules** to load all rules from Firefly III
   - Review rules in the table (filter by status or search by title)
   - Click **Export All Rules** to download as JSON

4. **Delete Rules**:
   - Go to the **Delete Rules** tab
   - Select rules to delete using the multi-select dropdown
   - Review the selected rules in the preview table
   - Check the confirmation checkbox
   - Click **Delete Selected Rules**

5. **Import Rules**:
   - Go to the **Import Rules** tab
   - Upload a JSON file (previously exported or manually created)
   - Review the preview of rules to import
   - Choose import options:
     - Import as inactive (all rules will be disabled)
     - Skip duplicates (rules with matching titles)
   - Check the confirmation checkbox
   - Click **Import Rules**

**Use Cases:**
- **Backup:** Export rules before making changes
- **Migration:** Move rules between Firefly III instances
- **Bulk Management:** Delete multiple obsolete rules at once
- **Testing:** Import rules as inactive to test before enabling

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

1. Navigate to the **📄 CSV Preprocessor** page using the sidebar navigation

2. Upload a CSV file from the `statements/<BankName>/` folder

3. Review the detected bank type and preprocessing rules

4. The system will validate your CSV structure against the matching import configuration

5. Toggle preprocessing rules on/off as needed

6. Download the processed CSV file

7. Import the processed file into Firefly III using the Data Importer with the matching configuration from `import-configs/`

**Note:** The CSV Preprocessor is integrated into the main dashboard. The standalone `app.py` file is kept for legacy purposes but is no longer the recommended way to run the preprocessor.

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

1. Open `pages/2_📄_CSV_Preprocessor.py`
2. Add bank detection logic based on CSV column names in the bank type detection section
3. Add preprocessing rules similar to existing bank examples (Revolut, T212, AIB, Revolut CC)
4. Follow the compact design patterns (see Design Principles above)
5. Create a matching import configuration JSON file in `import-configs/`
6. Test with sample CSV files

**Legacy Note:** The original standalone `app.py` file contains similar logic but is no longer actively maintained. All new features should be added to the integrated CSV Preprocessor page.

## Project Structure

```
pythondashboard/
├── Home.py                          # Main dashboard home page with navigation
├── app.py                           # Legacy CSV preprocessor (standalone version)
├── firefly_api.py                   # Complete Firefly III API client
├── import_config_validator.py       # Import configuration validation
├── requirements.txt                 # Python dependencies
├── README.md                        # This file
├── .env.example                     # Environment variable template
├── .env                             # Environment configuration (API credentials)
├── dashboard.db                     # SQLite database for caching
│
├── pages/                           # Streamlit dashboard pages (20 pages)
│   ├── 1_📊_Net_Worth.py
│   ├── 2_📄_CSV_Preprocessor.py
│   ├── 3_📈_Cash_Flow.py
│   ├── 4_💰_Budget.py
│   ├── 5_🏷️_Categories.py
│   ├── 6_📋_Rules_Management.py
│   ├── 7_🔧_Category_Management.py
│   ├── 8_💰_Revenue_Accounts.py
│   ├── 9_💸_Expense_Accounts.py
│   ├── 10_🏦_Asset_Accounts.py
│   ├── 11_💵_Budget_Management.py
│   ├── 12_📅_Bills_Management.py
│   ├── 13_🐷_Piggy_Banks_Management.py
│   ├── 14_📅_Budget_Timeline.py
│   ├── 15_🔍_Category_Details.py
│   ├── 16_🚀_Savings_Forecast.py
│   ├── 17_🏷️_Transaction_Tags.py
│   ├── 18_📄_PDF_Table_Extractor.py
│   ├── 19_📄_CSV_Combiner.py
│   └── 20_🌊_Cash_Flow_Sankey.py
│
├── utils/                           # Shared utility modules
│   ├── __init__.py
│   ├── api_client.py                # API client utilities
│   ├── calculations.py              # Financial calculations (budgets, forecasts)
│   ├── charts.py                    # Plotly chart generation
│   ├── config.py                    # Configuration management
│   ├── database.py                  # SQLite database operations
│   ├── d3_sankey_helper.py          # D3.js Sankey diagram generation
│   ├── navigation.py                # Collapsible sidebar navigation
│   └── sankey_helper.py             # Alternative Sankey utilities
│
├── statements/                      # Bank statement CSV files (organized by bank)
│   ├── AIB/                         # AIB bank statements
│   ├── Revolut/                     # Revolut current account exports
│   ├── Revolut_CC/                  # Revolut Credit Card exports (includes pdf/)
│   └── T212/                        # Trading 212 transaction history
│
├── import-configs/                  # Firefly III Data Importer configurations
│   ├── AIB_import_config_v1.json, v2.json
│   ├── Revolut_Personal_import_config_v2.json, v3.json, v4.json
│   ├── Revolut_CC_import_config_v1.json, v2.json, v3.json
│   ├── T212_All_import_config_v6.json
│   └── T212_onlyTransactions_import_config_OK_v5.json
│
├── firefly-configs/                 # Exported Firefly III configurations
│   ├── categories/                  # Category exports
│   ├── rules/                       # Transaction rule exports
│   └── exports_*/                   # Timestamped data exports
│
├── Docs/                            # Technical documentation
│   ├── BUDGET_IMPLEMENTATION.md
│   ├── CASH_FLOW_IMPLEMENTATION.md
│   ├── CATEGORY_IMPLEMENTATION.md
│   ├── D3_SANKEY_MIGRATION.md
│   ├── DASHBOARD_ROADMAP.md
│   ├── DOCKER_BUILD_GUIDE.md
│   ├── DOCKER_IMPLEMENTATION_REVIEW.md
│   ├── FIREFLY_SETUP_GUIDE.md
│   └── SAVINGS_FORECAST_IMPLEMENTATION.md
│
├── .streamlit/                      # Streamlit configuration
│   └── config.toml                  # Custom navigation and toolbar settings
│
└── venv/                            # Python virtual environment (created during setup)
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

## Architecture & Design

### Modular Structure
The dashboard follows a modular architecture with:
- **20 specialized pages** - Each page focuses on a specific financial management aspect
- **Shared utilities** - Common functionality in the `utils/` module
- **API integration** - Complete Firefly III API client (`firefly_api.py`)
- **Database caching** - SQLite database for performance optimization

### Key Components

**Firefly API Client (`firefly_api.py`):**
Complete Python client for Firefly III REST API with methods for:
- Account operations (list, create, update, delete)
- Transaction/journal management
- Budget and category operations
- Rules management
- Bills, piggy banks, and recurring transactions
- Data export functionality

**Utils Module:**
- `calculations.py` - Financial calculations (budgets, forecasts, pro-rata)
- `charts.py` - Plotly chart generation
- `database.py` - SQLite operations
- `d3_sankey_helper.py` - D3.js Sankey visualizations
- `navigation.py` - Collapsible sidebar navigation

### Custom Navigation
The dashboard uses a custom collapsible sidebar navigation (built with `utils/navigation.py`):
- Organized by functional categories
- Collapsible sections for better space utilization
- Persistent state across page navigation
- Dark mode optimized

### Dependencies
The dashboard requires the following Python packages:
- **streamlit** (>=1.35.0) - Web dashboard framework
- **pandas** (2.2.0) - Data manipulation and analysis
- **requests** (2.31.0) - HTTP library for API calls
- **plotly** (5.18.0) - Interactive charting library
- **streamlit-plotly-events** (0.0.6) - Plotly event handling in Streamlit
- **python-dotenv** (1.0.0) - Environment variable management
- **pdfplumber** (0.11.0) - PDF table extraction

## Technical Documentation

Comprehensive implementation guides are available in the `Docs/` directory:
- **BUDGET_IMPLEMENTATION.md** - Budget feature architecture
- **CASH_FLOW_IMPLEMENTATION.md** - Cash flow calculations
- **CATEGORY_IMPLEMENTATION.md** - Category management
- **D3_SANKEY_MIGRATION.md** - Sankey diagram implementation
- **SAVINGS_FORECAST_IMPLEMENTATION.md** - Savings forecasting algorithms
- **DASHBOARD_ROADMAP.md** - Feature roadmap and planned enhancements

## Future Development

The dashboard continues to evolve. Planned enhancements include:
- Advanced reporting and analytics
- Custom dashboard widgets
- Data import automation
- Multi-currency support improvements
- Enhanced forecasting models
- Mobile-responsive layouts
