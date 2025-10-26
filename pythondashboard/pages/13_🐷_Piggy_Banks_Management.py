"""
Firefly III Piggy Banks Management Page
Export, view, create, update, delete, and import piggy_banks
"""

import streamlit as st
import pandas as pd
import json
from pathlib import Path
import sys

# Add parent directory to path to import firefly_api
sys.path.append(str(Path(__file__).parent.parent))
from firefly_api import FireflyAPIClient
from utils.navigation import render_sidebar_navigation
from utils.config import get_firefly_url, get_firefly_token

# Page configuration
st.set_page_config(
    page_title="Piggy Banks Management - Firefly III",
    page_icon="🐷",
    layout="wide"
)

# Render custom navigation
render_sidebar_navigation()

st.title("🐷 Piggy Banks Management")
st.markdown("Manage your Firefly III piggy_banks: export, view, create, update, delete, and import")

# Initialize session state for API connection
if 'api_connected' not in st.session_state:
    st.session_state.api_connected = False
if 'firefly_url' not in st.session_state:
    st.session_state.firefly_url = get_firefly_url()
if 'firefly_token' not in st.session_state:
    st.session_state.firefly_token = get_firefly_token()
if 'piggy_banks_cache' not in st.session_state:
    st.session_state.piggy_banks_cache = None
if 'last_refresh_piggy_banks' not in st.session_state:
    st.session_state.last_refresh_piggy_banks = None
if 'last_refresh' not in st.session_state:
    st.session_state.last_refresh = None

# Auto-connect if credentials are available
if not st.session_state.api_connected and st.session_state.firefly_url and st.session_state.firefly_token:
    client = FireflyAPIClient(st.session_state.firefly_url, st.session_state.firefly_token)
    success, message = client.test_connection()
    if success:
        st.session_state.api_connected = True

# Sidebar - API Configuration
st.sidebar.header("🔌 API Connection")

# Show connection status
if st.session_state.api_connected:
    st.sidebar.success(f"✅ Connected to {st.session_state.firefly_url}")
else:
    st.sidebar.error("❌ Not Connected")
    st.sidebar.markdown("Edit `.env` file with credentials")

st.sidebar.markdown("---")

# Main content
if not st.session_state.api_connected:
    st.info("""
    ### 🔑 Getting Started

    Configure your Firefly III credentials in the `.env` file:

    1. **Edit `.env`** in the `pythondashboard` directory
    2. **Add credentials**:
       ```
       FIREFLY_III_URL=http://localhost
       FIREFLY_III_TOKEN=your_token_here
       ```
    3. **Restart the app**

    Generate a token at: Firefly III → Options → Profile → OAuth → Personal Access Tokens
    """)
else:
    # Recreate client from stored credentials (compatible with Dashboard pages)
    client = FireflyAPIClient(st.session_state.firefly_url, st.session_state.firefly_token)

    # Create tabs for different operations
    tab1, tab2, tab3, tab4 = st.tabs([
        "📋 View & Export Piggy Banks",
        "➕ Create Category",
        "🗑️ Delete Piggy Banks",
        "📥 Import Piggy Banks"
    ])

    # TAB 1: View & Export Piggy Banks
    with tab1:
        st.subheader("View & Export Piggy Banks")

        col1, col2 = st.columns([3, 1])

        with col1:
            if st.button("🔄 Refresh Piggy Banks", type="primary"):
                with st.spinner("Fetching piggy_banks from Firefly III..."):
                    success, piggy_banks, message = client.get_all_piggy_banks()
                    if success:
                        st.session_state.piggy_banks_cache = piggy_banks
                        st.session_state.last_refresh = pd.Timestamp.now()
                        st.success(message)
                    else:
                        st.error(message)

        with col2:
            if st.session_state.last_refresh:
                st.caption(f"Last refresh: {st.session_state.last_refresh.strftime('%H:%M:%S')}")

        if st.session_state.piggy_banks_cache is not None:
            piggy_banks = st.session_state.piggy_banks_cache

            if len(piggy_banks) == 0:
                st.info("No piggy_banks found in your Firefly III instance")
            else:
                # Display summary metrics
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Piggy Banks", len(piggy_banks))
                with col2:
                    # Count piggy_banks with notes
                    piggy_banks_with_notes = sum(1 for c in piggy_banks
                                               if c.get('attributes', {}).get('notes'))
                    st.metric("With Notes", piggy_banks_with_notes)
                with col3:
                    # Count piggy_banks spent last 365 days
                    piggy_banks_with_spending = 0
                    for c in piggy_banks:
                        spent_data = c.get('attributes', {}).get('spent', [])
                        if spent_data and len(spent_data) > 0 and spent_data[0]:
                            spent_sum = float(spent_data[0].get('sum', '0'))
                            if spent_sum != 0:
                                piggy_banks_with_spending += 1
                    st.metric("With Spending", piggy_banks_with_spending)

                # Convert piggy_banks to DataFrame for display
                piggy_banks_data = []
                for piggy_bank in piggy_banks:
                    attrs = piggy_bank.get('attributes', {})
                    # Get spending data
                    spent_data = attrs.get('spent', [])
                    total_spent = 0
                    if spent_data and len(spent_data) > 0 and spent_data[0]:
                        total_spent = abs(float(spent_data[0].get('sum', '0')))

                    notes = attrs.get('notes') or ''
                    notes_display = notes[:50] + '...' if len(notes) > 50 else notes

                    created_at = attrs.get('created_at') or 'N/A'
                    updated_at = attrs.get('updated_at') or 'N/A'

                    piggy_banks_data.append({
                        'ID': piggy_bank.get('id'),
                        'Name': attrs.get('name', 'N/A'),
                        'Notes': notes_display,
                        'Spent (Last 365d)': f"€{total_spent:,.2f}",
                        'Created': created_at[:10] if created_at != 'N/A' else 'N/A',
                        'Updated': updated_at[:10] if updated_at != 'N/A' else 'N/A'
                    })

                df = pd.DataFrame(piggy_banks_data)

                # Filter options
                st.markdown("**Filter Piggy Banks**")
                col1, col2 = st.columns(2)

                with col1:
                    search_term = st.text_input("Search by name", "")

                with col2:
                    show_with_spending_only = st.checkbox("Show only piggy_banks with spending")

                # Apply filters
                filtered_df = df.copy()

                if search_term:
                    filtered_df = filtered_df[
                        filtered_df['Name'].str.contains(search_term, case=False, na=False)
                    ]

                if show_with_spending_only:
                    filtered_df = filtered_df[filtered_df['Spent (Last 365d)'] != '€0.00']

                st.markdown(f"**Piggy Banks List** ({len(filtered_df)} piggy_banks)")
                st.dataframe(filtered_df, use_container_width=True, height=400)

                # Expandable details for each piggy_bank
                with st.expander("📄 View Detailed Category Information"):
                    selected_piggy_bank_id = st.selectbox(
                        "Select a piggy_bank to view details",
                        options=[c['ID'] for c in piggy_banks_data],
                        format_func=lambda x: f"ID {x}: {next((c['Name'] for c in piggy_banks_data if c['ID'] == x), 'N/A')}"
                    )

                    if selected_piggy_bank_id:
                        piggy_bank = next((c for c in piggy_banks if c.get('id') == selected_piggy_bank_id), None)
                        if piggy_bank:
                            attrs = piggy_bank.get('attributes', {})

                            col1, col2 = st.columns(2)

                            with col1:
                                st.markdown("**Category Information**")
                                st.markdown(f"- **Name:** {attrs.get('name', 'N/A')}")
                                st.markdown(f"- **Created:** {attrs.get('created_at', 'N/A')}")
                                st.markdown(f"- **Updated:** {attrs.get('updated_at', 'N/A')}")

                            with col2:
                                st.markdown("**Notes**")
                                notes = attrs.get('notes', '')
                                if notes:
                                    st.markdown(notes)
                                else:
                                    st.markdown("*No notes*")

                            st.markdown("**Spending Information (Last 365 days)**")
                            spent_data = attrs.get('spent', [])
                            if spent_data and len(spent_data) > 0:
                                for spend in spent_data:
                                    if spend:  # Check if spend is not None
                                        currency = spend.get('currency_code', 'EUR')
                                        amount = abs(float(spend.get('sum', '0')))
                                        st.markdown(f"- **{currency}:** €{amount:,.2f}")
                            else:
                                st.markdown("*No spending data*")

                            # Show raw JSON
                            st.markdown("---")
                            show_raw_json = st.checkbox("🔍 Show Raw JSON", key=f"show_json_{selected_piggy_bank_id}")
                            if show_raw_json:
                                st.json(piggy_bank)

                # Export functionality
                st.markdown("---")
                st.markdown("**Export Piggy Banks**")

                col1, col2 = st.columns([2, 1])

                with col1:
                    export_filename = st.text_input(
                        "Export filename",
                        value=f"firefly_piggy_banks_export_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.json"
                    )

                with col2:
                    st.markdown("")  # Spacing
                    st.markdown("")  # Spacing

                    if st.button("💾 Export All Piggy Banks", type="primary"):
                        # Create export data
                        export_data = {
                            'export_date': pd.Timestamp.now().isoformat(),
                            'firefly_iii_piggy_banks_export': True,
                            'total_piggy_banks': len(piggy_banks),
                            'piggy_banks': piggy_banks
                        }

                        # Convert to JSON string
                        json_str = json.dumps(export_data, indent=2, ensure_ascii=False)

                        # Offer download
                        st.download_button(
                            label="⬇️ Download JSON",
                            data=json_str,
                            file_name=export_filename,
                            mime="application/json"
                        )

                        st.success(f"✅ Prepared {len(piggy_banks)} piggy_banks for export")

    # TAB 2: Create Category
    with tab2:
        st.subheader("Create New Category")

        with st.form("create_piggy_bank_form"):
            st.markdown("**Category Details**")

            piggy_bank_name = st.text_input(
                "Category Name *",
                placeholder="e.g., Groceries, Entertainment, Travel",
                help="Required. The name of the piggy_bank."
            )

            piggy_bank_notes = st.text_area(
                "Notes (Optional)",
                placeholder="Add any additional information about this piggy_bank...",
                help="Optional. Additional notes or description for the piggy_bank."
            )

            submitted = st.form_submit_button("➕ Create Category", type="primary")

            if submitted:
                if not piggy_bank_name:
                    st.error("❌ Category name is required!")
                else:
                    # Prepare piggy_bank data
                    piggy_bank_data = {
                        'name': piggy_bank_name.strip()
                    }

                    if piggy_bank_notes and piggy_bank_notes.strip():
                        piggy_bank_data['notes'] = piggy_bank_notes.strip()

                    # Create the piggy_bank
                    with st.spinner(f"Creating piggy_bank '{piggy_bank_name}'..."):
                        success, created_piggy_bank, message = client.create_piggy_bank(piggy_bank_data)

                        if success:
                            st.success(f"✅ {message}")

                            # Show created piggy_bank details
                            with st.expander("View Created Category", expanded=True):
                                st.json(created_piggy_bank)

                            # Clear cache to force refresh
                            st.session_state.piggy_banks_cache = None
                            st.info("💡 Refresh the piggy_banks list in the 'View & Export Piggy Banks' tab to see the new piggy_bank")
                        else:
                            st.error(f"❌ {message}")

        st.markdown("---")
        st.markdown("### Edit Existing Category")
        st.markdown("To edit a piggy_bank, first refresh the piggy_banks list in the 'View & Export Piggy Banks' tab.")

        if st.session_state.piggy_banks_cache is not None:
            piggy_banks = st.session_state.piggy_banks_cache

            if len(piggy_banks) > 0:
                with st.form("update_piggy_bank_form"):
                    # Select piggy_bank to edit
                    piggy_banks_data = []
                    for piggy_bank in piggy_banks:
                        attrs = piggy_bank.get('attributes', {})
                        piggy_banks_data.append({
                            'ID': piggy_bank.get('id'),
                            'Name': attrs.get('name', 'N/A')
                        })

                    selected_piggy_bank_id = st.selectbox(
                        "Select piggy_bank to edit",
                        options=[c['ID'] for c in piggy_banks_data],
                        format_func=lambda x: f"ID {x}: {next((c['Name'] for c in piggy_banks_data if c['ID'] == x), 'N/A')}"
                    )

                    # Get selected piggy_bank details
                    selected_piggy_bank = next((c for c in piggy_banks if c.get('id') == selected_piggy_bank_id), None)
                    if selected_piggy_bank:
                        attrs = selected_piggy_bank.get('attributes', {})

                        st.markdown(f"**Editing: {attrs.get('name', 'N/A')}**")

                        new_name = st.text_input(
                            "Category Name *",
                            value=attrs.get('name', ''),
                            help="Required. The name of the piggy_bank."
                        )

                        new_notes = st.text_area(
                            "Notes (Optional)",
                            value=attrs.get('notes', ''),
                            help="Optional. Additional notes or description for the piggy_bank."
                        )

                        update_submitted = st.form_submit_button("💾 Update Category", type="primary")

                        if update_submitted:
                            if not new_name:
                                st.error("❌ Category name is required!")
                            else:
                                # Prepare updated piggy_bank data
                                updated_data = {
                                    'name': new_name.strip()
                                }

                                if new_notes and new_notes.strip():
                                    updated_data['notes'] = new_notes.strip()
                                else:
                                    updated_data['notes'] = ''

                                # Update the piggy_bank
                                with st.spinner(f"Updating piggy_bank '{new_name}'..."):
                                    success, updated_piggy_bank, message = client.update_piggy_bank(
                                        selected_piggy_bank_id,
                                        updated_data
                                    )

                                    if success:
                                        st.success(f"✅ {message}")

                                        # Show updated piggy_bank details
                                        with st.expander("View Updated Category", expanded=True):
                                            st.json(updated_piggy_bank)

                                        # Clear cache to force refresh
                                        st.session_state.piggy_banks_cache = None
                                        st.info("💡 Refresh the piggy_banks list in the 'View & Export Piggy Banks' tab to see the changes")
                                    else:
                                        st.error(f"❌ {message}")

    # TAB 3: Delete Piggy Banks
    with tab3:
        st.subheader("Delete Piggy Banks")
        st.warning("⚠️ **Warning:** Deleting piggy_banks is permanent and cannot be undone!")

        if st.session_state.piggy_banks_cache is None:
            st.info("Please refresh piggy_banks in the 'View & Export Piggy Banks' tab first")
        else:
            piggy_banks = st.session_state.piggy_banks_cache

            if len(piggy_banks) == 0:
                st.info("No piggy_banks to delete")
            else:
                # Select piggy_banks to delete
                st.markdown("**Select piggy_banks to delete:**")

                piggy_banks_data = []
                for piggy_bank in piggy_banks:
                    attrs = piggy_bank.get('attributes', {})
                    piggy_banks_data.append({
                        'ID': piggy_bank.get('id'),
                        'Name': attrs.get('name', 'N/A'),
                        'Notes': attrs.get('notes', '')[:50] if attrs.get('notes') else ''
                    })

                df = pd.DataFrame(piggy_banks_data)

                # Multi-select with checkboxes
                selected_for_deletion = st.multiselect(
                    "Choose piggy_banks to delete",
                    options=[c['ID'] for c in piggy_banks_data],
                    format_func=lambda x: f"ID {x}: {next((c['Name'] for c in piggy_banks_data if c['ID'] == x), 'N/A')}"
                )

                if selected_for_deletion:
                    st.markdown(f"**Selected {len(selected_for_deletion)} piggy_bank(ies) for deletion:**")

                    deletion_preview = df[df['ID'].isin(selected_for_deletion)]
                    st.dataframe(deletion_preview, use_container_width=True)

                    # Show detailed information for each selected piggy_bank
                    st.markdown("---")
                    st.markdown("**Review Category Details Before Deletion:**")

                    for piggy_bank_id in selected_for_deletion:
                        piggy_bank = next((c for c in piggy_banks if c.get('id') == piggy_bank_id), None)
                        if piggy_bank:
                            attrs = piggy_bank.get('attributes', {})

                            with st.expander(f"📄 Details for: {attrs.get('name', 'N/A')} (ID: {piggy_bank_id})", expanded=False):
                                col1, col2 = st.columns(2)

                                with col1:
                                    st.markdown("**Category Information**")
                                    st.markdown(f"- **Name:** {attrs.get('name', 'N/A')}")
                                    st.markdown(f"- **Created:** {attrs.get('created_at', 'N/A')}")
                                    st.markdown(f"- **Updated:** {attrs.get('updated_at', 'N/A')}")

                                with col2:
                                    st.markdown("**Notes**")
                                    notes = attrs.get('notes', '')
                                    if notes:
                                        st.markdown(notes)
                                    else:
                                        st.markdown("*No notes*")

                                # Show raw JSON
                                st.markdown("---")
                                show_raw_json = st.checkbox("🔍 Show Raw JSON", key=f"delete_json_{piggy_bank_id}")
                                if show_raw_json:
                                    st.json(piggy_bank)

                    st.markdown("---")
                    col1, col2 = st.columns([1, 3])

                    with col1:
                        confirm_delete = st.checkbox("I understand this action is permanent")

                    with col2:
                        if st.button("🗑️ Delete Selected Piggy Banks", type="primary", disabled=not confirm_delete):
                            success_count = 0
                            failed_count = 0
                            error_messages = []

                            progress_bar = st.progress(0)
                            status_text = st.empty()

                            for i, piggy_bank_id in enumerate(selected_for_deletion):
                                status_text.text(f"Deleting piggy_bank {i+1}/{len(selected_for_deletion)}...")
                                progress_bar.progress((i + 1) / len(selected_for_deletion))

                                success, message = client.delete_piggy_bank(piggy_bank_id)
                                if success:
                                    success_count += 1
                                else:
                                    failed_count += 1
                                    error_messages.append(f"Category {piggy_bank_id}: {message}")

                            status_text.empty()
                            progress_bar.empty()

                            if success_count > 0:
                                st.success(f"✅ Successfully deleted {success_count} piggy_bank(ies)")

                            if failed_count > 0:
                                st.error(f"❌ Failed to delete {failed_count} piggy_bank(ies)")
                                with st.expander("View Errors"):
                                    for error in error_messages:
                                        st.text(error)

                            # Clear cache to force refresh
                            st.session_state.piggy_banks_cache = None
                            st.info("Please refresh the piggy_banks list in the 'View & Export Piggy Banks' tab")

    # TAB 4: Import Piggy Banks
    with tab4:
        st.subheader("Import Piggy Banks")
        st.markdown("Upload a JSON file to import piggy_banks into Firefly III")

        uploaded_file = st.file_uploader(
            "Upload piggy_banks JSON file",
            type=['json'],
            help="Upload a JSON file exported from Firefly III or created manually"
        )

        if uploaded_file is not None:
            try:
                # Read the uploaded file
                file_content = uploaded_file.read().decode('utf-8')
                data = json.loads(file_content)

                # Validate the file structure
                if not isinstance(data, dict) or 'piggy_banks' not in data:
                    st.error("Invalid JSON file format. Expected 'piggy_banks' key.")
                else:
                    piggy_banks_to_import = data.get('piggy_banks', [])

                    if not isinstance(piggy_banks_to_import, list):
                        st.error("Invalid piggy_banks format. Expected a list.")
                    elif len(piggy_banks_to_import) == 0:
                        st.warning("No piggy_banks found in the uploaded file")
                    else:
                        st.success(f"✅ Loaded {len(piggy_banks_to_import)} piggy_bank(ies) from file")

                        # Show metadata if available
                        if 'export_date' in data:
                            st.info(f"Export Date: {data['export_date']}")

                        # Preview piggy_banks
                        st.markdown("**Preview of piggy_banks to import:**")

                        preview_data = []
                        for piggy_bank in piggy_banks_to_import:
                            attrs = piggy_bank.get('attributes', {})
                            notes = attrs.get('notes') or ''
                            notes_display = notes[:50] + '...' if len(notes) > 50 else notes
                            preview_data.append({
                                'Name': attrs.get('name', 'N/A'),
                                'Notes': notes_display
                            })

                        preview_df = pd.DataFrame(preview_data)
                        st.dataframe(preview_df, use_container_width=True, height=300)

                        # Import options
                        st.markdown("**Import Options**")

                        skip_existing = st.checkbox(
                            "Skip piggy_banks with matching names",
                            value=True,
                            help="Skip importing piggy_banks if a piggy_bank with the same name already exists"
                        )

                        # Debug option
                        show_debug = st.checkbox(
                            "Show debug information (API payload)",
                            value=False,
                            help="Display the exact data being sent to the API for debugging"
                        )

                        # Import button
                        col1, col2 = st.columns([1, 3])

                        with col1:
                            confirm_import = st.checkbox("Confirm import")

                        with col2:
                            if st.button("📥 Import Piggy Banks", type="primary", disabled=not confirm_import):
                                # Get existing piggy_banks to check for duplicates
                                existing_piggy_banks = []
                                if skip_existing:
                                    with st.spinner("Fetching existing piggy_banks..."):
                                        success, existing_piggy_banks_list, message = client.get_all_piggy_banks()
                                        if success:
                                            existing_piggy_banks = existing_piggy_banks_list
                                        else:
                                            st.warning("Could not fetch existing piggy_banks. Proceeding without duplicate check.")

                                existing_names = [
                                    c.get('attributes', {}).get('name', '')
                                    for c in existing_piggy_banks
                                ]

                                success_count = 0
                                skipped_count = 0
                                failed_count = 0
                                error_messages = []

                                progress_bar = st.progress(0)
                                status_text = st.empty()

                                for i, piggy_bank in enumerate(piggy_banks_to_import):
                                    attrs = piggy_bank.get('attributes', {})
                                    piggy_bank_name = attrs.get('name', 'Untitled')

                                    status_text.text(f"Importing piggy_bank {i+1}/{len(piggy_banks_to_import)}: {piggy_bank_name}")
                                    progress_bar.progress((i + 1) / len(piggy_banks_to_import))

                                    # Check for duplicates
                                    if skip_existing and piggy_bank_name in existing_names:
                                        skipped_count += 1
                                        continue

                                    # Clean and prepare piggy_bank data for import
                                    clean_attrs = {
                                        'name': attrs.get('name')
                                    }

                                    # Add notes if present
                                    if attrs.get('notes'):
                                        clean_attrs['notes'] = attrs.get('notes')

                                    # Prepare piggy_bank data for import
                                    import_piggy_bank_data = clean_attrs

                                    # Show debug info if enabled
                                    if show_debug and i == 0:  # Show only for first piggy_bank to avoid clutter
                                        with st.expander(f"Debug: API Payload for '{piggy_bank_name}'", expanded=True):
                                            st.json(import_piggy_bank_data)

                                    # Create piggy_bank
                                    success, created_piggy_bank, message = client.create_piggy_bank(import_piggy_bank_data)

                                    if success:
                                        success_count += 1
                                    else:
                                        failed_count += 1
                                        error_messages.append(f"{piggy_bank_name}: {message}")

                                status_text.empty()
                                progress_bar.empty()

                                # Show results
                                st.markdown("### Import Results")

                                col1, col2, col3 = st.columns(3)
                                with col1:
                                    st.metric("Imported", success_count)
                                with col2:
                                    st.metric("Skipped", skipped_count)
                                with col3:
                                    st.metric("Failed", failed_count)

                                if success_count > 0:
                                    st.success(f"✅ Successfully imported {success_count} piggy_bank(ies)")

                                if skipped_count > 0:
                                    st.info(f"ℹ️ Skipped {skipped_count} duplicate piggy_bank(ies)")

                                if failed_count > 0:
                                    st.error(f"❌ Failed to import {failed_count} piggy_bank(ies)")
                                    with st.expander("View Errors"):
                                        for error in error_messages:
                                            st.text(error)

                                # Clear cache to force refresh
                                st.session_state.piggy_banks_cache = None
                                st.info("Please refresh the piggy_banks list in the 'View & Export Piggy Banks' tab to see imported piggy_banks")

            except json.JSONDecodeError as e:
                st.error(f"Invalid JSON file: {str(e)}")
            except Exception as e:
                st.error(f"Error processing file: {str(e)}")

# Footer
st.sidebar.markdown("---")
st.sidebar.caption("Piggy Banks Management for Firefly III")
