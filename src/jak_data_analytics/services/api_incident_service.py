"""
JAK Data Analytics
API Incident Management Service

Features:
- Incident creation
- Incident severity classification
- Incident assignment
- Incident status management
- Alert association
- Investigation notes
- Incident resolution
- Incident reopening
- Incident filtering
- Incident statistics
- Incident history
- JSON export

Storage:
In-memory storage.

Production note:
Use database persistence and notification workers.
"""

from __future__ import annotations

import json
import threading
import uuid

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


class APIIncidentError(Exception):
    """Raised when an incident operation fails."""


class APIIncidentService:
    """Manages API incidents and their lifecycle."""

    VALID_SEVERITIES = {
        "low",
        "medium",
        "high",
        "critical",
    }

    VALID_STATUSES = {
        "open",
        "investigating",
        "identified",
        "monitoring",
        "resolved",
        "closed",
    }

    VALID_PRIORITIES = {
        "low",
        "normal",
        "high",
        "urgent",
    }

    DEFAULT_MAX_INCIDENTS = 5000

    def __init__(self, max_incidents: int = DEFAULT_MAX_INCIDENTS):
        self.max_incidents = self._validate_positive_integer(
            max_incidents,
            "max_incidents",
        )

        self._incidents: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.RLock()

    # --------------------------------------------------
    # VALIDATION
    # --------------------------------------------------

    @staticmethod
    def _validate_positive_integer(value: Any, name: str) -> int:
        if isinstance(value, bool) or not isinstance(value, int):
            raise APIIncidentError(
                f"{name} must be an integer."
            )

        if value <= 0:
            raise APIIncidentError(
                f"{name} must be greater than zero."
            )

        return value

    @staticmethod
    def _validate_text(
        value: Any,
        name: str,
        max_length: int = 500,
    ) -> str:
        if not isinstance(value, str):
            raise APIIncidentError(
                f"{name} must be a string."
            )

        value = value.strip()

        if not value:
            raise APIIncidentError(
                f"{name} cannot be empty."
            )

        if len(value) > max_length:
            raise APIIncidentError(
                f"{name} cannot exceed {max_length} characters."
            )

        return value

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat()

    # --------------------------------------------------
    # CREATE INCIDENT
    # --------------------------------------------------

    def create_incident(
        self,
        title: str,
        description: str,
        severity: str = "medium",
        priority: str = "normal",
        source: str = "jak-data-analytics",
        affected_service: Optional[str] = None,
        affected_endpoint: Optional[str] = None,
        created_by: str = "system",
        alert_ids: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Create a new incident."""

        title = self._validate_text(
            title,
            "title",
            200,
        )

        description = self._validate_text(
            description,
            "description",
            3000,
        )

        source = self._validate_text(
            source,
            "source",
            200,
        )

        created_by = self._validate_text(
            created_by,
            "created_by",
            200,
        )

        if severity not in self.VALID_SEVERITIES:
            raise APIIncidentError(
                "Invalid incident severity."
            )

        if priority not in self.VALID_PRIORITIES:
            raise APIIncidentError(
                "Invalid incident priority."
            )

        if affected_service is not None:
            affected_service = self._validate_text(
                affected_service,
                "affected_service",
                200,
            )

        if affected_endpoint is not None:
            affected_endpoint = self._validate_text(
                affected_endpoint,
                "affected_endpoint",
                500,
            )

        if alert_ids is None:
            alert_ids = []

        if not isinstance(alert_ids, list):
            raise APIIncidentError(
                "alert_ids must be a list."
            )

        clean_alert_ids = []

        for alert_id in alert_ids:
            clean_alert_ids.append(
                self._validate_text(
                    alert_id,
                    "alert_id",
                    100,
                )
            )

        if metadata is None:
            metadata = {}

        if not isinstance(metadata, dict):
            raise APIIncidentError(
                "metadata must be a dictionary."
            )

        clean_metadata = self._clean_metadata(metadata)

        with self._lock:
            if len(self._incidents) >= self.max_incidents:
                self._remove_oldest_closed_incidents()

            if len(self._incidents) >= self.max_incidents:
                raise APIIncidentError(
                    "Incident storage capacity reached."
                )

            incident_id = uuid.uuid4().hex
            incident_number = (
                f"JAK-INC-{uuid.uuid4().hex[:8].upper()}"
            )

            now = self._now()

            incident = {
                "incident_id": incident_id,
                "incident_number": incident_number,
                "title": title,
                "description": description,
                "severity": severity,
                "priority": priority,
                "status": "open",
                "source": source,
                "affected_service": affected_service,
                "affected_endpoint": affected_endpoint,
                "created_by": created_by,
                "assigned_to": None,
                "alert_ids": list(dict.fromkeys(clean_alert_ids)),
                "notes": [],
                "created_at": now,
                "updated_at": now,
                "acknowledged_at": None,
                "resolved_at": None,
                "closed_at": None,
                "resolution_summary": None,
                "metadata": clean_metadata,
            }

            self._incidents[incident_id] = incident

            return incident.copy()

    @staticmethod
    def _clean_metadata(
        metadata: Dict[str, Any],
    ) -> Dict[str, Any]:
        sensitive = {
            "password",
            "secret",
            "token",
            "access_token",
            "refresh_token",
            "api_key",
            "authorization",
            "cookie",
            "private_key",
        }

        cleaned = {}

        for key, value in metadata.items():
            safe_key = str(key).strip()

            if not safe_key:
                continue

            if safe_key.lower() in sensitive:
                cleaned[safe_key] = "[REDACTED]"
            elif isinstance(value, (str, int, float, bool)) or value is None:
                cleaned[safe_key] = value
            else:
                cleaned[safe_key] = str(value)[:500]

        return cleaned

    # --------------------------------------------------
    # RETRIEVE INCIDENTS
    # --------------------------------------------------

    def get_incident(
        self,
        incident_id: str,
    ) -> Optional[Dict[str, Any]]:
        """Retrieve one incident."""

        with self._lock:
            incident = self._incidents.get(incident_id)

            return incident.copy() if incident else None

    def get_incidents(
        self,
        status: Optional[str] = None,
        severity: Optional[str] = None,
        priority: Optional[str] = None,
        assigned_to: Optional[str] = None,
        source: Optional[str] = None,
        search: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Retrieve incidents using optional filters."""

        limit = self._validate_positive_integer(
            limit,
            "limit",
        )

        if status is not None and status not in self.VALID_STATUSES:
            raise APIIncidentError(
                "Invalid incident status filter."
            )

        if severity is not None and severity not in self.VALID_SEVERITIES:
            raise APIIncidentError(
                "Invalid severity filter."
            )

        if priority is not None and priority not in self.VALID_PRIORITIES:
            raise APIIncidentError(
                "Invalid priority filter."
            )

        with self._lock:
            incidents = [
                incident.copy()
                for incident in self._incidents.values()
            ]

        if status:
            incidents = [
                item for item in incidents
                if item["status"] == status
            ]

        if severity:
            incidents = [
                item for item in incidents
                if item["severity"] == severity
            ]

        if priority:
            incidents = [
                item for item in incidents
                if item["priority"] == priority
            ]

        if assigned_to:
            incidents = [
                item for item in incidents
                if item["assigned_to"] == assigned_to
            ]

        if source:
            incidents = [
                item for item in incidents
                if item["source"] == source
            ]

        if search:
            term = search.lower()

            incidents = [
                item for item in incidents
                if term in item["title"].lower()
                or term in item["description"].lower()
                or term in item["incident_number"].lower()
            ]

        incidents.sort(
            key=lambda item: item["updated_at"],
            reverse=True,
        )

        return incidents[:limit]

    # --------------------------------------------------
    # ASSIGN INCIDENT
    # --------------------------------------------------

    def assign_incident(
        self,
        incident_id: str,
        assigned_to: str,
    ) -> Dict[str, Any]:
        """Assign an incident to a team member."""

        assigned_to = self._validate_text(
            assigned_to,
            "assigned_to",
            200,
        )

        with self._lock:
            incident = self._get_mutable_incident(
                incident_id
            )

            if incident["status"] in {"resolved", "closed"}:
                raise APIIncidentError(
                    "Cannot assign a completed incident."
                )

            incident["assigned_to"] = assigned_to
            incident["updated_at"] = self._now()

            return incident.copy()

    # --------------------------------------------------
    # UPDATE INCIDENT STATUS
    # --------------------------------------------------

    def update_status(
        self,
        incident_id: str,
        status: str,
        updated_by: str,
    ) -> Dict[str, Any]:
        """Update the lifecycle status of an incident."""

        updated_by = self._validate_text(
            updated_by,
            "updated_by",
            200,
        )

        if status not in self.VALID_STATUSES:
            raise APIIncidentError(
                "Invalid incident status."
            )

        with self._lock:
            incident = self._get_mutable_incident(
                incident_id
            )

            current = incident["status"]

            if current in {"resolved", "closed"}:
                if status not in {"open", "investigating"}:
                    raise APIIncidentError(
                        "Reopen the incident before changing its status."
                    )

                incident["resolved_at"] = None
                incident["closed_at"] = None
                incident["resolution_summary"] = None

            if status == "closed" and current != "resolved":
                raise APIIncidentError(
                    "An incident must be resolved before it can be closed."
                )

            if status == "resolved":
                incident["resolved_at"] = self._now()

            if status == "closed":
                incident["closed_at"] = self._now()

            if status in {"investigating", "identified", "monitoring"}:
                if incident["acknowledged_at"] is None:
                    incident["acknowledged_at"] = self._now()

            incident["status"] = status
            incident["updated_at"] = self._now()

            self._append_note(
                incident,
                f"Status changed to {status} by {updated_by}.",
                updated_by,
                "status_change",
            )

            return incident.copy()

    # --------------------------------------------------
    # RESOLVE INCIDENT
    # --------------------------------------------------

    def resolve_incident(
        self,
        incident_id: str,
        resolved_by: str,
        resolution_summary: str,
    ) -> Dict[str, Any]:
        """Resolve an incident with a resolution summary."""

        resolved_by = self._validate_text(
            resolved_by,
            "resolved_by",
            200,
        )

        resolution_summary = self._validate_text(
            resolution_summary,
            "resolution_summary",
            3000,
        )

        with self._lock:
            incident = self._get_mutable_incident(
                incident_id
            )

            if incident["status"] in {"resolved", "closed"}:
                raise APIIncidentError(
                    "Incident is already resolved or closed."
                )

            incident["status"] = "resolved"
            incident["resolved_at"] = self._now()
            incident["resolution_summary"] = resolution_summary
            incident["updated_at"] = self._now()

            self._append_note(
                incident,
                resolution_summary,
                resolved_by,
                "resolution",
            )

            return incident.copy()

    # --------------------------------------------------
    # REOPEN INCIDENT
    # --------------------------------------------------

    def reopen_incident(
        self,
        incident_id: str,
        reopened_by: str,
        reason: str,
    ) -> Dict[str, Any]:
        """Reopen a resolved or closed incident."""

        reopened_by = self._validate_text(
            reopened_by,
            "reopened_by",
            200,
        )

        reason = self._validate_text(
            reason,
            "reason",
            2000,
        )

        with self._lock:
            incident = self._get_mutable_incident(
                incident_id
            )

            if incident["status"] not in {"resolved", "closed"}:
                raise APIIncidentError(
                    "Only resolved or closed incidents can be reopened."
                )

            incident["status"] = "investigating"
            incident["resolved_at"] = None
            incident["closed_at"] = None
            incident["resolution_summary"] = None
            incident["updated_at"] = self._now()

            self._append_note(
                incident,
                reason,
                reopened_by,
                "reopened",
            )

            return incident.copy()

    # --------------------------------------------------
    # ADD INVESTIGATION NOTE
    # --------------------------------------------------

    def add_note(
        self,
        incident_id: str,
        note: str,
        created_by: str,
        note_type: str = "investigation",
    ) -> Dict[str, Any]:
        """Add an investigation note to an incident."""

        note = self._validate_text(
            note,
            "note",
            3000,
        )

        created_by = self._validate_text(
            created_by,
            "created_by",
            200,
        )

        note_type = self._validate_text(
            note_type,
            "note_type",
            50,
        )

        with self._lock:
            incident = self._get_mutable_incident(
                incident_id
            )

            self._append_note(
                incident,
                note,
                created_by,
                note_type,
            )

            incident["updated_at"] = self._now()

            return incident.copy()

    @staticmethod
    def _append_note(
        incident: Dict[str, Any],
        note: str,
        created_by: str,
        note_type: str,
    ) -> None:
        incident["notes"].append({
            "note_id": uuid.uuid4().hex,
            "note": note,
            "created_by": created_by,
            "note_type": note_type,
            "created_at": datetime.now(
                timezone.utc
            ).isoformat(),
        })

    # --------------------------------------------------
    # LINK ALERT
    # --------------------------------------------------

    def link_alert(
        self,
        incident_id: str,
        alert_id: str,
    ) -> Dict[str, Any]:
        """Associate an alert ID with an incident."""

        alert_id = self._validate_text(
            alert_id,
            "alert_id",
            100,
        )

        with self._lock:
            incident = self._get_mutable_incident(
                incident_id
            )

            if incident["status"] in {"resolved", "closed"}:
                raise APIIncidentError(
                    "Cannot add alerts to a completed incident."
                )

            if alert_id not in incident["alert_ids"]:
                incident["alert_ids"].append(alert_id)

            incident["updated_at"] = self._now()

            return incident.copy()

    # --------------------------------------------------
    # UPDATE PRIORITY AND SEVERITY
    # --------------------------------------------------

    def update_classification(
        self,
        incident_id: str,
        severity: Optional[str] = None,
        priority: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Update incident severity and priority."""

        if severity is not None and severity not in self.VALID_SEVERITIES:
            raise APIIncidentError(
                "Invalid severity."
            )

        if priority is not None and priority not in self.VALID_PRIORITIES:
            raise APIIncidentError(
                "Invalid priority."
            )

        if severity is None and priority is None:
            raise APIIncidentError(
                "Provide a severity or priority to update."
            )

        with self._lock:
            incident = self._get_mutable_incident(
                incident_id
            )

            if incident["status"] in {"resolved", "closed"}:
                raise APIIncidentError(
                    "Cannot modify the classification of a completed incident."
                )

            if severity is not None:
                incident["severity"] = severity

            if priority is not None:
                incident["priority"] = priority

            incident["updated_at"] = self._now()

            return incident.copy()

    # --------------------------------------------------
    # INTERNAL HELPERS
    # --------------------------------------------------

    def _get_mutable_incident(
        self,
        incident_id: str,
    ) -> Dict[str, Any]:
        incident = self._incidents.get(incident_id)

        if incident is None:
            raise APIIncidentError(
                "Incident not found."
            )

        return incident

    def _remove_oldest_closed_incidents(self) -> None:
        """Remove old closed incidents when storage is full."""

        closed = sorted(
            [
                incident
                for incident in self._incidents.values()
                if incident["status"] == "closed"
            ],
            key=lambda item: item["updated_at"],
        )

        excess = len(self._incidents) - self.max_incidents + 1

        for incident in closed[:excess]:
            self._incidents.pop(
                incident["incident_id"],
                None,
            )

    # --------------------------------------------------
    # STATISTICS
    # --------------------------------------------------

    def get_statistics(self) -> Dict[str, Any]:
        """Return incident statistics."""

        with self._lock:
            incidents = list(self._incidents.values())

        return {
            "total_incidents": len(incidents),
            "open_incidents": sum(
                item["status"] == "open"
                for item in incidents
            ),
            "investigating_incidents": sum(
                item["status"] == "investigating"
                for item in incidents
            ),
            "identified_incidents": sum(
                item["status"] == "identified"
                for item in incidents
            ),
            "monitoring_incidents": sum(
                item["status"] == "monitoring"
                for item in incidents
            ),
            "resolved_incidents": sum(
                item["status"] == "resolved"
                for item in incidents
            ),
            "closed_incidents": sum(
                item["status"] == "closed"
                for item in incidents
            ),
            "critical_incidents": sum(
                item["severity"] == "critical"
                and item["status"] not in {"resolved", "closed"}
                for item in incidents
            ),
        }

    # --------------------------------------------------
    # EXPORT
    # --------------------------------------------------

    def export_incident(
        self,
        incident_id: str,
    ) -> str:
        """Export one incident as JSON."""

        incident = self.get_incident(incident_id)

        if incident is None:
            raise APIIncidentError(
                "Incident not found."
            )

        return json.dumps(
            incident,
            indent=4,
            ensure_ascii=False,
            default=str,
        )

    def export_incidents(
        self,
        status: Optional[str] = None,
        limit: int = 1000,
    ) -> str:
        """Export filtered incidents as JSON."""

        incidents = self.get_incidents(
            status=status,
            limit=limit,
        )

        return json.dumps(
            incidents,
            indent=4,
            ensure_ascii=False,
            default=str,
        )


# ------------------------------------------------------
# SHARED SERVICE INSTANCE
# ------------------------------------------------------

api_incident_service = APIIncidentService()
