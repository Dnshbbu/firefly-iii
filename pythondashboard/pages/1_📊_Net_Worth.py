import streamlit as st
import pandas as pd
import requests
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
from typing import Dict, List, Optional
import sys
from pathlib import Path

# Add parent directory to path to import utils
sys.path.append(str(Path(__file__).parent.parent))
from utils.navigation import render_sidebar_navigation
from utils.config import get_firefly_url, get_firefly_token

# Page configuration
st.set_page_config(
    page_title="Net Worth Dashboard - Firefly III",
    page_icon="📊",
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

    /* Reduce plot margins */
    .js-plotly-plot {
        margin-bottom: 0 !important;
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

            # Debug: Check what the API is actually returning for include_net_worth
            include_nw = attributes.get('include_net_worth', True)

            accounts.append({
                'id': account.get('id'),
                'name': attributes.get('name', ''),
                'type': attributes.get('type', ''),
                'account_role': attributes.get('account_role', ''),
                'currency_code': currency_code,
                'current_balance': float(current_balance),
                'iban': attributes.get('iban', ''),
                'active': attributes.get('active', True),
                'include_net_worth': include_nw,
                'raw_include_net_worth': attributes.get('include_net_worth', 'NOT_IN_API')
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
        height=250,
        margin=dict(t=40, b=10, l=10, r=10),
        font=dict(size=10)
    )

    return fig


def create_account_breakdown_chart(df: pd.DataFrame, currency: str = None, include_zero_balance: bool = False) -> go.Figure:
    """Create horizontal bar chart showing individual account balances for a specific currency"""
    # Filter active accounts
    if include_zero_balance:
        df_filtered = df[df['active'] == True].copy()
    else:
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
        height=max(300, len(df_filtered) * 20),
        margin=dict(t=35, b=30, l=120, r=10),
        showlegend=False,
        font=dict(size=9)
    )

    return fig


def calculate_account_statistics(df: pd.DataFrame) -> Dict:
    """Calculate useful statistics about accounts"""
    stats = {
        'total_accounts': len(df),
        'active_accounts': len(df[df['active'] == True]),
        'inactive_accounts': len(df[df['active'] == False]),
        'accounts_in_networth': len(df[df['include_net_worth'] == True]),
        'negative_balance_accounts': len(df[df['current_balance'] < 0]),
        'zero_balance_accounts': len(df[df['current_balance'] == 0]),
        'positive_balance_accounts': len(df[df['current_balance'] > 0]),
        'total_asset_value': df[df['type'] == 'asset']['current_balance'].sum(),
        'total_liability_value': df[df['type'] == 'liability']['current_balance'].sum(),
        'currencies': df['currency_code'].nunique(),
        'account_types': df['type'].nunique()
    }
    return stats


def create_asset_liability_comparison(df: pd.DataFrame, currency: str = None) -> go.Figure:
    """Create comparison chart of assets vs liabilities"""
    df_filtered = df[df['include_net_worth'] == True].copy()

    if currency:
        df_filtered = df_filtered[df_filtered['currency_code'] == currency]

    # Separate assets and liabilities
    assets = df_filtered[df_filtered['type'] == 'asset']['current_balance'].sum()
    liabilities = abs(df_filtered[df_filtered['type'] == 'liability']['current_balance'].sum())

    fig = go.Figure(data=[
        go.Bar(
            name='Assets',
            x=['Assets'],
            y=[assets],
            marker_color='green',
            text=[f"{assets:,.2f}"],
            textposition='auto'
        ),
        go.Bar(
            name='Liabilities',
            x=['Liabilities'],
            y=[liabilities],
            marker_color='red',
            text=[f"{liabilities:,.2f}"],
            textposition='auto'
        )
    ])

    title = f"Assets vs Liabilities ({currency})" if currency else "Assets vs Liabilities"
    fig.update_layout(
        title=title,
        height=250,
        margin=dict(t=40, b=10, l=20, r=10),
        showlegend=True,
        yaxis_title="Amount",
        font=dict(size=10)
    )

    return fig


def get_top_accounts(df: pd.DataFrame, n: int = 5, account_type: str = None, currency: str = None) -> pd.DataFrame:
    """Get top N accounts by balance"""
    df_filtered = df[(df['active'] == True) & (df['current_balance'] != 0)].copy()

    if account_type:
        df_filtered = df_filtered[df_filtered['type'] == account_type]

    if currency:
        df_filtered = df_filtered[df_filtered['currency_code'] == currency]

    # For liabilities, show by absolute value but keep original negative values
    if account_type == 'liability':
        df_filtered['sort_value'] = df_filtered['current_balance'].abs()
        top_accounts = df_filtered.nlargest(n, 'sort_value')[['name', 'current_balance', 'currency_code']]
    else:
        top_accounts = df_filtered.nlargest(n, 'current_balance')[['name', 'current_balance', 'currency_code']]

    return top_accounts


def create_currency_distribution_chart(df: pd.DataFrame) -> go.Figure:
    """Create donut chart showing net worth distribution by currency"""
    df_filtered = df[df['include_net_worth'] == True].copy()

    # Group by currency - only show positive net worth currencies
    currency_summary = df_filtered.groupby('currency_code')['current_balance'].sum().reset_index()
    currency_summary = currency_summary[currency_summary['current_balance'] > 0]

    if len(currency_summary) == 0:
        # No positive balances
        return None

    fig = go.Figure(data=[go.Pie(
        labels=currency_summary['currency_code'],
        values=currency_summary['current_balance'],
        hole=.4,
        marker=dict(colors=px.colors.qualitative.Bold),
        textinfo='label+percent+value',
        texttemplate='%{label}<br>%{value:,.0f}<br>(%{percent})'
    )])

    fig.update_layout(
        title="Net Worth by Currency",
        height=300,
        margin=dict(t=40, b=10, l=10, r=10),
        showlegend=False
    )

    return fig




# Main app
st.title("📊 Net Worth Dashboard")

# Sidebar for API configuration
st.sidebar.header("🔧 API Configuration")

# Initialize session state for API credentials from .env
if 'firefly_url' not in st.session_state:
    st.session_state.firefly_url = get_firefly_url()
if 'firefly_token' not in st.session_state:
    st.session_state.firefly_token = get_firefly_token()
if 'api_connected' not in st.session_state:
    st.session_state.api_connected = False

# Auto-connect if credentials are available and not yet connected
if not st.session_state.api_connected and st.session_state.firefly_url and st.session_state.firefly_token:
    client = FireflyAPIClient(st.session_state.firefly_url, st.session_state.firefly_token)
    success, message = client.test_connection()
    if success:
        st.session_state.api_connected = True

# Show config source
if not st.session_state.firefly_url or not st.session_state.firefly_token:
    st.sidebar.warning("⚠️ No credentials found in `.env` file")

# Connection status
if st.session_state.api_connected:
    st.sidebar.success(f"✅ Connected to {st.session_state.firefly_url}")
else:
    st.sidebar.error("❌ Connection failed")
    st.sidebar.markdown("Check your `.env` file configuration:")

# Display help if not connected
if not st.session_state.api_connected:
    st.info("""
    ### 🔑 Getting Started

    Configure your Firefly III credentials in the `.env` file:

    1. **Edit the `.env` file** in the `pythondashboard` directory
    2. **Set your Firefly III URL** (e.g., `http://192.168.0.242` or `http://localhost`)
    3. **Generate a Personal Access Token**:
       - Log in to your Firefly III instance
       - Go to **Options** → **Profile** → **OAuth**
       - Under "Personal Access Tokens", click **Create New Token**
       - Copy the token (it's shown only once!)
    4. **Add the credentials to `.env` file**:
       ```
       FIREFLY_III_URL=http://192.168.0.242
       FIREFLY_III_TOKEN=your_token_here
       ```
    5. **Restart the app** for changes to take effect

    Once configured, your net worth and account data will be displayed automatically.
    """)
    st.stop()

# Main content - Fetch and display data
try:
    client = FireflyAPIClient(st.session_state.firefly_url, st.session_state.firefly_token)

    # Add refresh button - compact header
    col1, col2 = st.columns([1, 5])
    with col1:
        if st.button("🔄 Refresh"):
            st.rerun()
    with col2:
        st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Fetch account data
    with st.spinner("Loading..."):
        # Fetch asset and liability accounts
        asset_accounts = client.get_accounts('asset')
        liability_accounts = client.get_accounts('liability')

        # Combine and parse
        all_accounts = asset_accounts + liability_accounts

        if all_accounts:
            df = client.parse_account_data(all_accounts)

            # Calculate net worth and statistics
            net_worth = calculate_net_worth(df)
            stats = calculate_account_statistics(df)

            # Get available currencies
            available_currencies = sorted(net_worth.keys()) if net_worth else []

            if not net_worth or len(available_currencies) == 0:
                st.warning("No accounts with balances included in net worth")
                st.stop()

            # === SECTION 1: Net Worth Overview (Ultra Compact) ===
            st.markdown("### 💰 Net Worth Overview")

            # Row 1: Main net worth metrics + account statistics
            metric_cols = st.columns(len(available_currencies) + 4)

            # Net worth by currency
            for idx, currency in enumerate(available_currencies):
                total = net_worth[currency]
                with metric_cols[idx]:
                    st.metric(f"Net Worth ({currency})", f"{total:,.0f}")

            # Key statistics
            with metric_cols[len(available_currencies)]:
                st.metric("Total Accounts", stats['total_accounts'])
            with metric_cols[len(available_currencies) + 1]:
                st.metric("Active", stats['active_accounts'])
            with metric_cols[len(available_currencies) + 2]:
                st.metric("Negative Bal.", stats['negative_balance_accounts'])
            with metric_cols[len(available_currencies) + 3]:
                st.metric("Currencies", stats['currencies'])

            st.markdown("---")

            # === SECTION 2: Global Overview (Multi-currency summary) ===
            st.markdown("### 📊 Portfolio Overview")

            col1, col2, col3 = st.columns([2, 2, 3])

            with col1:
                # Currency distribution donut chart
                currency_chart = create_currency_distribution_chart(df)
                if currency_chart:
                    st.plotly_chart(currency_chart, use_container_width=True)

            with col2:
                # Overall asset vs liability (all currencies combined for visual)
                st.markdown("#### Assets vs Liabilities")

                # Calculate totals across all currencies
                total_assets = stats['total_asset_value']
                total_liabilities = abs(stats['total_liability_value'])

                # Display as metrics
                st.metric("Total Assets", f"{total_assets:,.0f}")
                st.metric("Total Liabilities", f"{total_liabilities:,.0f}")

                if total_assets > 0:
                    debt_ratio = (total_liabilities / total_assets) * 100
                    st.metric("Debt Ratio", f"{debt_ratio:.1f}%")

            with col3:
                # Account health indicators - show breakdown by currency
                st.markdown("#### Account Health by Currency")

                health_rows = []
                for curr in available_currencies:
                    df_curr = df[df['currency_code'] == curr]
                    health_rows.append({
                        'Currency': curr,
                        'Total': len(df_curr),
                        'Active': len(df_curr[df_curr['active'] == True]),
                        'Pos.Bal': len(df_curr[df_curr['current_balance'] > 0]),
                        'Neg.Bal': len(df_curr[df_curr['current_balance'] < 0]),
                        'Zero': len(df_curr[df_curr['current_balance'] == 0]),
                        'In NW': len(df_curr[df_curr['include_net_worth'] == True])
                    })

                # Add global total row
                health_rows.append({
                    'Currency': 'ALL',
                    'Total': stats['total_accounts'],
                    'Active': stats['active_accounts'],
                    'Pos.Bal': stats['positive_balance_accounts'],
                    'Neg.Bal': stats['negative_balance_accounts'],
                    'Zero': stats['zero_balance_accounts'],
                    'In NW': stats['accounts_in_networth']
                })

                health_data = pd.DataFrame(health_rows)

                st.dataframe(
                    health_data,
                    use_container_width=True,
                    hide_index=True,
                    height=210
                )

            st.markdown("---")

            # Related dashboards navigation - compact
            st.markdown('<div style="background-color: rgba(49, 51, 63, 0.2); padding: 0.3rem 0.5rem; border-radius: 0.3rem; font-size: 0.75rem;">💡 <b>Related:</b> <a href="/Cash_Flow" style="color: #58a6ff;">📈 Cash Flow</a> for income/expense trends</div>', unsafe_allow_html=True)

            st.markdown("---")

            # === SECTION 3: Per-Currency Breakdown (Dense) ===
            for currency in available_currencies:
                st.markdown(f"### 💵 {currency} Accounts")

                # Filter data for this currency
                df_currency = df[df['currency_code'] == currency].copy()

                # Row 1: Charts (2 columns - more compact)
                chart_col1, chart_col2 = st.columns(2)

                with chart_col1:
                    st.plotly_chart(create_account_type_chart(df, currency), use_container_width=True, config={'displayModeBar': False})

                with chart_col2:
                    st.plotly_chart(create_asset_liability_comparison(df, currency), use_container_width=True, config={'displayModeBar': False})

                # Row 2: Full breakdown chart (compact) - include zero balances
                st.plotly_chart(create_account_breakdown_chart(df, currency, include_zero_balance=True), use_container_width=True, config={'displayModeBar': False})

                st.markdown("---")

            # === SECTION 4: Detailed Account Table (Collapsible) ===
            with st.expander("📋 Detailed Account Table", expanded=False):
                # Filter options (more compact)
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    show_inactive = st.checkbox("Show inactive", value=False)
                with col2:
                    account_type_filter = st.multiselect(
                        "Type",
                        options=df['type'].unique().tolist(),
                        default=df['type'].unique().tolist()
                    )
                with col3:
                    currency_filter = st.multiselect(
                        "Currency",
                        options=sorted(df['currency_code'].unique().tolist()),
                        default=sorted(df['currency_code'].unique().tolist())
                    )
                with col4:
                    show_zero_balance = st.checkbox("Show zeros", value=True)

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
                df_display_formatted = df_display[['name', 'type', 'account_role', 'current_balance', 'currency_code', 'iban', 'active', 'include_net_worth', 'raw_include_net_worth']].copy()
                df_display_formatted = df_display_formatted.sort_values('name')

                st.dataframe(
                    df_display_formatted,
                    use_container_width=True,
                    hide_index=True,
                    height=400,
                    column_config={
                        'name': 'Account Name',
                        'type': 'Type',
                        'account_role': 'Role',
                        'current_balance': st.column_config.NumberColumn('Balance', format="%.2f"),
                        'currency_code': 'Currency',
                        'iban': 'IBAN',
                        'active': st.column_config.CheckboxColumn('Active'),
                        'include_net_worth': st.column_config.CheckboxColumn('In Net Worth'),
                        'raw_include_net_worth': 'API Raw Value'
                    }
                )

                # Export option
                csv = df_display.to_csv(index=False)
                st.download_button(
                    label="📥 Download CSV",
                    data=csv,
                    file_name=f"firefly_accounts_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )

        else:
            st.warning("No accounts found. Please check your API connection.")

except Exception as e:
    st.error(f"An error occurred: {str(e)}")
    st.exception(e)
