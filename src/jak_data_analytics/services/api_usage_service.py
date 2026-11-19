"""
JAK Data Analytics — API Usage Service

Tracks API activity, request statistics, endpoint usage,
and API consumption limits.

Development implementation:
Records are stored in Streamlit session state.

Production requirements:
- Use a persistent database.
- Use Redis or another shared store for distributed quotas.
- Enforce quotas in the API middleware.
- Apply a retention policy to request logs.
"""

from __future__ import annotations

from collections import Counter
from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import uuid4

import streamlit as st


API_USAGE_STORE = "jak_api_usage_records"
API_LIMITS_STORE = "jak_api_usage_limits"


DEFAULT_DAILY_LIMIT = 1000
DEFAULT_MONTHLY_LIMIT = 20000


class APIUsageError(Exception):
    """Raised when API usage operations fail."""


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _get_records() -> list:
    """Return the API usage records."""
    if API_USAGE_STORE not in st.session_state:
        st.session_state[API_USAGE_STORE] = []

    return st.session_state[API_USAGE_STORE]


def _get_limits() -> dict:
    """Return configured API usage limits."""
    if API_LIMITS_STORE not in st.session_state:
        st.session_state[API_LIMITS_STORE] = {}

    return st.session_state[API_LIMITS_STORE]


def _parse_datetime(value: str) -> Optional[datetime]:
    """Parse an ISO datetime safely."""
    try:
        parsed = datetime.fromisoformat(value)

        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)

        return parsed.astimezone(timezone.utc)

    except (TypeError, ValueError):
        return None


def _normalize_identifier(
    value: str,
    field_name: str,
) -> str:
    """Validate an identifier."""
    if not isinstance(value, str) or not value.strip():
        raise APIUsageError(
            f"{field_name} is required."
        )

    value = value.strip()

    if len(value) > 150:
        raise APIUsageError(
            f"{field_name} cannot exceed 150 characters."
        )

    return value


def record_api_request(
    user_id: str,
    api_key_id: str,
    endpoint: str,
    method: str = "GET",
    status_code: int = 200,
    response_time_ms: float = 0,
    request_size_bytes: int = 0,
    response_size_bytes: int = 0,
    error_category: Optional[str] = None,
) -> dict:
    """
    Record one API request.

    Do not pass API keys, passwords, access tokens,
    personal request bodies, or other secrets.
    """
    user_id = _normalize_identifier(user_id, "User ID")

    api_key_id = _normalize_identifier(
        api_key_id,
        "API key ID",
    )

    endpoint = _normalize_identifier(
        endpoint,
        "Endpoint",
    )

    method = str(method).strip().upper()

    allowed_methods = {
        "GET",
        "POST",
        "PUT",
        "PATCH",
        "DELETE",
        "OPTIONS",
        "HEAD",
    }

    if method not in allowed_methods:
        raise APIUsageError("Unsupported HTTP method.")

    if (
        isinstance(status_code, bool)
        or not isinstance(status_code, int)
        or not 100 <= status_code <= 599
    ):
        raise APIUsageError(
            "HTTP status code must be between 100 and 599."
        )

    numeric_values = {
        "response_time_ms": response_time_ms,
        "request_size_bytes": request_size_bytes,
        "response_size_bytes": response_size_bytes,
    }

    for name, value in numeric_values.items():
        if isinstance(value, bool) or not isinstance(
            value, (int, float)
        ):
            raise APIUsageError(
                f"{name} must be numeric."
            )

        if value < 0:
            raise APIUsageError(
                f"{name} cannot be negative."
            )

    if (
        request_size_bytes != int(request_size_bytes)
        or response_size_bytes != int(response_size_bytes)
    ):
        raise APIUsageError(
            "Request and response sizes must be whole numbers."
        )

    if error_category is not None:
        error_category = str(error_category).strip()[:100]

    now = _utc_now()

    record = {
        "id": str(uuid4()),
        "user_id": user_id,
        "api_key_id": api_key_id,
        "endpoint": endpoint,
        "method": method,
        "status_code": status_code,
        "success": 200 <= status_code < 400,
        "response_time_ms": float(response_time_ms),
        "request_size_bytes": int(request_size_bytes),
        "response_size_bytes": int(response_size_bytes),
        "error_category": error_category,
        "created_at": now.isoformat(),
    }

    records = _get_records()
    records.append(record)

    return dict(record)


def get_api_usage_records(
    user_id: Optional[str] = None,
    api_key_id: Optional[str] = None,
    endpoint: Optional[str] = None,
    limit: int = 100,
    include_failed: bool = True,
) -> list[dict]:
    """Retrieve API usage records using optional filters."""
    if (
        isinstance(limit, bool)
        or not isinstance(limit, int)
        or limit < 1
        or limit > 10000
    ):
        raise APIUsageError(
            "Limit must be between 1 and 10000."
        )

    results = []

    for record in reversed(_get_records()):
        if user_id is not None:
            if record["user_id"] != str(user_id):
                continue

        if api_key_id is not None:
            if record["api_key_id"] != str(api_key_id):
                continue

        if endpoint is not None:
            if record["endpoint"] != endpoint:
                continue

        if not include_failed and not record["success"]:
            continue

        results.append(dict(record))

        if len(results) >= limit:
            break

    return results


def _filter_by_period(
    records: list,
    start: datetime,
    end: datetime,
) -> list:
    """Filter records between two UTC datetimes."""
    filtered = []

    for record in records:
        created_at = _parse_datetime(record["created_at"])

        if created_at is None:
            continue

        if start <= created_at <= end:
            filtered.append(record)

    return filtered


def get_api_usage_statistics(
    user_id: Optional[str] = None,
    days: int = 30,
) -> dict:
    """Calculate API usage statistics."""
    if (
        isinstance(days, bool)
        or not isinstance(days, int)
        or not 1 <= days <= 3650
    ):
        raise APIUsageError(
            "Days must be between 1 and 3650."
        )

    now = _utc_now()
    start = now - timedelta(days=days)

    records = get_api_usage_records(
        user_id=user_id,
        limit=10000,
    )

    period_records = _filter_by_period(
        records,
        start,
        now,
    )

    total = len(period_records)

    successful = sum(
        1 for record in period_records
        if record["success"]
    )

    failed = total - successful

    response_times = [
        record["response_time_ms"]
        for record in period_records
    ]

    average_response_time = (
        sum(response_times) / len(response_times)
        if response_times
        else 0
    )

    return {
        "period_days": days,
        "total_requests": total,
        "successful_requests": successful,
        "failed_requests": failed,
        "success_rate": (
            successful / total * 100
            if total
            else 0
        ),
        "failure_rate": (
            failed / total * 100
            if total
            else 0
        ),
        "average_response_time_ms": round(
            average_response_time,
            2,
        ),
        "total_request_bytes": sum(
            item["request_size_bytes"]
            for item in period_records
        ),
        "total_response_bytes": sum(
            item["response_size_bytes"]
            for item in period_records
        ),
    }


def get_endpoint_usage(
    user_id: Optional[str] = None,
    days: int = 30,
) -> list[dict]:
    """Calculate usage statistics grouped by endpoint."""
    now = _utc_now()
    start = now - timedelta(days=days)

    records = get_api_usage_records(
        user_id=user_id,
        limit=10000,
    )

    period_records = _filter_by_period(
        records,
        start,
        now,
    )

    grouped = {}

    for record in period_records:
        endpoint = record["endpoint"]

        if endpoint not in grouped:
            grouped[endpoint] = {
                "endpoint": endpoint,
                "requests": 0,
                "successful": 0,
                "failed": 0,
                "total_response_time_ms": 0,
            }

        item = grouped[endpoint]

        item["requests"] += 1
        item["total_response_time_ms"] += (
            record["response_time_ms"]
        )

        if record["success"]:
            item["successful"] += 1
        else:
            item["failed"] += 1

    results = []

    for item in grouped.values():
        count = item["requests"]

        item["average_response_time_ms"] = round(
            item["total_response_time_ms"] / count,
            2,
        )

        del item["total_response_time_ms"]

        results.append(item)

    return sorted(
        results,
        key=lambda item: item["requests"],
        reverse=True,
    )


def get_daily_api_usage(
    user_id: Optional[str] = None,
    days: int = 30,
) -> list[dict]:
    """Return daily API request counts."""
    if (
        isinstance(days, bool)
        or not isinstance(days, int)
        or not 1 <= days <= 3650
    ):
        raise APIUsageError(
            "Days must be between 1 and 3650."
        )

    now = _utc_now()
    start_date = (now - timedelta(days=days - 1)).date()

    records = get_api_usage_records(
        user_id=user_id,
        limit=10000,
    )

    counts = Counter()

    for record in records:
        created_at = _parse_datetime(record["created_at"])

        if created_at is None:
            continue

        day = created_at.date()

        if start_date <= day <= now.date():
            counts[day.isoformat()] += 1

    results = []

    for offset in range(days):
        day = start_date + timedelta(days=offset)

        results.append({
            "date": day.isoformat(),
            "requests": counts.get(day.isoformat(), 0),
        })

    return results


def set_api_usage_limits(
    user_id: str,
    daily_limit: int = DEFAULT_DAILY_LIMIT,
    monthly_limit: int = DEFAULT_MONTHLY_LIMIT,
) -> dict:
    """Set daily and monthly API request limits for a user."""
    user_id = _normalize_identifier(user_id, "User ID")

    for name, value in {
        "daily_limit": daily_limit,
        "monthly_limit": monthly_limit,
    }.items():
        if (
            isinstance(value, bool)
            or not isinstance(value, int)
            or value < 1
            or value > 10000000
        ):
            raise APIUsageError(
                f"{name} must be between 1 and 10000000."
            )

    if daily_limit > monthly_limit:
        raise APIUsageError(
            "Daily limit cannot exceed monthly limit."
        )

    limits = {
        "user_id": user_id,
        "daily_limit": daily_limit,
        "monthly_limit": monthly_limit,
        "updated_at": _utc_now().isoformat(),
    }

    _get_limits()[user_id] = limits

    return dict(limits)


def get_api_usage_limits(user_id: str) -> dict:
    """Retrieve usage limits for a user."""
    user_id = str(user_id)

    limits = _get_limits().get(user_id)

    if limits:
        return dict(limits)

    return {
        "user_id": user_id,
        "daily_limit": DEFAULT_DAILY_LIMIT,
        "monthly_limit": DEFAULT_MONTHLY_LIMIT,
        "updated_at": None,
    }


def get_current_api_consumption(
    user_id: str,
) -> dict:
    """Calculate daily and monthly API request consumption."""
    user_id = str(user_id)

    now = _utc_now()

    day_start = datetime(
        now.year,
        now.month,
        now.day,
        tzinfo=timezone.utc,
    )

    month_start = datetime(
        now.year,
        now.month,
        1,
        tzinfo=timezone.utc,
    )

    records = get_api_usage_records(
        user_id=user_id,
        limit=10000,
    )

    daily_records = _filter_by_period(
        records,
        day_start,
        now,
    )

    monthly_records = _filter_by_period(
        records,
        month_start,
        now,
    )

    limits = get_api_usage_limits(user_id)

    daily_used = len(daily_records)
    monthly_used = len(monthly_records)

    daily_limit = limits["daily_limit"]
    monthly_limit = limits["monthly_limit"]

    return {
        "user_id": user_id,
        "daily": {
            "used": daily_used,
            "limit": daily_limit,
            "remaining": max(
                daily_limit - daily_used,
                0,
            ),
            "usage_percentage": round(
                daily_used / daily_limit * 100,
                2,
            ),
            "exceeded": daily_used >= daily_limit,
        },
        "monthly": {
            "used": monthly_used,
            "limit": monthly_limit,
            "remaining": max(
                monthly_limit - monthly_used,
                0,
            ),
            "usage_percentage": round(
                monthly_used / monthly_limit * 100,
                2,
            ),
            "exceeded": monthly_used >= monthly_limit,
        },
    }


def check_api_usage_limit(
    user_id: str,
) -> dict:
    """
    Check whether a user can make another API request.

    Call this before processing an API request.

    Note:
    This check and request recording are not atomic.
    Production systems should enforce quotas through
    a shared transactional or atomic counter.
    """
    consumption = get_current_api_consumption(user_id)

    daily = consumption["daily"]
    monthly = consumption["monthly"]

    allowed = (
        not daily["exceeded"]
        and not monthly["exceeded"]
    )

    if daily["exceeded"]:
        reason = "Daily API request limit exceeded."
    elif monthly["exceeded"]:
        reason = "Monthly API request limit exceeded."
    else:
        reason = None

    return {
        "allowed": allowed,
        "reason": reason,
        "consumption": consumption,
    }


def get_api_usage_summary(
    user_id: str,
) -> dict:
    """Return a dashboard-ready usage summary."""
    statistics = get_api_usage_statistics(
        user_id=user_id,
        days=30,
    )

    consumption = get_current_api_consumption(
        user_id
    )

    return {
        "statistics": statistics,
        "daily_consumption": consumption["daily"],
        "monthly_consumption": consumption["monthly"],
        "top_endpoints": get_endpoint_usage(
            user_id=user_id,
            days=30,
        )[:5],
    }


def export_api_usage_records(
    user_id: Optional[str] = None,
    limit: int = 10000,
) -> list[dict]:
    """Export API usage records without secret credentials."""
    return get_api_usage_records(
        user_id=user_id,
        limit=limit,
        include_failed=True,
    )


def clear_api_usage_records(
    before: Optional[str] = None,
    user_id: Optional[str] = None,
) -> int:
    """
    Delete usage records before a specified ISO datetime.

    If before is omitted, all matching records are deleted.
    Use carefully because this operation cannot be undone.
    """
    cutoff = None

    if before is not None:
        cutoff = _parse_datetime(before)

        if cutoff is None:
            raise APIUsageError(
                "Invalid cutoff datetime."
            )

    records = _get_records()

    retained = []
    deleted_count = 0

    for record in records:
        matches_user = (
            user_id is None
            or record["user_id"] == str(user_id)
        )

        created_at = _parse_datetime(record["created_at"])

        matches_date = (
            cutoff is None
            or (
                created_at is not None
                and created_at < cutoff
            )
        )

        if matches_user and matches_date:
            deleted_count += 1
        else:
            retained.append(record)

    st.session_state[API_USAGE_STORE] = retained

    return deleted_count
