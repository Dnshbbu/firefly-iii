import streamlit as st
import pandas as pd
import os
from pathlib import Path
from datetime import datetime
import sys

# Add parent directory to path to import utils
sys.path.append(str(Path(__file__).parent.parent))
from utils.navigation import render_sidebar_navigation

# Page configuration
st.set_page_config(
    page_title="Firefly III CSV Preprocessor",
    page_icon="🔥",
    layout="wide"
)

# Render custom navigation
render_sidebar_navigation()

# Ultra-compact CSS styling - DENSE dashboard
st.markdown("""
<style>
    /* Minimal padding for maximum density */
    .block-container {
        padding-top: 3rem !important;
        padding-bottom: 0rem !important;
        padding-left: 1rem !important;
        padding-right: 1rem !important;
        max-width: 100% !important;
    }

    /* Compact headers */
    h1 {
        padding-top: 0rem !important;
        padding-bottom: 0.3rem !important;
        margin-top: 0 !important;
        margin-bottom: 0.3rem !important;
        font-size: 1.8rem !important;
    }
    h2 {
        padding-top: 0.2rem !important;
        padding-bottom: 0.2rem !important;
        margin-top: 0.3rem !important;
        margin-bottom: 0.3rem !important;
        font-size: 1.3rem !important;
    }
    h3 {
        padding-top: 0.1rem !important;
        padding-bottom: 0.1rem !important;
        margin-top: 0.2rem !important;
        margin-bottom: 0.2rem !important;
        font-size: 1.1rem !important;
    }

    /* Compact metrics */
    [data-testid="stMetricValue"] {
        font-size: 1.3rem !important;
    }
    [data-testid="stMetricLabel"] {
        font-size: 0.75rem !important;
        margin-bottom: 0 !important;
    }
    [data-testid="stMetric"] {
        padding: 0.3rem !important;
    }

    /* Compact dataframes */
    .dataframe {
        font-size: 0.75rem !important;
    }

    /* Reduce spacing between elements */
    .element-container {
        margin-bottom: 0.2rem !important;
    }

    /* Compact dividers */
    hr {
        margin-top: 0.3rem !important;
        margin-bottom: 0.3rem !important;
    }

    /* Compact file uploader */
    [data-testid="stFileUploader"] {
        padding: 0.3rem !important;
    }

    /* Compact checkbox labels */
    .stCheckbox {
        margin-bottom: 0.2rem !important;
    }

    /* Compact info/warning boxes */
    .stAlert {
        padding: 0.3rem !important;
        margin-bottom: 0.3rem !important;
        font-size: 0.85rem !important;
    }

    /* Compact expanders */
    .streamlit-expanderHeader {
        font-size: 0.9rem !important;
        padding: 0.3rem !important;
    }

    /* Compact buttons */
    .stButton button {
        padding: 0.25rem 0.75rem !important;
        font-size: 0.85rem !important;
    }

    /* Compact download button */
    .stDownloadButton {
        margin-top: 0.3rem !important;
    }
</style>
""", unsafe_allow_html=True)

st.title("🔥 Firefly III CSV Preprocessor")
st.markdown("---")

# Get the statements folder path (within pythondashboard directory)
STATEMENTS_FOLDER = Path(__file__).parent / "statements"

st.subheader("CSV Preprocessing")

# File uploader
uploaded_file = st.file_uploader("Upload CSV file from your bank", type=['csv'])

if uploaded_file is not None:
    # Read the CSV file
    try:
        df = pd.read_csv(uploaded_file)
        original_row_count = len(df)

        st.markdown(f"**Original Data** ({original_row_count} rows)")
        st.dataframe(df, width='stretch', height=250)

        # Detect bank type based on columns
        bank_type = "Unknown"

        # Get column names (stripped for comparison)
        columns = df.columns.tolist()
        columns_stripped = [col.strip() for col in columns]

        if all(col in columns for col in ['Type', 'Started Date', 'Completed Date', 'Description', 'Amount', 'Fee', 'Balance']) and 'Product' not in columns:
            bank_type = "Revolut Credit Card"
        elif all(col in columns for col in ['Type', 'Product', 'Started Date', 'Completed Date', 'Description', 'Amount', 'Currency']):
            bank_type = "Revolut"
        elif all(col in columns for col in ['Action', 'Time', 'ID', 'Total', 'Currency (Total)']):
            bank_type = "T212"
        elif all(col in columns_stripped for col in ['Posted Account', 'Posted Transactions Date', 'Debit Amount', 'Credit Amount']):
            bank_type = "AIB"
            # Find the actual column name (with or without leading space)
            aib_date_col = [col for col in columns if col.strip() == 'Posted Transactions Date'][0]

        st.info(f"Bank: **{bank_type}**")

        # Preprocessing options
        st.markdown("**Preprocessing Rules**")

        if bank_type == "Revolut":

            rule1 = st.checkbox(
                "Remove 'Saving vault topup prefunding wallet' transactions",
                value=True,
                help="Removes lines where Description equals 'Saving vault topup prefunding wallet'"
            )

            rule2 = st.checkbox(
                "Remove Deposit transfers to Flexible Cash Funds",
                value=True,
                help="Removes lines where Product='Deposit' AND Description='To Flexible Cash Funds'"
            )

            rule3 = st.checkbox(
                "Remove Savings transactions",
                value=True,
                help="Removes lines where Product='Savings'"
            )

            rule4 = st.checkbox(
                "Format dates to m/d/Y (e.g., 9/13/2025)",
                value=True,
                help="Converts 'Started Date' and 'Completed Date' columns to m/d/Y format for Firefly III import"
            )

            # Apply preprocessing
            processed_df = df.copy()
            removed_rows_list = []
            removed_rows = []
            applied_rules = []

            if rule1:
                mask = processed_df['Description'] == 'Saving vault topup prefunding wallet'
                removed_count = mask.sum()
                removed_rows.append(f"Rule 1: Removed {removed_count} 'Saving vault topup prefunding wallet' rows")
                # Collect removed rows
                removed_rows_list.append(processed_df[mask].copy().assign(Reason="Rule 1: Saving vault topup"))
                processed_df = processed_df[~mask]

            if rule2:
                mask = (processed_df['Product'] == 'Deposit') & (processed_df['Description'] == 'To Flexible Cash Funds')
                removed_count = mask.sum()
                removed_rows.append(f"Rule 2: Removed {removed_count} 'Deposit' + 'To Flexible Cash Funds' rows")
                # Collect removed rows
                removed_rows_list.append(processed_df[mask].copy().assign(Reason="Rule 2: Deposit to Flexible Cash"))
                processed_df = processed_df[~mask]

            if rule3:
                mask = processed_df['Product'] == 'Savings'
                removed_count = mask.sum()
                removed_rows.append(f"Rule 3: Removed {removed_count} 'Savings' product rows")
                # Collect removed rows
                removed_rows_list.append(processed_df[mask].copy().assign(Reason="Rule 3: Savings product"))
                processed_df = processed_df[~mask]

            if rule4:
                # Convert dates from YYYY-MM-DD HH:MM:SS to m/d/Y H:M:S
                # Adds 04:00:00 time to avoid timezone conversion issues
                def convert_date(date_str):
                    try:
                        # Try parsing with time
                        dt = pd.to_datetime(date_str)
                        # Format as m/d/Y H:M:S with 04:00:00 time to avoid midnight UTC issues
                        return f"{dt.month}/{dt.day}/{dt.year} 4:00:00"
                    except:
                        return date_str

                processed_df['Started Date'] = processed_df['Started Date'].apply(convert_date)
                processed_df['Completed Date'] = processed_df['Completed Date'].apply(convert_date)
                applied_rules.append("Date formatting: Converted 'Started Date' and 'Completed Date' to m/d/Y H:M:S format with 04:00:00 time")

            # Show results
            st.markdown("**Results**")

            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Original", original_row_count)
            with col2:
                st.metric("Removed", original_row_count - len(processed_df))
            with col3:
                st.metric("Final", len(processed_df))

            if removed_rows or applied_rules:
                with st.expander("Applied Rules", expanded=False):
                    for rule in removed_rows + applied_rules:
                        st.markdown(f"- {rule}")

            # Show removed rows table if any rows were removed
            if removed_rows_list:
                removed_df = pd.concat(removed_rows_list, ignore_index=True)
                with st.expander(f"Removed Rows ({len(removed_df)})", expanded=False):
                    st.dataframe(removed_df, width='stretch', height=300)

            st.markdown("**Processed Data**")
            st.dataframe(processed_df, width='stretch', height=400)

            # Download button
            csv = processed_df.to_csv(index=False)

            # Generate output filename
            original_filename = uploaded_file.name
            if original_filename.endswith('.csv'):
                base_name = original_filename[:-4]
                output_filename = f"{base_name}_processed.csv"
            else:
                output_filename = f"{original_filename}_processed.csv"

            st.download_button(
                label="Download Processed CSV",
                data=csv,
                file_name=output_filename,
                mime='text/csv',
                use_container_width=True
            )

        elif bank_type == "T212":

            rule1 = st.checkbox(
                "Format dates to m/d/Y (e.g., 9/13/2025)",
                value=True,
                help="Converts 'Time' column to m/d/Y format for Firefly III import (Note: T212 dates are typically already in correct format)"
            )

            # Apply preprocessing
            processed_df = df.copy()
            applied_rules = []

            if rule1:
                # Convert dates - they should already be in m/d/Y format, but ensure consistency
                # Adds 04:00:00 time to avoid timezone conversion issues
                def convert_date(date_str):
                    try:
                        dt = pd.to_datetime(date_str)
                        # Format as m/d/Y H:M:S with 04:00:00 time to avoid midnight UTC issues
                        return f"{dt.month}/{dt.day}/{dt.year} 4:00:00"
                    except:
                        return date_str

                processed_df['Time'] = processed_df['Time'].apply(convert_date)
                applied_rules.append("Date formatting: Ensured 'Time' column is in m/d/Y H:M:S format with 04:00:00 time")

            # Show results
            st.markdown("**Results**")

            col1, col2 = st.columns(2)
            with col1:
                st.metric("Original", original_row_count)
            with col2:
                st.metric("Final", len(processed_df))

            if applied_rules:
                with st.expander("Applied Rules", expanded=False):
                    for rule in applied_rules:
                        st.markdown(f"- {rule}")

            st.markdown("**Processed Data**")
            st.dataframe(processed_df, width='stretch', height=400)

            # Download button
            csv = processed_df.to_csv(index=False)

            # Generate output filename
            original_filename = uploaded_file.name
            if original_filename.endswith('.csv'):
                base_name = original_filename[:-4]
                output_filename = f"{base_name}_processed.csv"
            else:
                output_filename = f"{original_filename}_processed.csv"

            st.download_button(
                label="Download Processed CSV",
                data=csv,
                file_name=output_filename,
                mime='text/csv',
                use_container_width=True
            )

        elif bank_type == "AIB":

            rule1 = st.checkbox(
                "Format dates to d/m/Y (e.g., 13/9/2025)",
                value=True,
                help="Converts 'Posted Transactions Date' column to d/m/Y format for Firefly III import"
            )

            # Apply preprocessing
            processed_df = df.copy()
            applied_rules = []

            if rule1:
                # Convert dates from dd/mm/yyyy to d/m/Y H:M:S (no leading zeros)
                # Adds 04:00:00 time to avoid timezone conversion issues
                def convert_date(date_str):
                    try:
                        # Parse date - could be dd/mm/yyyy format
                        dt = pd.to_datetime(date_str, dayfirst=True)
                        # Format as d/m/Y H:M:S with 04:00:00 time to avoid midnight UTC issues
                        return f"{dt.day}/{dt.month}/{dt.year} 4:00:00"
                    except:
                        return date_str

                processed_df[aib_date_col] = processed_df[aib_date_col].apply(convert_date)
                applied_rules.append("Date formatting: Converted 'Posted Transactions Date' to d/m/Y H:M:S format with 04:00:00 time")

            # Show results
            st.markdown("**Results**")

            col1, col2 = st.columns(2)
            with col1:
                st.metric("Original", original_row_count)
            with col2:
                st.metric("Final", len(processed_df))

            if applied_rules:
                with st.expander("Applied Rules", expanded=False):
                    for rule in applied_rules:
                        st.markdown(f"- {rule}")

            st.markdown("**Processed Data**")
            st.dataframe(processed_df, width='stretch', height=400)

            # Download button
            csv = processed_df.to_csv(index=False)

            # Generate output filename
            original_filename = uploaded_file.name
            if original_filename.endswith('.csv'):
                base_name = original_filename[:-4]
                output_filename = f"{base_name}_processed.csv"
            else:
                output_filename = f"{original_filename}_processed.csv"

            st.download_button(
                label="Download Processed CSV",
                data=csv,
                file_name=output_filename,
                mime='text/csv',
                use_container_width=True
            )

        elif bank_type == "Revolut Credit Card":

            rule1 = st.checkbox(
                "Format dates to m/d/Y (e.g., 9/13/2025)",
                value=True,
                help="Converts 'Started Date' and 'Completed Date' columns to m/d/Y format for Firefly III import (handles both with and without timestamps)"
            )

            # Apply preprocessing
            processed_df = df.copy()
            applied_rules = []

            if rule1:
                # Convert dates - handles multiple formats:
                # - m/d/Y (already correct format, e.g., "10/1/2025")
                # - m/d/Y H:M (with time, e.g., "9/1/2025 13:22")
                # - YYYY-MM-DD (e.g., "2025-10-01")
                # - YYYY-MM-DD HH:MM:SS (e.g., "2025-10-01 13:22:00")
                # Adds 04:00:00 time to avoid timezone conversion issues
                def convert_date(date_str):
                    try:
                        # Try parsing - pandas will handle various formats
                        dt = pd.to_datetime(date_str)
                        # Format as m/d/Y H:M:S with 04:00:00 time to avoid midnight UTC issues
                        return f"{dt.month}/{dt.day}/{dt.year} 4:00:00"
                    except:
                        # If parsing fails, return as-is
                        return date_str

                processed_df['Started Date'] = processed_df['Started Date'].apply(convert_date)
                processed_df['Completed Date'] = processed_df['Completed Date'].apply(convert_date)
                applied_rules.append("Date formatting: Converted 'Started Date' and 'Completed Date' to m/d/Y H:M:S format with 04:00:00 time")

            # Show results
            st.markdown("**Results**")

            col1, col2 = st.columns(2)
            with col1:
                st.metric("Original", original_row_count)
            with col2:
                st.metric("Final", len(processed_df))

            if applied_rules:
                with st.expander("Applied Rules", expanded=False):
                    for rule in applied_rules:
                        st.markdown(f"- {rule}")

            st.markdown("**Processed Data**")
            st.dataframe(processed_df, width='stretch', height=400)

            # Download button
            csv = processed_df.to_csv(index=False)

            # Generate output filename
            original_filename = uploaded_file.name
            if original_filename.endswith('.csv'):
                base_name = original_filename[:-4]
                output_filename = f"{base_name}_processed.csv"
            else:
                output_filename = f"{original_filename}_processed.csv"

            st.download_button(
                label="Download Processed CSV",
                data=csv,
                file_name=output_filename,
                mime='text/csv',
                use_container_width=True
            )

        else:
            st.warning(f"No preprocessing rules for **{bank_type}**")

    except Exception as e:
        st.error(f"Error: {str(e)}")
