"""
JAK Data Analytics
Projects Management Page

Allows users to create, view and manage analytics projects.
"""

import streamlit as st
from datetime import datetime
import uuid

from ...ui.layout import (
    render_topbar,
    render_page_intro,
    render_section_heading,
)
from ...ui.theme import show_footer


def projects_styles():
    """Apply projects page styling."""

    st.markdown(
        """
        <style>
        .project-hero {
            background: linear-gradient(120deg, #101828, #1D4ED8);
            padding: 28px;
            border-radius: 18px;
            color: white;
            margin-bottom: 25px;
        }

        .project-hero h2 {
            color: white;
            font-size: 25px;
        }

        .project-hero p {
            color: #DCE7FF;
            font-size: 14px;
        }

        .project-card {
            background: white;
            border: 1px solid #EAECF0;
            border-radius: 15px;
            padding: 20px;
            margin-bottom: 15px;
        }

        .project-card h4 {
            color: #101828;
            margin-bottom: 8px;
        }

        .project-card p {
            color: #667085;
            font-size: 13px;
            line-height: 1.6;
        }

        .project-status {
            display: inline-block;
            background: #ECFDF3;
            color: #027A48;
            padding: 5px 10px;
            border-radius: 20px;
            font-size: 11px;
            font-weight: 600;
        }

        </style>
        """,
        unsafe_allow_html=True
    )


def initialize_projects():
    """Initialize project storage for the current session."""

    if "jak_projects" not in st.session_state:
        st.session_state["jak_projects"] = []


def create_project(name, description, category):
    """Create a new project record."""

    project = {
        "id": str(uuid.uuid4()),
        "name": name.strip(),
        "description": description.strip(),
        "category": category,
        "status": "Active",
        "created_at": datetime.now().strftime(
            "%Y-%m-%d %H:%M"
        ),
    }

    st.session_state["jak_projects"].append(project)


def render_projects_hero():
    """Display projects introduction."""

    st.markdown(
        """
        <div class="project-hero">
            <h2>My Analytics Projects</h2>
            <p>
                Organize your datasets, analyses, visualizations
                and reports in dedicated projects.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )


def render_project_statistics():
    """Display project statistics."""

    projects = st.session_state["jak_projects"]

    total = len(projects)
    active = sum(
        1 for project in projects
        if project["status"] == "Active"
    )

    col1, col2, col3 = st.columns(3)

    col1.metric("Total Projects", total)
    col2.metric("Active Projects", active)
    col3.metric("Completed Projects", 0)


def render_create_project():
    """Display the project creation form."""

    render_section_heading(
        "Create New Project",
        "Start a new data analytics project."
    )

    with st.form("jak_create_project_form"):

        name = st.text_input(
            "Project Name",
            placeholder="e.g. Employee Salary Analysis"
        )

        description = st.text_area(
            "Project Description",
            placeholder="Describe what you want to achieve..."
        )

        category = st.selectbox(
            "Project Category",
            [
                "Business Analytics",
                "Education Analytics",
                "Financial Analytics",
                "Agricultural Analytics",
                "Healthcare Analytics",
                "Marketing Analytics",
                "Research and Statistics",
                "General Data Analysis",
                "Other",
            ]
        )

        submitted = st.form_submit_button(
            "Create Project",
            use_container_width=True,
            type="primary"
        )

        if submitted:

            if not name.strip():
                st.error("Please enter a project name.")

            elif any(
                project["name"].lower() == name.strip().lower()
                for project in st.session_state["jak_projects"]
            ):
                st.error("A project with this name already exists.")

            else:
                create_project(
                    name,
                    description,
                    category
                )

                st.success(
                    f"Project '{name.strip()}' created successfully!"
                )

                st.rerun()


def render_project_card(project):
    """Display an individual project."""

    with st.container(border=True):

        col1, col2 = st.columns([4, 1])

        with col1:
            st.subheader(f"📁 {project['name']}")

            st.caption(project["description"] or "No description provided.")

            st.caption(
                f"Category: {project['category']} | "
                f"Created: {project['created_at']}"
            )

            st.success(project["status"])

        with col2:
            if st.button(
                "Delete",
                key=f"delete_{project['id']}",
                use_container_width=True
            ):
                st.session_state["jak_projects"] = [
                    item for item in st.session_state["jak_projects"]
                    if item["id"] != project["id"]
                ]

                st.success("Project deleted.")
                st.rerun()


def render_project_list():
    """Display all available projects."""

    render_section_heading(
        "Your Projects",
        "View and manage your analytics projects."
    )

    projects = st.session_state["jak_projects"]

    if not projects:
        st.info(
            "You haven't created any projects yet. "
            "Create your first project above."
        )
        return

    search = st.text_input(
        "Search Projects",
        placeholder="Search by project name..."
    )

    filtered_projects = [
        project for project in projects
        if search.lower() in project["name"].lower()
    ]

    if not filtered_projects:
        st.warning("No matching projects found.")
        return

    for project in reversed(filtered_projects):
        render_project_card(project)


def render_projects_page():
    """Main projects page renderer."""

    initialize_projects()

    projects_styles()

    username = st.session_state.get(
        "jak_user_name",
        "Guest"
    )

    role = st.session_state.get(
        "jak_user_role",
        "User"
    )

    render_topbar(
        username=username,
        role=role
    )

    render_page_intro(
        "My Projects",
        "Create, organize and manage your data analytics projects."
    )

    render_projects_hero()

    render_project_statistics()

    st.divider()

    render_create_project()

    st.divider()

    render_project_list()

    show_footer()


render_my_projects = render_projects_page