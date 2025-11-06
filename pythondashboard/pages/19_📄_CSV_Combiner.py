import streamlit as st
import pandas as pd
import io
from pathlib import Path
import sys

# Add parent directory to path to import utils
sys.path.append(str(Path(__file__).parent.parent))
from utils.navigation import render_sidebar_navigation

# Page configuration
st.set_page_config(
    page_title="CSV Combiner - Firefly III",
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

st.title("📄 CSV Combiner")
st.markdown("Combine multiple CSV files into a single file. Headers from subsequent files are automatically removed.")
st.markdown("---")

# Initialize session state for uploaded files
if 'uploaded_files_data' not in st.session_state:
    st.session_state.uploaded_files_data = []

# Initialize session state for ignored files (files user deleted but still in uploader)
if 'ignored_files' not in st.session_state:
    st.session_state.ignored_files = set()

# Initialize uploader key for resetting
if 'uploader_key' not in st.session_state:
    st.session_state.uploader_key = 0

# File uploader
st.subheader("1. Upload CSV Files")
uploaded_files = st.file_uploader(
    "Choose CSV files to combine",
    type=['csv'],
    accept_multiple_files=True,
    key=f"csv_uploader_{st.session_state.uploader_key}"
)

# Process uploaded files - sync with session state
if uploaded_files:
    # Get list of uploaded filenames from widget
    uploaded_names = [f.name for f in uploaded_files]

    # Remove files from session state that are no longer in the uploader (unless they're ignored)
    st.session_state.uploaded_files_data = [
        f for f in st.session_state.uploaded_files_data
        if f['name'] in uploaded_names or f['name'] in st.session_state.ignored_files
    ]

    # Get list of already uploaded filenames in session state
    existing_names = [f['name'] for f in st.session_state.uploaded_files_data]

    # Add only new files that aren't already uploaded or ignored
    for uploaded_file in uploaded_files:
        if uploaded_file.name not in existing_names and uploaded_file.name not in st.session_state.ignored_files:
            # Read the file data
            file_bytes = uploaded_file.read()

            # Try to read as CSV to get row count
            try:
                df_temp = pd.read_csv(io.BytesIO(file_bytes))
                row_count = len(df_temp)
                header = list(df_temp.columns)
            except Exception as e:
                st.error(f"Error reading {uploaded_file.name}: {str(e)}")
                continue

            # Store file data
            st.session_state.uploaded_files_data.append({
                'name': uploaded_file.name,
                'data': file_bytes,
                'rows': row_count,
                'header': header
            })
elif not uploaded_files and st.session_state.uploaded_files_data:
    # If uploader is empty but we have files in session state, clear them
    st.session_state.uploaded_files_data = []
    st.session_state.ignored_files = set()

# Show action buttons if there are files in uploader or session state
if uploaded_files or st.session_state.uploaded_files_data:
    st.markdown("---")
    col1, col2, col3, col4 = st.columns([1, 1, 1, 2])

    with col1:
        # Disable if no files in uploader to add
        files_to_add = len(st.session_state.ignored_files) if uploaded_files else 0
        if st.button("➕ Add All Files", use_container_width=True, help="Add all uploaded files back to the list", disabled=(files_to_add == 0)):
            # Clear ignored files and re-process uploader
            st.session_state.ignored_files = set()
            st.rerun()

    with col2:
        # Disable if no files to clear
        if st.button("🗑️ Clear All Files", use_container_width=True, help="Remove all files from the list (keeps them in uploader)", disabled=(len(st.session_state.uploaded_files_data) == 0)):
            # Add all current files to ignored list
            for file_info in st.session_state.uploaded_files_data:
                st.session_state.ignored_files.add(file_info['name'])
            st.session_state.uploaded_files_data = []
            st.rerun()

    with col3:
        if st.button("🔄 Reset Page", use_container_width=True, help="Reset entire page and clear uploader", type="secondary"):
            st.session_state.uploaded_files_data = []
            st.session_state.ignored_files = set()
            # Increment the uploader key to force a complete reset
            st.session_state.uploader_key += 1
            st.rerun()

# Display uploaded files with reordering controls
if st.session_state.uploaded_files_data:
    st.markdown("---")
    st.subheader("2. Reorder and Manage Files")
    st.caption("Use the buttons to reorder files or remove them from the list. Files will be combined in the order shown below.")

    # Display each file with controls
    for idx, file_info in enumerate(st.session_state.uploaded_files_data):
        col1, col2, col3, col4, col5 = st.columns([0.5, 0.5, 3, 1, 0.8])

        with col1:
            # Move up button (disabled for first item)
            if st.button("⬆️", key=f"up_{idx}", disabled=(idx == 0), help="Move up"):
                # Swap with previous item
                st.session_state.uploaded_files_data[idx], st.session_state.uploaded_files_data[idx-1] = \
                    st.session_state.uploaded_files_data[idx-1], st.session_state.uploaded_files_data[idx]
                st.rerun()

        with col2:
            # Move down button (disabled for last item)
            if st.button("⬇️", key=f"down_{idx}", disabled=(idx == len(st.session_state.uploaded_files_data) - 1), help="Move down"):
                # Swap with next item
                st.session_state.uploaded_files_data[idx], st.session_state.uploaded_files_data[idx+1] = \
                    st.session_state.uploaded_files_data[idx+1], st.session_state.uploaded_files_data[idx]
                st.rerun()

        with col3:
            st.markdown(f"**{idx + 1}. {file_info['name']}**")

        with col4:
            st.caption(f"{file_info['rows']} rows")

        with col5:
            # Remove button
            if st.button("🗑️", key=f"remove_{idx}", help="Remove"):
                # Remove from session state
                removed_file = st.session_state.uploaded_files_data.pop(idx)
                # Add to a list of files to ignore (so sync doesn't re-add them)
                if 'ignored_files' not in st.session_state:
                    st.session_state.ignored_files = set()
                st.session_state.ignored_files.add(removed_file['name'])
                st.rerun()

    # Show preview of headers
    with st.expander("📋 View Headers from Each File", expanded=False):
        for idx, file_info in enumerate(st.session_state.uploaded_files_data):
            st.markdown(f"**{idx + 1}. {file_info['name']}**")
            st.code(", ".join(file_info['header']), language=None)

    # Combine button and preview
    st.markdown("---")
    st.subheader("3. Combine Files")

    # Check if all files have the same header
    headers = [tuple(f['header']) for f in st.session_state.uploaded_files_data]
    all_headers_match = len(set(headers)) == 1

    if not all_headers_match:
        st.warning("⚠️ Warning: Not all files have the same headers. The combined file will use the headers from the first file.")

        # Show which headers differ
        with st.expander("Show Header Differences", expanded=False):
            for idx, file_info in enumerate(st.session_state.uploaded_files_data):
                if idx == 0:
                    st.markdown(f"**{idx + 1}. {file_info['name']}** (Reference)")
                else:
                    if tuple(file_info['header']) != headers[0]:
                        st.markdown(f"**{idx + 1}. {file_info['name']}** ⚠️ Different headers")
                    else:
                        st.markdown(f"**{idx + 1}. {file_info['name']}** ✓ Matching headers")
                st.code(", ".join(file_info['header']), language=None)
    else:
        st.success(f"✓ All {len(st.session_state.uploaded_files_data)} files have matching headers")

    # Option to keep or skip headers
    st.markdown("**Options**")
    keep_intermediate_headers = st.checkbox(
        "Keep headers from all files (not recommended)",
        value=False,
        help="By default, only the first file's header is kept. Enable this to keep headers from all files (they will appear as data rows)."
    )

    if st.button("🔗 Combine CSV Files", type="primary", use_container_width=True):
        try:
            combined_dfs = []

            # Read all files
            for idx, file_info in enumerate(st.session_state.uploaded_files_data):
                df = pd.read_csv(io.BytesIO(file_info['data']))

                # For all files after the first, either keep or remove header
                # If we're keeping headers, we need to convert to CSV and back to make header a row
                if idx > 0 and not keep_intermediate_headers:
                    # Just append the data (header is already removed by pandas)
                    pass
                elif idx > 0 and keep_intermediate_headers:
                    # Convert to CSV string with header, then read back without treating first row as header
                    csv_string = df.to_csv(index=False)
                    df = pd.read_csv(io.StringIO(csv_string), header=None)
                    # For the first file, also need to include its header as a row
                    if len(combined_dfs) == 1:
                        first_df = combined_dfs[0]
                        # Add column names as first row
                        header_row = pd.DataFrame([first_df.columns], columns=first_df.columns)
                        combined_dfs[0] = pd.concat([header_row, first_df], ignore_index=True)
                        # Rename columns to integers to match
                        combined_dfs[0].columns = range(len(combined_dfs[0].columns))

                combined_dfs.append(df)

            # Combine all dataframes
            combined_df = pd.concat(combined_dfs, ignore_index=True)

            # Show preview
            st.markdown("**Preview of Combined CSV**")
            st.dataframe(combined_df, width='stretch', height=400)

            # Show statistics
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Rows", len(combined_df))
            with col2:
                st.metric("Total Columns", len(combined_df.columns))
            with col3:
                st.metric("Files Combined", len(st.session_state.uploaded_files_data))

            # Breakdown by file
            with st.expander("📊 Row Breakdown by File", expanded=False):
                for idx, file_info in enumerate(st.session_state.uploaded_files_data):
                    st.markdown(f"**{idx + 1}. {file_info['name']}**: {file_info['rows']} rows")

                if not keep_intermediate_headers:
                    st.markdown(f"**Total**: {len(combined_df)} rows (headers removed from {len(st.session_state.uploaded_files_data) - 1} files)")
                else:
                    expected_total = sum(f['rows'] for f in st.session_state.uploaded_files_data) + len(st.session_state.uploaded_files_data)
                    st.markdown(f"**Total**: {len(combined_df)} rows (including {len(st.session_state.uploaded_files_data)} header rows)")

            # Generate download filename
            if len(st.session_state.uploaded_files_data) > 0:
                first_filename = st.session_state.uploaded_files_data[0]['name']
                if first_filename.endswith('.csv'):
                    base_name = first_filename[:-4]
                else:
                    base_name = first_filename
                output_filename = f"{base_name}_combined_{len(st.session_state.uploaded_files_data)}_files.csv"
            else:
                output_filename = "combined.csv"

            # Convert to CSV
            csv_output = combined_df.to_csv(index=False)

            # Download button
            st.download_button(
                label="📥 Download Combined CSV",
                data=csv_output,
                file_name=output_filename,
                mime='text/csv',
                use_container_width=True,
                type="primary"
            )

        except Exception as e:
            st.error(f"Error combining files: {str(e)}")
            st.exception(e)

else:
    st.info("👆 Upload CSV files to get started")

# Instructions
st.markdown("---")
with st.expander("ℹ️ How to Use", expanded=False):
    st.markdown("""
    ### Instructions

    1. **Upload Files**: Click "Browse files" to select multiple CSV files or drag and drop them
    2. **Reorder Files**: Use ⬆️ and ⬇️ buttons to change the order in which files will be combined
    3. **Remove Files**: Click 🗑️ to remove a file from the list
    4. **Combine**: Click "Combine CSV Files" to merge all files in the current order
    5. **Download**: Download the combined CSV file

    ### Important Notes

    - **Headers are automatically removed** from all files except the first one
    - Files are combined in the order shown in the list
    - All files should ideally have the same column structure
    - The combined file will use the headers from the first file
    - You can reorder files at any time before combining

    ### Use Case Example

    If you have monthly bank statements like:
    - `Revolut_CC_Jan.csv` (7 rows)
    - `Revolut_CC_Feb.csv` (5 rows)
    - `Revolut_CC_March.csv` (10 rows)

    The combined file will have:
    - Header from Jan file (1 row)
    - Data from Jan file (7 rows)
    - Data from Feb file (5 rows, header removed)
    - Data from March file (10 rows, header removed)
    - **Total: 23 rows** (including header)
    """)
