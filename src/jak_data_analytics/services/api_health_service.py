"""
JAK Data Analytics - API Health Service

Features:
- API health monitoring
- Register custom health checks
- Run individual health checks
- Run all registered checks
- Track healthy, degraded and unhealthy states
- Dependency health monitoring
- Readiness and liveness checks
- Health report generation
- Health history
- Export health reports

Framework-independent implementation.
"""

from __future__ import annotations

import json
import logging
import time

from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional


logger = logging.getLogger(__name__)


HEALTHY = "healthy"
DEGRADED = "degraded"
UNHEALTHY = "unhealthy"
UNKNOWN = "unknown"


class APIHealthError(Exception):
    """Base exception for API health operations."""


class HealthCheckNotFoundError(APIHealthError):
    """Raised when a health check does not exist."""


class APIHealthService:

    def __init__(self, history_limit: int = 500):

        if (
            not isinstance(history_limit, int)
            or isinstance(history_limit, bool)
            or history_limit < 1
        ):
            raise ValueError(
                "History limit must be a positive integer."
            )

        self.history_limit = history_limit

        self.checks: Dict[str, Dict[str, Any]] = {}

        self.history: List[Dict[str, Any]] = []

        self.last_report: Optional[Dict[str, Any]] = None

    # -----------------------------------------------------
    # TIME
    # -----------------------------------------------------

    @staticmethod
    def _timestamp() -> str:

        return datetime.now(timezone.utc).isoformat()

    # -----------------------------------------------------
    # REGISTER HEALTH CHECKS
    # -----------------------------------------------------

    def register_check(
        self,
        name: str,
        check_function: Callable[[], Any],
        description: str = "",
        critical: bool = True,
        timeout_seconds: float = 10,
        tags: Optional[List[str]] = None,
    ) -> Dict[str, Any]:

        if not isinstance(name, str) or not name.strip():
            raise ValueError("A valid health check name is required.")

        name = name.strip()

        if not callable(check_function):
            raise TypeError("Check function must be callable.")

        if not isinstance(description, str):
            raise ValueError("Description must be a string.")

        if not isinstance(critical, bool):
            raise ValueError("Critical must be a boolean.")

        if (
            not isinstance(timeout_seconds, (int, float))
            or isinstance(timeout_seconds, bool)
            or timeout_seconds <= 0
        ):
            raise ValueError(
                "Timeout must be a positive number."
            )

        if tags is None:
            tags = []

        if not isinstance(tags, list) or not all(
            isinstance(tag, str) for tag in tags
        ):
            raise ValueError("Tags must be a list of strings.")

        self.checks[name] = {
            "name": name,
            "function": check_function,
            "description": description,
            "critical": critical,
            "timeout_seconds": float(timeout_seconds),
            "tags": list(tags),
            "enabled": True,
            "registered_at": self._timestamp(),
        }

        return {
            "success": True,
            "message": "Health check registered successfully.",
            "name": name,
        }

    # -----------------------------------------------------
    # ENABLE AND DISABLE CHECKS
    # -----------------------------------------------------

    def enable_check(self, name: str) -> Dict[str, Any]:

        if name not in self.checks:
            raise HealthCheckNotFoundError(name)

        self.checks[name]["enabled"] = True

        return {
            "success": True,
            "message": "Health check enabled.",
            "name": name,
        }

    def disable_check(self, name: str) -> Dict[str, Any]:

        if name not in self.checks:
            raise HealthCheckNotFoundError(name)

        self.checks[name]["enabled"] = False

        return {
            "success": True,
            "message": "Health check disabled.",
            "name": name,
        }

    # -----------------------------------------------------
    # REMOVE CHECKS
    # -----------------------------------------------------

    def remove_check(self, name: str) -> Dict[str, Any]:

        if name not in self.checks:
            raise HealthCheckNotFoundError(name)

        del self.checks[name]

        return {
            "success": True,
            "message": "Health check removed.",
            "name": name,
        }

    # -----------------------------------------------------
    # LIST CHECKS
    # -----------------------------------------------------

    def list_checks(
        self,
        enabled_only: bool = False,
    ) -> List[Dict[str, Any]]:

        results = []

        for check in self.checks.values():

            if enabled_only and not check["enabled"]:
                continue

            results.append({
                "name": check["name"],
                "description": check["description"],
                "critical": check["critical"],
                "timeout_seconds": check["timeout_seconds"],
                "tags": list(check["tags"]),
                "enabled": check["enabled"],
                "registered_at": check["registered_at"],
            })

        return results

    # -----------------------------------------------------
    # NORMALISE CHECK RESULTS
    # -----------------------------------------------------

    @staticmethod
    def _normalise_result(result: Any) -> Dict[str, Any]:

        if isinstance(result, bool):

            return {
                "healthy": result,
                "message": (
                    "Check passed."
                    if result
                    else "Check failed."
                ),
                "details": {},
            }

        if isinstance(result, dict):

            healthy = result.get("healthy")

            if not isinstance(healthy, bool):
                raise ValueError(
                    "Health check dictionary must contain "
                    "a boolean 'healthy' field."
                )

            message = result.get("message", "Check completed.")

            if not isinstance(message, str):
                message = str(message)

            details = result.get("details", {})

            if not isinstance(details, dict):
                details = {"value": str(details)}

            return {
                "healthy": healthy,
                "message": message,
                "details": details,
            }

        raise ValueError(
            "Health check must return a boolean or dictionary."
        )

    # -----------------------------------------------------
    # RUN ONE HEALTH CHECK
    # -----------------------------------------------------

    def run_check(self, name: str) -> Dict[str, Any]:

        if name not in self.checks:
            raise HealthCheckNotFoundError(name)

        check = self.checks[name]

        if not check["enabled"]:

            return {
                "name": name,
                "status": UNKNOWN,
                "message": "Health check is disabled.",
                "critical": check["critical"],
                "duration_ms": 0,
                "timestamp": self._timestamp(),
                "details": {},
            }

        started = time.perf_counter()

        try:

            result = check["function"]()

            duration = (
                time.perf_counter() - started
            ) * 1000

            if duration > check["timeout_seconds"] * 1000:

                status = DEGRADED

                message = (
                    "Health check completed but exceeded "
                    "its configured timeout."
                )

                details = {}

            else:

                normalised = self._normalise_result(result)

                status = (
                    HEALTHY
                    if normalised["healthy"]
                    else UNHEALTHY
                )

                message = normalised["message"]
                details = normalised["details"]

            report = {
                "name": name,
                "status": status,
                "message": message,
                "critical": check["critical"],
                "duration_ms": round(duration, 3),
                "timestamp": self._timestamp(),
                "details": details,
            }

        except Exception as exc:

            duration = (
                time.perf_counter() - started
            ) * 1000

            logger.exception(
                "API health check failed: %s",
                name,
            )

            report = {
                "name": name,
                "status": UNHEALTHY,
                "message": "Health check execution failed.",
                "critical": check["critical"],
                "duration_ms": round(duration, 3),
                "timestamp": self._timestamp(),
                "details": {
                    "error_type": type(exc).__name__,
                },
            }

        self._record_history(report)

        return report

    # -----------------------------------------------------
    # RUN ALL HEALTH CHECKS
    # -----------------------------------------------------

    def run_all_checks(self) -> Dict[str, Any]:

        results = []

        for name, check in self.checks.items():

            if not check["enabled"]:
                continue

            results.append(
                self.run_check(name)
            )

        critical_failures = [
            item for item in results
            if item["critical"]
            and item["status"] == UNHEALTHY
        ]

        noncritical_failures = [
            item for item in results
            if not item["critical"]
            and item["status"] == UNHEALTHY
        ]

        degraded_checks = [
            item for item in results
            if item["status"] == DEGRADED
        ]

        if critical_failures:
            overall_status = UNHEALTHY

        elif noncritical_failures or degraded_checks:
            overall_status = DEGRADED

        elif results:
            overall_status = HEALTHY

        else:
            overall_status = UNKNOWN

        report = {
            "service": "JAK Data Analytics API",
            "status": overall_status,
            "timestamp": self._timestamp(),
            "summary": {
                "total_checks": len(results),
                "healthy": sum(
                    1 for item in results
                    if item["status"] == HEALTHY
                ),
                "degraded": len(degraded_checks),
                "unhealthy": sum(
                    1 for item in results
                    if item["status"] == UNHEALTHY
                ),
                "critical_failures": len(critical_failures),
                "noncritical_failures": len(noncritical_failures),
            },
            "checks": results,
        }

        self.last_report = report

        return report

    # -----------------------------------------------------
    # LIVENESS CHECK
    # -----------------------------------------------------

    def liveness_check(self) -> Dict[str, Any]:

        """
        Indicates whether the application process can respond.

        This is a basic process-level check. It does not prove
        that the database or external services are available.
        """

        return {
            "status": HEALTHY,
            "service": "JAK Data Analytics API",
            "message": "Application process is responding.",
            "timestamp": self._timestamp(),
        }

    # -----------------------------------------------------
    # READINESS CHECK
    # -----------------------------------------------------

    def readiness_check(self) -> Dict[str, Any]:

        """
        Checks whether registered critical dependencies are ready.

        Only registered critical checks are considered.
        """

        critical_checks = [
            name
            for name, check in self.checks.items()
            if check["critical"] and check["enabled"]
        ]

        results = [
            self.run_check(name)
            for name in critical_checks
        ]

        ready = all(
            result["status"] == HEALTHY
            for result in results
        )

        return {
            "ready": ready,
            "status": HEALTHY if ready else UNHEALTHY,
            "timestamp": self._timestamp(),
            "checks": results,
        }

    # -----------------------------------------------------
    # HISTORY
    # -----------------------------------------------------

    def _record_history(
        self,
        report: Dict[str, Any],
    ) -> None:

        self.history.append(dict(report))

        if len(self.history) > self.history_limit:
            self.history = self.history[-self.history_limit:]

    def get_history(
        self,
        name: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:

        if (
            not isinstance(limit, int)
            or isinstance(limit, bool)
            or limit < 1
        ):
            raise ValueError("Limit must be a positive integer.")

        records = self.history

        if name:
            records = [
                item for item in records
                if item["name"] == name
            ]

        return [
            dict(item)
            for item in records[-limit:]
        ]

    def clear_history(self) -> Dict[str, Any]:

        count = len(self.history)

        self.history.clear()

        return {
            "success": True,
            "message": "Health history cleared.",
            "deleted_records": count,
        }

    # -----------------------------------------------------
    # STATISTICS
    # -----------------------------------------------------

    def get_statistics(self) -> Dict[str, Any]:

        total = len(self.history)

        counts = {
            HEALTHY: 0,
            DEGRADED: 0,
            UNHEALTHY: 0,
            UNKNOWN: 0,
        }

        for item in self.history:

            status = item["status"]

            if status in counts:
                counts[status] += 1

        return {
            "total_executions": total,
            "healthy": counts[HEALTHY],
            "degraded": counts[DEGRADED],
            "unhealthy": counts[UNHEALTHY],
            "unknown": counts[UNKNOWN],
            "registered_checks": len(self.checks),
            "enabled_checks": sum(
                1 for item in self.checks.values()
                if item["enabled"]
            ),
        }

    # -----------------------------------------------------
    # EXPORT
    # -----------------------------------------------------

    def export_report(self) -> str:

        report = self.last_report or {
            "service": "JAK Data Analytics API",
            "status": UNKNOWN,
            "message": "No health report has been generated.",
            "timestamp": self._timestamp(),
            "checks": [],
        }

        return json.dumps(
            report,
            indent=4,
            ensure_ascii=False,
        )

    def export_history(self) -> str:

        return json.dumps(
            self.history,
            indent=4,
            ensure_ascii=False,
        )


# ---------------------------------------------------------
# SHARED SERVICE INSTANCE
# ---------------------------------------------------------

api_health_service = APIHealthService()


# ---------------------------------------------------------
# BASIC USAGE EXAMPLE
# ---------------------------------------------------------

if __name__ == "__main__":

    service = APIHealthService()

    # Example application check
    def application_check():

        return {
            "healthy": True,
            "message": "Application is running.",
            "details": {
                "component": "application",
            },
        }

    # Example database check
    def database_check():

        # Replace this example with a real database connection test.
        return {
            "healthy": True,
            "message": "Database connection test passed.",
            "details": {
                "component": "database",
                "example": True,
            },
        }

    service.register_check(
        name="application",
        check_function=application_check,
        description="Checks application availability.",
        critical=True,
    )

    service.register_check(
        name="database",
        check_function=database_check,
        description="Checks database connectivity.",
        critical=True,
    )

    # Run all checks
    report = service.run_all_checks()

    print("HEALTH REPORT")
    print(json.dumps(report, indent=4))

    # Check application liveness
    print("\nLIVENESS")
    print(json.dumps(service.liveness_check(), indent=4))

    # Check application readiness
    print("\nREADINESS")
    print(json.dumps(service.readiness_check(), indent=4))

    # Show statistics
    print("\nSTATISTICS")
    print(json.dumps(service.get_statistics(), indent=4))
