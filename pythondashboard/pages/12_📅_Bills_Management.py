"""
Firefly III Bills & Subscriptions Management Page
Export, view, create, update, delete, and import bills
"""

import streamlit as st
import pandas as pd
import json
from pathlib import Path
import sys

# Add parent directory to path to import firefly_api
sys.path.append(str(Path(__file__).parent.parent))
from firefly_api import FireflyAPIClient

# Page configuration
st.set_page_config(
    page_title="Bills & Subscriptions Management - Firefly III",
    page_icon="📅",
    layout="wide"
)

st.title("📅 Bills & Subscriptions Management")
st.markdown("Manage your Firefly III bills: export, view, create, update, delete, and import")

# Initialize session state for API connection
if 'api_connected' not in st.session_state:
    st.session_state.api_connected = False
if 'api_client' not in st.session_state:
    st.session_state.api_client = None
if 'bills_cache' not in st.session_state:
    st.session_state.bills_cache = None
if 'last_refresh' not in st.session_state:
    st.session_state.last_refresh = None

# Sidebar - API Configuration
st.sidebar.header("🔌 API Connection")

# Get saved credentials from session state or use defaults
if 'firefly_url' not in st.session_state:
    st.session_state.firefly_url = "http://localhost"
if 'firefly_token' not in st.session_state:
    st.session_state.firefly_token = ""

firefly_url = st.sidebar.text_input(
    "Firefly III URL",
    value=st.session_state.firefly_url,
    help="Base URL of your Firefly III instance (e.g., http://localhost or http://app:8080 for Docker)"
)

firefly_token = st.sidebar.text_input(
    "Personal Access Token",
    value=st.session_state.firefly_token,
    type="password",
    help="Generate a Personal Access Token in Firefly III at Profile > OAuth > Personal Access Tokens"
)

if st.sidebar.button("Connect to Firefly III", type="primary"):
    if not firefly_url or not firefly_token:
        st.sidebar.error("Please provide both URL and Access Token")
    else:
        # Save credentials to session state
        st.session_state.firefly_url = firefly_url
        st.session_state.firefly_token = firefly_token

        # Test connection
        client = FireflyAPIClient(firefly_url, firefly_token)
        success, message = client.test_connection()

        if success:
            st.session_state.api_client = client
            st.session_state.api_connected = True
            st.sidebar.success(message)
        else:
            st.session_state.api_connected = False
            st.sidebar.error(message)

# Show connection status
if st.session_state.api_connected:
    st.sidebar.success("✅ Connected")
else:
    st.sidebar.warning("⚠️ Not connected")

# Divider
st.sidebar.markdown("---")

# Main content
if not st.session_state.api_connected:
    st.info("👈 Please connect to your Firefly III instance using the sidebar to get started")
    st.markdown("### How to get a Personal Access Token:")
    st.markdown("""
    1. Log in to your Firefly III instance
    2. Go to **Options** (top right) → **Profile**
    3. Navigate to the **OAuth** tab
    4. Under **Personal Access Tokens**, click **Create New Token**
    5. Give it a name (e.g., "Streamlit Category Manager") and click **Create**
    6. Copy the generated token and paste it above
    """)
    st.warning("⚠️ **Important:** The token is shown only once. Store it securely!")
else:
    client = st.session_state.api_client

    # Create tabs for different operations
    tab1, tab2, tab3, tab4 = st.tabs([
        "📋 View & Export Bills",
        "➕ Create Category",
        "🗑️ Delete Bills",
        "📥 Import Bills"
    ])

    # TAB 1: View & Export Bills
    with tab1:
        st.subheader("View & Export Bills")

        col1, col2 = st.columns([3, 1])

        with col1:
            if st.button("🔄 Refresh Bills", type="primary"):
                with st.spinner("Fetching bills from Firefly III..."):
                    success, bills, message = client.get_all_bills()
                    if success:
                        st.session_state.bills_cache = bills
                        st.session_state.last_refresh = pd.Timestamp.now()
                        st.success(message)
                    else:
                        st.error(message)

        with col2:
            if st.session_state.last_refresh:
                st.caption(f"Last refresh: {st.session_state.last_refresh.strftime('%H:%M:%S')}")

        if st.session_state.bills_cache is not None:
            bills = st.session_state.bills_cache

            if len(bills) == 0:
                st.info("No bills found in your Firefly III instance")
            else:
                # Display summary metrics
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Bills", len(bills))
                with col2:
                    # Count bills with notes
                    bills_with_notes = sum(1 for c in bills
                                               if c.get('attributes', {}).get('notes'))
                    st.metric("With Notes", bills_with_notes)
                with col3:
                    # Count bills spent last 365 days
                    bills_with_spending = 0
                    for c in bills:
                        spent_data = c.get('attributes', {}).get('spent', [])
                        if spent_data and len(spent_data) > 0 and spent_data[0]:
                            spent_sum = float(spent_data[0].get('sum', '0'))
                            if spent_sum != 0:
                                bills_with_spending += 1
                    st.metric("With Spending", bills_with_spending)

                # Convert bills to DataFrame for display
                bills_data = []
                for bill in bills:
                    attrs = bill.get('attributes', {})
                    # Get spending data
                    spent_data = attrs.get('spent', [])
                    total_spent = 0
                    if spent_data and len(spent_data) > 0 and spent_data[0]:
                        total_spent = abs(float(spent_data[0].get('sum', '0')))

                    notes = attrs.get('notes') or ''
                    notes_display = notes[:50] + '...' if len(notes) > 50 else notes

                    created_at = attrs.get('created_at') or 'N/A'
                    updated_at = attrs.get('updated_at') or 'N/A'

                    bills_data.append({
                        'ID': bill.get('id'),
                        'Name': attrs.get('name', 'N/A'),
                        'Notes': notes_display,
                        'Spent (Last 365d)': f"€{total_spent:,.2f}",
                        'Created': created_at[:10] if created_at != 'N/A' else 'N/A',
                        'Updated': updated_at[:10] if updated_at != 'N/A' else 'N/A'
                    })

                df = pd.DataFrame(bills_data)

                # Filter options
                st.markdown("**Filter Bills**")
                col1, col2 = st.columns(2)

                with col1:
                    search_term = st.text_input("Search by name", "")

                with col2:
                    show_with_spending_only = st.checkbox("Show only bills with spending")

                # Apply filters
                filtered_df = df.copy()

                if search_term:
                    filtered_df = filtered_df[
                        filtered_df['Name'].str.contains(search_term, case=False, na=False)
                    ]

                if show_with_spending_only:
                    filtered_df = filtered_df[filtered_df['Spent (Last 365d)'] != '€0.00']

                st.markdown(f"**Bills List** ({len(filtered_df)} bills)")
                st.dataframe(filtered_df, use_container_width=True, height=400)

                # Expandable details for each bill
                with st.expander("📄 View Detailed Category Information"):
                    selected_bill_id = st.selectbox(
                        "Select a bill to view details",
                        options=[c['ID'] for c in bills_data],
                        format_func=lambda x: f"ID {x}: {next((c['Name'] for c in bills_data if c['ID'] == x), 'N/A')}"
                    )

                    if selected_bill_id:
                        bill = next((c for c in bills if c.get('id') == selected_bill_id), None)
                        if bill:
                            attrs = bill.get('attributes', {})

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
                            show_raw_json = st.checkbox("🔍 Show Raw JSON", key=f"show_json_{selected_bill_id}")
                            if show_raw_json:
                                st.json(bill)

                # Export functionality
                st.markdown("---")
                st.markdown("**Export Bills**")

                col1, col2 = st.columns([2, 1])

                with col1:
                    export_filename = st.text_input(
                        "Export filename",
                        value=f"firefly_bills_export_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.json"
                    )

                with col2:
                    st.markdown("")  # Spacing
                    st.markdown("")  # Spacing

                    if st.button("💾 Export All Bills", type="primary"):
                        # Create export data
                        export_data = {
                            'export_date': pd.Timestamp.now().isoformat(),
                            'firefly_iii_bills_export': True,
                            'total_bills': len(bills),
                            'bills': bills
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

                        st.success(f"✅ Prepared {len(bills)} bills for export")

    # TAB 2: Create Category
    with tab2:
        st.subheader("Create New Category")

        with st.form("create_bill_form"):
            st.markdown("**Category Details**")

            bill_name = st.text_input(
                "Category Name *",
                placeholder="e.g., Groceries, Entertainment, Travel",
                help="Required. The name of the bill."
            )

            bill_notes = st.text_area(
                "Notes (Optional)",
                placeholder="Add any additional information about this bill...",
                help="Optional. Additional notes or description for the bill."
            )

            submitted = st.form_submit_button("➕ Create Category", type="primary")

            if submitted:
                if not bill_name:
                    st.error("❌ Category name is required!")
                else:
                    # Prepare bill data
                    bill_data = {
                        'name': bill_name.strip()
                    }

                    if bill_notes and bill_notes.strip():
                        bill_data['notes'] = bill_notes.strip()

                    # Create the bill
                    with st.spinner(f"Creating bill '{bill_name}'..."):
                        success, created_bill, message = client.create_bill(bill_data)

                        if success:
                            st.success(f"✅ {message}")

                            # Show created bill details
                            with st.expander("View Created Category", expanded=True):
                                st.json(created_bill)

                            # Clear cache to force refresh
                            st.session_state.bills_cache = None
                            st.info("💡 Refresh the bills list in the 'View & Export Bills' tab to see the new bill")
                        else:
                            st.error(f"❌ {message}")

        st.markdown("---")
        st.markdown("### Edit Existing Category")
        st.markdown("To edit a bill, first refresh the bills list in the 'View & Export Bills' tab.")

        if st.session_state.bills_cache is not None:
            bills = st.session_state.bills_cache

            if len(bills) > 0:
                with st.form("update_bill_form"):
                    # Select bill to edit
                    bills_data = []
                    for bill in bills:
                        attrs = bill.get('attributes', {})
                        bills_data.append({
                            'ID': bill.get('id'),
                            'Name': attrs.get('name', 'N/A')
                        })

                    selected_bill_id = st.selectbox(
                        "Select bill to edit",
                        options=[c['ID'] for c in bills_data],
                        format_func=lambda x: f"ID {x}: {next((c['Name'] for c in bills_data if c['ID'] == x), 'N/A')}"
                    )

                    # Get selected bill details
                    selected_bill = next((c for c in bills if c.get('id') == selected_bill_id), None)
                    if selected_bill:
                        attrs = selected_bill.get('attributes', {})

                        st.markdown(f"**Editing: {attrs.get('name', 'N/A')}**")

                        new_name = st.text_input(
                            "Category Name *",
                            value=attrs.get('name', ''),
                            help="Required. The name of the bill."
                        )

                        new_notes = st.text_area(
                            "Notes (Optional)",
                            value=attrs.get('notes', ''),
                            help="Optional. Additional notes or description for the bill."
                        )

                        update_submitted = st.form_submit_button("💾 Update Category", type="primary")

                        if update_submitted:
                            if not new_name:
                                st.error("❌ Category name is required!")
                            else:
                                # Prepare updated bill data
                                updated_data = {
                                    'name': new_name.strip()
                                }

                                if new_notes and new_notes.strip():
                                    updated_data['notes'] = new_notes.strip()
                                else:
                                    updated_data['notes'] = ''

                                # Update the bill
                                with st.spinner(f"Updating bill '{new_name}'..."):
                                    success, updated_bill, message = client.update_bill(
                                        selected_bill_id,
                                        updated_data
                                    )

                                    if success:
                                        st.success(f"✅ {message}")

                                        # Show updated bill details
                                        with st.expander("View Updated Category", expanded=True):
                                            st.json(updated_bill)

                                        # Clear cache to force refresh
                                        st.session_state.bills_cache = None
                                        st.info("💡 Refresh the bills list in the 'View & Export Bills' tab to see the changes")
                                    else:
                                        st.error(f"❌ {message}")

    # TAB 3: Delete Bills
    with tab3:
        st.subheader("Delete Bills")
        st.warning("⚠️ **Warning:** Deleting bills is permanent and cannot be undone!")

        if st.session_state.bills_cache is None:
            st.info("Please refresh bills in the 'View & Export Bills' tab first")
        else:
            bills = st.session_state.bills_cache

            if len(bills) == 0:
                st.info("No bills to delete")
            else:
                # Select bills to delete
                st.markdown("**Select bills to delete:**")

                bills_data = []
                for bill in bills:
                    attrs = bill.get('attributes', {})
                    bills_data.append({
                        'ID': bill.get('id'),
                        'Name': attrs.get('name', 'N/A'),
                        'Notes': attrs.get('notes', '')[:50] if attrs.get('notes') else ''
                    })

                df = pd.DataFrame(bills_data)

                # Multi-select with checkboxes
                selected_for_deletion = st.multiselect(
                    "Choose bills to delete",
                    options=[c['ID'] for c in bills_data],
                    format_func=lambda x: f"ID {x}: {next((c['Name'] for c in bills_data if c['ID'] == x), 'N/A')}"
                )

                if selected_for_deletion:
                    st.markdown(f"**Selected {len(selected_for_deletion)} bill(ies) for deletion:**")

                    deletion_preview = df[df['ID'].isin(selected_for_deletion)]
                    st.dataframe(deletion_preview, use_container_width=True)

                    # Show detailed information for each selected bill
                    st.markdown("---")
                    st.markdown("**Review Category Details Before Deletion:**")

                    for bill_id in selected_for_deletion:
                        bill = next((c for c in bills if c.get('id') == bill_id), None)
                        if bill:
                            attrs = bill.get('attributes', {})

                            with st.expander(f"📄 Details for: {attrs.get('name', 'N/A')} (ID: {bill_id})", expanded=False):
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
                                show_raw_json = st.checkbox("🔍 Show Raw JSON", key=f"delete_json_{bill_id}")
                                if show_raw_json:
                                    st.json(bill)

                    st.markdown("---")
                    col1, col2 = st.columns([1, 3])

                    with col1:
                        confirm_delete = st.checkbox("I understand this action is permanent")

                    with col2:
                        if st.button("🗑️ Delete Selected Bills", type="primary", disabled=not confirm_delete):
                            success_count = 0
                            failed_count = 0
                            error_messages = []

                            progress_bar = st.progress(0)
                            status_text = st.empty()

                            for i, bill_id in enumerate(selected_for_deletion):
                                status_text.text(f"Deleting bill {i+1}/{len(selected_for_deletion)}...")
                                progress_bar.progress((i + 1) / len(selected_for_deletion))

                                success, message = client.delete_bill(bill_id)
                                if success:
                                    success_count += 1
                                else:
                                    failed_count += 1
                                    error_messages.append(f"Category {bill_id}: {message}")

                            status_text.empty()
                            progress_bar.empty()

                            if success_count > 0:
                                st.success(f"✅ Successfully deleted {success_count} bill(ies)")

                            if failed_count > 0:
                                st.error(f"❌ Failed to delete {failed_count} bill(ies)")
                                with st.expander("View Errors"):
                                    for error in error_messages:
                                        st.text(error)

                            # Clear cache to force refresh
                            st.session_state.bills_cache = None
                            st.info("Please refresh the bills list in the 'View & Export Bills' tab")

    # TAB 4: Import Bills
    with tab4:
        st.subheader("Import Bills")
        st.markdown("Upload a JSON file to import bills into Firefly III")

        uploaded_file = st.file_uploader(
            "Upload bills JSON file",
            type=['json'],
            help="Upload a JSON file exported from Firefly III or created manually"
        )

        if uploaded_file is not None:
            try:
                # Read the uploaded file
                file_content = uploaded_file.read().decode('utf-8')
                data = json.loads(file_content)

                # Validate the file structure
                if not isinstance(data, dict) or 'bills' not in data:
                    st.error("Invalid JSON file format. Expected 'bills' key.")
                else:
                    bills_to_import = data.get('bills', [])

                    if not isinstance(bills_to_import, list):
                        st.error("Invalid bills format. Expected a list.")
                    elif len(bills_to_import) == 0:
                        st.warning("No bills found in the uploaded file")
                    else:
                        st.success(f"✅ Loaded {len(bills_to_import)} bill(ies) from file")

                        # Show metadata if available
                        if 'export_date' in data:
                            st.info(f"Export Date: {data['export_date']}")

                        # Preview bills
                        st.markdown("**Preview of bills to import:**")

                        preview_data = []
                        for bill in bills_to_import:
                            attrs = bill.get('attributes', {})
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
                            "Skip bills with matching names",
                            value=True,
                            help="Skip importing bills if a bill with the same name already exists"
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
                            if st.button("📥 Import Bills", type="primary", disabled=not confirm_import):
                                # Get existing bills to check for duplicates
                                existing_bills = []
                                if skip_existing:
                                    with st.spinner("Fetching existing bills..."):
                                        success, existing_bills_list, message = client.get_all_bills()
                                        if success:
                                            existing_bills = existing_bills_list
                                        else:
                                            st.warning("Could not fetch existing bills. Proceeding without duplicate check.")

                                existing_names = [
                                    c.get('attributes', {}).get('name', '')
                                    for c in existing_bills
                                ]

                                success_count = 0
                                skipped_count = 0
                                failed_count = 0
                                error_messages = []

                                progress_bar = st.progress(0)
                                status_text = st.empty()

                                for i, bill in enumerate(bills_to_import):
                                    attrs = bill.get('attributes', {})
                                    bill_name = attrs.get('name', 'Untitled')

                                    status_text.text(f"Importing bill {i+1}/{len(bills_to_import)}: {bill_name}")
                                    progress_bar.progress((i + 1) / len(bills_to_import))

                                    # Check for duplicates
                                    if skip_existing and bill_name in existing_names:
                                        skipped_count += 1
                                        continue

                                    # Clean and prepare bill data for import
                                    clean_attrs = {
                                        'name': attrs.get('name')
                                    }

                                    # Add notes if present
                                    if attrs.get('notes'):
                                        clean_attrs['notes'] = attrs.get('notes')

                                    # Prepare bill data for import
                                    import_bill_data = clean_attrs

                                    # Show debug info if enabled
                                    if show_debug and i == 0:  # Show only for first bill to avoid clutter
                                        with st.expander(f"Debug: API Payload for '{bill_name}'", expanded=True):
                                            st.json(import_bill_data)

                                    # Create bill
                                    success, created_bill, message = client.create_bill(import_bill_data)

                                    if success:
                                        success_count += 1
                                    else:
                                        failed_count += 1
                                        error_messages.append(f"{bill_name}: {message}")

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
                                    st.success(f"✅ Successfully imported {success_count} bill(ies)")

                                if skipped_count > 0:
                                    st.info(f"ℹ️ Skipped {skipped_count} duplicate bill(ies)")

                                if failed_count > 0:
                                    st.error(f"❌ Failed to import {failed_count} bill(ies)")
                                    with st.expander("View Errors"):
                                        for error in error_messages:
                                            st.text(error)

                                # Clear cache to force refresh
                                st.session_state.bills_cache = None
                                st.info("Please refresh the bills list in the 'View & Export Bills' tab to see imported bills")

            except json.JSONDecodeError as e:
                st.error(f"Invalid JSON file: {str(e)}")
            except Exception as e:
                st.error(f"Error processing file: {str(e)}")

# Footer
st.sidebar.markdown("---")
st.sidebar.caption("Bills & Subscriptions Management for Firefly III")
