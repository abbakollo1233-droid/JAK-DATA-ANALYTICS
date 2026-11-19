"""
JAK Data Analytics
API Tracing Service

Provides lightweight application-level tracing for API operations.

Features:
- Trace and span creation
- Parent-child span relationships
- Trace correlation IDs
- Execution-time measurement
- Error recording
- Trace searching and filtering
- Trace summaries
- Trace export
- Automatic retention cleanup

Important:
This implementation uses in-memory storage.
Production deployments should use a persistent tracing backend.
"""

from __future__ import annotations

import json
import threading
import time
import uuid

from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Generator, List, Optional


class APITracingError(Exception):
    """Raised when an API tracing operation fails."""


class APITracingService:
    """Manages API traces and spans."""

    DEFAULT_MAX_TRACES = 5000
    DEFAULT_MAX_SPANS = 20000
    DEFAULT_RETENTION_DAYS = 7

    def __init__(
        self,
        max_traces: int = DEFAULT_MAX_TRACES,
        max_spans: int = DEFAULT_MAX_SPANS,
        retention_days: int = DEFAULT_RETENTION_DAYS,
    ):
        self.max_traces = self._validate_positive_integer(
            max_traces, "max_traces"
        )
        self.max_spans = self._validate_positive_integer(
            max_spans, "max_spans"
        )
        self.retention_days = self._validate_positive_integer(
            retention_days, "retention_days"
        )

        self._traces: Dict[str, Dict[str, Any]] = {}
        self._spans: Dict[str, Dict[str, Any]] = {}

        self._trace_span_index: Dict[str, List[str]] = {}

        self._lock = threading.RLock()

    # --------------------------------------------------
    # VALIDATION
    # --------------------------------------------------

    @staticmethod
    def _validate_positive_integer(value: Any, name: str) -> int:
        if isinstance(value, bool) or not isinstance(value, int):
            raise APITracingError(
                f"{name} must be an integer."
            )

        if value <= 0:
            raise APITracingError(
                f"{name} must be greater than zero."
            )

        return value

    @staticmethod
    def _validate_text(
        value: Any,
        name: str,
        max_length: int = 200,
    ) -> str:
        if not isinstance(value, str):
            raise APITracingError(
                f"{name} must be a string."
            )

        value = value.strip()

        if not value:
            raise APITracingError(
                f"{name} cannot be empty."
            )

        if len(value) > max_length:
            raise APITracingError(
                f"{name} cannot exceed {max_length} characters."
            )

        return value

    @staticmethod
    def _now() -> datetime:
        return datetime.now(timezone.utc)

    @staticmethod
    def _timestamp(value: Optional[datetime] = None) -> str:
        value = value or datetime.now(timezone.utc)

        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)

        return value.isoformat()

    @staticmethod
    def _safe_metadata(
        metadata: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        if metadata is None:
            return {}

        if not isinstance(metadata, dict):
            raise APITracingError(
                "Metadata must be a dictionary."
            )

        forbidden_keys = {
            "password",
            "passwd",
            "secret",
            "token",
            "access_token",
            "refresh_token",
            "api_key",
            "authorization",
            "cookie",
            "session_cookie",
            "private_key",
        }

        cleaned = {}

        for key, value in metadata.items():
            safe_key = str(key).strip()

            if not safe_key:
                continue

            if safe_key.lower() in forbidden_keys:
                cleaned[safe_key] = "[REDACTED]"
                continue

            if isinstance(value, (str, int, float, bool)) or value is None:
                cleaned[safe_key] = value
            else:
                cleaned[safe_key] = str(value)[:500]

        return cleaned

    # --------------------------------------------------
    # TRACE CREATION
    # --------------------------------------------------

    def start_trace(
        self,
        operation_name: str,
        service_name: str = "jak-data-analytics",
        user_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Create a new trace."""

        operation_name = self._validate_text(
            operation_name,
            "operation_name",
        )

        service_name = self._validate_text(
            service_name,
            "service_name",
        )

        trace_id = uuid.uuid4().hex

        now = self._now()

        trace = {
            "trace_id": trace_id,
            "operation_name": operation_name,
            "service_name": service_name,
            "user_id": str(user_id) if user_id is not None else None,
            "status": "running",
            "started_at": self._timestamp(now),
            "ended_at": None,
            "duration_ms": None,
            "span_count": 0,
            "error_count": 0,
            "metadata": self._safe_metadata(metadata),
        }

        with self._lock:
            self._traces[trace_id] = trace
            self._trace_span_index[trace_id] = []

            self._enforce_trace_limit()

        return trace.copy()

    # --------------------------------------------------
    # SPAN CREATION
    # --------------------------------------------------

    def start_span(
        self,
        trace_id: str,
        operation_name: str,
        parent_span_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Start a span inside an existing trace."""

        trace_id = self._validate_text(
            trace_id,
            "trace_id",
            100,
        )

        operation_name = self._validate_text(
            operation_name,
            "operation_name",
        )

        span_id = uuid.uuid4().hex

        with self._lock:
            trace = self._traces.get(trace_id)

            if trace is None:
                raise APITracingError(
                    "The requested trace does not exist."
                )

            if trace["status"] != "running":
                raise APITracingError(
                    "Cannot add spans to a completed trace."
                )

            if parent_span_id is not None:
                parent = self._spans.get(parent_span_id)

                if parent is None:
                    raise APITracingError(
                        "The parent span does not exist."
                    )

                if parent["trace_id"] != trace_id:
                    raise APITracingError(
                        "The parent span belongs to another trace."
                    )

                if parent["status"] != "running":
                    raise APITracingError(
                        "Cannot create a child of a completed span."
                    )

            if len(self._spans) >= self.max_spans:
                self._remove_oldest_spans()

            span = {
                "span_id": span_id,
                "trace_id": trace_id,
                "parent_span_id": parent_span_id,
                "operation_name": operation_name,
                "status": "running",
                "started_at": self._timestamp(),
                "ended_at": None,
                "duration_ms": None,
                "error": None,
                "metadata": self._safe_metadata(metadata),
            }

            self._spans[span_id] = span
            self._trace_span_index[trace_id].append(span_id)

            trace["span_count"] += 1

        return span.copy()

    # --------------------------------------------------
    # SPAN COMPLETION
    # --------------------------------------------------

    def end_span(
        self,
        span_id: str,
        status: str = "success",
        error: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Finish a running span."""

        if status not in {"success", "error", "cancelled"}:
            raise APITracingError(
                "Invalid span status."
            )

        span_id = self._validate_text(
            span_id,
            "span_id",
            100,
        )

        with self._lock:
            span = self._spans.get(span_id)

            if span is None:
                raise APITracingError(
                    "The requested span does not exist."
                )

            if span["status"] != "running":
                raise APITracingError(
                    "This span has already been completed."
                )

            now = self._now()

            started_at = datetime.fromisoformat(
                span["started_at"]
            )

            duration_ms = max(
                0.0,
                (now - started_at).total_seconds() * 1000,
            )

            span["status"] = status
            span["ended_at"] = self._timestamp(now)
            span["duration_ms"] = round(duration_ms, 3)

            if error is not None:
                span["error"] = str(error)[:1000]

            if metadata:
                span["metadata"].update(
                    self._safe_metadata(metadata)
                )

            if status == "error":
                trace = self._traces.get(span["trace_id"])

                if trace:
                    trace["error_count"] += 1

        return span.copy()

    # --------------------------------------------------
    # TRACE COMPLETION
    # --------------------------------------------------

    def end_trace(
        self,
        trace_id: str,
        status: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Complete a trace and calculate its duration."""

        trace_id = self._validate_text(
            trace_id,
            "trace_id",
            100,
        )

        with self._lock:
            trace = self._traces.get(trace_id)

            if trace is None:
                raise APITracingError(
                    "The requested trace does not exist."
                )

            if trace["status"] != "running":
                raise APITracingError(
                    "This trace has already been completed."
                )

            span_ids = self._trace_span_index.get(
                trace_id,
                [],
            )

            running_spans = [
                span_id
                for span_id in span_ids
                if self._spans.get(span_id, {}).get("status") == "running"
            ]

            if running_spans:
                raise APITracingError(
                    "All spans must be completed before ending the trace."
                )

            if status is None:
                status = (
                    "error"
                    if trace["error_count"] > 0
                    else "success"
                )

            if status not in {"success", "error", "cancelled"}:
                raise APITracingError(
                    "Invalid trace status."
                )

            now = self._now()

            started_at = datetime.fromisoformat(
                trace["started_at"]
            )

            trace["status"] = status
            trace["ended_at"] = self._timestamp(now)

            trace["duration_ms"] = round(
                max(
                    0.0,
                    (now - started_at).total_seconds() * 1000,
                ),
                3,
            )

        return trace.copy()

    # --------------------------------------------------
    # CONTEXT MANAGER
    # --------------------------------------------------

    @contextmanager
    def trace_operation(
        self,
        operation_name: str,
        service_name: str = "jak-data-analytics",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Generator[Dict[str, Any], None, None]:
        """
        Automatically create and finish a trace.

        Example:

            with tracer.trace_operation("import_dataset") as trace:
                print(trace["trace_id"])
        """

        trace = self.start_trace(
            operation_name=operation_name,
            service_name=service_name,
            metadata=metadata,
        )

        try:
            yield trace

        except Exception as exc:
            with self._lock:
                trace_record = self._traces.get(
                    trace["trace_id"]
                )

                if trace_record:
                    trace_record["error_count"] += 1

            self.end_trace(
                trace["trace_id"],
                status="error",
            )

            raise

        else:
            self.end_trace(
                trace["trace_id"]
            )

    @contextmanager
    def trace_span(
        self,
        trace_id: str,
        operation_name: str,
        parent_span_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Generator[Dict[str, Any], None, None]:
        """Automatically create and finish a span."""

        span = self.start_span(
            trace_id=trace_id,
            operation_name=operation_name,
            parent_span_id=parent_span_id,
            metadata=metadata,
        )

        try:
            yield span

        except Exception as exc:
            self.end_span(
                span["span_id"],
                status="error",
                error=type(exc).__name__,
            )
            raise

        else:
            self.end_span(
                span["span_id"],
                status="success",
            )

    # --------------------------------------------------
    # TRACE RETRIEVAL
    # --------------------------------------------------

    def get_trace(
        self,
        trace_id: str,
        include_spans: bool = True,
    ) -> Optional[Dict[str, Any]]:
        """Retrieve a trace and optionally its spans."""

        with self._lock:
            trace = self._traces.get(trace_id)

            if trace is None:
                return None

            result = trace.copy()

            if include_spans:
                result["spans"] = [
                    self._spans[span_id].copy()
                    for span_id in self._trace_span_index.get(
                        trace_id,
                        [],
                    )
                    if span_id in self._spans
                ]

            return result

    def get_span(
        self,
        span_id: str,
    ) -> Optional[Dict[str, Any]]:
        """Retrieve one span."""

        with self._lock:
            span = self._spans.get(span_id)

            return span.copy() if span else None

    # --------------------------------------------------
    # SEARCH AND FILTERING
    # --------------------------------------------------

    def search_traces(
        self,
        status: Optional[str] = None,
        operation_name: Optional[str] = None,
        service_name: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Search traces using basic filters."""

        limit = self._validate_positive_integer(
            limit,
            "limit",
        )

        if status is not None and status not in {
            "running",
            "success",
            "error",
            "cancelled",
        }:
            raise APITracingError(
                "Invalid trace status filter."
            )

        with self._lock:
            records = list(self._traces.values())

            if status:
                records = [
                    item for item in records
                    if item["status"] == status
                ]

            if operation_name:
                records = [
                    item for item in records
                    if operation_name.lower()
                    in item["operation_name"].lower()
                ]

            if service_name:
                records = [
                    item for item in records
                    if service_name.lower()
                    in item["service_name"].lower()
                ]

            records.sort(
                key=lambda item: item["started_at"],
                reverse=True,
            )

            return [
                item.copy()
                for item in records[:limit]
            ]

    def get_trace_spans(
        self,
        trace_id: str,
    ) -> List[Dict[str, Any]]:
        """Return all available spans for a trace."""

        with self._lock:
            if trace_id not in self._traces:
                return []

            return [
                self._spans[span_id].copy()
                for span_id in self._trace_span_index.get(
                    trace_id,
                    [],
                )
                if span_id in self._spans
            ]

    # --------------------------------------------------
    # STATISTICS
    # --------------------------------------------------

    def get_statistics(self) -> Dict[str, Any]:
        """Return tracing statistics."""

        with self._lock:
            traces = list(self._traces.values())
            spans = list(self._spans.values())

            completed = [
                trace for trace in traces
                if trace["duration_ms"] is not None
            ]

            durations = [
                trace["duration_ms"]
                for trace in completed
            ]

            total = len(traces)

            return {
                "total_traces": total,
                "total_spans": len(spans),
                "running_traces": sum(
                    trace["status"] == "running"
                    for trace in traces
                ),
                "successful_traces": sum(
                    trace["status"] == "success"
                    for trace in traces
                ),
                "failed_traces": sum(
                    trace["status"] == "error"
                    for trace in traces
                ),
                "cancelled_traces": sum(
                    trace["status"] == "cancelled"
                    for trace in traces
                ),
                "average_duration_ms": round(
                    sum(durations) / len(durations),
                    3,
                ) if durations else 0.0,
                "success_rate_percent": round(
                    (
                        sum(
                            trace["status"] == "success"
                            for trace in traces
                        ) / total
                    ) * 100,
                    2,
                ) if total else 0.0,
            }

    # --------------------------------------------------
    # EXPORT
    # --------------------------------------------------

    def export_trace(
        self,
        trace_id: str,
    ) -> str:
        """Export one trace as JSON."""

        trace = self.get_trace(
            trace_id,
            include_spans=True,
        )

        if trace is None:
            raise APITracingError(
                "The requested trace does not exist."
            )

        return json.dumps(
            trace,
            indent=4,
            ensure_ascii=False,
            default=str,
        )

    def export_all_traces(
        self,
        limit: int = 1000,
    ) -> str:
        """Export recent traces and their spans as JSON."""

        traces = self.search_traces(
            limit=limit,
        )

        exported = []

        for trace in traces:
            full_trace = self.get_trace(
                trace["trace_id"],
                include_spans=True,
            )

            if full_trace:
                exported.append(full_trace)

        return json.dumps(
            exported,
            indent=4,
            ensure_ascii=False,
            default=str,
        )

    # --------------------------------------------------
    # RETENTION AND CLEANUP
    # --------------------------------------------------

    def clean_old_traces(self) -> int:
        """Delete completed traces older than the retention period."""

        cutoff = self._now() - timedelta(
            days=self.retention_days
        )

        deleted = 0

        with self._lock:
            old_trace_ids = []

            for trace_id, trace in self._traces.items():
                if trace["status"] == "running":
                    continue

                started_at = datetime.fromisoformat(
                    trace["started_at"]
                )

                if started_at < cutoff:
                    old_trace_ids.append(trace_id)

            for trace_id in old_trace_ids:
                self._delete_trace(trace_id)
                deleted += 1

        return deleted

    def _delete_trace(self, trace_id: str) -> None:
        """Delete a trace and its associated spans."""

        self._traces.pop(trace_id, None)

        span_ids = self._trace_span_index.pop(
            trace_id,
            [],
        )

        for span_id in span_ids:
            self._spans.pop(span_id, None)

    def _remove_oldest_spans(self) -> None:
        """Remove the oldest completed spans to respect capacity."""

        completed_spans = sorted(
            [
                span
                for span in self._spans.values()
                if span["status"] != "running"
            ],
            key=lambda item: item["started_at"],
        )

        if not completed_spans:
            raise APITracingError(
                "Span capacity reached. No completed spans can be removed."
            )

        remove_count = max(
            1,
            len(self._spans) - self.max_spans + 1,
        )

        for span in completed_spans[:remove_count]:
            span_id = span["span_id"]
            trace_id = span["trace_id"]

            self._spans.pop(span_id, None)

            if trace_id in self._trace_span_index:
                try:
                    self._trace_span_index[trace_id].remove(
                        span_id
                    )
                except ValueError:
                    pass

    def _enforce_trace_limit(self) -> None:
        """Remove oldest completed traces when capacity is reached."""

        if len(self._traces) <= self.max_traces:
            return

        completed = sorted(
            [
                trace
                for trace in self._traces.values()
                if trace["status"] != "running"
            ],
            key=lambda item: item["started_at"],
        )

        remove_count = max(
            1,
            len(self._traces) - self.max_traces,
        )

        for trace in completed[:remove_count]:
            self._delete_trace(
                trace["trace_id"]
            )

        if len(self._traces) > self.max_traces:
            raise APITracingError(
                "Trace capacity reached. Running traces cannot be removed."
            )


# ------------------------------------------------------
# SHARED SERVICE INSTANCE
# ------------------------------------------------------

api_tracing_service = APITracingService()
