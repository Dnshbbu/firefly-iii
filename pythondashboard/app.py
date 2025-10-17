import streamlit as st
import pandas as pd
import os
from pathlib import Path

# Page configuration
st.set_page_config(
    page_title="Firefly III CSV Preprocessor",
    page_icon="🔥",
    layout="wide"
)

st.title("🔥 Firefly III CSV Preprocessor")
st.markdown("---")

# Get the statements folder path (relative to the project root)
STATEMENTS_FOLDER = Path(__file__).parent.parent / "statements"

# Sidebar for navigation
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["CSV Preprocessing", "Future: Dashboard"])

if page == "CSV Preprocessing":
    st.header("CSV Preprocessing")
    st.markdown("Upload CSV files from your bank and apply preprocessing rules before importing into Firefly III.")

    # File uploader
    uploaded_file = st.file_uploader("Choose a CSV file", type=['csv'])

    if uploaded_file is not None:
        # Read the CSV file
        try:
            df = pd.read_csv(uploaded_file)
            original_row_count = len(df)

            st.subheader("Original Data")
            st.write(f"Total rows: {original_row_count}")
            st.dataframe(df, use_container_width=True)

            # Detect bank type based on columns
            bank_type = "Unknown"
            if all(col in df.columns for col in ['Type', 'Product', 'Description', 'Amount', 'Currency']):
                bank_type = "Revolut"

            st.info(f"Detected bank type: **{bank_type}**")

            # Preprocessing options
            st.subheader("Preprocessing Rules")

            if bank_type == "Revolut":
                st.markdown("**Revolut-specific rules:**")

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

                # Apply preprocessing
                processed_df = df.copy()
                removed_rows = []

                if rule1:
                    mask = processed_df['Description'] == 'Saving vault topup prefunding wallet'
                    removed_count = mask.sum()
                    removed_rows.append(f"Rule 1: Removed {removed_count} 'Saving vault topup prefunding wallet' rows")
                    processed_df = processed_df[~mask]

                if rule2:
                    mask = (processed_df['Product'] == 'Deposit') & (processed_df['Description'] == 'To Flexible Cash Funds')
                    removed_count = mask.sum()
                    removed_rows.append(f"Rule 2: Removed {removed_count} 'Deposit' + 'To Flexible Cash Funds' rows")
                    processed_df = processed_df[~mask]

                # Show results
                st.subheader("Preprocessing Results")

                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Original Rows", original_row_count)
                with col2:
                    st.metric("Removed Rows", original_row_count - len(processed_df))
                with col3:
                    st.metric("Final Rows", len(processed_df))

                if removed_rows:
                    st.markdown("**Applied rules:**")
                    for rule in removed_rows:
                        st.markdown(f"- {rule}")

                st.subheader("Processed Data")
                st.dataframe(processed_df, use_container_width=True)

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
                st.warning("No preprocessing rules defined for this bank type yet.")
                st.markdown("You can still download the original file or add custom rules.")

        except Exception as e:
            st.error(f"Error reading CSV file: {str(e)}")
            st.info("Please ensure the file is a valid CSV file.")

elif page == "Future: Dashboard":
    st.header("Firefly III Dashboard")
    st.info("This section will contain interactive dashboards that interact with Firefly III APIs.")
    st.markdown("""
    **Planned features:**
    - Account balances and trends
    - Budget tracking and visualization
    - Transaction analytics
    - Category spending breakdown
    - Bill tracking
    - Net worth over time
    """)

# Footer
st.sidebar.markdown("---")
st.sidebar.markdown("### About")
st.sidebar.markdown("CSV preprocessor for Firefly III imports. Built with Streamlit.")
