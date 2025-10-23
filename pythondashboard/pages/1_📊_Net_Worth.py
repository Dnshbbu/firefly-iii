import streamlit as st
import pandas as pd
import requests
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
from typing import Dict, List, Optional

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
        padding-top: 5rem !important;
        padding-bottom: 0rem;
        padding-left: 2rem;
        padding-right: 2rem;
    }
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


def create_account_type_chart(df: pd.DataFrame, currency: str = None) -> go.Figure:
    """Create pie chart showing balance by account type for a specific currency"""
    # Filter accounts included in net worth
    df_filtered = df[df['include_net_worth'] == True].copy()

    # Filter by currency if specified
    if currency:
        df_filtered = df_filtered[df_filtered['currency_code'] == currency]

    # Group by account type
    type_summary = df_filtered.groupby('type')['current_balance'].sum().reset_index()
    type_summary = type_summary[type_summary['current_balance'] != 0]  # Remove zero balances

    fig = go.Figure(data=[go.Pie(
        labels=type_summary['type'],
        values=type_summary['current_balance'],
        hole=.3,
        marker=dict(colors=px.colors.qualitative.Set3)
    )])

    title = f"Balance by Account Type ({currency})" if currency else "Balance by Account Type"
    fig.update_layout(
        title=title,
        height=400,
        margin=dict(t=50, b=20, l=20, r=20)
    )

    return fig


def create_account_breakdown_chart(df: pd.DataFrame, currency: str = None) -> go.Figure:
    """Create horizontal bar chart showing individual account balances for a specific currency"""
    # Filter active accounts with non-zero balance
    df_filtered = df[(df['active'] == True) & (df['current_balance'] != 0)].copy()

    # Filter by currency if specified
    if currency:
        df_filtered = df_filtered[df_filtered['currency_code'] == currency]

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

    title = f"Account Balances ({currency})" if currency else "Account Balances"
    fig.update_layout(
        title=title,
        xaxis_title="Balance",
        yaxis_title="Account",
        height=max(400, len(df_filtered) * 25),
        margin=dict(t=50, b=50, l=150, r=20),
        showlegend=False
    )

    return fig




# Main app
st.title("📊 Net Worth Dashboard")

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

            # Get available currencies
            available_currencies = sorted(net_worth.keys()) if net_worth else []

            if net_worth and len(available_currencies) > 0:
                # Display metrics for each currency
                cols = st.columns(len(available_currencies))
                for idx, currency in enumerate(available_currencies):
                    total = net_worth[currency]
                    with cols[idx]:
                        delta_color = "normal" if total >= 0 else "inverse"
                        st.metric(
                            label=f"Total Net Worth ({currency})",
                            value=f"{total:,.2f} {currency}",
                            delta=None
                        )
            else:
                st.warning("No accounts found with balances included in net worth calculation")

            st.divider()

            # Display charts - separated by currency
            for currency in available_currencies:
                st.header(f"💵 {currency} Accounts")

                # Filter data for this currency
                df_currency = df[df['currency_code'] == currency].copy()

                col1, col2 = st.columns(2)

                with col1:
                    st.plotly_chart(create_account_type_chart(df, currency), use_container_width=True)

                with col2:
                    # Account type summary table for this currency
                    st.subheader(f"Account Type Summary ({currency})")
                    type_summary = df_currency[df_currency['include_net_worth'] == True].groupby('type').agg({
                        'current_balance': 'sum',
                        'name': 'count'
                    }).rename(columns={'name': 'count', 'current_balance': 'total_balance'})
                    type_summary = type_summary.reset_index()
                    type_summary['total_balance'] = type_summary['total_balance'].apply(lambda x: f"{x:,.2f}")
                    st.dataframe(type_summary, use_container_width=True, hide_index=True)

                st.divider()

                # Account breakdown chart for this currency
                st.plotly_chart(create_account_breakdown_chart(df, currency), use_container_width=True)

                st.divider()

            st.divider()

            # Detailed account table
            st.header("📋 Account Details")

            # Filter options
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                show_inactive = st.checkbox("Show inactive accounts", value=False)
            with col2:
                account_type_filter = st.multiselect(
                    "Filter by type",
                    options=df['type'].unique().tolist(),
                    default=df['type'].unique().tolist()
                )
            with col3:
                currency_filter = st.multiselect(
                    "Filter by currency",
                    options=sorted(df['currency_code'].unique().tolist()),
                    default=sorted(df['currency_code'].unique().tolist())
                )
            with col4:
                show_zero_balance = st.checkbox("Show zero balances", value=False)

            # Apply filters
            df_display = df.copy()
            if not show_inactive:
                df_display = df_display[df_display['active'] == True]
            if account_type_filter:
                df_display = df_display[df_display['type'].isin(account_type_filter)]
            if currency_filter:
                df_display = df_display[df_display['currency_code'].isin(currency_filter)]
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
