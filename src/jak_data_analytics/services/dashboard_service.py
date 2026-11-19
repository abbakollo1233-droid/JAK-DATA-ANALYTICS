"""
JAK Data Analytics
Dashboard Service

Handles dashboard business logic and connects
the application to the dashboard repository.

Features:
- Create dashboards
- Retrieve dashboards
- List user dashboards
- Update dashboard information
- Save dashboard layouts
- Manage dashboard favourites
- Search dashboards
- Delete dashboards
- Dashboard statistics
- Layout validation

All dashboard operations are scoped to their owner.

This module does not depend on Streamlit.
"""

import json
from copy import deepcopy

from ..database.repositories import dashboard_repository


# ==================================================
# CONSTANTS
# ==================================================

DEFAULT_DASHBOARD_NAME = "My Dashboard"

MAX_DASHBOARD_NAME_LENGTH = 150
MAX_DESCRIPTION_LENGTH = 2000
MAX_DASHBOARD_COMPONENTS = 100

SUPPORTED_COMPONENT_TYPES = [
    "metric",
    "chart",
    "table",
    "text",
    "image",
]

SUPPORTED_CHART_TYPES = [
    "bar",
    "line",
    "area",
    "pie",
    "donut",
    "scatter",
    "histogram",
    "box",
    "violin",
    "heatmap",
    "funnel",
    "treemap",
    "sunburst",
]


# ==================================================
# VALIDATION
# ==================================================

def validate_user_id(user_id):
    """Validate dashboard owner ID."""

    if not isinstance(user_id, int) or isinstance(user_id, bool):
        raise ValueError(
            "A valid integer user ID is required."
        )

    if user_id <= 0:
        raise ValueError(
            "User ID must be greater than zero."
        )

    return True


def validate_dashboard_name(name):
    """Validate dashboard name."""

    if not isinstance(name, str):
        raise ValueError(
            "Dashboard name must be text."
        )

    name = name.strip()

    if not name:
        raise ValueError(
            "Dashboard name cannot be empty."
        )

    if len(name) > MAX_DASHBOARD_NAME_LENGTH:
        raise ValueError(
            f"Dashboard name cannot exceed "
            f"{MAX_DASHBOARD_NAME_LENGTH} characters."
        )

    return name


def validate_description(description):
    """Validate dashboard description."""

    if description is None:
        return None

    if not isinstance(description, str):
        raise ValueError(
            "Dashboard description must be text."
        )

    description = description.strip()

    if len(description) > MAX_DESCRIPTION_LENGTH:
        raise ValueError(
            f"Description cannot exceed "
            f"{MAX_DESCRIPTION_LENGTH} characters."
        )

    return description or None


def validate_dashboard_id(dashboard_id):
    """Validate dashboard ID."""

    if not isinstance(dashboard_id, int) or isinstance(dashboard_id, bool):
        raise ValueError(
            "A valid integer dashboard ID is required."
        )

    if dashboard_id <= 0:
        raise ValueError(
            "Dashboard ID must be greater than zero."
        )

    return True


# ==================================================
# LAYOUT VALIDATION
# ==================================================

def validate_layout_config(layout_config):
    """
    Validate dashboard layout configuration.

    Expected general structure:

    {
        "components": [
            {
                "id": "component_1",
                "type": "chart",
                "title": "Sales Overview",
                "config": {}
            }
        ]
    }
    """

    if layout_config is None:
        return {
            "components": [],
            "version": 1,
        }

    if not isinstance(layout_config, dict):
        raise ValueError(
            "Dashboard layout must be a dictionary."
        )

    layout = deepcopy(layout_config)

    try:
        json.dumps(layout)
    except (TypeError, ValueError):
        raise ValueError(
            "Dashboard layout must contain JSON-compatible values."
        )

    components = layout.get(
        "components",
        []
    )

    if not isinstance(components, list):
        raise ValueError(
            "Dashboard components must be stored as a list."
        )

    if len(components) > MAX_DASHBOARD_COMPONENTS:
        raise ValueError(
            f"A dashboard cannot contain more than "
            f"{MAX_DASHBOARD_COMPONENTS} components."
        )

    component_ids = set()

    for component in components:

        if not isinstance(component, dict):
            raise ValueError(
                "Every dashboard component must be a dictionary."
            )

        component_id = component.get("id")

        if not isinstance(component_id, str) or not component_id.strip():
            raise ValueError(
                "Every component must have a valid ID."
            )

        if component_id in component_ids:
            raise ValueError(
                f"Duplicate component ID: {component_id}"
            )

        component_ids.add(component_id)

        component_type = component.get("type")

        if component_type not in SUPPORTED_COMPONENT_TYPES:
            raise ValueError(
                f"Unsupported component type: {component_type}"
            )

        title = component.get("title", "")

        if not isinstance(title, str):
            raise ValueError(
                "Component title must be text."
            )

        if len(title) > 200:
            raise ValueError(
                "Component title cannot exceed 200 characters."
            )

        config = component.get(
            "config",
            {}
        )

        if not isinstance(config, dict):
            raise ValueError(
                "Component configuration must be a dictionary."
            )

        if component_type == "chart":

            chart_type = config.get("chart_type")

            if chart_type is not None:
                if chart_type not in SUPPORTED_CHART_TYPES:
                    raise ValueError(
                        f"Unsupported chart type: {chart_type}"
                    )

    layout.setdefault(
        "version",
        1
    )

    return layout


# ==================================================
# CREATE DASHBOARD
# ==================================================

def create_dashboard(
    session,
    user_id,
    name=DEFAULT_DASHBOARD_NAME,
    description=None,
    layout_config=None,
):
    """Create a new dashboard for a user."""

    validate_user_id(user_id)

    name = validate_dashboard_name(name)

    description = validate_description(
        description
    )

    layout = validate_layout_config(
        layout_config
    )

    dashboard = dashboard_repository.create_dashboard(
        session=session,
        user_id=user_id,
        name=name,
        description=description,
        layout_config=layout,
    )

    return dashboard


# ==================================================
# GET DASHBOARD
# ==================================================

def get_dashboard(
    session,
    dashboard_id,
    user_id,
):
    """Retrieve a dashboard belonging to a user."""

    validate_dashboard_id(dashboard_id)
    validate_user_id(user_id)

    return dashboard_repository.get_dashboard_by_id(
        session=session,
        dashboard_id=dashboard_id,
        user_id=user_id,
    )


# ==================================================
# LIST DASHBOARDS
# ==================================================

def get_user_dashboards(
    session,
    user_id,
    limit=100,
    offset=0,
    favorites_only=False,
):
    """Retrieve dashboards belonging to a user."""

    validate_user_id(user_id)

    if not isinstance(limit, int) or isinstance(limit, bool):
        raise ValueError(
            "Limit must be an integer."
        )

    if not isinstance(offset, int) or isinstance(offset, bool):
        raise ValueError(
            "Offset must be an integer."
        )

    if limit < 1 or limit > 500:
        raise ValueError(
            "Limit must be between 1 and 500."
        )

    if offset < 0:
        raise ValueError(
            "Offset cannot be negative."
        )

    if not isinstance(favorites_only, bool):
        raise ValueError(
            "favorites_only must be True or False."
        )

    return dashboard_repository.get_user_dashboards(
        session=session,
        user_id=user_id,
        limit=limit,
        offset=offset,
        favorites_only=favorites_only,
    )


# ==================================================
# COUNT DASHBOARDS
# ==================================================

def count_user_dashboards(
    session,
    user_id,
):
    """Count dashboards owned by a user."""

    validate_user_id(user_id)

    return dashboard_repository.count_user_dashboards(
        session=session,
        user_id=user_id,
    )


# ==================================================
# UPDATE DASHBOARD INFORMATION
# ==================================================

def update_dashboard(
    session,
    dashboard_id,
    user_id,
    name=None,
    description=None,
):
    """Update dashboard name and description."""

    validate_dashboard_id(dashboard_id)
    validate_user_id(user_id)

    dashboard = get_dashboard(
        session,
        dashboard_id,
        user_id,
    )

    if dashboard is None:
        return None

    updates = {}

    if name is not None:
        updates["name"] = validate_dashboard_name(
            name
        )

    if description is not None:
        updates["description"] = validate_description(
            description
        )

    if not updates:
        return dashboard

    return dashboard_repository.update_dashboard(
        session=session,
        dashboard_id=dashboard_id,
        user_id=user_id,
        **updates,
    )


# ==================================================
# UPDATE DASHBOARD LAYOUT
# ==================================================

def update_dashboard_layout(
    session,
    dashboard_id,
    user_id,
    layout_config,
):
    """Save a dashboard's component layout."""

    validate_dashboard_id(dashboard_id)
    validate_user_id(user_id)

    dashboard = get_dashboard(
        session,
        dashboard_id,
        user_id,
    )

    if dashboard is None:
        return None

    layout = validate_layout_config(
        layout_config
    )

    return dashboard_repository.update_dashboard_layout(
        session=session,
        dashboard_id=dashboard_id,
        user_id=user_id,
        layout_config=layout,
    )


# ==================================================
# ADD COMPONENT
# ==================================================

def add_dashboard_component(
    session,
    dashboard_id,
    user_id,
    component,
):
    """Add a component to an existing dashboard."""

    validate_dashboard_id(dashboard_id)
    validate_user_id(user_id)

    if not isinstance(component, dict):
        raise ValueError(
            "Component must be a dictionary."
        )

    dashboard = get_dashboard(
        session,
        dashboard_id,
        user_id,
    )

    if dashboard is None:
        return None

    current_layout = validate_layout_config(
        dashboard.layout_config
    )

    updated_layout = deepcopy(
        current_layout
    )

    components = updated_layout["components"]

    components.append(
        deepcopy(component)
    )

    updated_layout = validate_layout_config(
        updated_layout
    )

    return dashboard_repository.update_dashboard_layout(
        session=session,
        dashboard_id=dashboard_id,
        user_id=user_id,
        layout_config=updated_layout,
    )


# ==================================================
# REMOVE COMPONENT
# ==================================================

def remove_dashboard_component(
    session,
    dashboard_id,
    user_id,
    component_id,
):
    """Remove a component from a dashboard."""

    validate_dashboard_id(dashboard_id)
    validate_user_id(user_id)

    if not isinstance(component_id, str) or not component_id.strip():
        raise ValueError(
            "A valid component ID is required."
        )

    dashboard = get_dashboard(
        session,
        dashboard_id,
        user_id,
    )

    if dashboard is None:
        return None

    current_layout = validate_layout_config(
        dashboard.layout_config
    )

    updated_layout = deepcopy(
        current_layout
    )

    original_count = len(
        updated_layout["components"]
    )

    updated_layout["components"] = [
        component
        for component in updated_layout["components"]
        if component.get("id") != component_id
    ]

    if len(updated_layout["components"]) == original_count:
        return dashboard

    return dashboard_repository.update_dashboard_layout(
        session=session,
        dashboard_id=dashboard_id,
        user_id=user_id,
        layout_config=updated_layout,
    )


# ==================================================
# REPLACE COMPONENT
# ==================================================

def update_dashboard_component(
    session,
    dashboard_id,
    user_id,
    component_id,
    updated_component,
):
    """Update an existing dashboard component."""

    validate_dashboard_id(dashboard_id)
    validate_user_id(user_id)

    if not isinstance(component_id, str) or not component_id.strip():
        raise ValueError(
            "A valid component ID is required."
        )

    if not isinstance(updated_component, dict):
        raise ValueError(
            "Updated component must be a dictionary."
        )

    dashboard = get_dashboard(
        session,
        dashboard_id,
        user_id,
    )

    if dashboard is None:
        return None

    current_layout = validate_layout_config(
        dashboard.layout_config
    )

    updated_layout = deepcopy(
        current_layout
    )

    found = False

    for index, component in enumerate(
        updated_layout["components"]
    ):

        if component.get("id") == component_id:

            replacement = deepcopy(
                updated_component
            )

            replacement["id"] = component_id

            updated_layout["components"][index] = replacement

            found = True

            break

    if not found:
        return dashboard

    updated_layout = validate_layout_config(
        updated_layout
    )

    return dashboard_repository.update_dashboard_layout(
        session=session,
        dashboard_id=dashboard_id,
        user_id=user_id,
        layout_config=updated_layout,
    )


# ==================================================
# FAVOURITES
# ==================================================

def toggle_dashboard_favorite(
    session,
    dashboard_id,
    user_id,
):
    """Toggle dashboard favourite status."""

    validate_dashboard_id(dashboard_id)
    validate_user_id(user_id)

    dashboard = get_dashboard(
        session,
        dashboard_id,
        user_id,
    )

    if dashboard is None:
        return None

    return dashboard_repository.toggle_dashboard_favorite(
        session=session,
        dashboard_id=dashboard_id,
        user_id=user_id,
    )


def set_dashboard_favorite(
    session,
    dashboard_id,
    user_id,
    is_favorite,
):
    """Set dashboard favourite status."""

    validate_dashboard_id(dashboard_id)
    validate_user_id(user_id)

    if not isinstance(is_favorite, bool):
        raise ValueError(
            "is_favorite must be True or False."
        )

    dashboard = get_dashboard(
        session,
        dashboard_id,
        user_id,
    )

    if dashboard is None:
        return None

    return dashboard_repository.set_dashboard_favorite(
        session=session,
        dashboard_id=dashboard_id,
        user_id=user_id,
        is_favorite=is_favorite,
    )


# ==================================================
# SEARCH DASHBOARDS
# ==================================================

def search_dashboards(
    session,
    user_id,
    search_term,
):
    """Search dashboards belonging to a user."""

    validate_user_id(user_id)

    if not isinstance(search_term, str):
        raise ValueError(
            "Search term must be text."
        )

    search_term = search_term.strip()

    if not search_term:
        return []

    return dashboard_repository.search_user_dashboards(
        session=session,
        user_id=user_id,
        search_term=search_term,
    )


# ==================================================
# DELETE DASHBOARD
# ==================================================

def delete_dashboard(
    session,
    dashboard_id,
    user_id,
):
    """Delete a dashboard belonging to a user."""

    validate_dashboard_id(dashboard_id)
    validate_user_id(user_id)

    dashboard = get_dashboard(
        session,
        dashboard_id,
        user_id,
    )

    if dashboard is None:
        return False

    return dashboard_repository.delete_dashboard(
        session=session,
        dashboard_id=dashboard_id,
        user_id=user_id,
    )


# ==================================================
# DASHBOARD STATISTICS
# ==================================================

def get_dashboard_statistics(
    session,
    user_id,
):
    """Retrieve dashboard statistics for a user."""

    validate_user_id(user_id)

    return dashboard_repository.get_dashboard_statistics(
        session=session,
        user_id=user_id,
    )


# ==================================================
# DUPLICATE DASHBOARD
# ==================================================

def duplicate_dashboard(
    session,
    dashboard_id,
    user_id,
    new_name=None,
):
    """Create a copy of an existing dashboard."""

    validate_dashboard_id(dashboard_id)
    validate_user_id(user_id)

    original = get_dashboard(
        session,
        dashboard_id,
        user_id,
    )

    if original is None:
        return None

    if new_name is None:
        new_name = f"{original.name} (Copy)"

    new_name = validate_dashboard_name(
        new_name
    )

    layout = deepcopy(
        validate_layout_config(
            original.layout_config
        )
    )

    return create_dashboard(
        session=session,
        user_id=user_id,
        name=new_name,
        description=original.description,
        layout_config=layout,
    )


# ==================================================
# DASHBOARD EXPORT DATA
# ==================================================

def prepare_dashboard_export(
    dashboard,
):
    """
    Prepare a dashboard definition for JSON export.

    This exports the dashboard configuration,
    not the underlying dataset contents.
    """

    if dashboard is None:
        raise ValueError(
            "Dashboard does not exist."
        )

    layout = validate_layout_config(
        dashboard.layout_config
    )

    export_data = {
        "name": dashboard.name,
        "description": dashboard.description,
        "layout": layout,
        "version": 1,
    }

    return json.dumps(
        export_data,
        indent=4,
        ensure_ascii=False,
    )