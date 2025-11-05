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
        {"label": "🔍 Category Details", "file": "15_🔍_Category_Details.py"},
        {"label": "🏷️ Transaction Tags", "file": "17_🏷️_Transaction_Tags.py"},
        {"label": "🚀 Savings Forecast", "file": "16_🚀_Savings_Forecast.py"},
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
        {"label": "📄 PDF Table Extractor", "file": "18_📄_PDF_Table_Extractor.py"},
    ]
}


def render_sidebar_navigation():
    """
    Renders a collapsible navigation sidebar with grouped sections.
    Uses buttons with st.switch_page for navigation.
    Each page also has a small external link icon to open in a new tab.
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

        /* Remove gap between columns in navigation */
        section[data-testid="stSidebar"] div[data-testid="column"] {
            padding-left: 0 !important;
            padding-right: 0 !important;
        }

        /* Ensure buttons and links align properly */
        section[data-testid="stSidebar"] div[data-testid="stHorizontalBlock"] {
            gap: 0.15rem !important;
        }

        /* External link styling - more modern look */
        .nav-external-link {
            font-size: 0.7rem;
            color: #888;
            text-decoration: none;
            padding: 0.25rem 0.4rem;
            border-radius: 4px;
            transition: all 0.25s ease;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            min-width: 1.6rem;
            background-color: rgba(0, 0, 0, 0.02);
            border: 1px solid rgba(0, 0, 0, 0.08);
            opacity: 0.7;
            align-self: center;
            margin-top: 0.3rem;
        }

        .nav-external-link:hover {
            background-color: rgba(59, 130, 246, 0.1);
            border-color: rgba(59, 130, 246, 0.3);
            color: #3b82f6;
            opacity: 1;
            transform: translateY(-1px);
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        }

        .nav-external-link:active {
            transform: translateY(0);
            box-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
        }
    </style>
    """, unsafe_allow_html=True)

    st.sidebar.markdown("### 🔥 Navigation")

    for section_name, page_list in PAGE_SECTIONS.items():
        # Create an expander for each section (default collapsed)
        with st.sidebar.expander(section_name, expanded=False):
            for page_info in page_list:
                # Create a row with button and external link icon
                # Use st.markdown with HTML to create the layout
                page_file = page_info['file']
                page_label = page_info['label']

                # Create columns for button and link icon
                # Use spec to ensure no gap between columns
                col1, col2 = st.columns([0.85, 0.15], gap="small")

                with col1:
                    # Create a button for each page that triggers navigation
                    if st.button(page_label, key=f"nav_{page_file}", use_container_width=True):
                        # Construct the full path to the page
                        page_path = os.path.join(BASE_DIR, "pages", page_file)
                        st.switch_page(page_path)

                with col2:
                    # Create external link icon using markdown link
                    # The link will open the page in a new tab
                    # Streamlit URL format: extract the page title after the number and emoji
                    # e.g., "4_💰_Budget.py" -> "Budget"
                    import re
                    # Remove the file extension first
                    page_name = page_file.replace('.py', '')
                    # Remove the number prefix and first emoji/underscore (e.g., "4_💰_")
                    # Pattern: starts with digits, underscore, emoji, underscore
                    page_url_part = re.sub(r'^\d+_[^_]+_', '', page_name)

                    # Using a modern external link SVG icon
                    external_link_svg = '''
                    <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"></path>
                        <polyline points="15 3 21 3 21 9"></polyline>
                        <line x1="10" y1="14" x2="21" y2="3"></line>
                    </svg>
                    '''

                    st.markdown(
                        f'<a href="/{page_url_part}" target="_blank" class="nav-external-link" title="Open in new tab">{external_link_svg}</a>',
                        unsafe_allow_html=True
                    )

    st.sidebar.markdown("---")
