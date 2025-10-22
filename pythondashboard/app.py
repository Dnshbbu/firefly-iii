import streamlit as st
import pandas as pd
import os
from pathlib import Path
from datetime import datetime
from import_config_validator import ImportConfigValidator

# Page configuration
st.set_page_config(
    page_title="Firefly III CSV Preprocessor",
    page_icon="🔥",
    layout="wide"
)

# Compact CSS styling
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

    /* Compact dataframes */
    .dataframe {
        font-size: 0.85rem;
    }

    /* Compact metrics */
    [data-testid="stMetricValue"] {
        font-size: 1.5rem;
    }

    [data-testid="stMetricLabel"] {
        font-size: 0.85rem;
    }

    /* Reduce spacing between elements */
    .element-container {
        margin-bottom: 0.5rem;
    }

    /* Compact file uploader */
    [data-testid="stFileUploader"] {
        padding: 0.5rem;
    }

    /* Compact checkbox labels */
    .stCheckbox {
        margin-bottom: 0.25rem;
    }

    /* Compact info/warning boxes */
    .stAlert {
        padding: 0.5rem;
        margin-bottom: 0.5rem;
    }

    /* Reduce spacing in markdown lists */
    ul, ol {
        margin-top: 0.25rem;
        margin-bottom: 0.25rem;
    }

    li {
        margin-bottom: 0.1rem;
    }

    /* Compact download button */
    .stDownloadButton {
        margin-top: 0.5rem;
    }

    /* Reduce horizontal rule thickness */
    hr {
        margin-top: 0.5rem;
        margin-bottom: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)

st.title("🔥 Firefly III CSV Preprocessor")
st.markdown("---")

# Get the statements folder path (within pythondashboard directory)
STATEMENTS_FOLDER = Path(__file__).parent / "statements"
IMPORT_CONFIGS_FOLDER = Path(__file__).parent / "import-configs"

# Initialize validator
validator = ImportConfigValidator(IMPORT_CONFIGS_FOLDER)

# Sidebar for navigation
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["CSV Preprocessing", "View Preprocessing Rules", "Future: Dashboard"])

if page == "CSV Preprocessing":
    st.subheader("CSV Preprocessing")

    # File uploader
    uploaded_file = st.file_uploader("Upload CSV file from your bank", type=['csv'])

    if uploaded_file is not None:
        # Read the CSV file
        try:
            df = pd.read_csv(uploaded_file)
            original_row_count = len(df)

            st.markdown(f"**Original Data** ({original_row_count} rows)")
            st.dataframe(df, use_container_width=True, height=250)

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

            st.info(f"🏦 Detected Bank: **{bank_type}**")

            # Validate column structure against import config
            is_valid, validation_info = validator.validate_csv_structure(
                csv_columns=df.columns.tolist(),
                bank_type=bank_type
            )

            # Show validation results
            st.markdown("---")
            st.markdown("### 📋 Import Configuration Validation")

            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"**Source File:** `{uploaded_file.name}`")
                st.markdown(f"**Columns in CSV:** {validation_info.get('actual_columns', 'N/A')}")
            with col2:
                config_file = validation_info.get('config_file', 'N/A')
                st.markdown(f"**Import Config:** `{config_file}`")
                st.markdown(f"**Expected Columns:** {validation_info.get('expected_columns', 'N/A')}")

            # Show validation status
            if validation_info.get('error'):
                st.error(f"❌ {validation_info['error']}")
            elif validation_info.get('is_match'):
                st.success("✅ **Perfect Match!** CSV structure matches import configuration exactly.")
            else:
                st.warning("⚠️ **Column Mismatch Detected**")

                # Show details about mismatches
                if validation_info.get('extra_columns'):
                    with st.expander("🔴 Extra Columns (will cause import errors)", expanded=True):
                        st.markdown(f"Your CSV has **{len(validation_info['extra_columns'])}** extra column(s) that the import config doesn't expect:")
                        for col in validation_info['extra_columns']:
                            st.markdown(f"- `{col}`")
                        st.info("💡 **Recommendation:** Enable 'Remove extra columns' option below")

                if validation_info.get('missing_count', 0) > 0:
                    with st.expander("🟡 Missing Columns", expanded=True):
                        st.markdown(f"Your CSV is missing **{validation_info['missing_count']}** column(s) that the import config expects.")
                        st.info("💡 **Recommendation:** Enable 'Add missing columns with empty values' option below")

                # Show column-by-role mapping comparison
                with st.expander("🔍 Detailed Column Mapping", expanded=False):
                    st.markdown("**Column-by-Column Comparison:**")

                    comparison_data = []
                    csv_cols = validation_info.get('csv_columns', [])
                    roles = validation_info.get('column_roles', [])

                    max_len = max(len(csv_cols), len(roles))

                    for i in range(max_len):
                        csv_col = csv_cols[i] if i < len(csv_cols) else '❌ MISSING'
                        role = roles[i] if i < len(roles) else '❌ NOT EXPECTED'
                        status = '✅' if i < len(csv_cols) and i < len(roles) else '⚠️'

                        comparison_data.append({
                            'Position': i + 1,
                            'CSV Column': csv_col,
                            'Expected Role': role,
                            'Status': status
                        })

                    comparison_df = pd.DataFrame(comparison_data)
                    st.dataframe(comparison_df, use_container_width=True, height=300)

            st.markdown("---")
            # Preprocessing options
            st.markdown("### 🔧 Preprocessing Options")

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
                    # Convert dates from YYYY-MM-DD HH:MM:SS to m/d/Y
                    def convert_date(date_str):
                        try:
                            # Try parsing with time
                            dt = pd.to_datetime(date_str)
                            # Format as m/d/Y (no leading zeros)
                            return f"{dt.month}/{dt.day}/{dt.year}"
                        except:
                            return date_str

                    processed_df['Started Date'] = processed_df['Started Date'].apply(convert_date)
                    processed_df['Completed Date'] = processed_df['Completed Date'].apply(convert_date)
                    applied_rules.append("Date formatting: Converted 'Started Date' and 'Completed Date' to m/d/Y format")

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
                        st.dataframe(removed_df, use_container_width=True, height=300)

                st.markdown("**Processed Data**")
                st.dataframe(processed_df, use_container_width=True, height=400)

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

                # Column normalization options (only show if there are mismatches)
                normalize_enabled = False
                remove_extra = False
                add_missing = False

                columns_to_remove = []

                if not validation_info.get('is_match'):
                    st.markdown("**Column Normalization**")

                    normalize_enabled = st.checkbox(
                        "🔧 Enable column normalization",
                        value=True,
                        help="Automatically fix column mismatches to match the import configuration"
                    )

                    if normalize_enabled:
                        # Handle extra columns
                        if validation_info.get('actual_columns', 0) > validation_info.get('expected_columns', 0):
                            excess_count = validation_info['actual_columns'] - validation_info['expected_columns']

                            st.markdown(f"**⚠️ Your CSV has {excess_count} extra column(s)**")
                            st.markdown("Select which columns to remove:")

                            # Let user select which columns to remove
                            all_csv_columns = validation_info.get('csv_columns', [])

                            # Default selection: suggest the last N columns
                            default_removals = all_csv_columns[-excess_count:] if excess_count > 0 else []

                            columns_to_remove = st.multiselect(
                                f"Choose {excess_count} column(s) to remove:",
                                options=all_csv_columns,
                                default=default_removals,
                                help=f"Select exactly {excess_count} column(s) to match the expected structure"
                            )

                            # Validate selection count
                            if len(columns_to_remove) != excess_count:
                                st.warning(f"⚠️ Please select exactly {excess_count} column(s). Currently selected: {len(columns_to_remove)}")
                                remove_extra = False
                            else:
                                # Show what will be removed and what will remain
                                remaining_columns = [col for col in all_csv_columns if col not in columns_to_remove]

                                col_a, col_b = st.columns(2)
                                with col_a:
                                    st.markdown("**🗑️ Removing:**")
                                    for col in columns_to_remove:
                                        st.markdown(f"- `{col}`")

                                with col_b:
                                    st.markdown(f"**✅ Keeping ({len(remaining_columns)} columns):**")
                                    for col in remaining_columns:
                                        st.markdown(f"- `{col}`")

                                remove_extra = True

                        if validation_info.get('missing_count', 0) > 0:
                            add_missing = st.checkbox(
                                f"Add {validation_info['missing_count']} missing column(s) with empty values",
                                value=True,
                                help="Add empty columns to match the expected structure"
                            )

                    st.markdown("")  # Add spacing

                st.markdown("**Data Transformation**")

                rule1 = st.checkbox(
                    "Format dates to m/d/Y (e.g., 9/13/2025)",
                    value=True,
                    help="Converts 'Time' column to m/d/Y format for Firefly III import (Note: T212 dates are typically already in correct format)"
                )

                # Apply preprocessing
                processed_df = df.copy()
                applied_rules = []

                # Apply column normalization first
                if normalize_enabled:
                    original_columns = processed_df.columns.tolist()

                    if remove_extra and columns_to_remove:
                        # Remove user-selected columns
                        processed_df = processed_df.drop(columns=columns_to_remove)
                        applied_rules.append(f"🔧 Removed {len(columns_to_remove)} column(s): {', '.join(columns_to_remove)}")

                    if add_missing and validation_info.get('missing_count', 0) > 0:
                        # Add missing columns with empty values
                        missing_count = validation_info['missing_count']
                        current_col_count = len(processed_df.columns)
                        expected_count = validation_info['expected_columns']

                        # Add empty columns to reach expected count
                        for i in range(missing_count):
                            col_name = f'_missing_col_{i+1}'
                            processed_df[col_name] = ''

                        applied_rules.append(f"🔧 Added {missing_count} empty column(s) to match expected structure")

                if rule1:
                    # Convert dates - they should already be in m/d/Y format, but ensure consistency
                    def convert_date(date_str):
                        try:
                            dt = pd.to_datetime(date_str)
                            # Format as m/d/Y (no leading zeros)
                            return f"{dt.month}/{dt.day}/{dt.year}"
                        except:
                            return date_str

                    if 'Time' in processed_df.columns:
                        processed_df['Time'] = processed_df['Time'].apply(convert_date)
                        applied_rules.append("📅 Date formatting: Ensured 'Time' column is in m/d/Y format")

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
                st.dataframe(processed_df, use_container_width=True, height=400)

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
                    # Convert dates from dd/mm/yyyy to d/m/Y (no leading zeros)
                    def convert_date(date_str):
                        try:
                            # Parse date - could be dd/mm/yyyy format
                            dt = pd.to_datetime(date_str, dayfirst=True)
                            # Format as d/m/Y (no leading zeros)
                            return f"{dt.day}/{dt.month}/{dt.year}"
                        except:
                            return date_str

                    processed_df[aib_date_col] = processed_df[aib_date_col].apply(convert_date)
                    applied_rules.append("Date formatting: Converted 'Posted Transactions Date' to d/m/Y format")

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
                st.dataframe(processed_df, use_container_width=True, height=400)

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
                    help="Converts 'Started Date' and 'Completed Date' columns to m/d/Y format for Firefly III import"
                )

                # Apply preprocessing
                processed_df = df.copy()
                applied_rules = []

                if rule1:
                    # Convert dates from YYYY-MM-DD HH:MM:SS to m/d/Y
                    def convert_date(date_str):
                        try:
                            # Try parsing with time
                            dt = pd.to_datetime(date_str)
                            # Format as m/d/Y (no leading zeros)
                            return f"{dt.month}/{dt.day}/{dt.year}"
                        except:
                            return date_str

                    processed_df['Started Date'] = processed_df['Started Date'].apply(convert_date)
                    processed_df['Completed Date'] = processed_df['Completed Date'].apply(convert_date)
                    applied_rules.append("Date formatting: Converted 'Started Date' and 'Completed Date' to m/d/Y format")

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
                st.dataframe(processed_df, use_container_width=True, height=400)

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

elif page == "View Preprocessing Rules":
    st.subheader("Configured Preprocessing Rules")
    st.markdown("View all configured preprocessing rules for each supported bank type.")
    st.markdown("---")

    # Revolut
    with st.expander("🏦 Revolut (Current Account)", expanded=False):
        st.markdown("#### Detection Criteria")
        st.code("Columns: Type, Product, Started Date, Completed Date, Description, Amount, Currency")

        st.markdown("#### Preprocessing Rules")

        st.markdown("**Rule 1: Remove 'Saving vault topup prefunding wallet' transactions**")
        st.markdown("- **Action:** Remove rows")
        st.markdown("- **Condition:** `Description == 'Saving vault topup prefunding wallet'`")
        st.markdown("- **Default:** Enabled")

        st.markdown("**Rule 2: Remove Deposit transfers to Flexible Cash Funds**")
        st.markdown("- **Action:** Remove rows")
        st.markdown("- **Condition:** `Product == 'Deposit' AND Description == 'To Flexible Cash Funds'`")
        st.markdown("- **Default:** Enabled")

        st.markdown("**Rule 3: Remove Savings transactions**")
        st.markdown("- **Action:** Remove rows")
        st.markdown("- **Condition:** `Product == 'Savings'`")
        st.markdown("- **Default:** Enabled")

        st.markdown("**Rule 4: Format dates to m/d/Y**")
        st.markdown("- **Action:** Transform dates")
        st.markdown("- **Columns:** `Started Date`, `Completed Date`")
        st.markdown("- **Format:** Convert from `YYYY-MM-DD HH:MM:SS` to `m/d/Y` (e.g., 9/13/2025)")
        st.markdown("- **Default:** Enabled")

    # Revolut Credit Card
    with st.expander("💳 Revolut Credit Card", expanded=False):
        st.markdown("#### Detection Criteria")
        st.code("Columns: Type, Started Date, Completed Date, Description, Amount, Fee, Balance\n(Product column NOT present)")

        st.markdown("#### Preprocessing Rules")

        st.markdown("**Rule 1: Format dates to m/d/Y**")
        st.markdown("- **Action:** Transform dates")
        st.markdown("- **Columns:** `Started Date`, `Completed Date`")
        st.markdown("- **Format:** Convert from `YYYY-MM-DD HH:MM:SS` to `m/d/Y` (e.g., 9/13/2025)")
        st.markdown("- **Default:** Enabled")

    # T212
    with st.expander("📈 Trading 212 (T212)", expanded=False):
        st.markdown("#### Detection Criteria")
        st.code("Columns: Action, Time, ID, Total, Currency (Total)")

        st.markdown("#### Preprocessing Rules")

        st.markdown("**Rule 1: Format dates to m/d/Y**")
        st.markdown("- **Action:** Transform dates")
        st.markdown("- **Columns:** `Time`")
        st.markdown("- **Format:** Ensure date is in `m/d/Y` format (e.g., 9/13/2025)")
        st.markdown("- **Default:** Enabled")
        st.markdown("- **Note:** T212 dates are typically already in correct format; this ensures consistency")

    # AIB
    with st.expander("🏦 AIB (Allied Irish Banks)", expanded=False):
        st.markdown("#### Detection Criteria")
        st.code("Columns: Posted Account, Posted Transactions Date, Debit Amount, Credit Amount")

        st.markdown("#### Preprocessing Rules")

        st.markdown("**Rule 1: Format dates to d/m/Y**")
        st.markdown("- **Action:** Transform dates")
        st.markdown("- **Columns:** `Posted Transactions Date`")
        st.markdown("- **Format:** Convert to `d/m/Y` format (e.g., 13/9/2025)")
        st.markdown("- **Default:** Enabled")
        st.markdown("- **Note:** AIB uses day-first format (d/m/Y) unlike Revolut/T212 (m/d/Y)")

    st.markdown("---")
    st.info("💡 **Tip:** These rules are automatically applied based on detected bank type when you upload a CSV in the 'CSV Preprocessing' page.")

elif page == "Future: Dashboard":
    st.subheader("Firefly III Dashboard")
    st.info("Interactive dashboards with Firefly III API integration (coming soon)")
    with st.expander("Planned Features"):
        st.markdown("""
        - Account balances and trends
        - Budget tracking and visualization
        - Transaction analytics
        - Category spending breakdown
        - Bill tracking
        - Net worth over time
        """)

# Footer
st.sidebar.markdown("---")
st.sidebar.caption("CSV preprocessor for Firefly III")
