"""
JAK Data Analytics - API Metrics Service

Features:
- Track API requests
- Track successful and failed requests
- Measure response times
- Track endpoint usage
- Calculate error rates
- Calculate average response times
- Identify slow endpoints
- Generate performance summaries
- Filter metrics by endpoint and time
- Export metrics

Framework-independent implementation.

Note:
This initial implementation stores metrics in memory.
Production deployment should use a shared metrics backend.
"""

from __future__ import annotations

import json
import math
import threading
import time

from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional


class APIMetricsError(Exception):
    """Base exception for API metrics operations."""


class APIMetricsService:

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

        self.records: List[Dict[str, Any]] = []

        self.endpoint_metrics = defaultdict(
            lambda: {
                "total_requests": 0,
                "successful_requests": 0,
                "failed_requests": 0,
                "total_response_time_ms": 0.0,
                "min_response_time_ms": None,
                "max_response_time_ms": 0.0,
            }
        )

        self._lock = threading.RLock()

        self.started_at = datetime.now(timezone.utc).isoformat()

    # -----------------------------------------------------
    # VALIDATION
    # -----------------------------------------------------

    @staticmethod
    def _validate_endpoint(endpoint: str) -> str:

        if not isinstance(endpoint, str) or not endpoint.strip():
            raise ValueError("A valid endpoint is required.")

        return endpoint.strip()

    @staticmethod
    def _validate_response_time(response_time_ms: float) -> float:

        if (
            not isinstance(response_time_ms, (int, float))
            or isinstance(response_time_ms, bool)
        ):
            raise ValueError("Response time must be a number.")

        response_time_ms = float(response_time_ms)

        if not math.isfinite(response_time_ms) or response_time_ms < 0:
            raise ValueError(
                "Response time must be a finite non-negative number."
            )

        return response_time_ms

    @staticmethod
    def _validate_status_code(status_code: int) -> int:

        if (
            not isinstance(status_code, int)
            or isinstance(status_code, bool)
            or not 100 <= status_code <= 599
        ):
            raise ValueError("Invalid HTTP status code.")

        return status_code

    # -----------------------------------------------------
    # RECORD API REQUEST
    # -----------------------------------------------------

    def record_request(
        self,
        endpoint: str,
        method: str,
        response_time_ms: float,
        status_code: int,
        success: Optional[bool] = None,
        user_id: Optional[str] = None,
        request_id: Optional[str] = None,
    ) -> Dict[str, Any]:

        endpoint = self._validate_endpoint(endpoint)

        if not isinstance(method, str) or not method.strip():
            raise ValueError("A valid HTTP method is required.")

        method = method.strip().upper()

        response_time_ms = self._validate_response_time(
            response_time_ms
        )

        status_code = self._validate_status_code(status_code)

        if success is None:
            success = 200 <= status_code < 400

        if not isinstance(success, bool):
            raise ValueError("Success must be a boolean.")

        record = {
            "endpoint": endpoint,
            "method": method,
            "response_time_ms": response_time_ms,
            "status_code": status_code,
            "success": success,
            "user_id": str(user_id) if user_id is not None else None,
            "request_id": str(request_id) if request_id is not None else None,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        with self._lock:

            self.records.append(record)

            if len(self.records) > self.history_limit:
                removed = self.records.pop(0)

                self._remove_from_aggregate(removed)

            self._update_aggregate(record)

        return {
            "success": True,
            "message": "API request metrics recorded.",
            "endpoint": endpoint,
        }

    # -----------------------------------------------------
    # UPDATE AGGREGATES
    # -----------------------------------------------------

    def _update_aggregate(self, record: Dict[str, Any]) -> None:

        metrics = self.endpoint_metrics[record["endpoint"]]

        metrics["total_requests"] += 1

        if record["success"]:
            metrics["successful_requests"] += 1
        else:
            metrics["failed_requests"] += 1

        duration = record["response_time_ms"]

        metrics["total_response_time_ms"] += duration

        current_min = metrics["min_response_time_ms"]

        if current_min is None or duration < current_min:
            metrics["min_response_time_ms"] = duration

        metrics["max_response_time_ms"] = max(
            metrics["max_response_time_ms"],
            duration,
        )

    def _remove_from_aggregate(self, record: Dict[str, Any]) -> None:

        endpoint = record["endpoint"]

        metrics = self.endpoint_metrics[endpoint]

        metrics["total_requests"] -= 1

        if record["success"]:
            metrics["successful_requests"] -= 1
        else:
            metrics["failed_requests"] -= 1

        metrics["total_response_time_ms"] -= record["response_time_ms"]

        remaining = [
            item for item in self.records
            if item["endpoint"] == endpoint
        ]

        if not remaining:
            self.endpoint_metrics.pop(endpoint, None)
            return

        durations = [
            item["response_time_ms"]
            for item in remaining
        ]

        metrics["min_response_time_ms"] = min(durations)
        metrics["max_response_time_ms"] = max(durations)

    # -----------------------------------------------------
    # FILTER RECORDS
    # -----------------------------------------------------

    def get_records(
        self,
        endpoint: Optional[str] = None,
        method: Optional[str] = None,
        success: Optional[bool] = None,
        hours: Optional[float] = None,
        limit: int = 1000,
    ) -> List[Dict[str, Any]]:

        if (
            not isinstance(limit, int)
            or isinstance(limit, bool)
            or limit < 1
        ):
            raise ValueError("Limit must be a positive integer.")

        if hours is not None:

            if (
                not isinstance(hours, (int, float))
                or isinstance(hours, bool)
                or not math.isfinite(hours)
                or hours <= 0
            ):
                raise ValueError("Hours must be a positive number.")

        if success is not None and not isinstance(success, bool):
            raise ValueError("Success must be a boolean or None.")

        cutoff = None

        if hours is not None:
            cutoff = datetime.now(timezone.utc) - timedelta(
                hours=hours
            )

        with self._lock:
            records = list(self.records)

        filtered = []

        for record in reversed(records):

            if endpoint and record["endpoint"] != endpoint:
                continue

            if method and record["method"] != method.upper():
                continue

            if success is not None and record["success"] != success:
                continue

            if cutoff is not None:

                timestamp = datetime.fromisoformat(
                    record["timestamp"]
                )

                if timestamp < cutoff:
                    continue

            filtered.append(dict(record))

            if len(filtered) >= limit:
                break

        return filtered

    # -----------------------------------------------------
    # OVERALL METRICS
    # -----------------------------------------------------

    def get_overall_metrics(
        self,
        hours: Optional[float] = None,
    ) -> Dict[str, Any]:

        records = self.get_records(
            hours=hours,
            limit=self.history_limit,
        )

        total = len(records)

        successful = sum(
            1 for item in records
            if item["success"]
        )

        failed = total - successful

        durations = [
            item["response_time_ms"]
            for item in records
        ]

        average = (
            sum(durations) / total
            if total
            else 0
        )

        return {
            "total_requests": total,
            "successful_requests": successful,
            "failed_requests": failed,
            "error_rate_percent": round(
                (failed / total) * 100,
                2,
            ) if total else 0,
            "success_rate_percent": round(
                (successful / total) * 100,
                2,
            ) if total else 0,
            "average_response_time_ms": round(average, 3),
            "minimum_response_time_ms": min(durations) if durations else 0,
            "maximum_response_time_ms": max(durations) if durations else 0,
            "period_hours": hours,
        }

    # -----------------------------------------------------
    # ENDPOINT METRICS
    # -----------------------------------------------------

    def get_endpoint_metrics(
        self,
        endpoint: str,
    ) -> Dict[str, Any]:

        endpoint = self._validate_endpoint(endpoint)

        with self._lock:
            metrics = self.endpoint_metrics.get(endpoint)

            if not metrics:
                return {
                    "endpoint": endpoint,
                    "found": False,
                    "total_requests": 0,
                }

            result = dict(metrics)

        total = result["total_requests"]

        result["endpoint"] = endpoint
        result["found"] = True

        result["average_response_time_ms"] = round(
            result["total_response_time_ms"] / total,
            3,
        ) if total else 0

        result["error_rate_percent"] = round(
            result["failed_requests"] / total * 100,
            2,
        ) if total else 0

        result["success_rate_percent"] = round(
            result["successful_requests"] / total * 100,
            2,
        ) if total else 0

        return result

    def get_all_endpoint_metrics(self) -> List[Dict[str, Any]]:

        with self._lock:
            endpoints = list(self.endpoint_metrics.keys())

        return [
            self.get_endpoint_metrics(endpoint)
            for endpoint in endpoints
        ]

    # -----------------------------------------------------
    # SLOW ENDPOINTS
    # -----------------------------------------------------

    def get_slow_endpoints(
        self,
        threshold_ms: float = 1000,
    ) -> List[Dict[str, Any]]:

        threshold_ms = self._validate_response_time(threshold_ms)

        results = []

        for metrics in self.get_all_endpoint_metrics():

            if (
                metrics.get("found")
                and metrics["average_response_time_ms"] > threshold_ms
            ):
                results.append(metrics)

        return sorted(
            results,
            key=lambda item: item["average_response_time_ms"],
            reverse=True,
        )

    # -----------------------------------------------------
    # HTTP STATUS DISTRIBUTION
    # -----------------------------------------------------

    def get_status_code_distribution(
        self,
        hours: Optional[float] = None,
    ) -> Dict[str, int]:

        records = self.get_records(
            hours=hours,
            limit=self.history_limit,
        )

        distribution = defaultdict(int)

        for record in records:
            distribution[str(record["status_code"])] += 1

        return dict(distribution)

    # -----------------------------------------------------
    # HOURLY REQUEST DISTRIBUTION
    # -----------------------------------------------------

    def get_hourly_distribution(
        self,
        hours: int = 24,
    ) -> List[Dict[str, Any]]:

        if (
            not isinstance(hours, int)
            or isinstance(hours, bool)
            or hours < 1
            or hours > 720
        ):
            raise ValueError("Hours must be between 1 and 720.")

        records = self.get_records(
            hours=hours,
            limit=self.history_limit,
        )

        distribution = defaultdict(int)

        for record in records:

            timestamp = datetime.fromisoformat(
                record["timestamp"]
            )

            hour_key = timestamp.strftime("%Y-%m-%d %H:00")

            distribution[hour_key] += 1

        return [
            {
                "hour": key,
                "requests": distribution[key],
            }
            for key in sorted(distribution)
        ]

    # -----------------------------------------------------
    # PERFORMANCE SUMMARY
    # -----------------------------------------------------

    def get_performance_summary(self) -> Dict[str, Any]:

        overall = self.get_overall_metrics()

        endpoints = self.get_all_endpoint_metrics()

        return {
            "service": "JAK Data Analytics API",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "started_at": self.started_at,
            "overall": overall,
            "endpoint_count": len(endpoints),
            "endpoints": endpoints,
            "slow_endpoints": self.get_slow_endpoints(),
            "status_code_distribution": (
                self.get_status_code_distribution()
            ),
        }

    # -----------------------------------------------------
    # RESET METRICS
    # -----------------------------------------------------

    def clear_metrics(self) -> Dict[str, Any]:

        with self._lock:

            count = len(self.records)

            self.records.clear()
            self.endpoint_metrics.clear()

            self.started_at = datetime.now(
                timezone.utc
            ).isoformat()

        return {
            "success": True,
            "message": "API metrics cleared.",
            "deleted_records": count,
        }

    # -----------------------------------------------------
    # EXPORT
    # -----------------------------------------------------

    def export_metrics(
        self,
        indent: int = 4,
    ) -> str:

        return json.dumps(
            self.get_performance_summary(),
            indent=indent,
            ensure_ascii=False,
        )

    def export_records(
        self,
        hours: Optional[float] = None,
    ) -> str:

        return json.dumps(
            self.get_records(
                hours=hours,
                limit=self.history_limit,
            ),
            indent=4,
            ensure_ascii=False,
        )


# ---------------------------------------------------------
# SHARED SERVICE INSTANCE
# ---------------------------------------------------------

api_metrics_service = APIMetricsService()


# ---------------------------------------------------------
# BASIC USAGE EXAMPLE
# ---------------------------------------------------------

if __name__ == "__main__":

    service = APIMetricsService()

    # Record successful requests
    service.record_request(
        endpoint="/api/v1/datasets",
        method="GET",
        response_time_ms=120,
        status_code=200,
    )

    service.record_request(
        endpoint="/api/v1/datasets",
        method="POST",
        response_time_ms=350,
        status_code=201,
    )

    # Record a failed request
    service.record_request(
        endpoint="/api/v1/datasets",
        method="GET",
        response_time_ms=80,
        status_code=500,
    )

    # Overall statistics
    print("\nOVERALL METRICS")
    print(json.dumps(
        service.get_overall_metrics(),
        indent=4,
    ))

    # Endpoint statistics
    print("\nENDPOINT METRICS")
    print(json.dumps(
        service.get_all_endpoint_metrics(),
        indent=4,
    ))

    # Slow endpoints
    print("\nSLOW ENDPOINTS")
    print(json.dumps(
        service.get_slow_endpoints(threshold_ms=100),
        indent=4,
    ))

    # Complete performance report
    print("\nPERFORMANCE SUMMARY")
    print(service.export_metrics())
