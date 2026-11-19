
"""
JAK Data Analytics
User Dashboard

Main dashboard for registered JAK users.

Uses native Streamlit components only.
No HTML tags or unsafe HTML rendering.
"""

import streamlit as st
from datetime import datetime

from ...ui.layout import (
    render_topbar,
    render_page_intro,
    render_section_heading,
    render_empty_state,
)

from ...ui.theme import show_footer


# =========================================================
# DASHBOARD DATA HELPERS
# =========================================================

def get_session_count(*keys):
    """Return the number of records stored under session keys."""

    for key in keys:
        value = st.session_state.get(key)

        if isinstance(value, (list, tuple, set, dict)):
            return len(value)

    return 0


def get_username():
    """Get the current user's display name."""

    return (
        st.session_state.get("jak_user_name")
        or st.session_state.get("username")
        or "Data Analyst"
    )


def get_user_role():
    """Get the current user's role."""

    return (
        st.session_state.get("jak_user_role")
        or st.session_state.get("user_role")
        or "User"
    )


# =========================================================
# WELCOME SECTION
# =========================================================

def render_welcome_section():
    """Display the personalized welcome section."""

    username = get_username()

    current_date = datetime.now().strftime(
        "%A, %d %B %Y"
    )

    with st.container(border=True):

        st.caption("📊 JAK ANALYTICS WORKSPACE")

        st.title(f"Welcome back, {username}!")

        st.write(
            """
            Your data analytics workspace is ready.

            Explore your datasets, discover insights, build
            visualizations and make better decisions with
            JAK Data Analytics.
            """
        )

        st.caption(f"📅 {current_date}")


# =========================================================
# WORKSPACE METRICS
# =========================================================

def render_dashboard_metrics():
    """Display live workspace overview metrics."""

    render_section_heading(
        "Workspace Overview",
        "A quick overview of your analytics workspace."
    )

    total_datasets = get_session_count(
        "jak_datasets"
    )

    total_projects = get_session_count(
        "jak_projects"
    )

    total_reports = get_session_count(
        "jak_reports",
        "jak_generated_reports",
        "jak_saved_reports"
    )

    total_models = get_session_count(
        "jak_models",
        "jak_saved_models",
        "jak_ml_models"
    )

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            label="📁 Total Datasets",
            value=total_datasets
        )

    with col2:
        st.metric(
            label="📊 Total Projects",
            value=total_projects
        )

    with col3:
        st.metric(
            label="📄 Reports Created",
            value=total_reports
        )

    with col4:
        st.metric(
            label="🤖 Models Created",
            value=total_models
        )


# =========================================================
# QUICK ACTIONS
# =========================================================

def navigate_to(page):
    """Navigate to another application page."""

    st.session_state["current_page"] = page

    # Keep the secondary key synchronized if another
    # part of the application still uses it.
    st.session_state["jak_current_page"] = page

    st.rerun()


def render_quick_actions():
    """Display dashboard quick action buttons."""

    render_section_heading(
        "Quick Actions",
        "Start working on your data with one click."
    )

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button(
            "📤 Upload Dataset",
            use_container_width=True,
            key="dashboard_upload_dataset"
        ):
            navigate_to("Datasets")

    with col2:
        if st.button(
            "🔍 Explore Data",
            use_container_width=True,
            key="dashboard_explore_data"
        ):
            navigate_to("Data Profiling")

    with col3:
        if st.button(
            "📈 Create Visualization",
            use_container_width=True,
            key="dashboard_create_visualization"
        ):
            navigate_to("Visualisations")


# =========================================================
# ANALYTICS TOOLS
# =========================================================

def render_tool_card(
    icon,
    title,
    description,
    page_name
):
    """Display an analytics tool card with navigation."""

    with st.container(border=True):

        st.subheader(f"{icon} {title}")

        st.write(description)

        st.write("")

        if st.button(
            f"Open {title}",
            use_container_width=True,
            key=f"dashboard_tool_{page_name.lower().replace(' ', '_')}"
        ):
            navigate_to(page_name)


def render_analysis_tools():
    """Display available analytics tools."""

    render_section_heading(
        "Analytics Tools",
        "Explore the tools available in JAK Data Analytics."
    )

    # First row
    col1, col2, col3 = st.columns(3)

    with col1:
        render_tool_card(
            icon="🔍",
            title="Data Profiling",
            description=(
                "Understand your dataset through summaries, "
                "statistics, missing values and data quality checks."
            ),
            page_name="Data Profiling"
        )

    with col2:
        render_tool_card(
            icon="🧹",
            title="Data Cleaning",
            description=(
                "Identify and handle missing values, duplicates "
                "and inconsistent records."
            ),
            page_name="Data Cleaning"
        )

    with col3:
        render_tool_card(
            icon="📊",
            title="Statistical Analysis",
            description=(
                "Perform statistical calculations, comparisons "
                "and exploratory data analysis."
            ),
            page_name="Statistical Analysis"
        )

    # Second row
    col4, col5, col6 = st.columns(3)

    with col4:
        render_tool_card(
            icon="🤖",
            title="Machine Learning",
            description=(
                "Build predictive models and discover patterns "
                "in your datasets."
            ),
            page_name="Machine Learning"
        )

    with col5:
        render_tool_card(
            icon="📈",
            title="Forecasting",
            description=(
                "Analyze historical patterns and estimate "
                "possible future outcomes."
            ),
            page_name="Forecasting"
        )

    with col6:
        render_tool_card(
            icon="🧠",
            title="AI Data Analyst",
            description=(
                "Get intelligent assistance when exploring "
                "and understanding your datasets."
            ),
            page_name="AI Data Analyst"
        )


# =========================================================
# RECENT ACTIVITY
# =========================================================

def render_recent_activity():
    """Display recent user activity."""

    render_section_heading(
        "Recent Activity",
        "Keep track of your latest activities."
    )

    activities = st.session_state.get(
        "jak_recent_activities",
        []
    )

    if not activities:

        render_empty_state(
            title="No Recent Activity",
            description=(
                "Your recent dataset uploads, analyses, "
                "projects and reports will appear here."
            )
        )

        return

    # Show the latest five activities.
    recent_items = activities[-5:][::-1]

    for activity in recent_items:

        if isinstance(activity, dict):

            title = activity.get(
                "title",
                "Activity"
            )

            description = activity.get(
                "description",
                ""
            )

            activity_date = activity.get(
                "date",
                activity.get("created_at", "")
            )

        else:

            title = "Activity"
            description = str(activity)
            activity_date = ""

        with st.container(border=True):

            st.markdown(f"**{title}**")

            if description:
                st.write(description)

            if activity_date:
                st.caption(str(activity_date))


# =========================================================
# MAIN DASHBOARD
# =========================================================

def render_dashboard():
    """Main user dashboard renderer."""

    username = get_username()

    role = get_user_role()

    # Application top bar.
    render_topbar(
        username=username,
        role=role
    )

    # Page introduction.
    render_page_intro(
        "Dashboard",
        "Your central workspace for data analysis and intelligence."
    )

    # Welcome section.
    render_welcome_section()

    st.divider()

    # Workspace statistics.
    render_dashboard_metrics()

    st.divider()

    # Quick navigation.
    render_quick_actions()

    st.divider()

    # Available analytics tools.
    render_analysis_tools()

    st.divider()

    # Recent activity.
    render_recent_activity()

    # Application footer.
    show_footer()


# =========================================================
# NAVIGATION COMPATIBILITY
# =========================================================

render_user_dashboard = render_dashboard
