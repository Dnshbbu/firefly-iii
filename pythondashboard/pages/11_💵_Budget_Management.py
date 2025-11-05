"""
Firefly III Budget Management Page
Export, view, create, update, delete, and import budgets
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
    page_title="Budget Management - Firefly III",
    page_icon="💵",
    layout="wide"
)

# Render custom navigation
render_sidebar_navigation()

st.title("💵 Budget Management")
st.markdown("Manage your Firefly III budgets: export, view, create, update, delete, and import")

# Initialize session state for API connection
if 'api_connected' not in st.session_state:
    st.session_state.api_connected = False
if 'firefly_url' not in st.session_state:
    st.session_state.firefly_url = get_firefly_url()
if 'firefly_token' not in st.session_state:
    st.session_state.firefly_token = get_firefly_token()
if 'budgets_cache' not in st.session_state:
    st.session_state.budgets_cache = None
if 'last_refresh_budgets' not in st.session_state:
    st.session_state.last_refresh_budgets = None
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
        "📋 View & Export Budgets",
        "➕ Create Category",
        "🗑️ Delete Budgets",
        "📥 Import Budgets"
    ])

    # TAB 1: View & Export Budgets
    with tab1:
        st.subheader("View & Export Budgets")

        col1, col2 = st.columns([3, 1])

        with col1:
            if st.button("🔄 Refresh Budgets", type="primary"):
                with st.spinner("Fetching budgets from Firefly III..."):
                    success, budgets, message = client.get_all_budgets()
                    if success:
                        st.session_state.budgets_cache = budgets
                        st.session_state.last_refresh = pd.Timestamp.now()
                        st.success(message)
                    else:
                        st.error(message)

        with col2:
            if st.session_state.last_refresh:
                st.caption(f"Last refresh: {st.session_state.last_refresh.strftime('%H:%M:%S')}")

        if st.session_state.budgets_cache is not None:
            budgets = st.session_state.budgets_cache

            if len(budgets) == 0:
                st.info("No budgets found in your Firefly III instance")
            else:
                # Display summary metrics
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Budgets", len(budgets))
                with col2:
                    # Count budgets with notes
                    budgets_with_notes = sum(1 for c in budgets
                                               if c.get('attributes', {}).get('notes'))
                    st.metric("With Notes", budgets_with_notes)
                with col3:
                    # Count budgets spent last 365 days
                    budgets_with_spending = 0
                    for c in budgets:
                        spent_data = c.get('attributes', {}).get('spent', [])
                        if spent_data and len(spent_data) > 0 and spent_data[0]:
                            spent_sum = float(spent_data[0].get('sum', '0'))
                            if spent_sum != 0:
                                budgets_with_spending += 1
                    st.metric("With Spending", budgets_with_spending)

                # Convert budgets to DataFrame for display
                budgets_data = []
                for budget in budgets:
                    attrs = budget.get('attributes', {})
                    # Get spending data
                    spent_data = attrs.get('spent', [])
                    total_spent = 0
                    if spent_data and len(spent_data) > 0 and spent_data[0]:
                        total_spent = abs(float(spent_data[0].get('sum', '0')))

                    notes = attrs.get('notes') or ''
                    notes_display = notes[:50] + '...' if len(notes) > 50 else notes

                    created_at = attrs.get('created_at') or 'N/A'
                    updated_at = attrs.get('updated_at') or 'N/A'

                    budgets_data.append({
                        'ID': budget.get('id'),
                        'Name': attrs.get('name', 'N/A'),
                        'Notes': notes_display,
                        'Spent (Last 365d)': f"€{total_spent:,.2f}",
                        'Created': created_at[:10] if created_at != 'N/A' else 'N/A',
                        'Updated': updated_at[:10] if updated_at != 'N/A' else 'N/A'
                    })

                df = pd.DataFrame(budgets_data)

                # Filter options
                st.markdown("**Filter Budgets**")
                col1, col2 = st.columns(2)

                with col1:
                    search_term = st.text_input("Search by name", "")

                with col2:
                    show_with_spending_only = st.checkbox("Show only budgets with spending")

                # Apply filters
                filtered_df = df.copy()

                if search_term:
                    filtered_df = filtered_df[
                        filtered_df['Name'].str.contains(search_term, case=False, na=False)
                    ]

                if show_with_spending_only:
                    filtered_df = filtered_df[filtered_df['Spent (Last 365d)'] != '€0.00']

                st.markdown(f"**Budgets List** ({len(filtered_df)} budgets)")
                st.dataframe(filtered_df, width='stretch', height=400)

                # Expandable details for each budget
                with st.expander("📄 View Detailed Category Information"):
                    selected_budget_id = st.selectbox(
                        "Select a budget to view details",
                        options=[c['ID'] for c in budgets_data],
                        format_func=lambda x: f"ID {x}: {next((c['Name'] for c in budgets_data if c['ID'] == x), 'N/A')}"
                    )

                    if selected_budget_id:
                        budget = next((c for c in budgets if c.get('id') == selected_budget_id), None)
                        if budget:
                            attrs = budget.get('attributes', {})

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
                            show_raw_json = st.checkbox("🔍 Show Raw JSON", key=f"show_json_{selected_budget_id}")
                            if show_raw_json:
                                st.json(budget)

                # Export functionality
                st.markdown("---")
                st.markdown("**Export Budgets**")

                col1, col2 = st.columns([2, 1])

                with col1:
                    export_filename = st.text_input(
                        "Export filename",
                        value=f"firefly_budgets_export_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.json"
                    )

                with col2:
                    st.markdown("")  # Spacing
                    st.markdown("")  # Spacing

                    if st.button("💾 Export All Budgets", type="primary"):
                        # Create export data
                        export_data = {
                            'export_date': pd.Timestamp.now().isoformat(),
                            'firefly_iii_budgets_export': True,
                            'total_budgets': len(budgets),
                            'budgets': budgets
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

                        st.success(f"✅ Prepared {len(budgets)} budgets for export")

    # TAB 2: Create Category
    with tab2:
        st.subheader("Create New Category")

        with st.form("create_budget_form"):
            st.markdown("**Category Details**")

            budget_name = st.text_input(
                "Category Name *",
                placeholder="e.g., Groceries, Entertainment, Travel",
                help="Required. The name of the budget."
            )

            budget_notes = st.text_area(
                "Notes (Optional)",
                placeholder="Add any additional information about this budget...",
                help="Optional. Additional notes or description for the budget."
            )

            submitted = st.form_submit_button("➕ Create Category", type="primary")

            if submitted:
                if not budget_name:
                    st.error("❌ Category name is required!")
                else:
                    # Prepare budget data
                    budget_data = {
                        'name': budget_name.strip()
                    }

                    if budget_notes and budget_notes.strip():
                        budget_data['notes'] = budget_notes.strip()

                    # Create the budget
                    with st.spinner(f"Creating budget '{budget_name}'..."):
                        success, created_budget, message = client.create_budget(budget_data)

                        if success:
                            st.success(f"✅ {message}")

                            # Show created budget details
                            with st.expander("View Created Category", expanded=True):
                                st.json(created_budget)

                            # Clear cache to force refresh
                            st.session_state.budgets_cache = None
                            st.info("💡 Refresh the budgets list in the 'View & Export Budgets' tab to see the new budget")
                        else:
                            st.error(f"❌ {message}")

        st.markdown("---")
        st.markdown("### Edit Existing Category")
        st.markdown("To edit a budget, first refresh the budgets list in the 'View & Export Budgets' tab.")

        if st.session_state.budgets_cache is not None:
            budgets = st.session_state.budgets_cache

            if len(budgets) > 0:
                with st.form("update_budget_form"):
                    # Select budget to edit
                    budgets_data = []
                    for budget in budgets:
                        attrs = budget.get('attributes', {})
                        budgets_data.append({
                            'ID': budget.get('id'),
                            'Name': attrs.get('name', 'N/A')
                        })

                    selected_budget_id = st.selectbox(
                        "Select budget to edit",
                        options=[c['ID'] for c in budgets_data],
                        format_func=lambda x: f"ID {x}: {next((c['Name'] for c in budgets_data if c['ID'] == x), 'N/A')}"
                    )

                    # Get selected budget details
                    selected_budget = next((c for c in budgets if c.get('id') == selected_budget_id), None)
                    if selected_budget:
                        attrs = selected_budget.get('attributes', {})

                        st.markdown(f"**Editing: {attrs.get('name', 'N/A')}**")

                        new_name = st.text_input(
                            "Category Name *",
                            value=attrs.get('name', ''),
                            help="Required. The name of the budget."
                        )

                        new_notes = st.text_area(
                            "Notes (Optional)",
                            value=attrs.get('notes', ''),
                            help="Optional. Additional notes or description for the budget."
                        )

                        update_submitted = st.form_submit_button("💾 Update Category", type="primary")

                        if update_submitted:
                            if not new_name:
                                st.error("❌ Category name is required!")
                            else:
                                # Prepare updated budget data
                                updated_data = {
                                    'name': new_name.strip()
                                }

                                if new_notes and new_notes.strip():
                                    updated_data['notes'] = new_notes.strip()
                                else:
                                    updated_data['notes'] = ''

                                # Update the budget
                                with st.spinner(f"Updating budget '{new_name}'..."):
                                    success, updated_budget, message = client.update_budget(
                                        selected_budget_id,
                                        updated_data
                                    )

                                    if success:
                                        st.success(f"✅ {message}")

                                        # Show updated budget details
                                        with st.expander("View Updated Category", expanded=True):
                                            st.json(updated_budget)

                                        # Clear cache to force refresh
                                        st.session_state.budgets_cache = None
                                        st.info("💡 Refresh the budgets list in the 'View & Export Budgets' tab to see the changes")
                                    else:
                                        st.error(f"❌ {message}")

    # TAB 3: Delete Budgets
    with tab3:
        st.subheader("Delete Budgets")
        st.warning("⚠️ **Warning:** Deleting budgets is permanent and cannot be undone!")

        if st.session_state.budgets_cache is None:
            st.info("Please refresh budgets in the 'View & Export Budgets' tab first")
        else:
            budgets = st.session_state.budgets_cache

            if len(budgets) == 0:
                st.info("No budgets to delete")
            else:
                # Select budgets to delete
                st.markdown("**Select budgets to delete:**")

                budgets_data = []
                for budget in budgets:
                    attrs = budget.get('attributes', {})
                    budgets_data.append({
                        'ID': budget.get('id'),
                        'Name': attrs.get('name', 'N/A'),
                        'Notes': attrs.get('notes', '')[:50] if attrs.get('notes') else ''
                    })

                df = pd.DataFrame(budgets_data)

                # Multi-select with checkboxes
                selected_for_deletion = st.multiselect(
                    "Choose budgets to delete",
                    options=[c['ID'] for c in budgets_data],
                    format_func=lambda x: f"ID {x}: {next((c['Name'] for c in budgets_data if c['ID'] == x), 'N/A')}"
                )

                if selected_for_deletion:
                    st.markdown(f"**Selected {len(selected_for_deletion)} budget(ies) for deletion:**")

                    deletion_preview = df[df['ID'].isin(selected_for_deletion)]
                    st.dataframe(deletion_preview, width='stretch')

                    # Show detailed information for each selected budget
                    st.markdown("---")
                    st.markdown("**Review Category Details Before Deletion:**")

                    for budget_id in selected_for_deletion:
                        budget = next((c for c in budgets if c.get('id') == budget_id), None)
                        if budget:
                            attrs = budget.get('attributes', {})

                            with st.expander(f"📄 Details for: {attrs.get('name', 'N/A')} (ID: {budget_id})", expanded=False):
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
                                show_raw_json = st.checkbox("🔍 Show Raw JSON", key=f"delete_json_{budget_id}")
                                if show_raw_json:
                                    st.json(budget)

                    st.markdown("---")
                    col1, col2 = st.columns([1, 3])

                    with col1:
                        confirm_delete = st.checkbox("I understand this action is permanent")

                    with col2:
                        if st.button("🗑️ Delete Selected Budgets", type="primary", disabled=not confirm_delete):
                            success_count = 0
                            failed_count = 0
                            error_messages = []

                            progress_bar = st.progress(0)
                            status_text = st.empty()

                            for i, budget_id in enumerate(selected_for_deletion):
                                status_text.text(f"Deleting budget {i+1}/{len(selected_for_deletion)}...")
                                progress_bar.progress((i + 1) / len(selected_for_deletion))

                                success, message = client.delete_budget(budget_id)
                                if success:
                                    success_count += 1
                                else:
                                    failed_count += 1
                                    error_messages.append(f"Category {budget_id}: {message}")

                            status_text.empty()
                            progress_bar.empty()

                            if success_count > 0:
                                st.success(f"✅ Successfully deleted {success_count} budget(ies)")

                            if failed_count > 0:
                                st.error(f"❌ Failed to delete {failed_count} budget(ies)")
                                with st.expander("View Errors"):
                                    for error in error_messages:
                                        st.text(error)

                            # Clear cache to force refresh
                            st.session_state.budgets_cache = None
                            st.info("Please refresh the budgets list in the 'View & Export Budgets' tab")

    # TAB 4: Import Budgets
    with tab4:
        st.subheader("Import Budgets")
        st.markdown("Upload a JSON file to import budgets into Firefly III")

        uploaded_file = st.file_uploader(
            "Upload budgets JSON file",
            type=['json'],
            help="Upload a JSON file exported from Firefly III or created manually"
        )

        if uploaded_file is not None:
            try:
                # Read the uploaded file
                file_content = uploaded_file.read().decode('utf-8')
                data = json.loads(file_content)

                # Validate the file structure
                if not isinstance(data, dict) or 'budgets' not in data:
                    st.error("Invalid JSON file format. Expected 'budgets' key.")
                else:
                    budgets_to_import = data.get('budgets', [])

                    if not isinstance(budgets_to_import, list):
                        st.error("Invalid budgets format. Expected a list.")
                    elif len(budgets_to_import) == 0:
                        st.warning("No budgets found in the uploaded file")
                    else:
                        st.success(f"✅ Loaded {len(budgets_to_import)} budget(ies) from file")

                        # Show metadata if available
                        if 'export_date' in data:
                            st.info(f"Export Date: {data['export_date']}")

                        # Preview budgets
                        st.markdown("**Preview of budgets to import:**")

                        preview_data = []
                        for budget in budgets_to_import:
                            attrs = budget.get('attributes', {})
                            notes = attrs.get('notes') or ''
                            notes_display = notes[:50] + '...' if len(notes) > 50 else notes
                            preview_data.append({
                                'Name': attrs.get('name', 'N/A'),
                                'Notes': notes_display
                            })

                        preview_df = pd.DataFrame(preview_data)
                        st.dataframe(preview_df, width='stretch', height=300)

                        # Import options
                        st.markdown("**Import Options**")

                        skip_existing = st.checkbox(
                            "Skip budgets with matching names",
                            value=True,
                            help="Skip importing budgets if a budget with the same name already exists"
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
                            if st.button("📥 Import Budgets", type="primary", disabled=not confirm_import):
                                # Get existing budgets to check for duplicates
                                existing_budgets = []
                                if skip_existing:
                                    with st.spinner("Fetching existing budgets..."):
                                        success, existing_budgets_list, message = client.get_all_budgets()
                                        if success:
                                            existing_budgets = existing_budgets_list
                                        else:
                                            st.warning("Could not fetch existing budgets. Proceeding without duplicate check.")

                                existing_names = [
                                    c.get('attributes', {}).get('name', '')
                                    for c in existing_budgets
                                ]

                                success_count = 0
                                skipped_count = 0
                                failed_count = 0
                                error_messages = []

                                progress_bar = st.progress(0)
                                status_text = st.empty()

                                for i, budget in enumerate(budgets_to_import):
                                    attrs = budget.get('attributes', {})
                                    budget_name = attrs.get('name', 'Untitled')

                                    status_text.text(f"Importing budget {i+1}/{len(budgets_to_import)}: {budget_name}")
                                    progress_bar.progress((i + 1) / len(budgets_to_import))

                                    # Check for duplicates
                                    if skip_existing and budget_name in existing_names:
                                        skipped_count += 1
                                        continue

                                    # Clean and prepare budget data for import
                                    clean_attrs = {
                                        'name': attrs.get('name')
                                    }

                                    # Add notes if present
                                    if attrs.get('notes'):
                                        clean_attrs['notes'] = attrs.get('notes')

                                    # Prepare budget data for import
                                    import_budget_data = clean_attrs

                                    # Show debug info if enabled
                                    if show_debug and i == 0:  # Show only for first budget to avoid clutter
                                        with st.expander(f"Debug: API Payload for '{budget_name}'", expanded=True):
                                            st.json(import_budget_data)

                                    # Create budget
                                    success, created_budget, message = client.create_budget(import_budget_data)

                                    if success:
                                        success_count += 1
                                    else:
                                        failed_count += 1
                                        error_messages.append(f"{budget_name}: {message}")

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
                                    st.success(f"✅ Successfully imported {success_count} budget(ies)")

                                if skipped_count > 0:
                                    st.info(f"ℹ️ Skipped {skipped_count} duplicate budget(ies)")

                                if failed_count > 0:
                                    st.error(f"❌ Failed to import {failed_count} budget(ies)")
                                    with st.expander("View Errors"):
                                        for error in error_messages:
                                            st.text(error)

                                # Clear cache to force refresh
                                st.session_state.budgets_cache = None
                                st.info("Please refresh the budgets list in the 'View & Export Budgets' tab to see imported budgets")

            except json.JSONDecodeError as e:
                st.error(f"Invalid JSON file: {str(e)}")
            except Exception as e:
                st.error(f"Error processing file: {str(e)}")

# Footer
st.sidebar.markdown("---")
st.sidebar.caption("Budget Management for Firefly III")
