"""
JAK Data Analytics
Project Service

Handles project-related business logic.

Features:
- Create projects
- Retrieve projects
- List user projects
- Update projects
- Change project status
- Search projects
- Delete projects
- Project statistics

All project operations are scoped to the project owner.

Database transactions are managed by the caller.
"""

from ..database.repositories import project_repository


# ==================================================
# PROJECT VALIDATION
# ==================================================

ALLOWED_PROJECT_STATUSES = [
    "active",
    "completed",
    "archived",
]


# ==================================================
# CREATE PROJECT
# ==================================================

def create_project(
    session,
    user_id,
    name,
    description=None,
    category=None,
):
    """Create a project for a user."""

    if not user_id:
        raise ValueError("User ID is required.")

    name = (name or "").strip()

    if not name:
        raise ValueError("Project name is required.")

    if len(name) > 150:
        raise ValueError(
            "Project name cannot exceed 150 characters."
        )

    description = (description or "").strip() or None
    category = (category or "").strip() or None

    project = project_repository.create_project(
        session=session,
        user_id=user_id,
        name=name,
        description=description,
        category=category,
    )

    return project


# ==================================================
# GET PROJECT
# ==================================================

def get_project(
    session,
    project_id,
    user_id,
):
    """Retrieve a project belonging to a user."""

    if not project_id or not user_id:
        return None

    return project_repository.get_project_by_id(
        session,
        project_id,
        user_id,
    )


# ==================================================
# GET USER PROJECTS
# ==================================================

def get_user_projects(
    session,
    user_id,
    limit=100,
    offset=0,
    status=None,
):
    """Retrieve projects belonging to a user."""

    if not user_id:
        return []

    projects = project_repository.get_user_projects(
        session,
        user_id,
        limit=limit,
        offset=offset,
    )

    if status:
        projects = [
            project
            for project in projects
            if project.status == status
        ]

    return projects


# ==================================================
# UPDATE PROJECT
# ==================================================

def update_project(
    session,
    project_id,
    user_id,
    name=None,
    description=None,
    category=None,
):
    """Update project information."""

    project = get_project(
        session,
        project_id,
        user_id,
    )

    if project is None:
        raise ValueError("Project was not found.")

    if name is not None:

        name = name.strip()

        if not name:
            raise ValueError("Project name cannot be empty.")

        if len(name) > 150:
            raise ValueError(
                "Project name cannot exceed 150 characters."
            )

    if description is not None:
        description = description.strip() or None

    if category is not None:
        category = category.strip() or None

    return project_repository.update_project(
        session=session,
        project_id=project_id,
        user_id=user_id,
        name=name,
        description=description,
        category=category,
    )


# ==================================================
# CHANGE PROJECT STATUS
# ==================================================

def change_project_status(
    session,
    project_id,
    user_id,
    status,
):
    """Change the status of a project."""

    if status not in ALLOWED_PROJECT_STATUSES:
        raise ValueError("Invalid project status.")

    project = get_project(
        session,
        project_id,
        user_id,
    )

    if project is None:
        raise ValueError("Project was not found.")

    return project_repository.update_project_status(
        session,
        project_id,
        user_id,
        status,
    )


# ==================================================
# SEARCH PROJECTS
# ==================================================

def search_projects(
    session,
    user_id,
    search_term,
    limit=100,
):
    """Search a user's projects."""

    if not user_id:
        return []

    search_term = (search_term or "").strip()

    if not search_term:
        return []

    return project_repository.search_user_projects(
        session,
        user_id,
        search_term,
        limit=limit,
    )


# ==================================================
# DELETE PROJECT
# ==================================================

def delete_project(
    session,
    project_id,
    user_id,
):
    """Delete a project belonging to a user."""

    project = get_project(
        session,
        project_id,
        user_id,
    )

    if project is None:
        return False

    return project_repository.delete_project(
        session,
        project_id,
        user_id,
    )


# ==================================================
# COUNT USER PROJECTS
# ==================================================

def count_projects(
    session,
    user_id,
):
    """Count projects belonging to a user."""

    if not user_id:
        return 0

    return project_repository.count_user_projects(
        session,
        user_id,
    )


# ==================================================
# PROJECT STATISTICS
# ==================================================

def get_project_statistics(
    session,
    user_id,
):
    """Retrieve project statistics for a user."""

    if not user_id:
        return {
            "total_projects": 0,
            "active_projects": 0,
            "completed_projects": 0,
            "archived_projects": 0,
        }

    statistics = project_repository.get_project_statistics(
        session,
        user_id,
    )

    return statistics