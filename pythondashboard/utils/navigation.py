"""
Navigation utility for organizing Streamlit pages into collapsible sidebar sections.
"""
import streamlit as st
import os

# Get the base directory (where Home.py is located)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Define page categories and their pages
PAGE_SECTIONS = {
    "📊 Dashboards": [
        {"label": "📊 Net Worth", "file": "1_📊_Net_Worth.py"},
        {"label": "📈 Cash Flow", "file": "3_📈_Cash_Flow.py"},
        {"label": "💰 Budget", "file": "4_💰_Budget.py"},
        {"label": "📅 Budget Timeline", "file": "14_📅_Budget_Timeline.py"},
        {"label": "🏷️ Categories", "file": "5_🏷️_Categories.py"},
    ],
    "🔧 Management": [
        {"label": "🏦 Asset Accounts", "file": "10_🏦_Asset_Accounts.py"},
        {"label": "💰 Revenue Accounts", "file": "8_💰_Revenue_Accounts.py"},
        {"label": "💸 Expense Accounts", "file": "9_💸_Expense_Accounts.py"},
        {"label": "💵 Budget Management", "file": "11_💵_Budget_Management.py"},
        {"label": "📅 Bills Management", "file": "12_📅_Bills_Management.py"},
        {"label": "🐷 Piggy Banks", "file": "13_🐷_Piggy_Banks_Management.py"},
        {"label": "🔧 Category Management", "file": "7_🔧_Category_Management.py"},
        {"label": "📋 Rules Management", "file": "6_📋_Rules_Management.py"},
    ],
    "🛠️ Tools": [
        {"label": "📄 CSV Preprocessor", "file": "2_📄_CSV_Preprocessor.py"},
    ]
}


def render_sidebar_navigation():
    """
    Renders a collapsible navigation sidebar with grouped sections.
    Uses buttons with st.switch_page for navigation.
    """
    # Load compact CSS for entire sidebar
    st.markdown("""
    <style>
        /* Compact all buttons in sidebar */
        section[data-testid="stSidebar"] button {
            padding: 0.25rem 0.5rem !important;
            font-size: 0.8rem !important;
            height: auto !important;
            margin-bottom: 0.1rem !important;
            min-height: 2rem !important;
        }

        /* Compact expanders */
        section[data-testid="stSidebar"] details summary {
            font-size: 0.85rem !important;
            padding: 0.25rem 0.5rem !important;
            font-weight: 600 !important;
            min-height: 2rem !important;
        }

        section[data-testid="stSidebar"] details[open] > div {
            padding-top: 0.2rem !important;
            padding-bottom: 0.2rem !important;
        }

        /* Compact all headers */
        section[data-testid="stSidebar"] h1 {
            font-size: 1.2rem !important;
            margin: 0.3rem 0 0.4rem 0 !important;
            padding: 0 !important;
        }

        section[data-testid="stSidebar"] h2 {
            font-size: 1rem !important;
            margin: 0.3rem 0 !important;
            padding: 0 !important;
        }

        section[data-testid="stSidebar"] h3 {
            font-size: 0.9rem !important;
            margin: 0.2rem 0 0.4rem 0 !important;
            padding: 0 !important;
        }

        /* Fix alerts - force proper text accommodation */
        section[data-testid="stSidebar"] div[role="alert"] {
            padding: 0.6rem 0.6rem 0.95rem 0.6rem !important;
            margin-bottom: 0.3rem !important;
            font-size: 0.8rem !important;
            line-height: 1.5 !important;
            display: block !important;
            box-sizing: content-box !important;
        }
        
        /* Reset all inner elements to prevent clipping */
        section[data-testid="stSidebar"] div[role="alert"] div {
            line-height: inherit !important;
            height: auto !important;
            min-height: 0 !important;
            overflow: visible !important;
        }
        
        /* Alert text - add pseudo element for descender space */
        section[data-testid="stSidebar"] div[role="alert"] p {
            margin: 0 !important;
            padding: 0 !important;
            font-size: 0.8rem !important;
            line-height: 1.5 !important;
            display: block !important;
        }
        
        /* Force descender space with after pseudo-element */
        section[data-testid="stSidebar"] div[role="alert"] p::after {
            content: "";
            display: block;
            height: 0.2rem;
            width: 100%;
        }

        /* Compact markdown */
        section[data-testid="stSidebar"] p {
            font-size: 0.82rem !important;
            margin-bottom: 0.3rem !important;
        }

        /* Compact captions */
        section[data-testid="stSidebar"] small {
            font-size: 0.72rem !important;
        }

        /* Compact dividers */
        section[data-testid="stSidebar"] hr {
            margin: 0.5rem 0 !important;
        }

        /* Compact forms */
        section[data-testid="stSidebar"] form {
            padding: 0.3rem !important;
        }

        /* Compact inputs */
        section[data-testid="stSidebar"] input {
            font-size: 0.8rem !important;
            padding: 0.3rem 0.5rem !important;
        }

        /* Compact labels */
        section[data-testid="stSidebar"] label {
            font-size: 0.8rem !important;
            margin-bottom: 0.2rem !important;
        }

        /* Reduce spacing between elements */
        section[data-testid="stSidebar"] div.element-container {
            margin-bottom: 0.3rem !important;
        }

        section[data-testid="stSidebar"] div[data-testid="stVerticalBlock"] > div {
            gap: 0.3rem !important;
        }

        /* Compact selectbox/dropdown elements */
        section[data-testid="stSidebar"] div[data-baseweb="select"] {
            font-size: 0.75rem !important;
            min-height: 1.8rem !important;
            height: 1.8rem !important;
        }

        section[data-testid="stSidebar"] div[data-baseweb="select"] > div {
            min-height: 1.8rem !important;
            height: 1.8rem !important;
            padding: 0.15rem 0.4rem !important;
            font-size: 0.75rem !important;
        }

        /* Target the input control inside selectbox */
        section[data-testid="stSidebar"] div[data-baseweb="select"] input {
            height: 1.8rem !important;
            min-height: 1.8rem !important;
            font-size: 0.75rem !important;
        }

        /* Target the value container */
        section[data-testid="stSidebar"] div[data-baseweb="select"] > div > div {
            padding: 0.15rem 0.25rem !important;
            min-height: 1.8rem !important;
            height: 1.8rem !important;
        }

        /* Compact the arrow/icon */
        section[data-testid="stSidebar"] div[data-baseweb="select"] svg {
            width: 16px !important;
            height: 16px !important;
        }

        /* Compact selectbox label */
        section[data-testid="stSidebar"] div[data-testid="stSelectbox"] label {
            font-size: 0.75rem !important;
            margin-bottom: 0.2rem !important;
        }

        /* Compact selectbox container */
        section[data-testid="stSidebar"] div[data-testid="stSelectbox"] {
            margin-bottom: 0.4rem !important;
        }

        /* Compact dropdown menu/popover - the options list that appears */
        div[data-baseweb="popover"] ul[role="listbox"] {
            max-height: 300px !important;
        }

        div[data-baseweb="popover"] li[role="option"] {
            font-size: 0.75rem !important;
            padding: 0.25rem 0.5rem !important;
            min-height: 1.8rem !important;
            line-height: 1.3 !important;
        }

        div[data-baseweb="popover"] ul {
            padding: 0.2rem 0 !important;
        }

        /* Compact the popover container itself */
        div[data-baseweb="popover"] {
            font-size: 0.75rem !important;
        }
    </style>
    """, unsafe_allow_html=True)

    st.sidebar.markdown("### 🔥 Navigation")

    for section_name, page_list in PAGE_SECTIONS.items():
        # Create an expander for each section (default collapsed)
        with st.sidebar.expander(section_name, expanded=False):
            for page_info in page_list:
                # Create a button for each page that triggers navigation
                if st.button(page_info['label'], key=f"nav_{page_info['file']}", use_container_width=True):
                    # Construct the full path to the page
                    page_path = os.path.join(BASE_DIR, "pages", page_info['file'])
                    st.switch_page(page_path)

    st.sidebar.markdown("---")
