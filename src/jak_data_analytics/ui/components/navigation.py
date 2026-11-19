"""
JAK Data Analytics
Navigation Manager

Controls navigation between application sections.
"""

import streamlit as st

from ..config.constants import APP_NAME


# =====================================
# NAVIGATION MENU
# =====================================

NAVIGATION_MENU = {

    "MAIN MENU": {
        "Dashboard": "🏠",
        "My Projects": "📁",
        "Datasets": "📊",
    },

    "DATA ANALYSIS": {
        "Data Profiling": "🔍",
        "Data Cleaning": "🧹",
        "Transformations": "🔄",
        "Statistical Analysis": "📈",
        "Visualisations": "📉",
        "Dashboard Builder": "📊",
    },

    "INTELLIGENCE": {
        "Machine Learning": "🤖",
        "Predictions": "🔮",
        "Forecasting": "📅",
        "Recommendations": "💡",
        "Decision Centre": "🧠",
        "Scenario Simulation": "🎯",
        "AI Data Analyst": "✨",
    },

    "REPORTS": {
        "Reports": "📄",
    },

    "ACCOUNT": {
        "Account Settings": "⚙️",
    },

}


# =====================================
# NAVIGATION FUNCTION
# =====================================

def render_sidebar():

    """
    Render the JAK application sidebar.

    Returns the selected navigation page.
    """

    with st.sidebar:

        # BRANDING
        st.markdown(
            """
            <div style="
                text-align: center;
                padding: 15px 5px 20px;
            ">

                <h1 style="
                    color: white;
                    font-size: 35px;
                    font-weight: 800;
                    margin-bottom: 0;
                ">
                    JAK
                </h1>

                <p style="
                    color: #98A2B3;
                    font-size: 11px;
                    letter-spacing: 2px;
                    margin-top: 0;
                ">
                    DATA ANALYTICS
                </p>

            </div>
            """,
            unsafe_allow_html=True
        )

        st.divider()

        # NAVIGATION SELECTION
        selected_page = "Dashboard"

        for section, pages in NAVIGATION_MENU.items():

            st.markdown(
                f"""
                <p style="
                    color: #98A2B3;
                    font-size: 10px;
                    font-weight: 700;
                    letter-spacing: 1px;
                    margin-top: 18px;
                    margin-bottom: 8px;
                ">
                    {section}
                </p>
                """,
                unsafe_allow_html=True
            )

            for page, icon in pages.items():

                if st.button(
                    f"{icon}  {page}",
                    key=f"nav_{page.lower().replace(' ', '_')}",
                    use_container_width=True
                ):

                    st.session_state["jak_current_page"] = page

        # GET CURRENT PAGE
        selected_page = st.session_state.get(
            "jak_current_page",
            "Dashboard"
        )

        st.divider()

        # VERSION INFORMATION
        st.markdown(
            """
            <div style="
                text-align: center;
                color: #98A2B3;
                font-size: 11px;
                padding: 10px 0;
            ">
                JAK Data Analytics<br>
                Version 1.0.0
            </div>
            """,
            unsafe_allow_html=True
        )

    return selected_page


# =====================================
# GET CURRENT PAGE
# =====================================

def get_current_page():

    """
    Return the currently selected application page.
    """

    return st.session_state.get(
        "jak_current_page",
        "Dashboard"
    )


# =====================================
# CHANGE PAGE
# =====================================

def navigate_to(page):

    """
    Programmatically select an application page.
    """

    st.session_state["jak_current_page"] = page