# Firefly III Dashboard

A Streamlit-based dashboard for preprocessing CSV files before importing into Firefly III, with plans for future analytics and visualization features.

## Features

### CSV Preprocessing (Current)
- Upload CSV files from your bank statements
- Automatically detect bank type (currently supports Revolut)
- Apply preprocessing rules to clean up data:
  - Remove duplicate/internal transactions
  - Filter out unwanted transaction types
  - Clean data for easier import
- Download processed CSV files ready for Firefly III Data Importer

### Future Dashboard Features (Planned)
- Interactive visualizations of Firefly III data
- Account balances and trends
- Budget tracking
- Transaction analytics
- Category spending breakdown
- Net worth over time

## Installation

1. Install dependencies:
```bash
cd pythondashboard
pip install -r requirements.txt
```

## Usage

1. Start the Streamlit dashboard:
```bash
cd pythondashboard
streamlit run app.py
```

2. Open your browser to the URL shown (usually `http://localhost:8501`)

3. Upload a CSV file from the `statements/` folder

4. Review the detected bank type and preprocessing rules

5. Toggle rules on/off as needed

6. Download the processed CSV file

7. Import the processed file into Firefly III using the Data Importer

## Supported Banks

### Revolut
**Preprocessing rules:**
- Removes transactions with Description='Saving vault topup prefunding wallet'
- Removes internal transfers where Product='Deposit' AND Description='To Flexible Cash Funds'

These rules remove duplicate internal accounting entries that would otherwise create incorrect double entries in Firefly III.

## Adding New Bank Rules

To add preprocessing rules for a new bank:

1. Open `app.py`
2. Add bank detection logic based on CSV column names
3. Add preprocessing rules similar to the Revolut example
4. Test with sample CSV files

## Project Structure

```
pythondashboard/
├── app.py              # Main Streamlit application
├── requirements.txt    # Python dependencies
└── README.md          # This file
```

## Future Development

The dashboard is designed to be extensible. Future tabs will include:
- Firefly III API integration
- Real-time budget tracking
- Spending analytics
- Custom reports and visualizations
