import streamlit as st

# Page configuration
st.set_page_config(
    page_title="Firefly III Dashboard",
    page_icon="🔥",
    layout="wide"
)

# Compact CSS styling for dark mode
st.markdown("""
<style>
    /* Reduce padding and margins */
    .block-container {
        padding-top: 1rem;
        padding-bottom: 0rem;
        padding-left: 2rem;
        padding-right: 2rem;
    }

    /* Compact headers */
    h1 {
        padding-top: 0rem;
        padding-bottom: 0.5rem;
        font-size: 2rem;
    }

    h2 {
        padding-top: 0.5rem;
        padding-bottom: 0.25rem;
        font-size: 1.5rem;
    }

    h3 {
        padding-top: 0.25rem;
        padding-bottom: 0.25rem;
        font-size: 1.2rem;
    }
</style>
""", unsafe_allow_html=True)

st.title("🔥 Firefly III Dashboard")

st.markdown("""
Welcome to the Firefly III Dashboard! This application provides tools for managing your Firefly III data.

## Available Tools

### 📊 Net Worth Dashboard
View your overall financial position with:
- Total net worth calculation
- Asset breakdown by account type
- Interactive charts and visualizations
- Account balance tracking

### 📈 Cash Flow Dashboard
Analyze your income and expenses over time:
- Income vs. expenses visualization
- Category spending breakdown
- Income sources analysis
- Cash flow trends and waterfall charts
- Customizable date ranges and aggregation periods
- Transaction filtering and export

### 💰 Budget Dashboard
Track and manage your budgets effectively:
- Budget vs. actual spending comparison
- Budget utilization gauges and progress bars
- Burn rate analysis and projections
- Over/under budget alerts
- Individual budget performance tracking
- End-of-period spending forecasts

### 📄 CSV Preprocessor
Prepare bank statement CSV files for import:
- Automatic bank type detection
- Data cleaning and standardization
- Duplicate transaction removal
- Format conversion for Firefly III import

---

Use the sidebar to navigate between different tools.
""")

st.info("💡 **Tip:** Configure your Firefly III API connection in the Net Worth Dashboard to get started!")
