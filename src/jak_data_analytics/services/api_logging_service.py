"""
JAK Data Analytics - API Logging Service

Features:
- Record API activity
- Log incoming requests and outgoing responses
- Record API errors
- Track request IDs
- Filter logs by endpoint, method, level and status
- Search log messages
- Track request duration
- Export logs as JSON
- Automatic log retention
- Sensitive information redaction

Framework-independent implementation.

Important:
This initial implementation stores logs in memory.
Production deployment should use persistent centralised logging.
"""

from __future__ import annotations

import json
import logging
import re
import threading

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional


logger = logging.getLogger(__name__)


LOG_LEVELS = {
    "DEBUG",
    "INFO",
    "WARNING",
    "ERROR",
    "CRITICAL",
}

SENSITIVE_FIELDS = {
    "password",
    "passwd",
    "secret",
    "token",
    "access_token",
    "refresh_token",
    "api_key",
    "authorization",
    "cookie",
    "set-cookie",
    "private_key",
    "client_secret",
}


class APILoggingError(Exception):
    """Base exception for API logging operations."""


class APILoggingService:

    def __init__(self, history_limit: int = 10000):

        if (
            not isinstance(history_limit, int)
            or isinstance(history_limit, bool)
            or history_limit < 1
        ):
            raise ValueError(
                "History limit must be a positive integer."
            )

        self.history_limit = history_limit
        self.logs: List[Dict[str, Any]] = []
        self._lock = threading.RLock()

    # -----------------------------------------------------
    # TIME
    # -----------------------------------------------------

    @staticmethod
    def _timestamp() -> str:

        return datetime.now(timezone.utc).isoformat()

    # -----------------------------------------------------
    # SENSITIVE DATA REDACTION
    # -----------------------------------------------------

    @classmethod
    def redact_sensitive_data(cls, value: Any) -> Any:
        """
        Recursively redact common sensitive fields.

        Never pass raw passwords, tokens, API keys or credentials
        into log messages or exception descriptions.
        """

        if isinstance(value, dict):

            cleaned = {}

            for key, item in value.items():

                key_name = str(key).lower().replace("-", "_")

                if key_name in SENSITIVE_FIELDS:
                    cleaned[str(key)] = "[REDACTED]"
                else:
                    cleaned[str(key)] = cls.redact_sensitive_data(item)

            return cleaned

        if isinstance(value, list):
            return [
                cls.redact_sensitive_data(item)
                for item in value
            ]

        if isinstance(value, tuple):
            return [
                cls.redact_sensitive_data(item)
                for item in value
            ]

        if isinstance(value, str):

            # Redact common credential patterns in free text.
            value = re.sub(
                r"(?i)(password|passwd|secret|api[_-]?key|access[_-]?token)"
                r"\s*[:=]\s*(['\"]?)[^\s,'\";]+",
                r"\1=[REDACTED]",
                value,
            )

            value = re.sub(
                r"(?i)Bearer\s+[A-Za-z0-9._~+/=-]+",
                "Bearer [REDACTED]",
                value,
            )

            return value

        return value

    # -----------------------------------------------------
    # VALIDATION
    # -----------------------------------------------------

    @staticmethod
    def _validate_level(level: str) -> str:

        if not isinstance(level, str):
            raise ValueError("Log level must be a string.")

        level = level.upper().strip()

        if level not in LOG_LEVELS:
            raise ValueError(
                "Invalid log level. Choose DEBUG, INFO, WARNING, "
                "ERROR or CRITICAL."
            )

        return level

    @staticmethod
    def _validate_endpoint(endpoint: str) -> str:

        if not isinstance(endpoint, str) or not endpoint.strip():
            raise ValueError("A valid endpoint is required.")

        return endpoint.strip()

    # -----------------------------------------------------
    # STORE LOG
    # -----------------------------------------------------

    def _store_log(
        self,
        record: Dict[str, Any],
    ) -> Dict[str, Any]:

        safe_record = self.redact_sensitive_data(record)

        with self._lock:

            self.logs.append(safe_record)

            if len(self.logs) > self.history_limit:
                self.logs = self.logs[-self.history_limit:]

        return {
            "success": True,
            "message": "API log recorded successfully.",
            "log_id": safe_record["log_id"],
        }

    # -----------------------------------------------------
    # GENERAL LOGGING
    # -----------------------------------------------------

    def log(
        self,
        message: str,
        level: str = "INFO",
        category: str = "application",
        endpoint: Optional[str] = None,
        method: Optional[str] = None,
        status_code: Optional[int] = None,
        request_id: Optional[str] = None,
        user_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:

        if not isinstance(message, str) or not message.strip():
            raise ValueError("A log message is required.")

        level = self._validate_level(level)

        if not isinstance(category, str) or not category.strip():
            raise ValueError("A valid category is required.")

        if endpoint is not None:
            endpoint = self._validate_endpoint(endpoint)

        if method is not None:
            if not isinstance(method, str) or not method.strip():
                raise ValueError("Invalid HTTP method.")
            method = method.strip().upper()

        if status_code is not None:
            if (
                not isinstance(status_code, int)
                or isinstance(status_code, bool)
                or not 100 <= status_code <= 599
            ):
                raise ValueError("Invalid HTTP status code.")

        if details is not None and not isinstance(details, dict):
            raise ValueError("Details must be a dictionary.")

        import uuid

        record = {
            "log_id": str(uuid.uuid4()),
            "timestamp": self._timestamp(),
            "level": level,
            "category": category.strip(),
            "message": message.strip(),
            "endpoint": endpoint,
            "method": method,
            "status_code": status_code,
            "request_id": str(request_id) if request_id else None,
            "user_id": str(user_id) if user_id else None,
            "details": details or {},
        }

        return self._store_log(record)

    # -----------------------------------------------------
    # REQUEST LOGGING
    # -----------------------------------------------------

    def log_request(
        self,
        endpoint: str,
        method: str,
        request_id: Optional[str] = None,
        user_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:

        endpoint = self._validate_endpoint(endpoint)

        if not isinstance(method, str) or not method.strip():
            raise ValueError("A valid HTTP method is required.")

        return self.log(
            message="API request received.",
            level="INFO",
            category="request",
            endpoint=endpoint,
            method=method,
            request_id=request_id,
            user_id=user_id,
            details=details,
        )

    # -----------------------------------------------------
    # RESPONSE LOGGING
    # -----------------------------------------------------

    def log_response(
        self,
        endpoint: str,
        method: str,
        status_code: int,
        duration_ms: float,
        request_id: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> Dict[str, Any]:

        endpoint = self._validate_endpoint(endpoint)

        if not isinstance(method, str) or not method.strip():
            raise ValueError("A valid HTTP method is required.")

        if (
            not isinstance(status_code, int)
            or isinstance(status_code, bool)
            or not 100 <= status_code <= 599
        ):
            raise ValueError("Invalid HTTP status code.")

        if (
            not isinstance(duration_ms, (int, float))
            or isinstance(duration_ms, bool)
            or duration_ms < 0
        ):
            raise ValueError("Duration must be non-negative.")

        if status_code >= 500:
            level = "ERROR"
        elif status_code >= 400:
            level = "WARNING"
        else:
            level = "INFO"

        return self.log(
            message="API response sent.",
            level=level,
            category="response",
            endpoint=endpoint,
            method=method,
            status_code=status_code,
            request_id=request_id,
            user_id=user_id,
            details={
                "duration_ms": round(float(duration_ms), 3),
            },
        )

    # -----------------------------------------------------
    # ERROR LOGGING
    # -----------------------------------------------------

    def log_error(
        self,
        message: str,
        endpoint: Optional[str] = None,
        request_id: Optional[str] = None,
        error_type: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> Dict[str, Any]:

        details = {}

        if error_type:
            details["error_type"] = str(error_type)

        return self.log(
            message=message,
            level="ERROR",
            category="error",
            endpoint=endpoint,
            request_id=request_id,
            user_id=user_id,
            details=details,
        )

    # -----------------------------------------------------
    # SECURITY LOGGING
    # -----------------------------------------------------

    def log_security_event(
        self,
        message: str,
        severity: str = "WARNING",
        user_id: Optional[str] = None,
        request_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:

        return self.log(
            message=message,
            level=severity,
            category="security",
            request_id=request_id,
            user_id=user_id,
            details=details,
        )

    # -----------------------------------------------------
    # FILTER LOGS
    # -----------------------------------------------------

    def get_logs(
        self,
        level: Optional[str] = None,
        category: Optional[str] = None,
        endpoint: Optional[str] = None,
        method: Optional[str] = None,
        request_id: Optional[str] = None,
        search: Optional[str] = None,
        hours: Optional[float] = None,
        limit: int = 1000,
    ) -> List[Dict[str, Any]]:

        if (
            not isinstance(limit, int)
            or isinstance(limit, bool)
            or limit < 1
        ):
            raise ValueError("Limit must be a positive integer.")

        if level:
            level = self._validate_level(level)

        if hours is not None:
            if (
                not isinstance(hours, (int, float))
                or isinstance(hours, bool)
                or hours <= 0
            ):
                raise ValueError("Hours must be positive.")

        cutoff = None

        if hours is not None:
            cutoff = datetime.now(timezone.utc) - timedelta(
                hours=hours
            )

        with self._lock:
            records = list(self.logs)

        results = []

        for record in reversed(records):

            if level and record["level"] != level:
                continue

            if category and record["category"] != category:
                continue

            if endpoint and record["endpoint"] != endpoint:
                continue

            if method and record["method"] != method.upper():
                continue

            if request_id and record["request_id"] != request_id:
                continue

            if search:

                searchable = (
                    record["message"]
                    + " "
                    + json.dumps(record["details"], ensure_ascii=False)
                ).lower()

                if search.lower() not in searchable:
                    continue

            if cutoff:

                timestamp = datetime.fromisoformat(
                    record["timestamp"]
                )

                if timestamp < cutoff:
                    continue

            results.append(dict(record))

            if len(results) >= limit:
                break

        return results

    # -----------------------------------------------------
    # GET LOG BY ID
    # -----------------------------------------------------

    def get_log(self, log_id: str) -> Optional[Dict[str, Any]]:

        if not isinstance(log_id, str):
            raise ValueError("Log ID must be a string.")

        with self._lock:
            for record in reversed(self.logs):

                if record["log_id"] == log_id:
                    return dict(record)

        return None

    # -----------------------------------------------------
    # LOG STATISTICS
    # -----------------------------------------------------

    def get_statistics(
        self,
        hours: Optional[float] = None,
    ) -> Dict[str, Any]:

        records = self.get_logs(
            hours=hours,
            limit=self.history_limit,
        )

        levels = {
            level: 0
            for level in LOG_LEVELS
        }

        categories = {}

        for record in records:

            levels[record["level"]] += 1

            category = record["category"]

            categories[category] = (
                categories.get(category, 0) + 1
            )

        return {
            "total_logs": len(records),
            "levels": levels,
            "categories": categories,
            "period_hours": hours,
        }

    # -----------------------------------------------------
    # CLEAN OLD LOGS
    # -----------------------------------------------------

    def clean_old_logs(
        self,
        retention_days: int = 30,
    ) -> Dict[str, Any]:

        if (
            not isinstance(retention_days, int)
            or isinstance(retention_days, bool)
            or retention_days < 1
        ):
            raise ValueError(
                "Retention days must be a positive integer."
            )

        cutoff = datetime.now(timezone.utc) - timedelta(
            days=retention_days
        )

        with self._lock:

            original_count = len(self.logs)

            self.logs = [
                record for record in self.logs
                if datetime.fromisoformat(
                    record["timestamp"]
                ) >= cutoff
            ]

            deleted = original_count - len(self.logs)

        return {
            "success": True,
            "deleted_logs": deleted,
            "remaining_logs": len(self.logs),
        }

    # -----------------------------------------------------
    # CLEAR LOGS
    # -----------------------------------------------------

    def clear_logs(self) -> Dict[str, Any]:

        with self._lock:

            count = len(self.logs)
            self.logs.clear()

        return {
            "success": True,
            "message": "API logs cleared.",
            "deleted_logs": count,
        }

    # -----------------------------------------------------
    # EXPORT
    # -----------------------------------------------------

    def export_logs(
        self,
        hours: Optional[float] = None,
        indent: int = 4,
    ) -> str:

        return json.dumps(
            self.get_logs(
                hours=hours,
                limit=self.history_limit,
            ),
            indent=indent,
            ensure_ascii=False,
        )

    def export_statistics(self) -> str:

        return json.dumps(
            self.get_statistics(),
            indent=4,
            ensure_ascii=False,
        )


# ---------------------------------------------------------
# SHARED SERVICE INSTANCE
# ---------------------------------------------------------

api_logging_service = APILoggingService()


# ---------------------------------------------------------
# BASIC USAGE EXAMPLE
# ---------------------------------------------------------

if __name__ == "__main__":

    service = APILoggingService()

    # Log an incoming request
    service.log_request(
        endpoint="/api/v1/datasets",
        method="GET",
        request_id="REQ-001",
        user_id="USER-001",
    )

    # Log a successful response
    service.log_response(
        endpoint="/api/v1/datasets",
        method="GET",
        status_code=200,
        duration_ms=125.5,
        request_id="REQ-001",
        user_id="USER-001",
    )

    # Log an application error
    service.log_error(
        message="Dataset processing failed.",
        endpoint="/api/v1/datasets/process",
        request_id="REQ-002",
        error_type="ProcessingError",
    )

    # Log a security event
    service.log_security_event(
        message="Repeated authentication failures detected.",
        severity="WARNING",
        user_id="USER-001",
    )

    # Display recent logs
    print("\nRECENT LOGS")
    print(json.dumps(
        service.get_logs(limit=10),
        indent=4,
    ))

    # Display statistics
    print("\nLOG STATISTICS")
    print(json.dumps(
        service.get_statistics(),
        indent=4,
    ))

    # Export logs
    print("\nLOG EXPORT")
    print(service.export_logs())
