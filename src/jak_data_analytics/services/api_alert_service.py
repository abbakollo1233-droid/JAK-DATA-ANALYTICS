"""
JAK Data Analytics
API Alert Service

Manages API monitoring alerts.

Features:
- Alert creation
- Alert severity levels
- Alert categories
- Alert acknowledgement
- Alert resolution
- Alert assignment
- Duplicate alert detection
- Alert filtering and searching
- Alert statistics
- Alert history
- JSON export

Storage:
In-memory storage.

Production note:
Use persistent database storage and a notification worker
for production alert delivery.
"""

from __future__ import annotations

import json
import threading
import uuid

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional


class APIAlertError(Exception):
    """Raised when an API alert operation fails."""


class APIAlertService:
    """Creates and manages API monitoring alerts."""

    VALID_SEVERITIES = {
        "info",
        "low",
        "medium",
        "high",
        "critical",
    }

    VALID_CATEGORIES = {
        "performance",
        "availability",
        "errors",
        "security",
        "usage",
        "quota",
        "system",
        "integration",
        "other",
    }

    VALID_STATUSES = {
        "open",
        "acknowledged",
        "resolved",
        "dismissed",
    }

    DEFAULT_MAX_ALERTS = 10000

    def __init__(
        self,
        max_alerts: int = DEFAULT_MAX_ALERTS,
    ):
        self.max_alerts = self._validate_positive_integer(
            max_alerts,
            "max_alerts",
        )

        self._alerts: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.RLock()

    # --------------------------------------------------
    # VALIDATION
    # --------------------------------------------------

    @staticmethod
    def _validate_positive_integer(
        value: Any,
        name: str,
    ) -> int:
        if isinstance(value, bool) or not isinstance(value, int):
            raise APIAlertError(
                f"{name} must be an integer."
            )

        if value <= 0:
            raise APIAlertError(
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
            raise APIAlertError(
                f"{name} must be a string."
            )

        value = value.strip()

        if not value:
            raise APIAlertError(
                f"{name} cannot be empty."
            )

        if len(value) > max_length:
            raise APIAlertError(
                f"{name} cannot exceed {max_length} characters."
            )

        return value

    @staticmethod
    def _now() -> datetime:
        return datetime.now(timezone.utc)

    @staticmethod
    def _timestamp(
        value: Optional[datetime] = None,
    ) -> str:
        value = value or datetime.now(timezone.utc)

        if value.tzinfo is None:
            value = value.replace(
                tzinfo=timezone.utc
            )

        return value.isoformat()

    @staticmethod
    def _clean_metadata(
        metadata: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        if metadata is None:
            return {}

        if not isinstance(metadata, dict):
            raise APIAlertError(
                "metadata must be a dictionary."
            )

        sensitive_keys = {
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

            if safe_key.lower() in sensitive_keys:
                cleaned[safe_key] = "[REDACTED]"
            elif isinstance(value, (str, int, float, bool)) or value is None:
                cleaned[safe_key] = value
            else:
                cleaned[safe_key] = str(value)[:500]

        return cleaned

    # --------------------------------------------------
    # CREATE ALERT
    # --------------------------------------------------

    def create_alert(
        self,
        title: str,
        message: str,
        severity: str = "medium",
        category: str = "system",
        source: str = "jak-data-analytics",
        endpoint: Optional[str] = None,
        alert_key: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        allow_duplicate: bool = False,
    ) -> Dict[str, Any]:
        """Create a new API monitoring alert."""

        title = self._validate_text(
            title,
            "title",
            200,
        )

        message = self._validate_text(
            message,
            "message",
            2000,
        )

        source = self._validate_text(
            source,
            "source",
            200,
        )

        if severity not in self.VALID_SEVERITIES:
            raise APIAlertError(
                "Invalid alert severity."
            )

        if category not in self.VALID_CATEGORIES:
            raise APIAlertError(
                "Invalid alert category."
            )

        if endpoint is not None:
            endpoint = self._validate_text(
                endpoint,
                "endpoint",
                500,
            )

        if alert_key is not None:
            alert_key = self._validate_text(
                alert_key,
                "alert_key",
                200,
            )

        safe_metadata = self._clean_metadata(
            metadata
        )

        with self._lock:
            if not allow_duplicate:
                existing = self._find_duplicate(
                    title=title,
                    source=source,
                    alert_key=alert_key,
                )

                if existing:
                    existing["occurrence_count"] += 1
                    existing["last_seen_at"] = self._timestamp()
                    existing["message"] = message

                    existing["metadata"].update(
                        safe_metadata
                    )

                    return existing.copy()

            alert_id = uuid.uuid4().hex
            now = self._timestamp()

            alert = {
                "alert_id": alert_id,
                "alert_key": alert_key,
                "title": title,
                "message": message,
                "severity": severity,
                "category": category,
                "source": source,
                "endpoint": endpoint,
                "status": "open",
                "created_at": now,
                "last_seen_at": now,
                "acknowledged_at": None,
                "acknowledged_by": None,
                "resolved_at": None,
                "resolved_by": None,
                "assigned_to": None,
                "occurrence_count": 1,
                "resolution_note": None,
                "metadata": safe_metadata,
            }

            self._alerts[alert_id] = alert

            self._enforce_capacity()

            return alert.copy()

    def _find_duplicate(
        self,
        title: str,
        source: str,
        alert_key: Optional[str],
    ) -> Optional[Dict[str, Any]]:
        """Find an existing unresolved matching alert."""

        for alert in self._alerts.values():
            if alert["status"] in {"resolved", "dismissed"}:
                continue

            same_source = alert["source"] == source

            if alert_key:
                same_alert = alert["alert_key"] == alert_key
            else:
                same_alert = alert["title"] == title

            if same_source and same_alert:
                return alert

        return None

    # --------------------------------------------------
    # RETRIEVE ALERTS
    # --------------------------------------------------

    def get_alert(
        self,
        alert_id: str,
    ) -> Optional[Dict[str, Any]]:
        """Retrieve one alert."""

        with self._lock:
            alert = self._alerts.get(alert_id)

            return alert.copy() if alert else None

    def get_alerts(
        self,
        status: Optional[str] = None,
        severity: Optional[str] = None,
        category: Optional[str] = None,
        source: Optional[str] = None,
        endpoint: Optional[str] = None,
        search: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Retrieve alerts using optional filters."""

        limit = self._validate_positive_integer(
            limit,
            "limit",
        )

        if status is not None and status not in self.VALID_STATUSES:
            raise APIAlertError(
                "Invalid alert status filter."
            )

        if severity is not None and severity not in self.VALID_SEVERITIES:
            raise APIAlertError(
                "Invalid severity filter."
            )

        if category is not None and category not in self.VALID_CATEGORIES:
            raise APIAlertError(
                "Invalid category filter."
            )

        with self._lock:
            records = list(self._alerts.values())

        if status:
            records = [
                item for item in records
                if item["status"] == status
            ]

        if severity:
            records = [
                item for item in records
                if item["severity"] == severity
            ]

        if category:
            records = [
                item for item in records
                if item["category"] == category
            ]

        if source:
            records = [
                item for item in records
                if item["source"] == source
            ]

        if endpoint:
            records = [
                item for item in records
                if item["endpoint"] == endpoint
            ]

        if search:
            term = search.lower()

            records = [
                item for item in records
                if term in item["title"].lower()
                or term in item["message"].lower()
                or term in item["source"].lower()
            ]

        records.sort(
            key=lambda item: item["last_seen_at"],
            reverse=True,
        )

        return [
            item.copy()
            for item in records[:limit]
        ]

    # --------------------------------------------------
    # ACKNOWLEDGE ALERT
    # --------------------------------------------------

    def acknowledge_alert(
        self,
        alert_id: str,
        acknowledged_by: str,
    ) -> Dict[str, Any]:
        """Mark an open alert as acknowledged."""

        acknowledged_by = self._validate_text(
            acknowledged_by,
            "acknowledged_by",
            200,
        )

        with self._lock:
            alert = self._alerts.get(alert_id)

            if alert is None:
                raise APIAlertError(
                    "Alert not found."
                )

            if alert["status"] != "open":
                raise APIAlertError(
                    "Only open alerts can be acknowledged."
                )

            alert["status"] = "acknowledged"
            alert["acknowledged_at"] = self._timestamp()
            alert["acknowledged_by"] = acknowledged_by

            return alert.copy()

    # --------------------------------------------------
    # ASSIGN ALERT
    # --------------------------------------------------

    def assign_alert(
        self,
        alert_id: str,
        assigned_to: str,
    ) -> Dict[str, Any]:
        """Assign an alert to an administrator or operator."""

        assigned_to = self._validate_text(
            assigned_to,
            "assigned_to",
            200,
        )

        with self._lock:
            alert = self._alerts.get(alert_id)

            if alert is None:
                raise APIAlertError(
                    "Alert not found."
                )

            if alert["status"] in {"resolved", "dismissed"}:
                raise APIAlertError(
                    "Cannot assign a closed alert."
                )

            alert["assigned_to"] = assigned_to

            return alert.copy()

    # --------------------------------------------------
    # RESOLVE ALERT
    # --------------------------------------------------

    def resolve_alert(
        self,
        alert_id: str,
        resolved_by: str,
        resolution_note: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Mark an alert as resolved."""

        resolved_by = self._validate_text(
            resolved_by,
            "resolved_by",
            200,
        )

        if resolution_note is not None:
            resolution_note = self._validate_text(
                resolution_note,
                "resolution_note",
                2000,
            )

        with self._lock:
            alert = self._alerts.get(alert_id)

            if alert is None:
                raise APIAlertError(
                    "Alert not found."
                )

            if alert["status"] in {"resolved", "dismissed"}:
                raise APIAlertError(
                    "This alert is already closed."
                )

            alert["status"] = "resolved"
            alert["resolved_at"] = self._timestamp()
            alert["resolved_by"] = resolved_by
            alert["resolution_note"] = resolution_note

            return alert.copy()

    # --------------------------------------------------
    # DISMISS ALERT
    # --------------------------------------------------

    def dismiss_alert(
        self,
        alert_id: str,
        dismissed_by: str,
    ) -> Dict[str, Any]:
        """Dismiss an alert without marking it resolved."""

        dismissed_by = self._validate_text(
            dismissed_by,
            "dismissed_by",
            200,
        )

        with self._lock:
            alert = self._alerts.get(alert_id)

            if alert is None:
                raise APIAlertError(
                    "Alert not found."
                )

            if alert["status"] in {"resolved", "dismissed"}:
                raise APIAlertError(
                    "This alert is already closed."
                )

            alert["status"] = "dismissed"
            alert["resolved_at"] = self._timestamp()
            alert["resolved_by"] = dismissed_by

            return alert.copy()

    # --------------------------------------------------
    # REOPEN ALERT
    # --------------------------------------------------

    def reopen_alert(
        self,
        alert_id: str,
    ) -> Dict[str, Any]:
        """Reopen a previously resolved or dismissed alert."""

        with self._lock:
            alert = self._alerts.get(alert_id)

            if alert is None:
                raise APIAlertError(
                    "Alert not found."
                )

            if alert["status"] not in {"resolved", "dismissed"}:
                raise APIAlertError(
                    "Only closed alerts can be reopened."
                )

            alert["status"] = "open"
            alert["resolved_at"] = None
            alert["resolved_by"] = None
            alert["resolution_note"] = None

            return alert.copy()

    # --------------------------------------------------
    # STATISTICS
    # --------------------------------------------------

    def get_statistics(self) -> Dict[str, Any]:
        """Return alert statistics."""

        with self._lock:
            alerts = list(self._alerts.values())

        total = len(alerts)

        return {
            "total_alerts": total,
            "open_alerts": sum(
                item["status"] == "open"
                for item in alerts
            ),
            "acknowledged_alerts": sum(
                item["status"] == "acknowledged"
                for item in alerts
            ),
            "resolved_alerts": sum(
                item["status"] == "resolved"
                for item in alerts
            ),
            "dismissed_alerts": sum(
                item["status"] == "dismissed"
                for item in alerts
            ),
            "critical_alerts": sum(
                item["severity"] == "critical"
                and item["status"] in {"open", "acknowledged"}
                for item in alerts
            ),
            "high_alerts": sum(
                item["severity"] == "high"
                and item["status"] in {"open", "acknowledged"}
                for item in alerts
            ),
            "total_occurrences": sum(
                item["occurrence_count"]
                for item in alerts
            ),
        }

    def get_severity_distribution(self) -> Dict[str, int]:
        """Count alerts by severity."""

        with self._lock:
            alerts = list(self._alerts.values())

        return {
            severity: sum(
                item["severity"] == severity
                for item in alerts
            )
            for severity in self.VALID_SEVERITIES
        }

    def get_category_distribution(self) -> Dict[str, int]:
        """Count alerts by category."""

        with self._lock:
            alerts = list(self._alerts.values())

        return {
            category: sum(
                item["category"] == category
                for item in alerts
            )
            for category in self.VALID_CATEGORIES
        }

    # --------------------------------------------------
    # ALERT HISTORY
    # --------------------------------------------------

    def get_recent_alerts(
        self,
        hours: int = 24,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Retrieve alerts first created within a recent time window."""

        hours = self._validate_positive_integer(
            hours,
            "hours",
        )

        limit = self._validate_positive_integer(
            limit,
            "limit",
        )

        cutoff = datetime.now(timezone.utc) - timedelta(
            hours=hours
        )

        with self._lock:
            alerts = list(self._alerts.values())

        recent = [
            item for item in alerts
            if datetime.fromisoformat(
                item["created_at"]
            ) >= cutoff
        ]

        recent.sort(
            key=lambda item: item["created_at"],
            reverse=True,
        )

        return [
            item.copy()
            for item in recent[:limit]
        ]

    # --------------------------------------------------
    # EXPORT
    # --------------------------------------------------

    def export_alerts(
        self,
        status: Optional[str] = None,
        limit: int = 5000,
    ) -> str:
        """Export filtered alerts as JSON."""

        alerts = self.get_alerts(
            status=status,
            limit=limit,
        )

        return json.dumps(
            alerts,
            indent=4,
            ensure_ascii=False,
            default=str,
        )

    # --------------------------------------------------
    # CLEANUP
    # --------------------------------------------------

    def clean_old_alerts(
        self,
        days: int = 90,
        include_resolved: bool = True,
    ) -> int:
        """Delete old alerts according to their last-seen date."""

        days = self._validate_positive_integer(
            days,
            "days",
        )

        cutoff = self._now() - timedelta(
            days=days
        )

        deleted = 0

        with self._lock:
            for alert_id, alert in list(self._alerts.items()):
                if alert["status"] in {"open", "acknowledged"}:
                    continue

                if (
                    not include_resolved
                    and alert["status"] == "resolved"
                ):
                    continue

                last_seen = datetime.fromisoformat(
                    alert["last_seen_at"]
                )

                if last_seen < cutoff:
                    del self._alerts[alert_id]
                    deleted += 1

        return deleted

    def _enforce_capacity(self) -> None:
        """Remove oldest closed alerts when storage reaches capacity."""

        if len(self._alerts) <= self.max_alerts:
            return

        closed = sorted(
            [
                alert for alert in self._alerts.values()
                if alert["status"] in {"resolved", "dismissed"}
            ],
            key=lambda item: item["last_seen_at"],
        )

        excess = len(self._alerts) - self.max_alerts

        for alert in closed[:excess]:
            self._alerts.pop(
                alert["alert_id"],
                None,
            )

        if len(self._alerts) > self.max_alerts:
            raise APIAlertError(
                "Alert capacity reached. Open alerts cannot be automatically removed."
            )


# ------------------------------------------------------
# SHARED SERVICE INSTANCE
# ------------------------------------------------------

api_alert_service = APIAlertService()
