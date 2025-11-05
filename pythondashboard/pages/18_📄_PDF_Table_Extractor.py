import streamlit as st
import pandas as pd
import pdfplumber
from io import BytesIO
from datetime import datetime
from utils.navigation import render_sidebar_navigation

# Page configuration
st.set_page_config(
    page_title="PDF Table Extractor",
    page_icon="📄",
    layout="wide"
)

# Render sidebar navigation
render_sidebar_navigation()

# Compact CSS styling (matching app.py)
st.markdown("""
<style>
    /* Reduce padding and margins - but keep enough space for header */
    .block-container {
        padding-top: 5rem !important;
        padding-bottom: 0rem;
        padding-left: 2rem;
        padding-right: 2rem;
    }

    /* Compact headers */
    h1 {
        padding-top: 0rem;
        padding-bottom: 0.5rem;
        font-size: 2rem;
        margin-top: 0;
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

    /* Compact info/warning boxes */
    .stAlert {
        padding: 0.5rem;
        margin-bottom: 0.5rem;
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

st.title("📄 PDF Table Extractor")
st.markdown("Extract tables from PDF files and download them as CSV")
st.markdown("---")

# File uploader
uploaded_file = st.file_uploader("Upload a PDF file", type=['pdf'])

if uploaded_file is not None:
    try:
        # Read PDF using pdfplumber
        with pdfplumber.open(uploaded_file) as pdf:
            total_pages = len(pdf.pages)

            st.info(f"📑 PDF loaded successfully: **{uploaded_file.name}** ({total_pages} pages)")

            # Extract tables from all pages with custom settings
            all_tables = []
            table_info = []

            # Custom table settings for better detection
            table_settings = {
                "vertical_strategy": "lines_strict",
                "horizontal_strategy": "lines_strict",
                "explicit_vertical_lines": [],
                "explicit_horizontal_lines": [],
                "snap_tolerance": 3,
                "join_tolerance": 3,
                "edge_min_length": 3,
                "min_words_vertical": 1,
                "min_words_horizontal": 1,
                "intersection_tolerance": 3,
            }

            for page_num, page in enumerate(pdf.pages, start=1):
                # Try with strict line detection first
                tables = page.extract_tables(table_settings=table_settings)

                # If no tables found, try with text-based detection (more lenient)
                if not tables:
                    table_settings_lenient = {
                        "vertical_strategy": "text",
                        "horizontal_strategy": "text",
                        "snap_tolerance": 5,
                        "join_tolerance": 5,
                        "edge_min_length": 3,
                        "min_words_vertical": 1,
                        "min_words_horizontal": 1,
                    }
                    tables = page.extract_tables(table_settings=table_settings_lenient)

                if tables:
                    for table_num, table in enumerate(tables, start=1):
                        if table and len(table) > 0:
                            # Filter out tables with too many columns (likely parsing errors)
                            if len(table[0]) > 15:
                                # Skip tables with suspiciously many columns
                                continue

                            try:
                                # Convert to DataFrame
                                # First row is typically headers
                                if len(table) > 1:
                                    headers = table[0]

                                    # Handle duplicate column names by making them unique
                                    seen = {}
                                    unique_headers = []
                                    for header in headers:
                                        header_str = str(header) if header else ''
                                        if header_str == '' or header_str in seen:
                                            # Generate unique name
                                            count = seen.get(header_str, 0) + 1
                                            seen[header_str] = count
                                            unique_headers.append(f"{header_str}_{count}" if header_str else f"col_{count}")
                                        else:
                                            seen[header_str] = 1
                                            unique_headers.append(header_str)

                                    df = pd.DataFrame(table[1:], columns=unique_headers)
                                else:
                                    df = pd.DataFrame(table)

                                # Clean up - remove completely empty rows and columns
                                df = df.dropna(how='all')
                                df = df.loc[:, df.notna().any(axis=0)]

                                # Remove rows where all values are empty strings
                                df = df[~df.apply(lambda row: all(str(val).strip() == '' if val else True for val in row), axis=1)]

                                # Only keep tables with at least 3 rows and 3 columns
                                if not df.empty and len(df) >= 3 and len(df.columns) >= 3:
                                    # Store table info
                                    all_tables.append(df)
                                    table_info.append({
                                        'page': page_num,
                                        'table_num': table_num,
                                        'rows': len(df),
                                        'cols': len(df.columns)
                                    })
                            except Exception as table_error:
                                # Skip problematic tables
                                continue

            # Display results
            if all_tables:
                st.markdown(f"### 📊 Found {len(all_tables)} table(s)")
                st.markdown("---")

                # Show each table with download option
                for idx, (df, info) in enumerate(zip(all_tables, table_info)):
                    with st.expander(
                        f"📋 Table {idx + 1} - Page {info['page']} ({info['rows']} rows × {info['cols']} columns)",
                        expanded=True
                    ):
                        # Display metrics
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Page", info['page'])
                        with col2:
                            st.metric("Rows", info['rows'])
                        with col3:
                            st.metric("Columns", info['cols'])

                        st.markdown("**Table Preview:**")
                        st.dataframe(df, use_container_width=True, height=300)

                        # Download button for this table
                        csv_data = df.to_csv(index=False)

                        # Generate filename
                        base_name = uploaded_file.name.replace('.pdf', '')
                        csv_filename = f"{base_name}_table_{idx + 1}_page_{info['page']}.csv"

                        st.download_button(
                            label=f"⬇️ Download Table {idx + 1} as CSV",
                            data=csv_data,
                            file_name=csv_filename,
                            mime='text/csv',
                            key=f"download_table_{idx}",
                            use_container_width=True
                        )

                        st.markdown("")  # Add spacing

                # Option to download all tables combined
                if len(all_tables) > 1:
                    st.markdown("---")
                    st.markdown("### 📦 Download All Tables")

                    download_option = st.radio(
                        "Choose download format:",
                        ["Separate sheets (requires Excel)", "Combined into one CSV"],
                        index=1
                    )

                    if download_option == "Combined into one CSV":
                        # Add page/table identifier column to each table
                        combined_tables = []
                        for idx, (df, info) in enumerate(zip(all_tables, table_info)):
                            df_copy = df.copy()
                            df_copy.insert(0, 'PDF_Page', info['page'])
                            df_copy.insert(1, 'Table_Number', idx + 1)
                            combined_tables.append(df_copy)

                        # Combine all tables
                        combined_df = pd.concat(combined_tables, ignore_index=True)
                        combined_csv = combined_df.to_csv(index=False)

                        base_name = uploaded_file.name.replace('.pdf', '')
                        combined_filename = f"{base_name}_all_tables_combined.csv"

                        st.download_button(
                            label="⬇️ Download All Tables (Combined CSV)",
                            data=combined_csv,
                            file_name=combined_filename,
                            mime='text/csv',
                            use_container_width=True
                        )
                    else:
                        st.info("💡 Excel export with separate sheets requires additional libraries. For now, please download tables individually.")

            else:
                st.warning("⚠️ No tables found using automatic detection. Trying manual text extraction...")

                # Fallback: Manual text extraction for Revolut-style PDFs
                st.markdown("---")
                st.markdown("### 🔧 Manual Table Extraction")
                st.info("This tool will attempt to extract text and parse it into table format.")

                # Try to extract text from each page and look for transaction patterns
                for page_num, page in enumerate(pdf.pages, start=1):
                    text = page.extract_text()

                    if text and "Date" in text and "Description" in text:
                        st.markdown(f"**Page {page_num} - Raw Text Preview:**")
                        with st.expander(f"View text from page {page_num}", expanded=False):
                            st.text(text[:2000])  # Show first 2000 chars

                        # Try to parse Revolut-style transaction table
                        lines = text.split('\n')

                        # Find the header line
                        header_idx = None
                        for i, line in enumerate(lines):
                            if 'Date' in line and 'Description' in line and 'Money' in line:
                                header_idx = i
                                break

                        if header_idx is not None:
                            st.success(f"✅ Found potential transaction table on page {page_num}!")

                            # Try to parse Revolut CC transactions
                            try:
                                transactions = []
                                i = header_idx + 1

                                while i < len(lines):
                                    line = lines[i].strip()

                                    # Check if line starts with a date pattern
                                    if line and any(month in line for month in ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']):
                                        # Split the line by multiple spaces to get fields
                                        parts = line.split()

                                        if len(parts) >= 4:
                                            # Parse date (e.g., "1 Oct 2025")
                                            date_str = ' '.join(parts[:3])

                                            # Find amount and balance (they have € symbol)
                                            amounts = [p for p in parts if '€' in p]

                                            # Description is between date and amounts
                                            desc_start = 3
                                            desc_end = len(parts) - len(amounts)
                                            description = ' '.join(parts[desc_start:desc_end]) if desc_end > desc_start else parts[3] if len(parts) > 3 else ''

                                            # Determine money_out, money_in, balance
                                            money_out = ''
                                            money_in = ''
                                            balance = amounts[-1] if amounts else ''

                                            if len(amounts) >= 2:
                                                amount_val = amounts[0]
                                                # If negative balance or amount without minus, it's money out
                                                if '-' not in amount_val and 'repayment' not in description.lower():
                                                    money_out = amount_val
                                                else:
                                                    money_in = amount_val.replace('-', '')

                                            # Skip "To:" and "Card:" detail lines by checking next lines
                                            details = []
                                            j = i + 1
                                            while j < len(lines) and not any(m in lines[j] for m in ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec', 'Transaction types']):
                                                detail_line = lines[j].strip()
                                                if detail_line and not detail_line.startswith('To:') and not detail_line.startswith('Card:'):
                                                    break
                                                if detail_line:
                                                    details.append(detail_line)
                                                j += 1

                                            # Build transaction entry
                                            # Convert date to expected format
                                            try:
                                                from datetime import datetime
                                                dt = datetime.strptime(date_str, '%d %b %Y')
                                                formatted_date = f"{dt.month}/{dt.day}/{dt.year}"
                                            except:
                                                formatted_date = date_str

                                            transactions.append({
                                                'Type': 'CARD_PAYMENT' if 'repayment' not in description.lower() else 'TRANSFER',
                                                'Started Date': formatted_date,
                                                'Completed Date': formatted_date,
                                                'Description': description,
                                                'Amount': money_out if money_out else f"-{money_in}" if money_in else '',
                                                'Fee': '0.00',
                                                'Balance': balance.replace('€', '').replace('-€', '-')
                                            })

                                            i = j
                                            continue

                                    # Stop at "Transaction types" section
                                    if 'Transaction types' in line:
                                        break

                                    i += 1

                                if transactions:
                                    # Create DataFrame
                                    df_parsed = pd.DataFrame(transactions)

                                    st.markdown("**✅ Successfully Parsed Transactions:**")
                                    st.dataframe(df_parsed, use_container_width=True, height=300)

                                    # Download as CSV
                                    csv_data = df_parsed.to_csv(index=False)
                                    base_name = uploaded_file.name.replace('.pdf', '')
                                    csv_filename = f"{base_name}_page_{page_num}_transactions.csv"

                                    st.download_button(
                                        label=f"⬇️ Download Parsed Transactions as CSV",
                                        data=csv_data,
                                        file_name=csv_filename,
                                        mime='text/csv',
                                        use_container_width=True
                                    )
                                else:
                                    st.warning("Could not parse transactions automatically.")

                            except Exception as parse_error:
                                st.warning(f"Automatic parsing failed: {str(parse_error)}")

                            # Also provide raw text download as fallback
                            st.markdown("---")
                            st.markdown("**Alternative: Download Raw Text**")
                            text_data = "\n".join(lines[header_idx:])
                            base_name = uploaded_file.name.replace('.pdf', '')
                            text_filename = f"{base_name}_page_{page_num}_raw_text.txt"

                            st.download_button(
                                label=f"⬇️ Download Page {page_num} Raw Text",
                                data=text_data,
                                file_name=text_filename,
                                mime='text/plain',
                                use_container_width=True
                            )

                st.markdown("---")
                st.markdown("**Alternative Options:**")
                st.markdown("- Export transactions directly as CSV from Revolut app/website")
                st.markdown("- Use a PDF table extraction tool like Tabula or Adobe Acrobat")
                st.markdown("- Screenshot the table and use OCR tools")

    except Exception as e:
        st.error(f"❌ Error processing PDF: {str(e)}")
        st.markdown("**Common issues:**")
        st.markdown("- The PDF may be password-protected")
        st.markdown("- The PDF may be corrupted or have an unsupported format")
        st.markdown("- Tables may be embedded as images rather than text")

else:
    # Instructions
    st.info("👆 Upload a PDF file to get started")

    st.markdown("### 📖 How to use")
    st.markdown("""
    1. **Upload PDF**: Click the upload button and select your PDF file
    2. **View Tables**: The app will automatically detect and display all tables
    3. **Download**: Click the download button for any table to save it as CSV
    4. **Import**: Use the downloaded CSV with the Firefly III Data Importer
    """)

    st.markdown("### ✨ Features")
    st.markdown("""
    - Automatically detects all tables in the PDF
    - Shows table previews with row/column counts
    - Download individual tables as CSV files
    - Download all tables combined into one CSV
    - Works with bank statements, reports, and any PDF with structured tables
    """)

    st.markdown("### 💡 Tips")
    st.markdown("""
    - Works best with PDFs that have structured, text-based tables
    - If tables aren't detected, the PDF may have tables as images
    - For Revolut CC statements, look for the transaction table (usually on page 2)
    - After downloading, you can preprocess the CSV using the **CSV Preprocessor** page
    """)

# Footer
st.markdown("---")
st.caption("Extract tables from PDF files and export as CSV for Firefly III import")
