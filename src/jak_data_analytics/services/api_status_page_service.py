"""
JAK Data Analytics
API Status Page Service

Features:
- Status page configuration
- Service component management
- Component health updates
- Overall system status
- Incident publication
- Incident update history
- Scheduled maintenance
- Maintenance completion
- Public status summaries
- JSON export

Storage:
In-memory storage.

Production note:
Use database persistence and connect this service to
the API monitoring and incident management services.
"""

from __future__ import annotations

import json
import threading
import uuid

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


class APIStatusPageError(Exception):
    """Raised when a status page operation fails."""


class APIStatusPageService:
    """Manages JAK API status page information."""

    COMPONENT_STATUSES = {
        "operational",
        "degraded",
        "partial_outage",
        "major_outage",
        "maintenance",
        "unknown",
    }

    INCIDENT_STATUSES = {
        "investigating",
        "identified",
        "monitoring",
        "resolved",
    }

    INCIDENT_IMPACTS = {
        "none",
        "minor",
        "major",
        "critical",
    }

    MAINTENANCE_STATUSES = {
        "scheduled",
        "in_progress",
        "completed",
        "cancelled",
    }

    DEFAULT_MAX_RECORDS = 5000

    def __init__(self, max_records: int = DEFAULT_MAX_RECORDS):
        if (
            isinstance(max_records, bool)
            or not isinstance(max_records, int)
            or max_records <= 0
        ):
            raise APIStatusPageError(
                "max_records must be a positive integer."
            )

        self.max_records = max_records

        self._components: Dict[str, Dict[str, Any]] = {}
        self._incidents: Dict[str, Dict[str, Any]] = {}
        self._maintenance: Dict[str, Dict[str, Any]] = {}

        self._lock = threading.RLock()

        self._configuration = {
            "name": "JAK Data Analytics System Status",
            "description": (
                "Official operational status of JAK Data Analytics services."
            ),
            "website_url": None,
            "support_email": None,
            "is_public": True,
            "created_at": self._now(),
            "updated_at": self._now(),
        }

    # --------------------------------------------------
    # GENERAL HELPERS
    # --------------------------------------------------

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat()

    @staticmethod
    def _validate_text(
        value: Any,
        field_name: str,
        max_length: int = 500,
    ) -> str:
        if not isinstance(value, str):
            raise APIStatusPageError(
                f"{field_name} must be a string."
            )

        value = value.strip()

        if not value:
            raise APIStatusPageError(
                f"{field_name} cannot be empty."
            )

        if len(value) > max_length:
            raise APIStatusPageError(
                f"{field_name} cannot exceed {max_length} characters."
            )

        return value

    @staticmethod
    def _copy(value: Dict[str, Any]) -> Dict[str, Any]:
        return json.loads(
            json.dumps(value, default=str)
        )

    def _check_capacity(self, collection: Dict[str, Any]) -> None:
        if len(collection) >= self.max_records:
            raise APIStatusPageError(
                "Status page storage capacity reached."
            )

    # --------------------------------------------------
    # CONFIGURATION
    # --------------------------------------------------

    def get_configuration(self) -> Dict[str, Any]:
        """Return status page configuration."""

        with self._lock:
            return self._copy(self._configuration)

    def update_configuration(
        self,
        name: Optional[str] = None,
        description: Optional[str] = None,
        website_url: Optional[str] = None,
        support_email: Optional[str] = None,
        is_public: Optional[bool] = None,
    ) -> Dict[str, Any]:
        """Update status page settings."""

        updates = {}

        if name is not None:
            updates["name"] = self._validate_text(
                name,
                "name",
                200,
            )

        if description is not None:
            updates["description"] = self._validate_text(
                description,
                "description",
                1000,
            )

        if website_url is not None:
            website_url = self._validate_text(
                website_url,
                "website_url",
                500,
            )

            if not website_url.startswith("https://"):
                raise APIStatusPageError(
                    "website_url must use HTTPS."
                )

            updates["website_url"] = website_url

        if support_email is not None:
            support_email = self._validate_text(
                support_email,
                "support_email",
                254,
            )

            if (
                "@" not in support_email
                or "." not in support_email.rsplit("@", 1)[-1]
            ):
                raise APIStatusPageError(
                    "Invalid support email address."
                )

            updates["support_email"] = support_email

        if is_public is not None:
            if not isinstance(is_public, bool):
                raise APIStatusPageError(
                    "is_public must be a boolean."
                )

            updates["is_public"] = is_public

        if not updates:
            raise APIStatusPageError(
                "No configuration changes were supplied."
            )

        with self._lock:
            self._configuration.update(updates)
            self._configuration["updated_at"] = self._now()

            return self._copy(self._configuration)

    # --------------------------------------------------
    # COMPONENT MANAGEMENT
    # --------------------------------------------------

    def create_component(
        self,
        name: str,
        description: str,
        group: str = "Core Services",
        initial_status: str = "unknown",
        display_order: int = 0,
    ) -> Dict[str, Any]:
        """Register a service component."""

        name = self._validate_text(
            name,
            "name",
            150,
        )

        description = self._validate_text(
            description,
            "description",
            1000,
        )

        group = self._validate_text(
            group,
            "group",
            150,
        )

        if initial_status not in self.COMPONENT_STATUSES:
            raise APIStatusPageError(
                "Invalid component status."
            )

        if (
            isinstance(display_order, bool)
            or not isinstance(display_order, int)
        ):
            raise APIStatusPageError(
                "display_order must be an integer."
            )

        with self._lock:
            for component in self._components.values():
                if component["name"].lower() == name.lower():
                    raise APIStatusPageError(
                        "A component with this name already exists."
                    )

            self._check_capacity(self._components)

            component_id = uuid.uuid4().hex
            now = self._now()

            component = {
                "component_id": component_id,
                "name": name,
                "description": description,
                "group": group,
                "status": initial_status,
                "display_order": display_order,
                "created_at": now,
                "updated_at": now,
                "status_history": [
                    {
                        "status": initial_status,
                        "message": "Component registered.",
                        "created_at": now,
                    }
                ],
            }

            self._components[component_id] = component

            return self._copy(component)

    def get_component(
        self,
        component_id: str,
    ) -> Optional[Dict[str, Any]]:
        """Retrieve a component."""

        with self._lock:
            component = self._components.get(component_id)

            return (
                self._copy(component)
                if component
                else None
            )

    def get_components(
        self,
        group: Optional[str] = None,
        status: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Retrieve registered components."""

        if status is not None and status not in self.COMPONENT_STATUSES:
            raise APIStatusPageError(
                "Invalid component status filter."
            )

        with self._lock:
            components = [
                self._copy(component)
                for component in self._components.values()
            ]

        if group:
            components = [
                item for item in components
                if item["group"].lower() == group.lower()
            ]

        if status:
            components = [
                item for item in components
                if item["status"] == status
            ]

        components.sort(
            key=lambda item: (
                item["display_order"],
                item["name"].lower(),
            )
        )

        return components

    def update_component_status(
        self,
        component_id: str,
        status: str,
        message: str = "Component status updated.",
    ) -> Dict[str, Any]:
        """Update the operational status of a component."""

        if status not in self.COMPONENT_STATUSES:
            raise APIStatusPageError(
                "Invalid component status."
            )

        message = self._validate_text(
            message,
            "message",
            1000,
        )

        with self._lock:
            component = self._components.get(component_id)

            if component is None:
                raise APIStatusPageError(
                    "Component not found."
                )

            now = self._now()

            component["status"] = status
            component["updated_at"] = now

            component["status_history"].append({
                "status": status,
                "message": message,
                "created_at": now,
            })

            return self._copy(component)

    def delete_component(
        self,
        component_id: str,
    ) -> bool:
        """Delete a component from the status page."""

        with self._lock:
            if component_id not in self._components:
                return False

            del self._components[component_id]

            return True

    # --------------------------------------------------
    # OVERALL SYSTEM STATUS
    # --------------------------------------------------

    def get_overall_status(self) -> Dict[str, Any]:
        """Calculate the overall operational status."""

        with self._lock:
            statuses = [
                component["status"]
                for component in self._components.values()
            ]

            active_maintenance = [
                item
                for item in self._maintenance.values()
                if item["status"] == "in_progress"
            ]

            active_incidents = [
                item
                for item in self._incidents.values()
                if item["status"] != "resolved"
            ]

        if not statuses:
            overall = "unknown"

        elif "major_outage" in statuses:
            overall = "major_outage"

        elif "partial_outage" in statuses:
            overall = "partial_outage"

        elif "degraded" in statuses:
            overall = "degraded"

        elif (
            active_maintenance
            or "maintenance" in statuses
        ):
            overall = "maintenance"

        elif "unknown" in statuses:
            overall = "unknown"

        else:
            overall = "operational"

        return {
            "overall_status": overall,
            "total_components": len(statuses),
            "operational_components": statuses.count("operational"),
            "degraded_components": statuses.count("degraded"),
            "partial_outage_components": statuses.count("partial_outage"),
            "major_outage_components": statuses.count("major_outage"),
            "maintenance_components": statuses.count("maintenance"),
            "unknown_components": statuses.count("unknown"),
            "active_incidents": len(active_incidents),
            "active_maintenance": len(active_maintenance),
            "checked_at": self._now(),
        }

    # --------------------------------------------------
    # PUBLIC INCIDENT MANAGEMENT
    # --------------------------------------------------

    def publish_incident(
        self,
        title: str,
        message: str,
        status: str = "investigating",
        impact: str = "minor",
        affected_components: Optional[List[str]] = None,
        source_incident_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Publish an incident on the status page."""

        title = self._validate_text(
            title,
            "title",
            200,
        )

        message = self._validate_text(
            message,
            "message",
            3000,
        )

        if status not in self.INCIDENT_STATUSES:
            raise APIStatusPageError(
                "Invalid incident status."
            )

        if impact not in self.INCIDENT_IMPACTS:
            raise APIStatusPageError(
                "Invalid incident impact."
            )

        if affected_components is None:
            affected_components = []

        if not isinstance(affected_components, list):
            raise APIStatusPageError(
                "affected_components must be a list."
            )

        clean_components = []

        with self._lock:
            for component_id in affected_components:
                component_id = self._validate_text(
                    component_id,
                    "component_id",
                    100,
                )

                if component_id not in self._components:
                    raise APIStatusPageError(
                        f"Unknown component: {component_id}"
                    )

                clean_components.append(component_id)

            self._check_capacity(self._incidents)

            incident_id = uuid.uuid4().hex
            now = self._now()

            incident = {
                "incident_id": incident_id,
                "title": title,
                "message": message,
                "status": status,
                "impact": impact,
                "affected_components": list(
                    dict.fromkeys(clean_components)
                ),
                "source_incident_id": source_incident_id,
                "is_public": True,
                "created_at": now,
                "updated_at": now,
                "resolved_at": (
                    now if status == "resolved" else None
                ),
                "updates": [
                    {
                        "status": status,
                        "message": message,
                        "created_at": now,
                    }
                ],
            }

            self._incidents[incident_id] = incident

            return self._copy(incident)

    def update_incident(
        self,
        incident_id: str,
        message: str,
        status: str,
        impact: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Publish a new update for an existing incident."""

        message = self._validate_text(
            message,
            "message",
            3000,
        )

        if status not in self.INCIDENT_STATUSES:
            raise APIStatusPageError(
                "Invalid incident status."
            )

        if impact is not None and impact not in self.INCIDENT_IMPACTS:
            raise APIStatusPageError(
                "Invalid incident impact."
            )

        with self._lock:
            incident = self._incidents.get(incident_id)

            if incident is None:
                raise APIStatusPageError(
                    "Status page incident not found."
                )

            if incident["status"] == "resolved":
                raise APIStatusPageError(
                    "A resolved incident cannot be updated."
                )

            now = self._now()

            incident["message"] = message
            incident["status"] = status
            incident["updated_at"] = now

            if impact is not None:
                incident["impact"] = impact

            if status == "resolved":
                incident["resolved_at"] = now

            incident["updates"].append({
                "status": status,
                "message": message,
                "created_at": now,
            })

            return self._copy(incident)

    def set_incident_visibility(
        self,
        incident_id: str,
        is_public: bool,
    ) -> Dict[str, Any]:
        """Control whether an incident appears publicly."""

        if not isinstance(is_public, bool):
            raise APIStatusPageError(
                "is_public must be a boolean."
            )

        with self._lock:
            incident = self._incidents.get(incident_id)

            if incident is None:
                raise APIStatusPageError(
                    "Status page incident not found."
                )

            incident["is_public"] = is_public
            incident["updated_at"] = self._now()

            return self._copy(incident)

    def get_incidents(
        self,
        public_only: bool = False,
        status: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Retrieve status page incidents."""

        if (
            isinstance(limit, bool)
            or not isinstance(limit, int)
            or limit <= 0
        ):
            raise APIStatusPageError(
                "limit must be a positive integer."
            )

        if status is not None and status not in self.INCIDENT_STATUSES:
            raise APIStatusPageError(
                "Invalid incident status filter."
            )

        with self._lock:
            incidents = [
                self._copy(item)
                for item in self._incidents.values()
            ]

        if public_only:
            incidents = [
                item for item in incidents
                if item["is_public"]
            ]

        if status:
            incidents = [
                item for item in incidents
                if item["status"] == status
            ]

        incidents.sort(
            key=lambda item: item["updated_at"],
            reverse=True,
        )

        return incidents[:limit]

    # --------------------------------------------------
    # SCHEDULED MAINTENANCE
    # --------------------------------------------------

    def schedule_maintenance(
        self,
        title: str,
        description: str,
        scheduled_start: str,
        scheduled_end: str,
        affected_components: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Create a scheduled maintenance announcement."""

        title = self._validate_text(
            title,
            "title",
            200,
        )

        description = self._validate_text(
            description,
            "description",
            2000,
        )

        try:
            start = datetime.fromisoformat(
                scheduled_start.replace("Z", "+00:00")
            )

            end = datetime.fromisoformat(
                scheduled_end.replace("Z", "+00:00")
            )

        except (ValueError, AttributeError):
            raise APIStatusPageError(
                "Maintenance dates must be valid ISO 8601 timestamps."
            )

        if start.tzinfo is None or end.tzinfo is None:
            raise APIStatusPageError(
                "Maintenance timestamps must include a timezone."
            )

        if end <= start:
            raise APIStatusPageError(
                "Maintenance end must be after its start."
            )

        if affected_components is None:
            affected_components = []

        if not isinstance(affected_components, list):
            raise APIStatusPageError(
                "affected_components must be a list."
            )

        with self._lock:
            clean_components = []

            for component_id in affected_components:
                component_id = self._validate_text(
                    component_id,
                    "component_id",
                    100,
                )

                if component_id not in self._components:
                    raise APIStatusPageError(
                        f"Unknown component: {component_id}"
                    )

                clean_components.append(component_id)

            self._check_capacity(self._maintenance)

            maintenance_id = uuid.uuid4().hex
            now = self._now()

            maintenance = {
                "maintenance_id": maintenance_id,
                "title": title,
                "description": description,
                "scheduled_start": start.isoformat(),
                "scheduled_end": end.isoformat(),
                "affected_components": list(
                    dict.fromkeys(clean_components)
                ),
                "status": "scheduled",
                "created_at": now,
                "updated_at": now,
                "completed_at": None,
            }

            self._maintenance[maintenance_id] = maintenance

            return self._copy(maintenance)

    def update_maintenance_status(
        self,
        maintenance_id: str,
        status: str,
    ) -> Dict[str, Any]:
        """Update scheduled maintenance status."""

        if status not in self.MAINTENANCE_STATUSES:
            raise APIStatusPageError(
                "Invalid maintenance status."
            )

        with self._lock:
            maintenance = self._maintenance.get(
                maintenance_id
            )

            if maintenance is None:
                raise APIStatusPageError(
                    "Maintenance record not found."
                )

            if maintenance["status"] in {"completed", "cancelled"}:
                raise APIStatusPageError(
                    "Completed or cancelled maintenance cannot be changed."
                )

            now = self._now()

            maintenance["status"] = status
            maintenance["updated_at"] = now

            if status == "completed":
                maintenance["completed_at"] = now

            return self._copy(maintenance)

    def get_maintenance(
        self,
        status: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Retrieve scheduled maintenance records."""

        if (
            isinstance(limit, bool)
            or not isinstance(limit, int)
            or limit <= 0
        ):
            raise APIStatusPageError(
                "limit must be a positive integer."
            )

        if status is not None and status not in self.MAINTENANCE_STATUSES:
            raise APIStatusPageError(
                "Invalid maintenance status filter."
            )

        with self._lock:
            records = [
                self._copy(item)
                for item in self._maintenance.values()
            ]

        if status:
            records = [
                item for item in records
                if item["status"] == status
            ]

        records.sort(
            key=lambda item: item["scheduled_start"]
        )

        return records[:limit]

    # --------------------------------------------------
    # PUBLIC STATUS SUMMARY
    # --------------------------------------------------

    def get_public_status(self) -> Dict[str, Any]:
        """Return information intended for public display."""

        with self._lock:
            configuration = self._copy(
                self._configuration
            )

        if not configuration["is_public"]:
            raise APIStatusPageError(
                "The public status page is currently disabled."
            )

        return {
            "page": {
                "name": configuration["name"],
                "description": configuration["description"],
                "website_url": configuration["website_url"],
                "support_email": configuration["support_email"],
            },
            "overall": self.get_overall_status(),
            "components": self.get_components(),
            "active_incidents": self.get_incidents(
                public_only=True,
                limit=100,
            ),
            "scheduled_maintenance": self.get_maintenance(
                status="scheduled",
                limit=100,
            ),
            "generated_at": self._now(),
        }

    # --------------------------------------------------
    # EXPORT
    # --------------------------------------------------

    def export_status_page(self) -> str:
        """Export status page information as JSON."""

        with self._lock:
            data = {
                "configuration": self._copy(
                    self._configuration
                ),
                "components": self.get_components(),
                "incidents": self.get_incidents(
                    public_only=False,
                    limit=self.max_records,
                ),
                "maintenance": self.get_maintenance(
                    limit=self.max_records
                ),
                "overall": self.get_overall_status(),
                "exported_at": self._now(),
            }

        return json.dumps(
            data,
            indent=4,
            ensure_ascii=False,
            default=str,
        )


# ------------------------------------------------------
# SHARED SERVICE INSTANCE
# ------------------------------------------------------

api_status_page_service = APIStatusPageService()
