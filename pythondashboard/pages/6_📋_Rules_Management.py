"""
Firefly III Rules Management Page
Export, view, delete, and import transaction rules
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
    page_title="Rules Management - Firefly III",
    page_icon="📋",
    layout="wide"
)

# Render custom navigation
render_sidebar_navigation()

st.title("📋 Rules Management")
st.markdown("Manage your Firefly III transaction rules: export, view, delete, and import")

# Initialize session state for API connection
if 'api_connected' not in st.session_state:
    st.session_state.api_connected = False
if 'api_client' not in st.session_state:
    st.session_state.api_client = None
if 'rules_cache' not in st.session_state:
    st.session_state.rules_cache = None
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
    5. Give it a name (e.g., "Streamlit Rules Manager") and click **Create**
    6. Copy the generated token and paste it above
    """)
    st.warning("⚠️ **Important:** The token is shown only once. Store it securely!")
else:
    # Recreate client from stored credentials (compatible with Dashboard pages)
    client = FireflyAPIClient(st.session_state.firefly_url, st.session_state.firefly_token)

    # Create tabs for different operations
    tab1, tab2, tab3 = st.tabs(["📋 View & Export Rules", "🗑️ Delete Rules", "📥 Import Rules"])

    # TAB 1: View & Export Rules
    with tab1:
        st.subheader("View & Export Rules")

        col1, col2 = st.columns([3, 1])

        with col1:
            if st.button("🔄 Refresh Rules", type="primary"):
                with st.spinner("Fetching rules from Firefly III..."):
                    success, rules, message = client.get_all_rules()
                    if success:
                        st.session_state.rules_cache = rules
                        st.session_state.last_refresh = pd.Timestamp.now()
                        st.success(message)
                    else:
                        st.error(message)

        with col2:
            if st.session_state.last_refresh:
                st.caption(f"Last refresh: {st.session_state.last_refresh.strftime('%H:%M:%S')}")

        if st.session_state.rules_cache is not None:
            rules = st.session_state.rules_cache

            if len(rules) == 0:
                st.info("No rules found in your Firefly III instance")
            else:
                # Display summary metrics
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Rules", len(rules))
                with col2:
                    active_count = sum(1 for r in rules if r.get('attributes', {}).get('active', False))
                    st.metric("Active Rules", active_count)
                with col3:
                    inactive_count = len(rules) - active_count
                    st.metric("Inactive Rules", inactive_count)

                # Convert rules to DataFrame for display
                rules_data = []
                for rule in rules:
                    attrs = rule.get('attributes', {})
                    rules_data.append({
                        'ID': rule.get('id'),
                        'Title': attrs.get('title', 'N/A'),
                        'Active': '✅' if attrs.get('active', False) else '❌',
                        'Rule Group': attrs.get('rule_group_title', 'N/A'),
                        'Trigger': attrs.get('trigger', 'N/A'),
                        'Order': attrs.get('order', 0),
                        'Stop Processing': '✅' if attrs.get('stop_processing', False) else '❌',
                        'Strict': '✅' if attrs.get('strict', False) else '❌',
                        'Triggers': len(attrs.get('triggers', [])),
                        'Actions': len(attrs.get('actions', []))
                    })

                df = pd.DataFrame(rules_data)

                # Filter options
                st.markdown("**Filter Rules**")
                col1, col2 = st.columns(2)

                with col1:
                    status_filter = st.selectbox(
                        "Status",
                        ["All", "Active Only", "Inactive Only"]
                    )

                with col2:
                    search_term = st.text_input("Search by title", "")

                # Apply filters
                filtered_df = df.copy()

                if status_filter == "Active Only":
                    filtered_df = filtered_df[filtered_df['Active'] == '✅']
                elif status_filter == "Inactive Only":
                    filtered_df = filtered_df[filtered_df['Active'] == '❌']

                if search_term:
                    filtered_df = filtered_df[
                        filtered_df['Title'].str.contains(search_term, case=False, na=False)
                    ]

                st.markdown(f"**Rules List** ({len(filtered_df)} rules)")
                st.dataframe(filtered_df, use_container_width=True, height=400)

                # Expandable details for each rule
                with st.expander("📄 View Detailed Rule Information"):
                    selected_rule_id = st.selectbox(
                        "Select a rule to view details",
                        options=[r['ID'] for r in rules_data],
                        format_func=lambda x: f"ID {x}: {next((r['Title'] for r in rules_data if r['ID'] == x), 'N/A')}"
                    )

                    if selected_rule_id:
                        rule = next((r for r in rules if r.get('id') == selected_rule_id), None)
                        if rule:
                            attrs = rule.get('attributes', {})

                            col1, col2 = st.columns(2)

                            with col1:
                                st.markdown("**Rule Information**")
                                st.markdown(f"- **Title:** {attrs.get('title', 'N/A')}")
                                st.markdown(f"- **Description:** {attrs.get('description', 'N/A')}")
                                st.markdown(f"- **Active:** {attrs.get('active', False)}")
                                st.markdown(f"- **Order:** {attrs.get('order', 0)}")
                                st.markdown(f"- **Trigger:** {attrs.get('trigger', 'N/A')}")
                                st.markdown(f"- **Stop Processing:** {attrs.get('stop_processing', False)}")
                                st.markdown(f"- **Strict:** {attrs.get('strict', False)}")

                            with col2:
                                st.markdown("**Triggers**")
                                triggers = attrs.get('triggers', [])
                                if triggers:
                                    for i, trigger in enumerate(triggers, 1):
                                        st.markdown(f"{i}. **{trigger.get('type', 'N/A')}**: {trigger.get('value', 'N/A')}")
                                else:
                                    st.markdown("*No triggers defined*")

                            st.markdown("**Actions**")
                            actions = attrs.get('actions', [])
                            if actions:
                                for i, action in enumerate(actions, 1):
                                    st.markdown(f"{i}. **{action.get('type', 'N/A')}**: {action.get('value', 'N/A')}")
                            else:
                                st.markdown("*No actions defined*")

                            # Show raw JSON
                            st.markdown("---")
                            show_raw_json = st.checkbox("🔍 Show Raw JSON", key=f"show_json_{selected_rule_id}")
                            if show_raw_json:
                                st.json(rule)

                # Export functionality
                st.markdown("---")
                st.markdown("**Export Rules**")

                col1, col2 = st.columns([2, 1])

                with col1:
                    export_filename = st.text_input(
                        "Export filename",
                        value=f"firefly_rules_export_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.json"
                    )

                with col2:
                    st.markdown("")  # Spacing
                    st.markdown("")  # Spacing

                    if st.button("💾 Export All Rules", type="primary"):
                        # Create export data
                        export_data = {
                            'export_date': pd.Timestamp.now().isoformat(),
                            'firefly_iii_rules_export': True,
                            'total_rules': len(rules),
                            'rules': rules
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

                        st.success(f"✅ Prepared {len(rules)} rules for export")

    # TAB 2: Delete Rules
    with tab2:
        st.subheader("Delete Rules")
        st.warning("⚠️ **Warning:** Deleting rules is permanent and cannot be undone!")

        if st.session_state.rules_cache is None:
            st.info("Please refresh rules in the 'View & Export Rules' tab first")
        else:
            rules = st.session_state.rules_cache

            if len(rules) == 0:
                st.info("No rules to delete")
            else:
                # Select rules to delete
                st.markdown("**Select rules to delete:**")

                rules_data = []
                for rule in rules:
                    attrs = rule.get('attributes', {})
                    rules_data.append({
                        'ID': rule.get('id'),
                        'Title': attrs.get('title', 'N/A'),
                        'Active': attrs.get('active', False),
                        'Rule Group': attrs.get('rule_group_title', 'N/A')
                    })

                df = pd.DataFrame(rules_data)

                # Multi-select with checkboxes
                selected_for_deletion = st.multiselect(
                    "Choose rules to delete",
                    options=[r['ID'] for r in rules_data],
                    format_func=lambda x: f"ID {x}: {next((r['Title'] for r in rules_data if r['ID'] == x), 'N/A')}"
                )

                if selected_for_deletion:
                    st.markdown(f"**Selected {len(selected_for_deletion)} rule(s) for deletion:**")

                    deletion_preview = df[df['ID'].isin(selected_for_deletion)]
                    st.dataframe(deletion_preview, use_container_width=True)

                    # Show detailed information for each selected rule
                    st.markdown("---")
                    st.markdown("**Review Rule Details Before Deletion:**")

                    for rule_id in selected_for_deletion:
                        rule = next((r for r in rules if r.get('id') == rule_id), None)
                        if rule:
                            attrs = rule.get('attributes', {})

                            with st.expander(f"📄 Details for: {attrs.get('title', 'N/A')} (ID: {rule_id})", expanded=False):
                                col1, col2 = st.columns(2)

                                with col1:
                                    st.markdown("**Rule Information**")
                                    st.markdown(f"- **Title:** {attrs.get('title', 'N/A')}")
                                    st.markdown(f"- **Description:** {attrs.get('description', 'N/A')}")
                                    st.markdown(f"- **Rule Group:** {attrs.get('rule_group_title', 'N/A')}")
                                    st.markdown(f"- **Active:** {attrs.get('active', False)}")
                                    st.markdown(f"- **Order:** {attrs.get('order', 0)}")
                                    st.markdown(f"- **Trigger:** {attrs.get('trigger', 'N/A')}")
                                    st.markdown(f"- **Stop Processing:** {attrs.get('stop_processing', False)}")
                                    st.markdown(f"- **Strict:** {attrs.get('strict', False)}")

                                with col2:
                                    st.markdown("**Triggers**")
                                    triggers = attrs.get('triggers', [])
                                    if triggers:
                                        for i, trigger in enumerate(triggers, 1):
                                            prohibited_text = " (prohibited)" if trigger.get('prohibited', False) else ""
                                            st.markdown(f"{i}. **{trigger.get('type', 'N/A')}**: {trigger.get('value', 'N/A')}{prohibited_text}")
                                    else:
                                        st.markdown("*No triggers defined*")

                                st.markdown("**Actions**")
                                actions = attrs.get('actions', [])
                                if actions:
                                    action_cols = st.columns(2)
                                    for i, action in enumerate(actions):
                                        col_idx = i % 2
                                        with action_cols[col_idx]:
                                            st.markdown(f"{i+1}. **{action.get('type', 'N/A')}**: {action.get('value', 'N/A')}")
                                else:
                                    st.markdown("*No actions defined*")

                                # Show raw JSON
                                st.markdown("---")
                                show_raw_json = st.checkbox("🔍 Show Raw JSON", key=f"delete_json_{rule_id}")
                                if show_raw_json:
                                    st.json(rule)

                    st.markdown("---")
                    col1, col2 = st.columns([1, 3])

                    with col1:
                        confirm_delete = st.checkbox("I understand this action is permanent")

                    with col2:
                        if st.button("🗑️ Delete Selected Rules", type="primary", disabled=not confirm_delete):
                            success_count = 0
                            failed_count = 0
                            error_messages = []

                            progress_bar = st.progress(0)
                            status_text = st.empty()

                            for i, rule_id in enumerate(selected_for_deletion):
                                status_text.text(f"Deleting rule {i+1}/{len(selected_for_deletion)}...")
                                progress_bar.progress((i + 1) / len(selected_for_deletion))

                                success, message = client.delete_rule(rule_id)
                                if success:
                                    success_count += 1
                                else:
                                    failed_count += 1
                                    error_messages.append(f"Rule {rule_id}: {message}")

                            status_text.empty()
                            progress_bar.empty()

                            if success_count > 0:
                                st.success(f"✅ Successfully deleted {success_count} rule(s)")

                            if failed_count > 0:
                                st.error(f"❌ Failed to delete {failed_count} rule(s)")
                                with st.expander("View Errors"):
                                    for error in error_messages:
                                        st.text(error)

                            # Clear cache to force refresh
                            st.session_state.rules_cache = None
                            st.info("Please refresh the rules list in the 'View & Export Rules' tab")

    # TAB 3: Import Rules
    with tab3:
        st.subheader("Import Rules")
        st.markdown("Upload a JSON file to import rules into Firefly III")

        uploaded_file = st.file_uploader(
            "Upload rules JSON file",
            type=['json'],
            help="Upload a JSON file exported from Firefly III or created manually"
        )

        if uploaded_file is not None:
            try:
                # Read the uploaded file
                file_content = uploaded_file.read().decode('utf-8')
                data = json.loads(file_content)

                # Validate the file structure
                if not isinstance(data, dict) or 'rules' not in data:
                    st.error("Invalid JSON file format. Expected 'rules' key.")
                else:
                    rules_to_import = data.get('rules', [])

                    if not isinstance(rules_to_import, list):
                        st.error("Invalid rules format. Expected a list.")
                    elif len(rules_to_import) == 0:
                        st.warning("No rules found in the uploaded file")
                    else:
                        st.success(f"✅ Loaded {len(rules_to_import)} rule(s) from file")

                        # Show metadata if available
                        if 'export_date' in data:
                            st.info(f"Export Date: {data['export_date']}")

                        # Preview rules
                        st.markdown("**Preview of rules to import:**")

                        preview_data = []
                        for rule in rules_to_import:
                            attrs = rule.get('attributes', {})
                            preview_data.append({
                                'Title': attrs.get('title', 'N/A'),
                                'Active': '✅' if attrs.get('active', False) else '❌',
                                'Triggers': len(attrs.get('triggers', [])),
                                'Actions': len(attrs.get('actions', []))
                            })

                        preview_df = pd.DataFrame(preview_data)
                        st.dataframe(preview_df, use_container_width=True, height=300)

                        # Import options
                        st.markdown("**Import Options**")

                        col1, col2 = st.columns(2)

                        with col1:
                            import_as_inactive = st.checkbox(
                                "Import all rules as inactive",
                                value=False,
                                help="Import rules but set them as inactive by default"
                            )

                        with col2:
                            skip_existing = st.checkbox(
                                "Skip rules with matching titles",
                                value=True,
                                help="Skip importing rules if a rule with the same title already exists"
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
                            if st.button("📥 Import Rules", type="primary", disabled=not confirm_import):
                                # Get existing rules to check for duplicates
                                existing_rules = []
                                if skip_existing:
                                    with st.spinner("Fetching existing rules..."):
                                        success, existing_rules_list, message = client.get_all_rules()
                                        if success:
                                            existing_rules = existing_rules_list
                                        else:
                                            st.warning("Could not fetch existing rules. Proceeding without duplicate check.")

                                existing_titles = [
                                    r.get('attributes', {}).get('title', '')
                                    for r in existing_rules
                                ]

                                success_count = 0
                                skipped_count = 0
                                failed_count = 0
                                error_messages = []

                                progress_bar = st.progress(0)
                                status_text = st.empty()

                                for i, rule in enumerate(rules_to_import):
                                    attrs = rule.get('attributes', {})
                                    rule_title = attrs.get('title', 'Untitled')

                                    status_text.text(f"Importing rule {i+1}/{len(rules_to_import)}: {rule_title}")
                                    progress_bar.progress((i + 1) / len(rules_to_import))

                                    # Check for duplicates
                                    if skip_existing and rule_title in existing_titles:
                                        skipped_count += 1
                                        continue

                                    # Clean and prepare rule data for import
                                    # Remove metadata fields that shouldn't be in create request
                                    clean_attrs = {
                                        'title': attrs.get('title'),
                                        'description': attrs.get('description', ''),
                                        'order': attrs.get('order', 1),
                                        'active': False if import_as_inactive else attrs.get('active', True),
                                        'strict': attrs.get('strict', True),
                                        'stop_processing': attrs.get('stop_processing', False),
                                        'trigger': attrs.get('trigger', 'store-journal'),
                                        'triggers': [],
                                        'actions': []
                                    }

                                    # Handle rule group - prefer title over ID for portability
                                    if attrs.get('rule_group_title'):
                                        clean_attrs['rule_group_title'] = attrs.get('rule_group_title')
                                    elif attrs.get('rule_group_id'):
                                        clean_attrs['rule_group_id'] = attrs.get('rule_group_id')
                                    else:
                                        # Default to "Default rules" group if neither is present
                                        clean_attrs['rule_group_title'] = 'Default rules'

                                    # Clean triggers - remove metadata fields
                                    for trigger in attrs.get('triggers', []):
                                        clean_attrs['triggers'].append({
                                            'type': trigger.get('type'),
                                            'value': trigger.get('value'),
                                            'prohibited': trigger.get('prohibited', False),
                                            'stop_processing': trigger.get('stop_processing', False)
                                        })

                                    # Clean actions - remove metadata fields
                                    for action in attrs.get('actions', []):
                                        clean_attrs['actions'].append({
                                            'type': action.get('type'),
                                            'value': action.get('value'),
                                            'stop_processing': action.get('stop_processing', False)
                                        })

                                    # Prepare rule data for import
                                    import_rule_data = clean_attrs

                                    # Show debug info if enabled
                                    if show_debug and i == 0:  # Show only for first rule to avoid clutter
                                        with st.expander(f"Debug: API Payload for '{rule_title}'", expanded=True):
                                            st.json(import_rule_data)

                                    # Create rule
                                    success, created_rule, message = client.create_rule(import_rule_data)

                                    if success:
                                        success_count += 1
                                    else:
                                        failed_count += 1
                                        error_messages.append(f"{rule_title}: {message}")

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
                                    st.success(f"✅ Successfully imported {success_count} rule(s)")

                                if skipped_count > 0:
                                    st.info(f"ℹ️ Skipped {skipped_count} duplicate rule(s)")

                                if failed_count > 0:
                                    st.error(f"❌ Failed to import {failed_count} rule(s)")
                                    with st.expander("View Errors"):
                                        for error in error_messages:
                                            st.text(error)

                                # Clear cache to force refresh
                                st.session_state.rules_cache = None
                                st.info("Please refresh the rules list in the 'View & Export Rules' tab to see imported rules")

            except json.JSONDecodeError as e:
                st.error(f"Invalid JSON file: {str(e)}")
            except Exception as e:
                st.error(f"Error processing file: {str(e)}")

# Footer
st.sidebar.markdown("---")
st.sidebar.caption("Rules Management for Firefly III")
