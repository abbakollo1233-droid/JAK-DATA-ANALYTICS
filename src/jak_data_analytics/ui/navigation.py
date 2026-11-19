"""
JAK Data Analytics
Navigation Components
"""

import streamlit as st


NAVIGATION_ITEMS = {
    "WORKSPACE": [
        ("🏠", "Dashboard"),
        ("📁", "My Projects"),
        ("📊", "Datasets"),
    ],
    "DATA ANALYSIS": [
        ("🔍", "Data Profiling"),
        ("🧹", "Data Cleaning"),
        ("🔄", "Transformations"),
        ("📈", "Statistical Analysis"),
        ("📉", "Visualisations"),
        ("🎨", "Dashboard Builder"),
    ],
    "INTELLIGENCE": [
        ("🤖", "Machine Learning"),
        ("🔮", "Predictions"),
        ("📅", "Forecasting"),
        ("🚨", "Anomaly Detection"),
        ("✨", "AI Data Analyst"),
        ("💡", "Recommendations"),
        ("🧠", "Decision Centre"),
        ("🎯", "Scenario Simulation"),
    ],
    "MANAGEMENT": [
        ("📄", "Reports"),
        ("⚙️", "Settings"),
    ],
}


def render_navigation():
    """Render the JAK application navigation sidebar."""

    current_page = st.session_state.get(
        "current_page",
        "Dashboard"
    )

    with st.sidebar:

        for section, items in NAVIGATION_ITEMS.items():

            st.markdown(
                f"""
                <div style="
                    color:#94A3B8;
                    font-size:10px;
                    font-weight:800;
                    letter-spacing:1.2px;
                    padding:14px 5px 8px;
                ">{section}</div>
                """,
                unsafe_allow_html=True
            )

            for icon, page in items:

                if st.button(
                    f"{icon}  {page}",
                    key=f"ui_navigation_{page}",
                    use_container_width=True,
                    type=(
                        "primary"
                        if current_page == page
                        else "secondary"
                    ),
                ):
                    st.session_state.current_page = page
                    st.rerun()