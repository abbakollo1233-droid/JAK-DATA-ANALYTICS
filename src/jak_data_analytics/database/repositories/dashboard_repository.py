"""
JAK Data Analytics
Dashboard Repository

Manages saved user dashboards.

Features:
- Create dashboards
- Retrieve dashboards
- List user dashboards
- Update dashboard information
- Save dashboard layouts
- Favourite dashboards
- Search dashboards
- Delete dashboards

Transactions are managed by the service layer.
"""

from sqlalchemy import select, func, or_

from ..models import SavedDashboard


# ==================================================
# CREATE DASHBOARD
# ==================================================

def create_dashboard(
    session,
    user_id,
    name,
    description=None,
    layout_config=None
):
    """Create a saved dashboard."""

    if not user_id:
        raise ValueError("User ID is required.")

    name = name.strip()

    if not name:
        raise ValueError("Dashboard name is required.")

    dashboard = SavedDashboard(
        user_id=user_id,
        name=name,
        description=description,
        layout_config=layout_config or {},
        is_favorite=False
    )

    session.add(dashboard)
    session.flush()

    return dashboard


# ==================================================
# GET DASHBOARD BY ID
# ==================================================

def get_dashboard_by_id(
    session,
    dashboard_id,
    user_id
):
    """Retrieve a dashboard belonging to a user."""

    statement = select(SavedDashboard).where(
        SavedDashboard.id == dashboard_id,
        SavedDashboard.user_id == user_id
    )

    return session.execute(
        statement
    ).scalar_one_or_none()


# ==================================================
# GET USER DASHBOARDS
# ==================================================

def get_user_dashboards(
    session,
    user_id,
    limit=100,
    offset=0,
    favorites_only=False
):
    """Retrieve saved dashboards for a user."""

    statement = select(SavedDashboard).where(
        SavedDashboard.user_id == user_id
    )

    if favorites_only:

        statement = statement.where(
            SavedDashboard.is_favorite.is_(True)
        )

    statement = (
        statement
        .order_by(
            SavedDashboard.is_favorite.desc(),
            SavedDashboard.updated_at.desc(),
            SavedDashboard.id.desc()
        )
        .offset(max(0, offset))
        .limit(max(1, min(limit, 500)))
    )

    return list(
        session.execute(statement).scalars().all()
    )


# ==================================================
# COUNT USER DASHBOARDS
# ==================================================

def count_user_dashboards(
    session,
    user_id,
    favorites_only=False
):
    """Count dashboards belonging to a user."""

    statement = select(
        func.count(SavedDashboard.id)
    ).where(
        SavedDashboard.user_id == user_id
    )

    if favorites_only:

        statement = statement.where(
            SavedDashboard.is_favorite.is_(True)
        )

    return session.execute(
        statement
    ).scalar_one()


# ==================================================
# UPDATE DASHBOARD INFORMATION
# ==================================================

def update_dashboard(
    session,
    dashboard_id,
    user_id,
    name=None,
    description=None
):
    """Update dashboard name or description."""

    dashboard = get_dashboard_by_id(
        session,
        dashboard_id,
        user_id
    )

    if dashboard is None:
        return None

    if name is not None:

        name = name.strip()

        if not name:
            raise ValueError(
                "Dashboard name cannot be empty."
            )

        dashboard.name = name

    if description is not None:
        dashboard.description = description

    session.flush()

    return dashboard


# ==================================================
# UPDATE DASHBOARD LAYOUT
# ==================================================

def update_dashboard_layout(
    session,
    dashboard_id,
    user_id,
    layout_config
):
    """Save a dashboard's component and layout configuration."""

    dashboard = get_dashboard_by_id(
        session,
        dashboard_id,
        user_id
    )

    if dashboard is None:
        return None

    dashboard.layout_config = layout_config or {}

    session.flush()

    return dashboard


# ==================================================
# TOGGLE DASHBOARD FAVORITE
# ==================================================

def toggle_dashboard_favorite(
    session,
    dashboard_id,
    user_id
):
    """Toggle dashboard favourite status."""

    dashboard = get_dashboard_by_id(
        session,
        dashboard_id,
        user_id
    )

    if dashboard is None:
        return None

    dashboard.is_favorite = not dashboard.is_favorite

    session.flush()

    return dashboard


# ==================================================
# SET DASHBOARD FAVORITE
# ==================================================

def set_dashboard_favorite(
    session,
    dashboard_id,
    user_id,
    is_favorite
):
    """Explicitly set dashboard favourite status."""

    dashboard = get_dashboard_by_id(
        session,
        dashboard_id,
        user_id
    )

    if dashboard is None:
        return None

    dashboard.is_favorite = bool(is_favorite)

    session.flush()

    return dashboard


# ==================================================
# SEARCH DASHBOARDS
# ==================================================

def search_user_dashboards(
    session,
    user_id,
    search_term,
    limit=100
):
    """Search dashboards by name or description."""

    search_term = search_term.strip()

    if not search_term:
        return []

    pattern = f"%{search_term}%"

    statement = (
        select(SavedDashboard)
        .where(
            SavedDashboard.user_id == user_id,
            or_(
                SavedDashboard.name.ilike(pattern),
                SavedDashboard.description.ilike(pattern)
            )
        )
        .order_by(
            SavedDashboard.updated_at.desc()
        )
        .limit(max(1, min(limit, 200)))
    )

    return list(
        session.execute(statement).scalars().all()
    )


# ==================================================
# DELETE DASHBOARD
# ==================================================

def delete_dashboard(
    session,
    dashboard_id,
    user_id
):
    """Delete a dashboard belonging to a specific user."""

    dashboard = get_dashboard_by_id(
        session,
        dashboard_id,
        user_id
    )

    if dashboard is None:
        return False

    session.delete(dashboard)
    session.flush()

    return True


# ==================================================
# DASHBOARD STATISTICS
# ==================================================

def get_dashboard_statistics(
    session,
    user_id
):
    """Return dashboard statistics for a user."""

    total = count_user_dashboards(
        session,
        user_id
    )

    favorites = count_user_dashboards(
        session,
        user_id,
        favorites_only=True
    )

    return {
        "total_dashboards": total,
        "favorite_dashboards": favorites,
        "regular_dashboards": total - favorites
    }