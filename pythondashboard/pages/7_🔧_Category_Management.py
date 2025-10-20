"""
Firefly III Category Management Page
Export, view, create, update, delete, and import categories
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
    page_title="Category Management - Firefly III",
    page_icon="🔧",
    layout="wide"
)

st.title("🔧 Category Management")
st.markdown("Manage your Firefly III categories: export, view, create, update, delete, and import")

# Initialize session state for API connection
if 'api_connected' not in st.session_state:
    st.session_state.api_connected = False
if 'api_client' not in st.session_state:
    st.session_state.api_client = None
if 'categories_cache' not in st.session_state:
    st.session_state.categories_cache = None
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
        "📋 View & Export Categories",
        "➕ Create Category",
        "🗑️ Delete Categories",
        "📥 Import Categories"
    ])

    # TAB 1: View & Export Categories
    with tab1:
        st.subheader("View & Export Categories")

        col1, col2 = st.columns([3, 1])

        with col1:
            if st.button("🔄 Refresh Categories", type="primary"):
                with st.spinner("Fetching categories from Firefly III..."):
                    success, categories, message = client.get_all_categories()
                    if success:
                        st.session_state.categories_cache = categories
                        st.session_state.last_refresh = pd.Timestamp.now()
                        st.success(message)
                    else:
                        st.error(message)

        with col2:
            if st.session_state.last_refresh:
                st.caption(f"Last refresh: {st.session_state.last_refresh.strftime('%H:%M:%S')}")

        if st.session_state.categories_cache is not None:
            categories = st.session_state.categories_cache

            if len(categories) == 0:
                st.info("No categories found in your Firefly III instance")
            else:
                # Display summary metrics
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Categories", len(categories))
                with col2:
                    # Count categories with notes
                    categories_with_notes = sum(1 for c in categories
                                               if c.get('attributes', {}).get('notes'))
                    st.metric("With Notes", categories_with_notes)
                with col3:
                    # Count categories spent last 365 days
                    categories_with_spending = 0
                    for c in categories:
                        spent_data = c.get('attributes', {}).get('spent', [])
                        if spent_data and len(spent_data) > 0 and spent_data[0]:
                            spent_sum = float(spent_data[0].get('sum', '0'))
                            if spent_sum != 0:
                                categories_with_spending += 1
                    st.metric("With Spending", categories_with_spending)

                # Convert categories to DataFrame for display
                categories_data = []
                for category in categories:
                    attrs = category.get('attributes', {})
                    # Get spending data
                    spent_data = attrs.get('spent', [])
                    total_spent = 0
                    if spent_data and len(spent_data) > 0 and spent_data[0]:
                        total_spent = abs(float(spent_data[0].get('sum', '0')))

                    notes = attrs.get('notes') or ''
                    notes_display = notes[:50] + '...' if len(notes) > 50 else notes

                    created_at = attrs.get('created_at') or 'N/A'
                    updated_at = attrs.get('updated_at') or 'N/A'

                    categories_data.append({
                        'ID': category.get('id'),
                        'Name': attrs.get('name', 'N/A'),
                        'Notes': notes_display,
                        'Spent (Last 365d)': f"€{total_spent:,.2f}",
                        'Created': created_at[:10] if created_at != 'N/A' else 'N/A',
                        'Updated': updated_at[:10] if updated_at != 'N/A' else 'N/A'
                    })

                df = pd.DataFrame(categories_data)

                # Filter options
                st.markdown("**Filter Categories**")
                col1, col2 = st.columns(2)

                with col1:
                    search_term = st.text_input("Search by name", "")

                with col2:
                    show_with_spending_only = st.checkbox("Show only categories with spending")

                # Apply filters
                filtered_df = df.copy()

                if search_term:
                    filtered_df = filtered_df[
                        filtered_df['Name'].str.contains(search_term, case=False, na=False)
                    ]

                if show_with_spending_only:
                    filtered_df = filtered_df[filtered_df['Spent (Last 365d)'] != '€0.00']

                st.markdown(f"**Categories List** ({len(filtered_df)} categories)")
                st.dataframe(filtered_df, use_container_width=True, height=400)

                # Expandable details for each category
                with st.expander("📄 View Detailed Category Information"):
                    selected_category_id = st.selectbox(
                        "Select a category to view details",
                        options=[c['ID'] for c in categories_data],
                        format_func=lambda x: f"ID {x}: {next((c['Name'] for c in categories_data if c['ID'] == x), 'N/A')}"
                    )

                    if selected_category_id:
                        category = next((c for c in categories if c.get('id') == selected_category_id), None)
                        if category:
                            attrs = category.get('attributes', {})

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
                            show_raw_json = st.checkbox("🔍 Show Raw JSON", key=f"show_json_{selected_category_id}")
                            if show_raw_json:
                                st.json(category)

                # Export functionality
                st.markdown("---")
                st.markdown("**Export Categories**")

                col1, col2 = st.columns([2, 1])

                with col1:
                    export_filename = st.text_input(
                        "Export filename",
                        value=f"firefly_categories_export_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.json"
                    )

                with col2:
                    st.markdown("")  # Spacing
                    st.markdown("")  # Spacing

                    if st.button("💾 Export All Categories", type="primary"):
                        # Create export data
                        export_data = {
                            'export_date': pd.Timestamp.now().isoformat(),
                            'firefly_iii_categories_export': True,
                            'total_categories': len(categories),
                            'categories': categories
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

                        st.success(f"✅ Prepared {len(categories)} categories for export")

    # TAB 2: Create Category
    with tab2:
        st.subheader("Create New Category")

        with st.form("create_category_form"):
            st.markdown("**Category Details**")

            category_name = st.text_input(
                "Category Name *",
                placeholder="e.g., Groceries, Entertainment, Travel",
                help="Required. The name of the category."
            )

            category_notes = st.text_area(
                "Notes (Optional)",
                placeholder="Add any additional information about this category...",
                help="Optional. Additional notes or description for the category."
            )

            submitted = st.form_submit_button("➕ Create Category", type="primary")

            if submitted:
                if not category_name:
                    st.error("❌ Category name is required!")
                else:
                    # Prepare category data
                    category_data = {
                        'name': category_name.strip()
                    }

                    if category_notes and category_notes.strip():
                        category_data['notes'] = category_notes.strip()

                    # Create the category
                    with st.spinner(f"Creating category '{category_name}'..."):
                        success, created_category, message = client.create_category(category_data)

                        if success:
                            st.success(f"✅ {message}")

                            # Show created category details
                            with st.expander("View Created Category", expanded=True):
                                st.json(created_category)

                            # Clear cache to force refresh
                            st.session_state.categories_cache = None
                            st.info("💡 Refresh the categories list in the 'View & Export Categories' tab to see the new category")
                        else:
                            st.error(f"❌ {message}")

        st.markdown("---")
        st.markdown("### Edit Existing Category")
        st.markdown("To edit a category, first refresh the categories list in the 'View & Export Categories' tab.")

        if st.session_state.categories_cache is not None:
            categories = st.session_state.categories_cache

            if len(categories) > 0:
                with st.form("update_category_form"):
                    # Select category to edit
                    categories_data = []
                    for category in categories:
                        attrs = category.get('attributes', {})
                        categories_data.append({
                            'ID': category.get('id'),
                            'Name': attrs.get('name', 'N/A')
                        })

                    selected_category_id = st.selectbox(
                        "Select category to edit",
                        options=[c['ID'] for c in categories_data],
                        format_func=lambda x: f"ID {x}: {next((c['Name'] for c in categories_data if c['ID'] == x), 'N/A')}"
                    )

                    # Get selected category details
                    selected_category = next((c for c in categories if c.get('id') == selected_category_id), None)
                    if selected_category:
                        attrs = selected_category.get('attributes', {})

                        st.markdown(f"**Editing: {attrs.get('name', 'N/A')}**")

                        new_name = st.text_input(
                            "Category Name *",
                            value=attrs.get('name', ''),
                            help="Required. The name of the category."
                        )

                        new_notes = st.text_area(
                            "Notes (Optional)",
                            value=attrs.get('notes', ''),
                            help="Optional. Additional notes or description for the category."
                        )

                        update_submitted = st.form_submit_button("💾 Update Category", type="primary")

                        if update_submitted:
                            if not new_name:
                                st.error("❌ Category name is required!")
                            else:
                                # Prepare updated category data
                                updated_data = {
                                    'name': new_name.strip()
                                }

                                if new_notes and new_notes.strip():
                                    updated_data['notes'] = new_notes.strip()
                                else:
                                    updated_data['notes'] = ''

                                # Update the category
                                with st.spinner(f"Updating category '{new_name}'..."):
                                    success, updated_category, message = client.update_category(
                                        selected_category_id,
                                        updated_data
                                    )

                                    if success:
                                        st.success(f"✅ {message}")

                                        # Show updated category details
                                        with st.expander("View Updated Category", expanded=True):
                                            st.json(updated_category)

                                        # Clear cache to force refresh
                                        st.session_state.categories_cache = None
                                        st.info("💡 Refresh the categories list in the 'View & Export Categories' tab to see the changes")
                                    else:
                                        st.error(f"❌ {message}")

    # TAB 3: Delete Categories
    with tab3:
        st.subheader("Delete Categories")
        st.warning("⚠️ **Warning:** Deleting categories is permanent and cannot be undone!")

        if st.session_state.categories_cache is None:
            st.info("Please refresh categories in the 'View & Export Categories' tab first")
        else:
            categories = st.session_state.categories_cache

            if len(categories) == 0:
                st.info("No categories to delete")
            else:
                # Select categories to delete
                st.markdown("**Select categories to delete:**")

                categories_data = []
                for category in categories:
                    attrs = category.get('attributes', {})
                    categories_data.append({
                        'ID': category.get('id'),
                        'Name': attrs.get('name', 'N/A'),
                        'Notes': attrs.get('notes', '')[:50] if attrs.get('notes') else ''
                    })

                df = pd.DataFrame(categories_data)

                # Multi-select with checkboxes
                selected_for_deletion = st.multiselect(
                    "Choose categories to delete",
                    options=[c['ID'] for c in categories_data],
                    format_func=lambda x: f"ID {x}: {next((c['Name'] for c in categories_data if c['ID'] == x), 'N/A')}"
                )

                if selected_for_deletion:
                    st.markdown(f"**Selected {len(selected_for_deletion)} category(ies) for deletion:**")

                    deletion_preview = df[df['ID'].isin(selected_for_deletion)]
                    st.dataframe(deletion_preview, use_container_width=True)

                    # Show detailed information for each selected category
                    st.markdown("---")
                    st.markdown("**Review Category Details Before Deletion:**")

                    for category_id in selected_for_deletion:
                        category = next((c for c in categories if c.get('id') == category_id), None)
                        if category:
                            attrs = category.get('attributes', {})

                            with st.expander(f"📄 Details for: {attrs.get('name', 'N/A')} (ID: {category_id})", expanded=False):
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
                                show_raw_json = st.checkbox("🔍 Show Raw JSON", key=f"delete_json_{category_id}")
                                if show_raw_json:
                                    st.json(category)

                    st.markdown("---")
                    col1, col2 = st.columns([1, 3])

                    with col1:
                        confirm_delete = st.checkbox("I understand this action is permanent")

                    with col2:
                        if st.button("🗑️ Delete Selected Categories", type="primary", disabled=not confirm_delete):
                            success_count = 0
                            failed_count = 0
                            error_messages = []

                            progress_bar = st.progress(0)
                            status_text = st.empty()

                            for i, category_id in enumerate(selected_for_deletion):
                                status_text.text(f"Deleting category {i+1}/{len(selected_for_deletion)}...")
                                progress_bar.progress((i + 1) / len(selected_for_deletion))

                                success, message = client.delete_category(category_id)
                                if success:
                                    success_count += 1
                                else:
                                    failed_count += 1
                                    error_messages.append(f"Category {category_id}: {message}")

                            status_text.empty()
                            progress_bar.empty()

                            if success_count > 0:
                                st.success(f"✅ Successfully deleted {success_count} category(ies)")

                            if failed_count > 0:
                                st.error(f"❌ Failed to delete {failed_count} category(ies)")
                                with st.expander("View Errors"):
                                    for error in error_messages:
                                        st.text(error)

                            # Clear cache to force refresh
                            st.session_state.categories_cache = None
                            st.info("Please refresh the categories list in the 'View & Export Categories' tab")

    # TAB 4: Import Categories
    with tab4:
        st.subheader("Import Categories")
        st.markdown("Upload a JSON file to import categories into Firefly III")

        uploaded_file = st.file_uploader(
            "Upload categories JSON file",
            type=['json'],
            help="Upload a JSON file exported from Firefly III or created manually"
        )

        if uploaded_file is not None:
            try:
                # Read the uploaded file
                file_content = uploaded_file.read().decode('utf-8')
                data = json.loads(file_content)

                # Validate the file structure
                if not isinstance(data, dict) or 'categories' not in data:
                    st.error("Invalid JSON file format. Expected 'categories' key.")
                else:
                    categories_to_import = data.get('categories', [])

                    if not isinstance(categories_to_import, list):
                        st.error("Invalid categories format. Expected a list.")
                    elif len(categories_to_import) == 0:
                        st.warning("No categories found in the uploaded file")
                    else:
                        st.success(f"✅ Loaded {len(categories_to_import)} category(ies) from file")

                        # Show metadata if available
                        if 'export_date' in data:
                            st.info(f"Export Date: {data['export_date']}")

                        # Preview categories
                        st.markdown("**Preview of categories to import:**")

                        preview_data = []
                        for category in categories_to_import:
                            attrs = category.get('attributes', {})
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
                            "Skip categories with matching names",
                            value=True,
                            help="Skip importing categories if a category with the same name already exists"
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
                            if st.button("📥 Import Categories", type="primary", disabled=not confirm_import):
                                # Get existing categories to check for duplicates
                                existing_categories = []
                                if skip_existing:
                                    with st.spinner("Fetching existing categories..."):
                                        success, existing_categories_list, message = client.get_all_categories()
                                        if success:
                                            existing_categories = existing_categories_list
                                        else:
                                            st.warning("Could not fetch existing categories. Proceeding without duplicate check.")

                                existing_names = [
                                    c.get('attributes', {}).get('name', '')
                                    for c in existing_categories
                                ]

                                success_count = 0
                                skipped_count = 0
                                failed_count = 0
                                error_messages = []

                                progress_bar = st.progress(0)
                                status_text = st.empty()

                                for i, category in enumerate(categories_to_import):
                                    attrs = category.get('attributes', {})
                                    category_name = attrs.get('name', 'Untitled')

                                    status_text.text(f"Importing category {i+1}/{len(categories_to_import)}: {category_name}")
                                    progress_bar.progress((i + 1) / len(categories_to_import))

                                    # Check for duplicates
                                    if skip_existing and category_name in existing_names:
                                        skipped_count += 1
                                        continue

                                    # Clean and prepare category data for import
                                    clean_attrs = {
                                        'name': attrs.get('name')
                                    }

                                    # Add notes if present
                                    if attrs.get('notes'):
                                        clean_attrs['notes'] = attrs.get('notes')

                                    # Prepare category data for import
                                    import_category_data = clean_attrs

                                    # Show debug info if enabled
                                    if show_debug and i == 0:  # Show only for first category to avoid clutter
                                        with st.expander(f"Debug: API Payload for '{category_name}'", expanded=True):
                                            st.json(import_category_data)

                                    # Create category
                                    success, created_category, message = client.create_category(import_category_data)

                                    if success:
                                        success_count += 1
                                    else:
                                        failed_count += 1
                                        error_messages.append(f"{category_name}: {message}")

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
                                    st.success(f"✅ Successfully imported {success_count} category(ies)")

                                if skipped_count > 0:
                                    st.info(f"ℹ️ Skipped {skipped_count} duplicate category(ies)")

                                if failed_count > 0:
                                    st.error(f"❌ Failed to import {failed_count} category(ies)")
                                    with st.expander("View Errors"):
                                        for error in error_messages:
                                            st.text(error)

                                # Clear cache to force refresh
                                st.session_state.categories_cache = None
                                st.info("Please refresh the categories list in the 'View & Export Categories' tab to see imported categories")

            except json.JSONDecodeError as e:
                st.error(f"Invalid JSON file: {str(e)}")
            except Exception as e:
                st.error(f"Error processing file: {str(e)}")

# Footer
st.sidebar.markdown("---")
st.sidebar.caption("Category Management for Firefly III")
