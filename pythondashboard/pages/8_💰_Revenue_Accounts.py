"""
Firefly III Revenue Accounts Management Page
Export, view, create, update, delete, and import revenue accounts
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

# Page configuration
st.set_page_config(
    page_title="Revenue Accounts - Firefly III",
    page_icon="💰",
    layout="wide"
)

# Render custom navigation
render_sidebar_navigation()

st.title("💰 Revenue Accounts Management")
st.markdown("Manage your Firefly III revenue accounts: export, view, create, update, delete, and import")

# Account type for this page
ACCOUNT_TYPE = "revenue"
ACCOUNT_TYPE_DISPLAY = "Revenue"

# Initialize session state for API connection
if 'api_connected' not in st.session_state:
    st.session_state.api_connected = False
if 'api_client' not in st.session_state:
    st.session_state.api_client = None
if 'revenue_accounts_cache' not in st.session_state:
    st.session_state.revenue_accounts_cache = None
if 'last_refresh_revenue' not in st.session_state:
    st.session_state.last_refresh_revenue = None

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
    5. Give it a name (e.g., "Streamlit Account Manager") and click **Create**
    6. Copy the generated token and paste it above
    """)
    st.warning("⚠️ **Important:** The token is shown only once. Store it securely!")
else:
    client = st.session_state.api_client

    # Create tabs for different operations
    tab1, tab2, tab3, tab4 = st.tabs([
        "📋 View & Export Accounts",
        "➕ Create Account",
        "🗑️ Delete Accounts",
        "📥 Import Accounts"
    ])

    # TAB 1: View & Export Accounts
    with tab1:
        st.subheader(f"View & Export {ACCOUNT_TYPE_DISPLAY} Accounts")

        col1, col2 = st.columns([3, 1])

        with col1:
            if st.button(f"🔄 Refresh {ACCOUNT_TYPE_DISPLAY} Accounts", type="primary"):
                with st.spinner(f"Fetching {ACCOUNT_TYPE_DISPLAY.lower()} accounts from Firefly III..."):
                    success, accounts, message = client.get_all_accounts(account_type=ACCOUNT_TYPE)
                    if success:
                        st.session_state.revenue_accounts_cache = accounts
                        st.session_state.last_refresh_revenue = pd.Timestamp.now()
                        st.success(message)
                    else:
                        st.error(message)

        with col2:
            if st.session_state.last_refresh_revenue:
                st.caption(f"Last refresh: {st.session_state.last_refresh_revenue.strftime('%H:%M:%S')}")

        if st.session_state.revenue_accounts_cache is not None:
            accounts = st.session_state.revenue_accounts_cache

            if len(accounts) == 0:
                st.info(f"No {ACCOUNT_TYPE_DISPLAY.lower()} accounts found in your Firefly III instance")
            else:
                # Display summary metrics
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric(f"Total {ACCOUNT_TYPE_DISPLAY} Accounts", len(accounts))
                with col2:
                    active_count = sum(1 for a in accounts
                                      if a.get('attributes', {}).get('active', True))
                    st.metric("Active", active_count)
                with col3:
                    inactive_count = len(accounts) - active_count
                    st.metric("Inactive", inactive_count)

                # Convert accounts to DataFrame for display
                accounts_data = []
                for account in accounts:
                    attrs = account.get('attributes', {})

                    # Get current balance
                    current_balance = attrs.get('current_balance') or '0'
                    currency_code = attrs.get('currency_code') or 'EUR'

                    notes = attrs.get('notes') or ''
                    notes_display = notes[:50] + '...' if len(notes) > 50 else notes

                    created_at = attrs.get('created_at') or 'N/A'
                    updated_at = attrs.get('updated_at') or 'N/A'

                    accounts_data.append({
                        'ID': account.get('id'),
                        'Name': attrs.get('name', 'N/A'),
                        'Active': '✅' if attrs.get('active', True) else '❌',
                        'Balance': f"{currency_code} {float(current_balance):,.2f}",
                        'Notes': notes_display,
                        'Created': created_at[:10] if created_at != 'N/A' else 'N/A',
                        'Updated': updated_at[:10] if updated_at != 'N/A' else 'N/A'
                    })

                df = pd.DataFrame(accounts_data)

                # Filter options
                st.markdown("**Filter Accounts**")
                col1, col2 = st.columns(2)

                with col1:
                    search_term = st.text_input("Search by name", "")

                with col2:
                    status_filter = st.selectbox("Status", ["All", "Active Only", "Inactive Only"])

                # Apply filters
                filtered_df = df.copy()

                if search_term:
                    filtered_df = filtered_df[
                        filtered_df['Name'].str.contains(search_term, case=False, na=False)
                    ]

                if status_filter == "Active Only":
                    filtered_df = filtered_df[filtered_df['Active'] == '✅']
                elif status_filter == "Inactive Only":
                    filtered_df = filtered_df[filtered_df['Active'] == '❌']

                st.markdown(f"**Accounts List** ({len(filtered_df)} accounts)")
                st.dataframe(filtered_df, use_container_width=True, height=400)

                # Expandable details for each account
                with st.expander("📄 View Detailed Account Information"):
                    selected_account_id = st.selectbox(
                        "Select an account to view details",
                        options=[a['ID'] for a in accounts_data],
                        format_func=lambda x: f"ID {x}: {next((a['Name'] for a in accounts_data if a['ID'] == x), 'N/A')}"
                    )

                    if selected_account_id:
                        account = next((a for a in accounts if a.get('id') == selected_account_id), None)
                        if account:
                            attrs = account.get('attributes', {})

                            col1, col2 = st.columns(2)

                            with col1:
                                st.markdown("**Account Information**")
                                st.markdown(f"- **Name:** {attrs.get('name', 'N/A')}")
                                st.markdown(f"- **Type:** {attrs.get('type', 'N/A')}")
                                st.markdown(f"- **Active:** {attrs.get('active', True)}")
                                st.markdown(f"- **Currency:** {attrs.get('currency_code', 'N/A')}")
                                st.markdown(f"- **Current Balance:** {attrs.get('currency_code', 'EUR')} {float(attrs.get('current_balance', '0')):,.2f}")
                                st.markdown(f"- **IBAN:** {attrs.get('iban', 'N/A')}")
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
                            show_raw_json = st.checkbox("🔍 Show Raw JSON", key=f"show_json_{selected_account_id}")
                            if show_raw_json:
                                st.json(account)

                # Export functionality
                st.markdown("---")
                st.markdown("**Export Accounts**")

                col1, col2 = st.columns([2, 1])

                with col1:
                    export_filename = st.text_input(
                        "Export filename",
                        value=f"firefly_{ACCOUNT_TYPE}_accounts_export_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.json"
                    )

                with col2:
                    st.markdown("")  # Spacing
                    st.markdown("")  # Spacing

                    if st.button(f"💾 Export All {ACCOUNT_TYPE_DISPLAY} Accounts", type="primary"):
                        # Create export data
                        export_data = {
                            'export_date': pd.Timestamp.now().isoformat(),
                            'firefly_iii_accounts_export': True,
                            'account_type': ACCOUNT_TYPE,
                            'total_accounts': len(accounts),
                            'accounts': accounts
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

                        st.success(f"✅ Prepared {len(accounts)} {ACCOUNT_TYPE_DISPLAY.lower()} accounts for export")

    # TAB 2: Create Account
    with tab2:
        st.subheader(f"Create New {ACCOUNT_TYPE_DISPLAY} Account")

        with st.form("create_account_form"):
            st.markdown("**Account Details**")

            account_name = st.text_input(
                "Account Name *",
                placeholder=f"e.g., Freelance Income, Salary, Investment Returns",
                help="Required. The name of the account."
            )

            account_currency = st.selectbox(
                "Currency *",
                options=["EUR", "USD", "GBP", "JPY", "AUD", "CAD", "CHF", "CNY", "INR"],
                help="Required. The currency for this account."
            )

            account_iban = st.text_input(
                "IBAN (Optional)",
                placeholder="e.g., GB29 NWBK 6016 1331 9268 19",
                help="Optional. International Bank Account Number."
            )

            account_notes = st.text_area(
                "Notes (Optional)",
                placeholder="Add any additional information about this account...",
                help="Optional. Additional notes or description for the account."
            )

            col1, col2 = st.columns(2)

            with col1:
                account_active = st.checkbox("Active", value=True, help="Is this account active?")

            with col2:
                include_net_worth = st.checkbox(
                    "Include in net worth",
                    value=False,
                    help="Should this account be included in net worth calculations?"
                )

            submitted = st.form_submit_button(f"➕ Create {ACCOUNT_TYPE_DISPLAY} Account", type="primary")

            if submitted:
                if not account_name:
                    st.error("❌ Account name is required!")
                else:
                    # Prepare account data
                    account_data = {
                        'name': account_name.strip(),
                        'type': ACCOUNT_TYPE,
                        'currency_code': account_currency,
                        'active': account_active,
                        'include_net_worth': include_net_worth
                    }

                    if account_iban and account_iban.strip():
                        account_data['iban'] = account_iban.strip()

                    if account_notes and account_notes.strip():
                        account_data['notes'] = account_notes.strip()

                    # Create the account
                    with st.spinner(f"Creating {ACCOUNT_TYPE_DISPLAY.lower()} account '{account_name}'..."):
                        success, created_account, message = client.create_account(account_data)

                        if success:
                            st.success(f"✅ {message}")

                            # Show created account details
                            with st.expander("View Created Account", expanded=True):
                                st.json(created_account)

                            # Clear cache to force refresh
                            st.session_state.revenue_accounts_cache = None
                            st.info("💡 Refresh the accounts list in the 'View & Export Accounts' tab to see the new account")
                        else:
                            st.error(f"❌ {message}")

        st.markdown("---")
        st.markdown("### Edit Existing Account")
        st.markdown("To edit an account, first refresh the accounts list in the 'View & Export Accounts' tab.")

        if st.session_state.revenue_accounts_cache is not None:
            accounts = st.session_state.revenue_accounts_cache

            if len(accounts) > 0:
                with st.form("update_account_form"):
                    # Select account to edit
                    accounts_data = []
                    for account in accounts:
                        attrs = account.get('attributes', {})
                        accounts_data.append({
                            'ID': account.get('id'),
                            'Name': attrs.get('name', 'N/A')
                        })

                    selected_account_id = st.selectbox(
                        "Select account to edit",
                        options=[a['ID'] for a in accounts_data],
                        format_func=lambda x: f"ID {x}: {next((a['Name'] for a in accounts_data if a['ID'] == x), 'N/A')}"
                    )

                    # Get selected account details
                    selected_account = next((a for a in accounts if a.get('id') == selected_account_id), None)
                    if selected_account:
                        attrs = selected_account.get('attributes', {})

                        st.markdown(f"**Editing: {attrs.get('name', 'N/A')}**")

                        new_name = st.text_input(
                            "Account Name *",
                            value=attrs.get('name', ''),
                            help="Required. The name of the account."
                        )

                        new_currency = st.selectbox(
                            "Currency *",
                            options=["EUR", "USD", "GBP", "JPY", "AUD", "CAD", "CHF", "CNY", "INR"],
                            index=["EUR", "USD", "GBP", "JPY", "AUD", "CAD", "CHF", "CNY", "INR"].index(attrs.get('currency_code', 'EUR')) if attrs.get('currency_code', 'EUR') in ["EUR", "USD", "GBP", "JPY", "AUD", "CAD", "CHF", "CNY", "INR"] else 0,
                            help="Required. The currency for this account."
                        )

                        new_iban = st.text_input(
                            "IBAN (Optional)",
                            value=attrs.get('iban', ''),
                            help="Optional. International Bank Account Number."
                        )

                        new_notes = st.text_area(
                            "Notes (Optional)",
                            value=attrs.get('notes', ''),
                            help="Optional. Additional notes or description for the account."
                        )

                        col1, col2 = st.columns(2)

                        with col1:
                            new_active = st.checkbox("Active", value=attrs.get('active', True), help="Is this account active?")

                        with col2:
                            new_include_net_worth = st.checkbox(
                                "Include in net worth",
                                value=attrs.get('include_net_worth', False),
                                help="Should this account be included in net worth calculations?"
                            )

                        update_submitted = st.form_submit_button("💾 Update Account", type="primary")

                        if update_submitted:
                            if not new_name:
                                st.error("❌ Account name is required!")
                            else:
                                # Prepare updated account data
                                updated_data = {
                                    'name': new_name.strip(),
                                    'type': ACCOUNT_TYPE,
                                    'currency_code': new_currency,
                                    'active': new_active,
                                    'include_net_worth': new_include_net_worth
                                }

                                if new_iban and new_iban.strip():
                                    updated_data['iban'] = new_iban.strip()
                                else:
                                    updated_data['iban'] = ''

                                if new_notes and new_notes.strip():
                                    updated_data['notes'] = new_notes.strip()
                                else:
                                    updated_data['notes'] = ''

                                # Update the account
                                with st.spinner(f"Updating account '{new_name}'..."):
                                    success, updated_account, message = client.update_account(
                                        selected_account_id,
                                        updated_data
                                    )

                                    if success:
                                        st.success(f"✅ {message}")

                                        # Show updated account details
                                        with st.expander("View Updated Account", expanded=True):
                                            st.json(updated_account)

                                        # Clear cache to force refresh
                                        st.session_state.revenue_accounts_cache = None
                                        st.info("💡 Refresh the accounts list in the 'View & Export Accounts' tab to see the changes")
                                    else:
                                        st.error(f"❌ {message}")

    # TAB 3: Delete Accounts
    with tab3:
        st.subheader(f"Delete {ACCOUNT_TYPE_DISPLAY} Accounts")
        st.warning("⚠️ **Warning:** Deleting accounts is permanent and cannot be undone!")

        if st.session_state.revenue_accounts_cache is None:
            st.info("Please refresh accounts in the 'View & Export Accounts' tab first")
        else:
            accounts = st.session_state.revenue_accounts_cache

            if len(accounts) == 0:
                st.info(f"No {ACCOUNT_TYPE_DISPLAY.lower()} accounts to delete")
            else:
                # Select accounts to delete
                st.markdown("**Select accounts to delete:**")

                accounts_data = []
                for account in accounts:
                    attrs = account.get('attributes', {})
                    accounts_data.append({
                        'ID': account.get('id'),
                        'Name': attrs.get('name', 'N/A'),
                        'Active': '✅' if attrs.get('active', True) else '❌',
                        'Balance': f"{attrs.get('currency_code', 'EUR')} {float(attrs.get('current_balance', '0')):,.2f}"
                    })

                df = pd.DataFrame(accounts_data)

                # Multi-select with checkboxes
                selected_for_deletion = st.multiselect(
                    "Choose accounts to delete",
                    options=[a['ID'] for a in accounts_data],
                    format_func=lambda x: f"ID {x}: {next((a['Name'] for a in accounts_data if a['ID'] == x), 'N/A')}"
                )

                if selected_for_deletion:
                    st.markdown(f"**Selected {len(selected_for_deletion)} account(s) for deletion:**")

                    deletion_preview = df[df['ID'].isin(selected_for_deletion)]
                    st.dataframe(deletion_preview, use_container_width=True)

                    # Show detailed information for each selected account
                    st.markdown("---")
                    st.markdown("**Review Account Details Before Deletion:**")

                    for account_id in selected_for_deletion:
                        account = next((a for a in accounts if a.get('id') == account_id), None)
                        if account:
                            attrs = account.get('attributes', {})

                            with st.expander(f"📄 Details for: {attrs.get('name', 'N/A')} (ID: {account_id})", expanded=False):
                                col1, col2 = st.columns(2)

                                with col1:
                                    st.markdown("**Account Information**")
                                    st.markdown(f"- **Name:** {attrs.get('name', 'N/A')}")
                                    st.markdown(f"- **Type:** {attrs.get('type', 'N/A')}")
                                    st.markdown(f"- **Active:** {attrs.get('active', True)}")
                                    st.markdown(f"- **Currency:** {attrs.get('currency_code', 'N/A')}")
                                    st.markdown(f"- **Balance:** {attrs.get('currency_code', 'EUR')} {float(attrs.get('current_balance', '0')):,.2f}")
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
                                show_raw_json = st.checkbox("🔍 Show Raw JSON", key=f"delete_json_{account_id}")
                                if show_raw_json:
                                    st.json(account)

                    st.markdown("---")
                    col1, col2 = st.columns([1, 3])

                    with col1:
                        confirm_delete = st.checkbox("I understand this action is permanent")

                    with col2:
                        if st.button(f"🗑️ Delete Selected {ACCOUNT_TYPE_DISPLAY} Accounts", type="primary", disabled=not confirm_delete):
                            success_count = 0
                            failed_count = 0
                            error_messages = []

                            progress_bar = st.progress(0)
                            status_text = st.empty()

                            for i, account_id in enumerate(selected_for_deletion):
                                status_text.text(f"Deleting account {i+1}/{len(selected_for_deletion)}...")
                                progress_bar.progress((i + 1) / len(selected_for_deletion))

                                success, message = client.delete_account(account_id)
                                if success:
                                    success_count += 1
                                else:
                                    failed_count += 1
                                    error_messages.append(f"Account {account_id}: {message}")

                            status_text.empty()
                            progress_bar.empty()

                            if success_count > 0:
                                st.success(f"✅ Successfully deleted {success_count} account(s)")

                            if failed_count > 0:
                                st.error(f"❌ Failed to delete {failed_count} account(s)")
                                with st.expander("View Errors"):
                                    for error in error_messages:
                                        st.text(error)

                            # Clear cache to force refresh
                            st.session_state.revenue_accounts_cache = None
                            st.info("Please refresh the accounts list in the 'View & Export Accounts' tab")

    # TAB 4: Import Accounts
    with tab4:
        st.subheader(f"Import {ACCOUNT_TYPE_DISPLAY} Accounts")
        st.markdown("Upload a JSON file to import accounts into Firefly III")

        uploaded_file = st.file_uploader(
            "Upload accounts JSON file",
            type=['json'],
            help="Upload a JSON file exported from Firefly III or created manually"
        )

        if uploaded_file is not None:
            try:
                # Read the uploaded file
                file_content = uploaded_file.read().decode('utf-8')
                data = json.loads(file_content)

                # Validate the file structure
                if not isinstance(data, dict) or 'accounts' not in data:
                    st.error("Invalid JSON file format. Expected 'accounts' key.")
                else:
                    accounts_to_import = data.get('accounts', [])

                    # Filter by account type if specified
                    if data.get('account_type') and data.get('account_type') != ACCOUNT_TYPE:
                        st.warning(f"⚠️ This file contains {data.get('account_type')} accounts, but you're importing into {ACCOUNT_TYPE} accounts. Filtering...")
                        accounts_to_import = [a for a in accounts_to_import if a.get('attributes', {}).get('type') == ACCOUNT_TYPE]

                    if not isinstance(accounts_to_import, list):
                        st.error("Invalid accounts format. Expected a list.")
                    elif len(accounts_to_import) == 0:
                        st.warning("No accounts found in the uploaded file")
                    else:
                        st.success(f"✅ Loaded {len(accounts_to_import)} account(s) from file")

                        # Show metadata if available
                        if 'export_date' in data:
                            st.info(f"Export Date: {data['export_date']}")

                        # Preview accounts
                        st.markdown("**Preview of accounts to import:**")

                        preview_data = []
                        for account in accounts_to_import:
                            attrs = account.get('attributes', {})
                            notes = attrs.get('notes') or ''
                            notes_display = notes[:50] + '...' if len(notes) > 50 else notes
                            preview_data.append({
                                'Name': attrs.get('name', 'N/A'),
                                'Type': attrs.get('type', 'N/A'),
                                'Currency': attrs.get('currency_code', 'N/A'),
                                'Active': '✅' if attrs.get('active', True) else '❌',
                                'Notes': notes_display
                            })

                        preview_df = pd.DataFrame(preview_data)
                        st.dataframe(preview_df, use_container_width=True, height=300)

                        # Import options
                        st.markdown("**Import Options**")

                        skip_existing = st.checkbox(
                            "Skip accounts with matching names",
                            value=True,
                            help="Skip importing accounts if an account with the same name already exists"
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
                            if st.button(f"📥 Import {ACCOUNT_TYPE_DISPLAY} Accounts", type="primary", disabled=not confirm_import):
                                # Get existing accounts to check for duplicates
                                existing_accounts = []
                                if skip_existing:
                                    with st.spinner("Fetching existing accounts..."):
                                        success, existing_accounts_list, message = client.get_all_accounts(account_type=ACCOUNT_TYPE)
                                        if success:
                                            existing_accounts = existing_accounts_list
                                        else:
                                            st.warning("Could not fetch existing accounts. Proceeding without duplicate check.")

                                existing_names = [
                                    a.get('attributes', {}).get('name', '')
                                    for a in existing_accounts
                                ]

                                success_count = 0
                                skipped_count = 0
                                failed_count = 0
                                error_messages = []

                                progress_bar = st.progress(0)
                                status_text = st.empty()

                                for i, account in enumerate(accounts_to_import):
                                    attrs = account.get('attributes', {})
                                    account_name = attrs.get('name', 'Untitled')

                                    status_text.text(f"Importing account {i+1}/{len(accounts_to_import)}: {account_name}")
                                    progress_bar.progress((i + 1) / len(accounts_to_import))

                                    # Check for duplicates
                                    if skip_existing and account_name in existing_names:
                                        skipped_count += 1
                                        continue

                                    # Clean and prepare account data for import
                                    clean_attrs = {
                                        'name': attrs.get('name'),
                                        'type': ACCOUNT_TYPE,  # Force the type to match this page
                                        'currency_code': attrs.get('currency_code', 'EUR'),
                                        'active': attrs.get('active', True),
                                        'include_net_worth': attrs.get('include_net_worth', False)
                                    }

                                    # Add optional fields
                                    if attrs.get('iban'):
                                        clean_attrs['iban'] = attrs.get('iban')

                                    if attrs.get('notes'):
                                        clean_attrs['notes'] = attrs.get('notes')

                                    # Prepare account data for import
                                    import_account_data = clean_attrs

                                    # Show debug info if enabled
                                    if show_debug and i == 0:  # Show only for first account to avoid clutter
                                        with st.expander(f"Debug: API Payload for '{account_name}'", expanded=True):
                                            st.json(import_account_data)

                                    # Create account
                                    success, created_account, message = client.create_account(import_account_data)

                                    if success:
                                        success_count += 1
                                    else:
                                        failed_count += 1
                                        error_messages.append(f"{account_name}: {message}")

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
                                    st.success(f"✅ Successfully imported {success_count} account(s)")

                                if skipped_count > 0:
                                    st.info(f"ℹ️ Skipped {skipped_count} duplicate account(s)")

                                if failed_count > 0:
                                    st.error(f"❌ Failed to import {failed_count} account(s)")
                                    with st.expander("View Errors"):
                                        for error in error_messages:
                                            st.text(error)

                                # Clear cache to force refresh
                                st.session_state.revenue_accounts_cache = None
                                st.info("Please refresh the accounts list in the 'View & Export Accounts' tab to see imported accounts")

            except json.JSONDecodeError as e:
                st.error(f"Invalid JSON file: {str(e)}")
            except Exception as e:
                st.error(f"Error processing file: {str(e)}")

# Footer
st.sidebar.markdown("---")
st.sidebar.caption(f"{ACCOUNT_TYPE_DISPLAY} Accounts Management for Firefly III")
