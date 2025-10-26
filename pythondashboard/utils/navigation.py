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

        /* Compact alerts/notifications */
        section[data-testid="stSidebar"] div[role="alert"] {
            padding: 0.3rem 0.5rem !important;
            font-size: 0.8rem !important;
            margin-bottom: 0.3rem !important;
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
