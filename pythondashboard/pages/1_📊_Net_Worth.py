import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import requests
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
from typing import Dict, List, Optional
import json

# Page configuration
st.set_page_config(
    page_title="Net Worth Dashboard - Firefly III",
    page_icon="📊",
    layout="wide"
)

# Compact CSS styling with gridstack integration and dark mode support
st.markdown("""
<style>
    .block-container {
        padding-top: 1rem;
        padding-bottom: 0rem;
        padding-left: 2rem;
        padding-right: 2rem;
    }
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
    .dataframe {
        font-size: 0.85rem;
    }
    [data-testid="stMetricValue"] {
        font-size: 1.5rem;
    }
    [data-testid="stMetricLabel"] {
        font-size: 0.85rem;
    }
</style>
""", unsafe_allow_html=True)


class FireflyAPIClient:
    """Client for interacting with Firefly III API"""

    def __init__(self, base_url: str, api_token: str):
        self.base_url = base_url.rstrip('/')
        self.api_token = api_token
        self.headers = {
            'Authorization': f'Bearer {api_token}',
            'Accept': 'application/vnd.api+json',
            'Content-Type': 'application/json'
        }

    def test_connection(self) -> tuple[bool, str]:
        """Test API connection"""
        try:
            response = requests.get(
                f"{self.base_url}/api/v1/about",
                headers=self.headers,
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                version = data.get('data', {}).get('version', 'unknown')
                return True, f"Connected to Firefly III v{version}"
            else:
                return False, f"Error: {response.status_code} - {response.text}"
        except requests.exceptions.RequestException as e:
            return False, f"Connection failed: {str(e)}"

    def get_accounts(self, account_type: Optional[str] = None) -> List[Dict]:
        """Fetch accounts from Firefly III"""
        try:
            url = f"{self.base_url}/api/v1/accounts"
            params = {}
            if account_type:
                params['type'] = account_type

            response = requests.get(
                url,
                headers=self.headers,
                params=params,
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                return data.get('data', [])
            else:
                st.error(f"Error fetching accounts: {response.status_code}")
                return []
        except requests.exceptions.RequestException as e:
            st.error(f"Failed to fetch accounts: {str(e)}")
            return []

    def parse_account_data(self, accounts_data: List[Dict]) -> pd.DataFrame:
        """Parse account data into a pandas DataFrame"""
        accounts = []

        for account in accounts_data:
            attributes = account.get('attributes', {})

            # Get current balance
            current_balance = attributes.get('current_balance', '0')
            currency_code = attributes.get('currency_code', 'EUR')

            accounts.append({
                'id': account.get('id'),
                'name': attributes.get('name', ''),
                'type': attributes.get('type', ''),
                'account_role': attributes.get('account_role', ''),
                'currency_code': currency_code,
                'current_balance': float(current_balance),
                'iban': attributes.get('iban', ''),
                'active': attributes.get('active', True),
                'include_net_worth': attributes.get('include_net_worth', True)
            })

        return pd.DataFrame(accounts)


def calculate_net_worth(df: pd.DataFrame) -> Dict[str, float]:
    """Calculate net worth by currency"""
    # Filter accounts that should be included in net worth
    net_worth_accounts = df[df['include_net_worth'] == True]

    # Group by currency and sum balances
    net_worth_by_currency = net_worth_accounts.groupby('currency_code')['current_balance'].sum().to_dict()

    return net_worth_by_currency


def create_account_type_chart(df: pd.DataFrame) -> go.Figure:
    """Create pie chart showing balance by account type"""
    # Filter accounts included in net worth
    df_filtered = df[df['include_net_worth'] == True].copy()

    # Group by account type
    type_summary = df_filtered.groupby('type')['current_balance'].sum().reset_index()
    type_summary = type_summary[type_summary['current_balance'] != 0]  # Remove zero balances

    fig = go.Figure(data=[go.Pie(
        labels=type_summary['type'],
        values=type_summary['current_balance'],
        hole=.3,
        marker=dict(colors=px.colors.qualitative.Set3)
    )])

    fig.update_layout(
        title="Balance by Account Type",
        height=400,
        margin=dict(t=50, b=20, l=20, r=20)
    )

    return fig


def create_account_breakdown_chart(df: pd.DataFrame) -> go.Figure:
    """Create horizontal bar chart showing individual account balances"""
    # Filter active accounts with non-zero balance
    df_filtered = df[(df['active'] == True) & (df['current_balance'] != 0)].copy()
    df_filtered = df_filtered.sort_values('current_balance', ascending=True)

    # Create color based on positive/negative
    colors = ['green' if x >= 0 else 'red' for x in df_filtered['current_balance']]

    fig = go.Figure(data=[go.Bar(
        y=df_filtered['name'],
        x=df_filtered['current_balance'],
        orientation='h',
        marker=dict(color=colors),
        text=df_filtered['current_balance'].apply(lambda x: f"{x:,.2f}"),
        textposition='auto',
    )])

    fig.update_layout(
        title="Account Balances",
        xaxis_title="Balance",
        yaxis_title="Account",
        height=max(400, len(df_filtered) * 25),
        margin=dict(t=50, b=50, l=150, r=20),
        showlegend=False
    )

    return fig


def create_gridstack_dashboard(widgets_html: str, height: int = 800) -> None:
    """Create a gridstack.js dashboard with draggable/resizable widgets - dark mode compatible"""

    gridstack_component = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/gridstack@9.4.0/dist/gridstack.min.css" />
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/gridstack@9.4.0/dist/gridstack-extra.min.css" />
        <script src="https://cdn.jsdelivr.net/npm/gridstack@9.4.0/dist/gridstack-all.js"></script>
        <style>
            body {{
                margin: 0;
                padding: 10px;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background: #0e1117;
                color: #fafafa;
            }}
            .grid-stack {{
                background: #0e1117;
            }}
            .grid-stack-item-content {{
                background: #262730;
                border: 1px solid rgba(250, 250, 250, 0.1);
                border-radius: 8px;
                padding: 15px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.5);
                overflow: auto;
            }}
            .widget-header {{
                font-size: 1.1rem;
                font-weight: 600;
                margin-bottom: 10px;
                color: #fafafa;
                display: flex;
                justify-content: space-between;
                align-items: center;
                cursor: move;
                border-bottom: 1px solid rgba(250, 250, 250, 0.1);
                padding-bottom: 8px;
            }}
            .drag-handle {{
                color: #b0b0b0;
                font-size: 0.9rem;
            }}
            .grid-stack-item.grid-stack-item-moving .grid-stack-item-content {{
                box-shadow: 0 4px 16px rgba(0,0,0,0.5);
                border-color: rgba(250, 250, 250, 0.2);
            }}
            .widget-content {{
                font-size: 0.95rem;
                color: #e0e0e0;
            }}
            .metric {{
                text-align: center;
                padding: 20px;
            }}
            .metric-value {{
                font-size: 2rem;
                font-weight: 700;
                color: #fafafa;
            }}
            .metric-label {{
                font-size: 0.9rem;
                color: #b0b0b0;
                margin-top: 5px;
            }}
            table {{
                color: #e0e0e0;
            }}
            th {{
                background: rgba(250, 250, 250, 0.05) !important;
                color: #fafafa !important;
            }}
            tr:hover {{
                background: rgba(250, 250, 250, 0.03);
            }}
        </style>
    </head>
    <body>
        <div class="grid-stack">
            {widgets_html}
        </div>

        <script>
            GridStack.init({{
                float: true,
                cellHeight: '70px',
                minRow: 1,
                margin: 10,
                resizable: {{
                    handles: 'e, se, s, sw, w'
                }}
            }});
        </script>
    </body>
    </html>
    """

    components.html(gridstack_component, height=height, scrolling=True)


def create_widget(title: str, content: str, x: int, y: int, w: int, h: int, widget_id: str = "") -> str:
    """Create a single gridstack widget"""
    return f"""
    <div class="grid-stack-item" gs-x="{x}" gs-y="{y}" gs-w="{w}" gs-h="{h}" gs-id="{widget_id}">
        <div class="grid-stack-item-content">
            <div class="widget-header">
                {title}
                <span class="drag-handle">⋮⋮</span>
            </div>
            <div class="widget-content">
                {content}
            </div>
        </div>
    </div>
    """


# Main app
st.title("📊 Net Worth Dashboard")

# Add layout toggle
use_gridstack = st.sidebar.checkbox("🎨 Use Draggable Dashboard Layout", value=False, help="Enable drag-and-drop widgets")

# Sidebar for API configuration
st.sidebar.header("🔧 API Configuration")

# Initialize session state for API credentials
if 'firefly_url' not in st.session_state:
    st.session_state.firefly_url = "http://192.168.0.242"
if 'firefly_token' not in st.session_state:
    st.session_state.firefly_token = ""
if 'api_connected' not in st.session_state:
    st.session_state.api_connected = False

# API configuration form
with st.sidebar.form("api_config"):
    firefly_url = st.text_input(
        "Firefly III URL",
        value=st.session_state.firefly_url,
        placeholder="http://192.168.0.242"
    )

    firefly_token = st.text_input(
        "API Token",
        value=st.session_state.firefly_token,
        type="password",
        help="Generate a Personal Access Token in Firefly III under Profile → OAuth"
    )

    submit_button = st.form_submit_button("Connect")

    if submit_button:
        if not firefly_url or not firefly_token:
            st.sidebar.error("Please provide both URL and API token")
        else:
            st.session_state.firefly_url = firefly_url
            st.session_state.firefly_token = firefly_token

            # Test connection
            client = FireflyAPIClient(firefly_url, firefly_token)
            success, message = client.test_connection()

            if success:
                st.session_state.api_connected = True
                st.sidebar.success(message)
                st.rerun()
            else:
                st.session_state.api_connected = False
                st.sidebar.error(message)

# Connection status
if st.session_state.api_connected:
    st.sidebar.success("✅ Connected to Firefly III")
else:
    st.sidebar.warning("⚠️ Not connected")

# Display help if not connected
if not st.session_state.api_connected:
    st.info("""
    ### 🔑 Getting Started

    To use this dashboard, you need to configure the API connection:

    1. **Generate an API Token** in Firefly III:
       - Go to your Firefly III instance
       - Navigate to **Profile → OAuth**
       - Click **Create New Token**
       - Copy the generated token

    2. **Enter your details** in the sidebar:
       - Firefly III URL (e.g., `http://192.168.0.242`)
       - Paste the API token
       - Click **Connect**

    Once connected, your net worth and account data will be displayed automatically.
    """)
    st.stop()

# Main content - Fetch and display data
try:
    client = FireflyAPIClient(st.session_state.firefly_url, st.session_state.firefly_token)

    # Add refresh button
    col1, col2, col3 = st.columns([1, 1, 4])
    with col1:
        if st.button("🔄 Refresh Data"):
            st.rerun()
    with col2:
        st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    st.divider()

    # Fetch account data
    with st.spinner("Loading account data..."):
        # Fetch asset and liability accounts
        asset_accounts = client.get_accounts('asset')
        liability_accounts = client.get_accounts('liability')

        # Combine and parse
        all_accounts = asset_accounts + liability_accounts

        if all_accounts:
            df = client.parse_account_data(all_accounts)

            # Calculate net worth
            net_worth = calculate_net_worth(df)

            # Display net worth summary
            st.header("💰 Net Worth Summary")

            cols = st.columns(len(net_worth) if len(net_worth) > 0 else 1)

            if net_worth:
                for idx, (currency, total) in enumerate(net_worth.items()):
                    with cols[idx % len(cols)]:
                        delta_color = "normal" if total >= 0 else "inverse"
                        st.metric(
                            label=f"Total Net Worth ({currency})",
                            value=f"{total:,.2f} {currency}",
                            delta=None
                        )
            else:
                st.warning("No accounts found with balances included in net worth calculation")

            st.divider()

            # Display charts - either gridstack or regular layout
            if use_gridstack:
                # Prepare data for widgets
                type_summary = df[df['include_net_worth'] == True].groupby('type').agg({
                    'current_balance': 'sum',
                    'name': 'count'
                }).rename(columns={'name': 'count', 'current_balance': 'total_balance'})
                type_summary = type_summary.reset_index()

                # Create table HTML (dark mode)
                type_table_html = "<table style='width:100%; border-collapse: collapse;'>"
                type_table_html += "<tr style='background: rgba(250, 250, 250, 0.05);'><th style='padding:8px; text-align:left; color: #fafafa;'>Type</th><th style='padding:8px; text-align:right; color: #fafafa;'>Count</th><th style='padding:8px; text-align:right; color: #fafafa;'>Total</th></tr>"
                for _, row in type_summary.iterrows():
                    type_table_html += f"<tr style='border-bottom: 1px solid rgba(250, 250, 250, 0.1);'><td style='padding:8px; color: #e0e0e0;'>{row['type']}</td><td style='padding:8px; text-align:right; color: #e0e0e0;'>{row['count']}</td><td style='padding:8px; text-align:right; color: #e0e0e0;'>{row['total_balance']:,.2f}</td></tr>"
                type_table_html += "</table>"

                # Account balance list (dark mode)
                df_active = df[(df['active'] == True) & (df['current_balance'] != 0)].copy()
                df_active = df_active.sort_values('current_balance', ascending=False)

                accounts_html = "<div style='max-height: 400px; overflow-y: auto;'>"
                for _, acc in df_active.head(10).iterrows():
                    color = '#4ade80' if acc['current_balance'] >= 0 else '#f87171'  # Green-400 / Red-400
                    accounts_html += f"<div style='padding: 8px; border-bottom: 1px solid rgba(250, 250, 250, 0.1); display: flex; justify-content: space-between;'>"
                    accounts_html += f"<span style='color: #e0e0e0;'>{acc['name']}</span>"
                    accounts_html += f"<span style='color: {color}; font-weight: 600;'>{acc['current_balance']:,.2f} {acc['currency_code']}</span>"
                    accounts_html += "</div>"
                accounts_html += "</div>"

                # Create gridstack widgets
                widgets = ""

                # Net worth widget(s)
                widget_y = 0
                for idx, (currency, total) in enumerate(net_worth.items()):
                    color = '#4ade80' if total >= 0 else '#f87171'  # Green-400 / Red-400
                    content = f"""
                    <div class="metric">
                        <div class="metric-value" style="color: {color};">{total:,.2f}</div>
                        <div class="metric-label">{currency}</div>
                    </div>
                    """
                    widgets += create_widget(f"💰 Net Worth ({currency})", content, idx * 3, widget_y, 3, 2, f"net-worth-{currency}")

                widget_y = 2

                # Account type summary widget
                widgets += create_widget("📊 Account Type Summary", type_table_html, 0, widget_y, 6, 4, "type-summary")

                # Top accounts widget
                widgets += create_widget("🏦 Top Accounts", accounts_html, 6, widget_y, 6, 4, "top-accounts")

                # Info widget (dark mode)
                info_html = f"""
                <div style='padding: 10px; color: #e0e0e0;'>
                    <p style='margin: 8px 0;'><strong style='color: #fafafa;'>Total Accounts:</strong> {len(df)}</p>
                    <p style='margin: 8px 0;'><strong style='color: #fafafa;'>Active Accounts:</strong> {len(df[df['active'] == True])}</p>
                    <p style='margin: 8px 0;'><strong style='color: #fafafa;'>Asset Accounts:</strong> {len(df[df['type'] == 'asset'])}</p>
                    <p style='margin: 8px 0;'><strong style='color: #fafafa;'>Liability Accounts:</strong> {len(df[df['type'] == 'liabilities'])}</p>
                </div>
                """
                widgets += create_widget("ℹ️ Account Statistics", info_html, 0, widget_y + 4, 4, 3, "stats")

                # Create the gridstack dashboard
                create_gridstack_dashboard(widgets, height=900)

                st.info("💡 **Tip:** Drag widgets by their headers and resize them by their corners to customize your dashboard!")

            else:
                # Regular Streamlit layout
                col1, col2 = st.columns(2)

                with col1:
                    st.plotly_chart(create_account_type_chart(df), use_container_width=True)

                with col2:
                    # Account type summary table
                    st.subheader("Account Type Summary")
                    type_summary = df[df['include_net_worth'] == True].groupby('type').agg({
                        'current_balance': 'sum',
                        'name': 'count'
                    }).rename(columns={'name': 'count', 'current_balance': 'total_balance'})
                    type_summary = type_summary.reset_index()
                    type_summary['total_balance'] = type_summary['total_balance'].apply(lambda x: f"{x:,.2f}")
                    st.dataframe(type_summary, use_container_width=True, hide_index=True)

                st.divider()

                # Account breakdown chart
                st.plotly_chart(create_account_breakdown_chart(df), use_container_width=True)

            st.divider()

            # Detailed account table
            st.header("📋 Account Details")

            # Filter options
            col1, col2, col3 = st.columns(3)
            with col1:
                show_inactive = st.checkbox("Show inactive accounts", value=False)
            with col2:
                account_type_filter = st.multiselect(
                    "Filter by type",
                    options=df['type'].unique().tolist(),
                    default=df['type'].unique().tolist()
                )
            with col3:
                show_zero_balance = st.checkbox("Show zero balances", value=False)

            # Apply filters
            df_display = df.copy()
            if not show_inactive:
                df_display = df_display[df_display['active'] == True]
            if account_type_filter:
                df_display = df_display[df_display['type'].isin(account_type_filter)]
            if not show_zero_balance:
                df_display = df_display[df_display['current_balance'] != 0]

            # Format for display
            df_display_formatted = df_display[['name', 'type', 'account_role', 'current_balance', 'currency_code', 'iban', 'active', 'include_net_worth']].copy()
            df_display_formatted['current_balance'] = df_display_formatted['current_balance'].apply(lambda x: f"{x:,.2f}")
            df_display_formatted = df_display_formatted.sort_values('name')

            st.dataframe(
                df_display_formatted,
                use_container_width=True,
                hide_index=True,
                column_config={
                    'name': 'Account Name',
                    'type': 'Type',
                    'account_role': 'Role',
                    'current_balance': 'Balance',
                    'currency_code': 'Currency',
                    'iban': 'IBAN',
                    'active': st.column_config.CheckboxColumn('Active'),
                    'include_net_worth': st.column_config.CheckboxColumn('In Net Worth')
                }
            )

            # Export option
            st.divider()
            csv = df_display.to_csv(index=False)
            st.download_button(
                label="📥 Download Account Data (CSV)",
                data=csv,
                file_name=f"firefly_accounts_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )

        else:
            st.warning("No accounts found. Please check your API connection and ensure you have accounts set up in Firefly III.")

except Exception as e:
    st.error(f"An error occurred: {str(e)}")
    st.exception(e)
