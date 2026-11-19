"""
JAK Data Analytics
Activity Repository

Manages user activity records.

Features:
- Record user activities
- Retrieve activity records
- List user activities
- Search activity history
- Count activities
- Generate activity statistics

Activity records are normally treated as historical records.
Transactions are managed by the service layer.
"""

from sqlalchemy import select, func, or_

from ..models import ActivityLog


# ==================================================
# CREATE ACTIVITY
# ==================================================

def create_activity(
    session,
    user_id,
    action,
    description=None,
    metadata=None,
    ip_address=None
):
    """Record an activity performed by a user."""

    if not user_id:
        raise ValueError("User ID is required.")

    if not action or not action.strip():
        raise ValueError("Activity action is required.")

    activity = ActivityLog(
        user_id=user_id,
        action=action.strip(),
        description=description,
        activity_metadata=metadata or {},
        ip_address=ip_address
    )

    session.add(activity)
    session.flush()

    return activity


# ==================================================
# GET ACTIVITY BY ID
# ==================================================

def get_activity_by_id(
    session,
    activity_id,
    user_id
):
    """Retrieve an activity belonging to a specific user."""

    statement = select(ActivityLog).where(
        ActivityLog.id == activity_id,
        ActivityLog.user_id == user_id
    )

    return session.execute(
        statement
    ).scalar_one_or_none()


# ==================================================
# GET USER ACTIVITIES
# ==================================================

def get_user_activities(
    session,
    user_id,
    limit=100,
    offset=0,
    action=None
):
    """Retrieve activity history for a user."""

    statement = select(ActivityLog).where(
        ActivityLog.user_id == user_id
    )

    if action:
        statement = statement.where(
            ActivityLog.action == action
        )

    statement = (
        statement
        .order_by(
            ActivityLog.created_at.desc(),
            ActivityLog.id.desc()
        )
        .offset(max(0, offset))
        .limit(max(1, min(limit, 500)))
    )

    return list(
        session.execute(statement).scalars().all()
    )


# ==================================================
# COUNT USER ACTIVITIES
# ==================================================

def count_user_activities(
    session,
    user_id,
    action=None
):
    """Count activities belonging to a user."""

    statement = select(
        func.count(ActivityLog.id)
    ).where(
        ActivityLog.user_id == user_id
    )

    if action:
        statement = statement.where(
            ActivityLog.action == action
        )

    return session.execute(
        statement
    ).scalar_one()


# ==================================================
# SEARCH USER ACTIVITIES
# ==================================================

def search_user_activities(
    session,
    user_id,
    search_term,
    limit=100
):
    """Search activities by action or description."""

    search_term = search_term.strip()

    if not search_term:
        return []

    pattern = f"%{search_term}%"

    statement = (
        select(ActivityLog)
        .where(
            ActivityLog.user_id == user_id,
            or_(
                ActivityLog.action.ilike(pattern),
                ActivityLog.description.ilike(pattern)
            )
        )
        .order_by(
            ActivityLog.created_at.desc()
        )
        .limit(max(1, min(limit, 200)))
    )

    return list(
        session.execute(statement).scalars().all()
    )


# ==================================================
# GET ACTIVITIES BY ACTION
# ==================================================

def get_activities_by_action(
    session,
    user_id,
    action,
    limit=100
):
    """Retrieve activities matching a specific action."""

    statement = (
        select(ActivityLog)
        .where(
            ActivityLog.user_id == user_id,
            ActivityLog.action == action
        )
        .order_by(
            ActivityLog.created_at.desc()
        )
        .limit(max(1, min(limit, 500)))
    )

    return list(
        session.execute(statement).scalars().all()
    )


# ==================================================
# GET RECENT ACTIVITIES
# ==================================================

def get_recent_activities(
    session,
    user_id,
    limit=10
):
    """Retrieve the most recent user activities."""

    statement = (
        select(ActivityLog)
        .where(
            ActivityLog.user_id == user_id
        )
        .order_by(
            ActivityLog.created_at.desc(),
            ActivityLog.id.desc()
        )
        .limit(max(1, min(limit, 100)))
    )

    return list(
        session.execute(statement).scalars().all()
    )


# ==================================================
# ACTIVITY STATISTICS
# ==================================================

def get_activity_statistics(
    session,
    user_id
):
    """Return activity statistics for a user."""

    total = count_user_activities(
        session,
        user_id
    )

    statement = (
        select(
            ActivityLog.action,
            func.count(ActivityLog.id)
        )
        .where(
            ActivityLog.user_id == user_id
        )
        .group_by(
            ActivityLog.action
        )
        .order_by(
            func.count(ActivityLog.id).desc()
        )
    )

    action_counts = {
        action: count
        for action, count in session.execute(statement).all()
    }

    return {
        "total_activities": total,
        "action_counts": action_counts,
        "unique_actions": len(action_counts)
    }