"""
JAK Data Analytics
User Interface Theme

Controls the application's visual design.
"""

import streamlit as st

from ..config.constants import COLORS


# =====================================
# APPLY APPLICATION THEME
# =====================================

def apply_theme():

    """
    Apply the global JAK Data Analytics design.
    """

    st.markdown(
        f"""
        <style>

        @import url(
            'https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap'
        );

        /* GLOBAL STYLING */

        html, body, [class*="css"] {{
            font-family: 'Inter', sans-serif;
        }}

        .stApp {{
            background-color: {COLORS['background']};
            color: {COLORS['text']};
        }}

        /* MAIN CONTENT */

        .block-container {{
            padding-top: 2rem;
            padding-bottom: 3rem;
            max-width: 1500px;
        }}

        /* SIDEBAR */

        [data-testid="stSidebar"] {{
            background-color: {COLORS['sidebar']};
        }}

        [data-testid="stSidebar"] * {{
            color: white;
        }}

        [data-testid="stSidebar"] button {{
            border-radius: 8px;
        }}

        /* HEADINGS */

        h1, h2, h3 {{
            color: {COLORS['text']};
            font-weight: 700;
        }}

        /* BUTTONS */

        .stButton > button {{
            background-color: {COLORS['primary']};
            color: white;
            border: none;
            border-radius: 9px;
            padding: 0.55rem 1rem;
            font-weight: 600;
            transition: 0.2s ease;
        }}

        .stButton > button:hover {{
            background-color: #1D4ED8;
            color: white;
            border: none;
        }}

        /* INPUT FIELDS */

        .stTextInput input,
        .stNumberInput input,
        .stSelectbox div[data-baseweb="select"] {{
            border-radius: 8px;
        }}

        /* METRIC CARDS */

        [data-testid="stMetric"] {{
            background-color: white;
            border: 1px solid {COLORS['border']};
            padding: 18px;
            border-radius: 12px;
        }}

        /* DATA TABLES */

        [data-testid="stDataFrame"] {{
            border: 1px solid {COLORS['border']};
            border-radius: 10px;
        }}

        /* LINKS */

        a {{
            color: {COLORS['primary']};
        }}

        /* DIVIDERS */

        hr {{
            border-color: {COLORS['border']};
        }}

        /* FOOTER */

        .jak-footer {{
            text-align: center;
            color: {COLORS['muted']};
            padding: 25px 0;
            font-size: 12px;
        }}

        </style>
        """,
        unsafe_allow_html=True
    )


# =====================================
# REUSABLE PAGE HEADER
# =====================================

def page_header(title, description=""):

    """
    Display a consistent page heading.
    """

    st.markdown(
        f"""
        <h1 style="
            font-size: 30px;
            font-weight: 800;
            margin-bottom: 5px;
        ">
            {title}
        </h1>

        <p style="
            color: {COLORS['muted']};
            font-size: 14px;
            margin-bottom: 25px;
        ">
            {description}
        </p>
        """,
        unsafe_allow_html=True
    )


# =====================================
# REUSABLE FOOTER
# =====================================

def show_footer():

    """
    Display the application footer.
    """

    st.markdown(
        """
        <div class="jak-footer">
            © 2026 JAK Data Analytics.
            All rights reserved.
        </div>
        """,
        unsafe_allow_html=True
    )