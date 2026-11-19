"""
JAK Data Analytics - API Error Handling Service

Provides centralised API error handling.

Features:
- Standard API error responses.
- Custom API exception classes.
- HTTP status code mapping.
- Error categorisation.
- Validation error formatting.
- Error correlation IDs.
- Safe error messages.
- Development and production response modes.
- Error statistics.
- Error history and export.

Development storage:
- Uses Streamlit session state.

Production requirements:
- Integrate with the actual HTTP framework.
- Persist error records in a database or logging service.
- Avoid exposing internal exception details.
- Apply access controls to error logs.
"""

from __future__ import annotations

import uuid
import traceback

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import streamlit as st


# ============================================================
# CONSTANTS
# ============================================================

ERRORS_KEY = "jak_api_error_records"

HTTP_STATUS_MESSAGES = {
    400: "Bad Request",
    401: "Unauthorized",
    403: "Forbidden",
    404: "Not Found",
    405: "Method Not Allowed",
    408: "Request Timeout",
    409: "Conflict",
    410: "Gone",
    413: "Payload Too Large",
    415: "Unsupported Media Type",
    422: "Unprocessable Entity",
    423: "Locked",
    425: "Too Early",
    429: "Too Many Requests",
    500: "Internal Server Error",
    501: "Not Implemented",
    502: "Bad Gateway",
    503: "Service Unavailable",
    504: "Gateway Timeout",
}

ERROR_CATEGORIES = {
    "validation",
    "authentication",
    "authorization",
    "not_found",
    "conflict",
    "rate_limit",
    "database",
    "external_service",
    "server",
    "unknown",
}

DEFAULT_ERROR_MESSAGES = {
    "validation": "The supplied request data is invalid.",
    "authentication": "Authentication is required.",
    "authorization": "You are not permitted to perform this action.",
    "not_found": "The requested resource was not found.",
    "conflict": "The request conflicts with existing data.",
    "rate_limit": "Too many requests. Please try again later.",
    "database": "A database operation could not be completed.",
    "external_service": "An external service is temporarily unavailable.",
    "server": "An unexpected server error occurred.",
    "unknown": "An unexpected error occurred.",
}


# ============================================================
# STORAGE
# ============================================================

def _ensure_storage() -> None:
    if ERRORS_KEY not in st.session_state:
        st.session_state[ERRORS_KEY] = []


def _get_errors() -> List[Dict[str, Any]]:
    _ensure_storage()
    return st.session_state[ERRORS_KEY]


# ============================================================
# GENERAL HELPERS
# ============================================================

def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _iso_now() -> str:
    return _utc_now().isoformat()


def _validate_status_code(status_code: int) -> int:
    if (
        isinstance(status_code, bool)
        or not isinstance(status_code, int)
        or status_code < 400
        or status_code > 599
    ):
        raise ValueError(
            "HTTP error status must be between 400 and 599."
        )

    return status_code


def _validate_category(category: str) -> str:
    if category not in ERROR_CATEGORIES:
        raise ValueError("Invalid API error category.")

    return category


def _safe_message(
    category: str,
    custom_message: Optional[str] = None,
    debug: bool = False,
) -> str:
    if debug and custom_message:
        return str(custom_message)[:1000]

    return DEFAULT_ERROR_MESSAGES.get(
        category,
        DEFAULT_ERROR_MESSAGES["unknown"],
    )


# ============================================================
# CUSTOM API EXCEPTIONS
# ============================================================

class APIError(Exception):
    """Base exception for JAK API errors."""

    def __init__(
        self,
        message: str,
        status_code: int = 500,
        category: str = "unknown",
        details: Optional[Any] = None,
    ):
        super().__init__(message)

        self.message = str(message)
        self.status_code = _validate_status_code(status_code)
        self.category = _validate_category(category)
        self.details = details


class APIValidationError(APIError):
    def __init__(
        self,
        message: str = "Request validation failed.",
        details: Optional[Any] = None,
    ):
        super().__init__(
            message,
            status_code=422,
            category="validation",
            details=details,
        )


class APIAuthenticationError(APIError):
    def __init__(
        self,
        message: str = "Authentication is required.",
    ):
        super().__init__(
            message,
            status_code=401,
            category="authentication",
        )


class APIAuthorizationError(APIError):
    def __init__(
        self,
        message: str = "Permission denied.",
    ):
        super().__init__(
            message,
            status_code=403,
            category="authorization",
        )


class APIResourceNotFoundError(APIError):
    def __init__(
        self,
        message: str = "Resource not found.",
    ):
        super().__init__(
            message,
            status_code=404,
            category="not_found",
        )


class APIConflictError(APIError):
    def __init__(
        self,
        message: str = "Resource conflict.",
    ):
        super().__init__(
            message,
            status_code=409,
            category="conflict",
        )


class APIRateLimitError(APIError):
    def __init__(
        self,
        message: str = "Rate limit exceeded.",
    ):
        super().__init__(
            message,
            status_code=429,
            category="rate_limit",
        )


class APIDatabaseError(APIError):
    def __init__(
        self,
        message: str = "Database operation failed.",
    ):
        super().__init__(
            message,
            status_code=500,
            category="database",
        )


class APIExternalServiceError(APIError):
    def __init__(
        self,
        message: str = "External service unavailable.",
    ):
        super().__init__(
            message,
            status_code=502,
            category="external_service",
        )


# ============================================================
# ERROR RESPONSE BUILDER
# ============================================================

def build_error_response(
    status_code: int,
    category: str = "unknown",
    message: Optional[str] = None,
    details: Optional[Any] = None,
    request_id: Optional[str] = None,
    debug: bool = False,
) -> Dict[str, Any]:

    status_code = _validate_status_code(status_code)
    category = _validate_category(category)

    correlation_id = request_id or str(uuid.uuid4())

    response_message = _safe_message(
        category=category,
        custom_message=message,
        debug=debug,
    )

    error_object = {
        "code": category.upper(),
        "message": response_message,
        "status": status_code,
        "status_text": HTTP_STATUS_MESSAGES.get(
            status_code,
            "HTTP Error",
        ),
        "request_id": correlation_id,
    }

    # Detailed errors should only be returned when they have
    # been explicitly sanitised for public exposure.
    if details is not None and debug:
        error_object["details"] = details

    return {
        "success": False,
        "error": error_object,
        "timestamp": _iso_now(),
    }


# ============================================================
# EXCEPTION CONVERSION
# ============================================================

def exception_to_response(
    exception: Exception,
    request_id: Optional[str] = None,
    debug: bool = False,
) -> Dict[str, Any]:

    if isinstance(exception, APIError):
        return build_error_response(
            status_code=exception.status_code,
            category=exception.category,
            message=exception.message,
            details=exception.details,
            request_id=request_id,
            debug=debug,
        )

    return build_error_response(
        status_code=500,
        category="server",
        message=str(exception),
        request_id=request_id,
        debug=debug,
    )


# ============================================================
# VALIDATION ERROR CONVERSION
# ============================================================

def validation_errors_to_response(
    errors: List[Dict[str, Any]],
    request_id: Optional[str] = None,
) -> Dict[str, Any]:

    if not isinstance(errors, list):
        raise ValueError("Validation errors must be a list.")

    sanitised_errors = []

    for item in errors:
        if not isinstance(item, dict):
            continue

        sanitised_errors.append({
            "field": str(item.get("field", "unknown"))[:200],
            "message": str(item.get("message", "Invalid value."))[:500],
        })

    return build_error_response(
        status_code=422,
        category="validation",
        message="One or more fields failed validation.",
        details={
            "validation_errors": sanitised_errors,
        },
        request_id=request_id,
        debug=True,
    )


# ============================================================
# ERROR LOGGING
# ============================================================

def log_api_error(
    exception: Exception,
    endpoint: Optional[str] = None,
    user_id: Optional[str] = None,
    request_id: Optional[str] = None,
    severity: str = "error",
) -> Dict[str, Any]:
    """
    Record an API error without storing arbitrary exception
    tracebacks or request payloads.

    Production logging should use a structured logging service.
    """

    if severity not in {"warning", "error", "critical"}:
        raise ValueError("Invalid error severity.")

    if isinstance(exception, APIError):
        category = exception.category
        status_code = exception.status_code
        message = exception.message
    else:
        category = "server"
        status_code = 500
        message = "An unexpected internal error occurred."

    record = {
        "id": str(uuid.uuid4()),
        "request_id": request_id or str(uuid.uuid4()),
        "endpoint": (
            str(endpoint)[:300]
            if endpoint
            else None
        ),
        "user_id": (
            str(user_id)
            if user_id is not None
            else None
        ),
        "category": category,
        "status_code": status_code,
        "severity": severity,
        "message": message[:1000],
        "created_at": _iso_now(),
    }

    _get_errors().append(record)

    return dict(record)


# ============================================================
# ERROR HISTORY
# ============================================================

def list_api_errors(
    category: Optional[str] = None,
    severity: Optional[str] = None,
    status_code: Optional[int] = None,
    user_id: Optional[str] = None,
    limit: int = 100,
) -> List[Dict[str, Any]]:

    if (
        isinstance(limit, bool)
        or not isinstance(limit, int)
        or limit < 1
        or limit > 1000
    ):
        raise ValueError(
            "Limit must be between 1 and 1000."
        )

    if category is not None:
        _validate_category(category)

    if severity is not None:
        if severity not in {"warning", "error", "critical"}:
            raise ValueError("Invalid severity.")

    results = []

    for record in _get_errors():

        if category is not None:
            if record["category"] != category:
                continue

        if severity is not None:
            if record["severity"] != severity:
                continue

        if status_code is not None:
            if record["status_code"] != status_code:
                continue

        if user_id is not None:
            if record["user_id"] != str(user_id):
                continue

        results.append(dict(record))

    results.sort(
        key=lambda item: item["created_at"],
        reverse=True,
    )

    return results[:limit]


# ============================================================
# ERROR STATISTICS
# ============================================================

def get_api_error_statistics() -> Dict[str, Any]:

    records = _get_errors()

    category_counts = {
        category: 0
        for category in ERROR_CATEGORIES
    }

    severity_counts = {
        "warning": 0,
        "error": 0,
        "critical": 0,
    }

    status_counts = {}

    for record in records:
        category_counts[record["category"]] += 1
        severity_counts[record["severity"]] += 1

        status = str(record["status_code"])

        status_counts[status] = (
            status_counts.get(status, 0) + 1
        )

    return {
        "total_errors": len(records),
        "category_counts": category_counts,
        "severity_counts": severity_counts,
        "status_code_counts": status_counts,
        "generated_at": _iso_now(),
    }


# ============================================================
# ERROR EXPORT
# ============================================================

def export_api_errors() -> List[Dict[str, Any]]:
    return [
        dict(record)
        for record in _get_errors()
    ]


def export_api_error_data() -> Dict[str, Any]:
    return {
        "errors": export_api_errors(),
        "statistics": get_api_error_statistics(),
        "exported_at": _iso_now(),
    }


# ============================================================
# ERROR CLEANUP
# ============================================================

def clear_api_errors() -> int:
    """
    Clear development error history.

    This is destructive and should only be called intentionally.
    """

    records = _get_errors()
    count = len(records)

    records.clear()

    return count
