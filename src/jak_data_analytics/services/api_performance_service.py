"""
JAK Data Analytics
API Performance Service

Tracks API performance and helps identify slow endpoints.

Features:
- Request performance recording
- Response-time statistics
- Average, minimum and maximum response times
- P50, P90, P95 and P99 percentiles
- Slow endpoint identification
- Endpoint comparison
- Error-rate monitoring
- Performance trend summaries
- JSON export

Storage:
In-memory, thread-safe storage.

Production note:
Use persistent metrics storage for multi-worker deployments.
"""

from __future__ import annotations

import json
import math
import threading
import uuid

from collections import defaultdict
from datetime import datetime, timedelta, timezone
from statistics import mean
from typing import Any, Dict, List, Optional


class APIPerformanceError(Exception):
    """Raised when API performance operations fail."""


class APIPerformanceService:
    """Collects and analyses API performance measurements."""

    DEFAULT_MAX_RECORDS = 20000
    DEFAULT_SLOW_THRESHOLD_MS = 1000.0

    def __init__(
        self,
        max_records: int = DEFAULT_MAX_RECORDS,
        slow_threshold_ms: float = DEFAULT_SLOW_THRESHOLD_MS,
    ):
        self.max_records = self._validate_positive_integer(
            max_records,
            "max_records",
        )

        self.slow_threshold_ms = self._validate_duration(
            slow_threshold_ms,
            "slow_threshold_ms",
        )

        self._records: List[Dict[str, Any]] = []
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
            raise APIPerformanceError(
                f"{name} must be an integer."
            )

        if value <= 0:
            raise APIPerformanceError(
                f"{name} must be greater than zero."
            )

        return value

    @staticmethod
    def _validate_duration(
        value: Any,
        name: str,
    ) -> float:
        if isinstance(value, bool):
            raise APIPerformanceError(
                f"{name} must be a number."
            )

        try:
            duration = float(value)
        except (TypeError, ValueError):
            raise APIPerformanceError(
                f"{name} must be a number."
            )

        if not math.isfinite(duration) or duration < 0:
            raise APIPerformanceError(
                f"{name} must be a finite non-negative number."
            )

        return duration

    @staticmethod
    def _validate_text(
        value: Any,
        name: str,
        max_length: int = 300,
    ) -> str:
        if not isinstance(value, str):
            raise APIPerformanceError(
                f"{name} must be a string."
            )

        value = value.strip()

        if not value:
            raise APIPerformanceError(
                f"{name} cannot be empty."
            )

        if len(value) > max_length:
            raise APIPerformanceError(
                f"{name} cannot exceed {max_length} characters."
            )

        return value

    @staticmethod
    def _now() -> datetime:
        return datetime.now(timezone.utc)

    @staticmethod
    def _percentile(
        values: List[float],
        percentile: float,
    ) -> float:
        """Calculate a percentile using linear interpolation."""

        if not values:
            return 0.0

        ordered = sorted(values)

        if len(ordered) == 1:
            return round(ordered[0], 3)

        position = (len(ordered) - 1) * percentile
        lower = math.floor(position)
        upper = math.ceil(position)

        if lower == upper:
            result = ordered[lower]
        else:
            fraction = position - lower

            result = (
                ordered[lower] * (1 - fraction)
                + ordered[upper] * fraction
            )

        return round(result, 3)

    # --------------------------------------------------
    # RECORD PERFORMANCE
    # --------------------------------------------------

    def record_request(
        self,
        endpoint: str,
        method: str,
        response_time_ms: float,
        status_code: int,
        request_id: Optional[str] = None,
        service_name: str = "jak-data-analytics",
        timestamp: Optional[datetime] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Record one API request measurement."""

        endpoint = self._validate_text(
            endpoint,
            "endpoint",
        )

        method = self._validate_text(
            method,
            "method",
            20,
        ).upper()

        service_name = self._validate_text(
            service_name,
            "service_name",
        )

        response_time_ms = self._validate_duration(
            response_time_ms,
            "response_time_ms",
        )

        if (
            isinstance(status_code, bool)
            or not isinstance(status_code, int)
            or not 100 <= status_code <= 599
        ):
            raise APIPerformanceError(
                "status_code must be an HTTP status code between 100 and 599."
            )

        if timestamp is None:
            timestamp = self._now()

        if not isinstance(timestamp, datetime):
            raise APIPerformanceError(
                "timestamp must be a datetime object."
            )

        if timestamp.tzinfo is None:
            timestamp = timestamp.replace(
                tzinfo=timezone.utc
            )

        safe_metadata = self._clean_metadata(metadata)

        record = {
            "record_id": uuid.uuid4().hex,
            "request_id": (
                str(request_id)[:100]
                if request_id is not None
                else None
            ),
            "endpoint": endpoint,
            "method": method,
            "service_name": service_name,
            "response_time_ms": response_time_ms,
            "status_code": status_code,
            "is_error": status_code >= 400,
            "is_slow": (
                response_time_ms >= self.slow_threshold_ms
            ),
            "timestamp": timestamp.astimezone(
                timezone.utc
            ).isoformat(),
            "metadata": safe_metadata,
        }

        with self._lock:
            self._records.append(record)

            if len(self._records) > self.max_records:
                excess = len(self._records) - self.max_records

                self._records = self._records[excess:]

        return record.copy()

    @staticmethod
    def _clean_metadata(
        metadata: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        if metadata is None:
            return {}

        if not isinstance(metadata, dict):
            raise APIPerformanceError(
                "metadata must be a dictionary."
            )

        sensitive = {
            "password",
            "secret",
            "token",
            "access_token",
            "refresh_token",
            "api_key",
            "authorization",
            "cookie",
            "session",
            "private_key",
        }

        cleaned = {}

        for key, value in metadata.items():
            key = str(key).strip()

            if not key:
                continue

            if key.lower() in sensitive:
                cleaned[key] = "[REDACTED]"
            elif isinstance(value, (str, int, float, bool)) or value is None:
                cleaned[key] = value
            else:
                cleaned[key] = str(value)[:500]

        return cleaned

    # --------------------------------------------------
    # RETRIEVE RECORDS
    # --------------------------------------------------

    def get_records(
        self,
        endpoint: Optional[str] = None,
        method: Optional[str] = None,
        status_code: Optional[int] = None,
        slow_only: bool = False,
        limit: int = 1000,
    ) -> List[Dict[str, Any]]:
        """Retrieve performance records using optional filters."""

        limit = self._validate_positive_integer(
            limit,
            "limit",
        )

        with self._lock:
            records = list(self._records)

        if endpoint:
            records = [
                record for record in records
                if endpoint.lower() in record["endpoint"].lower()
            ]

        if method:
            records = [
                record for record in records
                if record["method"] == method.upper()
            ]

        if status_code is not None:
            records = [
                record for record in records
                if record["status_code"] == status_code
            ]

        if slow_only:
            records = [
                record for record in records
                if record["is_slow"]
            ]

        records.sort(
            key=lambda record: record["timestamp"],
            reverse=True,
        )

        return [
            record.copy()
            for record in records[:limit]
        ]

    # --------------------------------------------------
    # RESPONSE TIME STATISTICS
    # --------------------------------------------------

    def calculate_response_statistics(
        self,
        records: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """Calculate response-time statistics."""

        if records is None:
            records = self.get_records(
                limit=self.max_records,
            )

        values = [
            float(record["response_time_ms"])
            for record in records
        ]

        if not values:
            return {
                "request_count": 0,
                "average_ms": 0.0,
                "minimum_ms": 0.0,
                "maximum_ms": 0.0,
                "median_ms": 0.0,
                "p50_ms": 0.0,
                "p90_ms": 0.0,
                "p95_ms": 0.0,
                "p99_ms": 0.0,
            }

        return {
            "request_count": len(values),
            "average_ms": round(mean(values), 3),
            "minimum_ms": round(min(values), 3),
            "maximum_ms": round(max(values), 3),
            "median_ms": self._percentile(values, 0.50),
            "p50_ms": self._percentile(values, 0.50),
            "p90_ms": self._percentile(values, 0.90),
            "p95_ms": self._percentile(values, 0.95),
            "p99_ms": self._percentile(values, 0.99),
        }

    # --------------------------------------------------
    # ENDPOINT PERFORMANCE
    # --------------------------------------------------

    def get_endpoint_performance(
        self,
    ) -> List[Dict[str, Any]]:
        """Return performance statistics grouped by endpoint and method."""

        with self._lock:
            records = list(self._records)

        groups = defaultdict(list)

        for record in records:
            key = (
                record["endpoint"],
                record["method"],
            )
            groups[key].append(record)

        results = []

        for (endpoint, method), group in groups.items():
            response_times = [
                item["response_time_ms"]
                for item in group
            ]

            total = len(group)

            errors = sum(
                item["is_error"]
                for item in group
            )

            slow = sum(
                item["is_slow"]
                for item in group
            )

            results.append({
                "endpoint": endpoint,
                "method": method,
                "request_count": total,
                "average_ms": round(
                    mean(response_times),
                    3,
                ),
                "p95_ms": self._percentile(
                    response_times,
                    0.95,
                ),
                "maximum_ms": round(
                    max(response_times),
                    3,
                ),
                "error_count": errors,
                "error_rate_percent": round(
                    errors / total * 100,
                    2,
                ),
                "slow_request_count": slow,
            })

        results.sort(
            key=lambda item: item["average_ms"],
            reverse=True,
        )

        return results

    def get_slowest_endpoints(
        self,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """Return endpoints with the highest average response times."""

        limit = self._validate_positive_integer(
            limit,
            "limit",
        )

        return self.get_endpoint_performance()[:limit]

    def get_slowest_requests(
        self,
        limit: int = 20,
    ) -> List[Dict[str, Any]]:
        """Return individual requests with the longest response times."""

        limit = self._validate_positive_integer(
            limit,
            "limit",
        )

        records = self.get_records(
            limit=self.max_records,
        )

        records.sort(
            key=lambda item: item["response_time_ms"],
            reverse=True,
        )

        return records[:limit]

    # --------------------------------------------------
    # ERROR MONITORING
    # --------------------------------------------------

    def get_error_statistics(self) -> Dict[str, Any]:
        """Calculate API error statistics."""

        with self._lock:
            records = list(self._records)

        total = len(records)

        errors = [
            record for record in records
            if record["is_error"]
        ]

        client_errors = [
            record for record in errors
            if 400 <= record["status_code"] < 500
        ]

        server_errors = [
            record for record in errors
            if 500 <= record["status_code"] < 600
        ]

        return {
            "total_requests": total,
            "total_errors": len(errors),
            "client_errors": len(client_errors),
            "server_errors": len(server_errors),
            "error_rate_percent": round(
                len(errors) / total * 100,
                2,
            ) if total else 0.0,
        }

    # --------------------------------------------------
    # TIME-WINDOW ANALYSIS
    # --------------------------------------------------

    def get_recent_performance(
        self,
        minutes: int = 60,
    ) -> Dict[str, Any]:
        """Calculate performance for a recent time window."""

        minutes = self._validate_positive_integer(
            minutes,
            "minutes",
        )

        cutoff = self._now() - timedelta(
            minutes=minutes
        )

        records = self.get_records(
            limit=self.max_records,
        )

        recent = [
            record for record in records
            if datetime.fromisoformat(
                record["timestamp"]
            ) >= cutoff
        ]

        statistics = self.calculate_response_statistics(
            recent
        )

        errors = sum(
            record["is_error"]
            for record in recent
        )

        slow = sum(
            record["is_slow"]
            for record in recent
        )

        return {
            "window_minutes": minutes,
            "request_count": len(recent),
            "error_count": errors,
            "slow_request_count": slow,
            "error_rate_percent": round(
                errors / len(recent) * 100,
                2,
            ) if recent else 0.0,
            "slow_request_rate_percent": round(
                slow / len(recent) * 100,
                2,
            ) if recent else 0.0,
            "response_statistics": statistics,
        }

    # --------------------------------------------------
    # SERVICE SUMMARY
    # --------------------------------------------------

    def get_performance_summary(self) -> Dict[str, Any]:
        """Return an overall API performance summary."""

        records = self.get_records(
            limit=self.max_records,
        )

        statistics = self.calculate_response_statistics(
            records
        )

        errors = sum(
            record["is_error"]
            for record in records
        )

        slow = sum(
            record["is_slow"]
            for record in records
        )

        endpoint_count = len({
            (
                record["endpoint"],
                record["method"],
            )
            for record in records
        })

        return {
            "total_requests": len(records),
            "unique_endpoints": endpoint_count,
            "slow_threshold_ms": self.slow_threshold_ms,
            "slow_requests": slow,
            "error_requests": errors,
            "error_rate_percent": round(
                errors / len(records) * 100,
                2,
            ) if records else 0.0,
            "slow_request_rate_percent": round(
                slow / len(records) * 100,
                2,
            ) if records else 0.0,
            "response_times": statistics,
        }

    # --------------------------------------------------
    # EXPORT
    # --------------------------------------------------

    def export_records(
        self,
        limit: int = 5000,
    ) -> str:
        """Export performance records as JSON."""

        records = self.get_records(
            limit=limit,
        )

        return json.dumps(
            records,
            indent=4,
            ensure_ascii=False,
            default=str,
        )

    def export_endpoint_performance(self) -> str:
        """Export grouped endpoint performance."""

        return json.dumps(
            self.get_endpoint_performance(),
            indent=4,
            ensure_ascii=False,
        )

    # --------------------------------------------------
    # CONFIGURATION
    # --------------------------------------------------

    def set_slow_threshold(
        self,
        threshold_ms: float,
    ) -> float:
        """Change the slow-request threshold."""

        threshold = self._validate_duration(
            threshold_ms,
            "threshold_ms",
        )

        if threshold <= 0:
            raise APIPerformanceError(
                "The slow-request threshold must be greater than zero."
            )

        with self._lock:
            self.slow_threshold_ms = threshold

            for record in self._records:
                record["is_slow"] = (
                    record["response_time_ms"] >= threshold
                )

        return self.slow_threshold_ms

    # --------------------------------------------------
    # CLEANUP
    # --------------------------------------------------

    def clear_records(self) -> int:
        """Clear all stored performance records."""

        with self._lock:
            count = len(self._records)
            self._records.clear()

        return count


# ------------------------------------------------------
# SHARED SERVICE INSTANCE
# ------------------------------------------------------

api_performance_service = APIPerformanceService()
