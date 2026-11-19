"""
JAK Data Analytics
Project Repository

Handles database operations for user projects.

Features:
- Create projects
- Retrieve projects
- List projects belonging to a user
- Search projects
- Update project information
- Change project status
- Delete projects
- Count projects

Security:
Every user-specific operation checks ownership
using the user_id supplied by the service layer.

Transaction commits are managed by the service layer.
"""

from sqlalchemy import select, func, or_

from ..models import Project


# ==================================================
# CREATE PROJECT
# ==================================================

def create_project(
    session,
    user_id,
    name,
    description=None,
    category=None
):
    """Create a new project for a user."""

    if not user_id:
        raise ValueError("User ID is required.")

    name = name.strip()

    if not name:
        raise ValueError("Project name is required.")

    project = Project(
        user_id=user_id,
        name=name,
        description=description.strip() if description else None,
        category=category.strip() if category else None,
        status="active"
    )

    session.add(project)
    session.flush()

    return project


# ==================================================
# GET PROJECT BY ID
# ==================================================

def get_project_by_id(
    session,
    project_id,
    user_id
):
    """Retrieve a project belonging to a specific user."""

    statement = select(Project).where(
        Project.id == project_id,
        Project.user_id == user_id
    )

    return session.execute(
        statement
    ).scalar_one_or_none()


# ==================================================
# GET ALL USER PROJECTS
# ==================================================

def get_user_projects(
    session,
    user_id,
    limit=100,
    offset=0,
    status=None
):
    """Retrieve projects belonging to one user."""

    statement = select(Project).where(
        Project.user_id == user_id
    )

    if status:
        statement = statement.where(
            Project.status == status
        )

    statement = (
        statement
        .order_by(
            Project.created_at.desc(),
            Project.id.desc()
        )
        .offset(max(0, offset))
        .limit(max(1, min(limit, 500)))
    )

    return list(
        session.execute(statement).scalars().all()
    )


# ==================================================
# COUNT USER PROJECTS
# ==================================================

def count_user_projects(
    session,
    user_id,
    status=None
):
    """Count projects belonging to a user."""

    statement = select(
        func.count(Project.id)
    ).where(
        Project.user_id == user_id
    )

    if status:
        statement = statement.where(
            Project.status == status
        )

    return session.execute(
        statement
    ).scalar_one()


# ==================================================
# UPDATE PROJECT
# ==================================================

def update_project(
    session,
    project_id,
    user_id,
    name=None,
    description=None,
    category=None
):
    """Update a project after checking ownership."""

    project = get_project_by_id(
        session,
        project_id,
        user_id
    )

    if project is None:
        return None

    if name is not None:

        name = name.strip()

        if not name:
            raise ValueError("Project name cannot be empty.")

        project.name = name

    if description is not None:
        project.description = description.strip()

    if category is not None:
        project.category = category.strip()

    session.flush()

    return project


# ==================================================
# UPDATE PROJECT STATUS
# ==================================================

def update_project_status(
    session,
    project_id,
    user_id,
    status
):
    """Change the status of a user's project."""

    allowed_statuses = {
        "active",
        "completed",
        "archived",
        "on_hold"
    }

    status = status.strip().lower()

    if status not in allowed_statuses:
        raise ValueError("Invalid project status.")

    project = get_project_by_id(
        session,
        project_id,
        user_id
    )

    if project is None:
        return None

    project.status = status

    session.flush()

    return project


# ==================================================
# SEARCH USER PROJECTS
# ==================================================

def search_user_projects(
    session,
    user_id,
    search_term,
    limit=100
):
    """Search a user's projects by name or description."""

    search_term = search_term.strip()

    if not search_term:
        return []

    pattern = f"%{search_term}%"

    statement = (
        select(Project)
        .where(
            Project.user_id == user_id,
            or_(
                Project.name.ilike(pattern),
                Project.description.ilike(pattern),
                Project.category.ilike(pattern)
            )
        )
        .order_by(Project.created_at.desc())
        .limit(max(1, min(limit, 200)))
    )

    return list(
        session.execute(statement).scalars().all()
    )


# ==================================================
# DELETE PROJECT
# ==================================================

def delete_project(
    session,
    project_id,
    user_id
):
    """Delete a project belonging to a specific user."""

    project = get_project_by_id(
        session,
        project_id,
        user_id
    )

    if project is None:
        return False

    session.delete(project)
    session.flush()

    return True


# ==================================================
# GET PROJECT STATISTICS
# ==================================================

def get_project_statistics(
    session,
    user_id
):
    """Return project counts grouped by status."""

    statement = (
        select(
            Project.status,
            func.count(Project.id)
        )
        .where(Project.user_id == user_id)
        .group_by(Project.status)
    )

    results = session.execute(statement).all()

    statistics = {
        "total": 0,
        "active": 0,
        "completed": 0,
        "archived": 0,
        "on_hold": 0
    }

    for status, count in results:

        statistics[status] = count
        statistics["total"] += count

    return statistics