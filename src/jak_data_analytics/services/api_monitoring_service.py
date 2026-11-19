"""
JAK Data Analytics
API Monitoring Service

Coordinates API performance monitoring and alert evaluation.

Features:
- API request monitoring
- Performance measurements
- Error-rate monitoring
- Slow-request monitoring
- Availability monitoring
- Automatic alert-rule evaluation
- Monitoring summaries
- Endpoint performance reports
- Recent activity reports
- JSON exports

Dependencies:
- api_performance_service.py
- api_alert_service.py
- api_alert_rules_service.py

Storage:
Uses the storage mechanisms of the connected services.
"""

from __future__ import annotations

import json
import math
import threading

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from .api_performance_service import (
    APIPerformanceService,
    api_performance_service,
)

from .api_alert_service import (
    APIAlertService,
    api_alert_service,
)

from .api_alert_rules_service import (
    APIAlertRulesService,
    api_alert_rules_service,
)


class APIMonitoringError(Exception):
    """Raised when an API monitoring operation fails."""


class APIMonitoringService:
    """Coordinates API monitoring and alert evaluation."""

    def __init__(
        self,
        performance_service: Optional[APIPerformanceService] = None,
        alert_service: Optional[APIAlertService] = None,
        alert_rules_service: Optional[APIAlertRulesService] = None,
    ):
        self.performance_service = (
            performance_service or api_performance_service
        )

        self.alert_service = (
            alert_service or api_alert_service
        )

        self.alert_rules_service = (
            alert_rules_service or api_alert_rules_service
        )

        self._service_status: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.RLock()

    # --------------------------------------------------
    # VALIDATION
    # --------------------------------------------------

    @staticmethod
    def _validate_text(
        value: Any,
        name: str,
        max_length: int = 300,
    ) -> str:
        if not isinstance(value, str):
            raise APIMonitoringError(
                f"{name} must be a string."
            )

        value = value.strip()

        if not value:
            raise APIMonitoringError(
                f"{name} cannot be empty."
            )

        if len(value) > max_length:
            raise APIMonitoringError(
                f"{name} cannot exceed {max_length} characters."
            )

        return value

    @staticmethod
    def _validate_number(
        value: Any,
        name: str,
    ) -> float:
        if isinstance(value, bool):
            raise APIMonitoringError(
                f"{name} must be a number."
            )

        try:
            number = float(value)
        except (TypeError, ValueError):
            raise APIMonitoringError(
                f"{name} must be a number."
            )

        if not math.isfinite(number) or number < 0:
            raise APIMonitoringError(
                f"{name} must be a finite non-negative number."
            )

        return number

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat()

    # --------------------------------------------------
    # RECORD API REQUEST
    # --------------------------------------------------

    def record_api_request(
        self,
        endpoint: str,
        method: str,
        response_time_ms: float,
        status_code: int,
        request_id: Optional[str] = None,
        service_name: str = "jak-data-analytics",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Record a request and evaluate monitoring rules.

        This method records the request first, then evaluates
        the current performance summary.
        """

        endpoint = self._validate_text(
            endpoint,
            "endpoint",
        )

        service_name = self._validate_text(
            service_name,
            "service_name",
        )

        response_time_ms = self._validate_number(
            response_time_ms,
            "response_time_ms",
        )

        try:
            record = self.performance_service.record_request(
                endpoint=endpoint,
                method=method,
                response_time_ms=response_time_ms,
                status_code=status_code,
                request_id=request_id,
                service_name=service_name,
                metadata=metadata,
            )

            summary = self.get_performance_summary()

            alert_results = self.alert_rules_service.evaluate_metrics(
                summary["metrics"]
            )

            return {
                "recorded": True,
                "request": record,
                "monitoring": summary,
                "alert_evaluations": alert_results,
            }

        except Exception as exc:
            if isinstance(exc, APIMonitoringError):
                raise

            raise APIMonitoringError(
                f"Unable to record API monitoring data: {exc}"
            ) from exc

    # --------------------------------------------------
    # RECORD SERVICE HEALTH
    # --------------------------------------------------

    def record_service_health(
        self,
        service_name: str,
        status: str,
        response_time_ms: Optional[float] = None,
        message: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Record the latest observed service health.

        Supported statuses:
        healthy, degraded, unhealthy, unknown
        """

        service_name = self._validate_text(
            service_name,
            "service_name",
        )

        allowed_statuses = {
            "healthy",
            "degraded",
            "unhealthy",
            "unknown",
        }

        if status not in allowed_statuses:
            raise APIMonitoringError(
                "Invalid service health status."
            )

        if response_time_ms is not None:
            response_time_ms = self._validate_number(
                response_time_ms,
                "response_time_ms",
            )

        if message is not None:
            if not isinstance(message, str):
                raise APIMonitoringError(
                    "message must be a string."
                )

            message = message[:1000]

        if metadata is not None and not isinstance(metadata, dict):
            raise APIMonitoringError(
                "metadata must be a dictionary."
            )

        safe_metadata = self._clean_metadata(metadata)

        record = {
            "service_name": service_name,
            "status": status,
            "response_time_ms": response_time_ms,
            "message": message,
            "checked_at": self._now(),
            "metadata": safe_metadata,
        }

        with self._lock:
            previous = self._service_status.get(service_name)

            self._service_status[service_name] = record

        if status == "unhealthy":
            self.alert_service.create_alert(
                title=f"Service Unhealthy: {service_name}",
                message=message or (
                    f"The monitored service {service_name} is unhealthy."
                ),
                severity="critical",
                category="availability",
                source="jak-service-monitor",
                alert_key=f"service-health:{service_name}",
                metadata=safe_metadata,
            )

        elif status == "degraded":
            self.alert_service.create_alert(
                title=f"Service Degraded: {service_name}",
                message=message or (
                    f"The monitored service {service_name} is degraded."
                ),
                severity="high",
                category="availability",
                source="jak-service-monitor",
                alert_key=f"service-health:{service_name}",
                metadata=safe_metadata,
            )

        elif previous and previous["status"] in {
            "unhealthy",
            "degraded",
        }:
            self.alert_service.create_alert(
                title=f"Service Recovered: {service_name}",
                message=(
                    f"The service {service_name} is now reporting "
                    f"{status} status."
                ),
                severity="info",
                category="availability",
                source="jak-service-monitor",
                alert_key=f"service-recovery:{service_name}",
                metadata=safe_metadata,
            )

        return record.copy()

    @staticmethod
    def _clean_metadata(
        metadata: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        if metadata is None:
            return {}

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
    # SERVICE HEALTH RETRIEVAL
    # --------------------------------------------------

    def get_service_health(
        self,
        service_name: Optional[str] = None,
    ) -> Any:
        """Retrieve one service status or all service statuses."""

        with self._lock:
            if service_name:
                record = self._service_status.get(service_name)

                return record.copy() if record else None

            return {
                name: record.copy()
                for name, record in self._service_status.items()
            }

    def get_unhealthy_services(self) -> List[Dict[str, Any]]:
        """Return services currently reporting unhealthy status."""

        with self._lock:
            return [
                record.copy()
                for record in self._service_status.values()
                if record["status"] == "unhealthy"
            ]

    def get_degraded_services(self) -> List[Dict[str, Any]]:
        """Return services currently reporting degraded status."""

        with self._lock:
            return [
                record.copy()
                for record in self._service_status.values()
                if record["status"] == "degraded"
            ]

    # --------------------------------------------------
    # PERFORMANCE SUMMARY
    # --------------------------------------------------

    def get_performance_summary(self) -> Dict[str, Any]:
        """Calculate overall performance metrics."""

        summary = self.performance_service.get_performance_summary()

        response_times = summary["response_times"]

        error_rate = summary["error_rate_percent"]
        slow_rate = summary["slow_request_rate_percent"]

        metrics = {
            "response_time_ms": response_times["average_ms"],
            "error_rate_percent": error_rate,
            "request_count": summary["total_requests"],
            "slow_request_rate_percent": slow_rate,
        }

        return {
            "generated_at": self._now(),
            "total_requests": summary["total_requests"],
            "unique_endpoints": summary["unique_endpoints"],
            "slow_requests": summary["slow_requests"],
            "error_requests": summary["error_requests"],
            "error_rate_percent": error_rate,
            "slow_request_rate_percent": slow_rate,
            "response_times": response_times,
            "metrics": metrics,
        }

    # --------------------------------------------------
    # AVAILABILITY
    # --------------------------------------------------

    def get_availability_summary(self) -> Dict[str, Any]:
        """
        Calculate observed availability from recorded service checks.

        Availability here is based on the latest recorded status
        for each service, not a historical uptime calculation.
        """

        with self._lock:
            services = list(self._service_status.values())

        total = len(services)

        healthy = sum(
            item["status"] == "healthy"
            for item in services
        )

        degraded = sum(
            item["status"] == "degraded"
            for item in services
        )

        unhealthy = sum(
            item["status"] == "unhealthy"
            for item in services
        )

        unknown = sum(
            item["status"] == "unknown"
            for item in services
        )

        availability = (
            healthy / total * 100
            if total else None
        )

        return {
            "total_services": total,
            "healthy_services": healthy,
            "degraded_services": degraded,
            "unhealthy_services": unhealthy,
            "unknown_services": unknown,
            "observed_healthy_percentage": round(
                availability,
                2,
            ) if availability is not None else None,
        }

    # --------------------------------------------------
    # MONITORING RULES
    # --------------------------------------------------

    def evaluate_monitoring_rules(self) -> List[Dict[str, Any]]:
        """Evaluate rules using the latest performance summary."""

        summary = self.get_performance_summary()

        results = self.alert_rules_service.evaluate_metrics(
            summary["metrics"]
        )

        availability = self.get_availability_summary()

        if availability["total_services"] > 0:
            availability_metric = (
                availability["observed_healthy_percentage"]
            )

            availability_results = (
                self.alert_rules_service.evaluate_metrics({
                    "availability_percent": availability_metric
                })
            )

            results.extend(availability_results)

        return results

    # --------------------------------------------------
    # ENDPOINT REPORTS
    # --------------------------------------------------

    def get_endpoint_report(self) -> List[Dict[str, Any]]:
        """Return performance information for all endpoints."""

        return self.performance_service.get_endpoint_performance()

    def get_slowest_endpoints(
        self,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """Return the slowest endpoints."""

        return self.performance_service.get_slowest_endpoints(
            limit=limit
        )

    def get_recent_requests(
        self,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Return recent API requests."""

        return self.performance_service.get_records(
            limit=limit
        )

    # --------------------------------------------------
    # ALERT REPORTS
    # --------------------------------------------------

    def get_open_alerts(
        self,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Return open and acknowledged alerts."""

        open_alerts = self.alert_service.get_alerts(
            status="open",
            limit=limit,
        )

        remaining = max(1, limit - len(open_alerts))

        acknowledged = self.alert_service.get_alerts(
            status="acknowledged",
            limit=remaining,
        )

        return sorted(
            open_alerts + acknowledged,
            key=lambda item: item["last_seen_at"],
            reverse=True,
        )[:limit]

    # --------------------------------------------------
    # COMPLETE MONITORING DASHBOARD DATA
    # --------------------------------------------------

    def get_monitoring_dashboard(self) -> Dict[str, Any]:
        """Return combined data for an API monitoring dashboard."""

        return {
            "generated_at": self._now(),
            "performance": self.get_performance_summary(),
            "availability": self.get_availability_summary(),
            "alerts": self.alert_service.get_statistics(),
            "alert_rules": self.alert_rules_service.get_statistics(),
            "service_health": self.get_service_health(),
            "slowest_endpoints": self.get_slowest_endpoints(
                limit=10
            ),
            "open_alerts": self.get_open_alerts(
                limit=20
            ),
        }

    # --------------------------------------------------
    # EXPORT
    # --------------------------------------------------

    def export_monitoring_report(self) -> str:
        """Export the complete monitoring dashboard as JSON."""

        report = self.get_monitoring_dashboard()

        return json.dumps(
            report,
            indent=4,
            ensure_ascii=False,
            default=str,
        )


# ------------------------------------------------------
# SHARED SERVICE INSTANCE
# ------------------------------------------------------

api_monitoring_service = APIMonitoringService()
