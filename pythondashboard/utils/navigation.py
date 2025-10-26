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
    st.sidebar.markdown("### 🔥 Navigation")
    st.sidebar.markdown("")  # Add some spacing

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
    st.sidebar.caption("💡 Click sections to expand/collapse")
