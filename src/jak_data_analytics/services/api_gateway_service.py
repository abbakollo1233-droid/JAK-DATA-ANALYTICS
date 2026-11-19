
"""
JAK Data Analytics — API Gateway Service

Central API request authentication and validation.

Connects:
- api_key_service.py
- api_usage_service.py

Responsibilities:
- Authenticate API keys.
- Verify permission scopes.
- Check API usage limits.
- Validate request metadata.
- Record API activity.
- Generate standardized responses.

Development note:
This is a framework-independent gateway service.
It is not yet an HTTP server or middleware.
Integrate it with the API routing layer later.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional
from uuid import uuid4

from .api_key_service import verify_api_key
from .api_usage_service import (
    check_api_usage_limit,
    record_api_request,
)


class APIGatewayError(Exception):
    """Raised when API gateway processing fails."""


VALID_METHODS = {
    "GET",
    "POST",
    "PUT",
    "PATCH",
    "DELETE",
    "OPTIONS",
    "HEAD",
}

VALID_SCOPES = {
    "datasets:read",
    "datasets:write",
    "projects:read",
    "projects:write",
    "analysis:read",
    "analysis:run",
    "reports:read",
    "reports:write",
}


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _validate_text(
    value: Any,
    field_name: str,
    maximum_length: int = 200,
) -> str:
    """Validate a required text field."""
    if not isinstance(value, str):
        raise APIGatewayError(
            f"{field_name} must be a string."
        )

    value = value.strip()

    if not value:
        raise APIGatewayError(
            f"{field_name} is required."
        )

    if len(value) > maximum_length:
        raise APIGatewayError(
            f"{field_name} is too long."
        )

    return value


def create_api_response(
    success: bool,
    message: str,
    data: Any = None,
    error_code: Optional[str] = None,
    status_code: int = 200,
    request_id: Optional[str] = None,
) -> dict:
    """Create a standardized API response."""
    if (
        isinstance(status_code, bool)
        or not isinstance(status_code, int)
        or not 100 <= status_code <= 599
    ):
        raise APIGatewayError(
            "Invalid HTTP status code."
        )

    response = {
        "success": bool(success),
        "message": str(message),
        "data": data,
        "error": (
            {"code": error_code}
            if error_code
            else None
        ),
        "status_code": status_code,
        "request_id": request_id or str(uuid4()),
        "timestamp": _utc_now(),
    }

    return response


def _failure(
    message: str,
    status_code: int,
    error_code: str,
    request_id: str,
) -> dict:
    """Build a standardized failure response."""
    return create_api_response(
        success=False,
        message=message,
        error_code=error_code,
        status_code=status_code,
        request_id=request_id,
    )


def authenticate_api_request(
    api_key: str,
    required_scope: Optional[str] = None,
    check_usage_limit: bool = True,
) -> dict:
    """
    Authenticate an API key and verify permissions.

    Returns authentication information when successful.

    The API key must never be written to application logs.
    """
    if not isinstance(api_key, str) or not api_key.strip():
        return {
            "authenticated": False,
            "user": None,
            "error": "API key is required.",
            "status_code": 401,
        }

    if required_scope is not None:
        required_scope = required_scope.strip().lower()

        if required_scope not in VALID_SCOPES:
            return {
                "authenticated": False,
                "user": None,
                "error": "Unsupported permission scope.",
                "status_code": 400,
            }

    key_record = verify_api_key(
        api_key=api_key,
        required_scope=required_scope,
        update_last_used=True,
    )

    if key_record is None:
        return {
            "authenticated": False,
            "user": None,
            "error": "Invalid API key or insufficient permissions.",
            "status_code": 401,
        }

    user_id = key_record["user_id"]

    if check_usage_limit:
        usage_check = check_api_usage_limit(user_id)

        if not usage_check["allowed"]:
            return {
                "authenticated": False,
                "user": None,
                "error": usage_check["reason"],
                "status_code": 429,
                "usage": usage_check["consumption"],
            }

    return {
        "authenticated": True,
        "user": {
            "id": user_id,
            "api_key_id": key_record["id"],
            "api_key_name": key_record["name"],
            "scopes": key_record["scopes"],
        },
        "error": None,
        "status_code": 200,
    }


def authorize_api_action(
    authentication: dict,
    required_scope: str,
) -> bool:
    """Check whether an authenticated API identity has a scope."""
    if not isinstance(authentication, dict):
        return False

    if not authentication.get("authenticated"):
        return False

    required_scope = str(required_scope).strip().lower()

    if required_scope not in VALID_SCOPES:
        return False

    user = authentication.get("user")

    if not isinstance(user, dict):
        return False

    scopes = user.get("scopes", [])

    return required_scope in scopes


def validate_api_request(
    api_key: str,
    endpoint: str,
    method: str = "GET",
    required_scope: Optional[str] = None,
) -> dict:
    """
    Validate an API request before processing it.

    This function performs authentication and authorization.
    It does not execute the requested operation.
    """
    request_id = str(uuid4())

    try:
        endpoint = _validate_text(
            endpoint,
            "Endpoint",
            maximum_length=300,
        )

        method = _validate_text(
            method,
            "HTTP method",
            maximum_length=10,
        ).upper()

        if method not in VALID_METHODS:
            return _failure(
                "Unsupported HTTP method.",
                405,
                "METHOD_NOT_ALLOWED",
                request_id,
            )

        authentication = authenticate_api_request(
            api_key=api_key,
            required_scope=required_scope,
            check_usage_limit=True,
        )

        if not authentication["authenticated"]:
            status = authentication["status_code"]

            error_code = (
                "RATE_LIMIT_EXCEEDED"
                if status == 429
                else "AUTHENTICATION_FAILED"
            )

            return _failure(
                authentication["error"],
                status,
                error_code,
                request_id,
            )

        if required_scope and not authorize_api_action(
            authentication,
            required_scope,
        ):
            return _failure(
                "You do not have permission to perform this action.",
                403,
                "INSUFFICIENT_PERMISSION",
                request_id,
            )

        return {
            "valid": True,
            "request_id": request_id,
            "authentication": authentication,
            "endpoint": endpoint,
            "method": method,
            "required_scope": required_scope,
            "validated_at": _utc_now(),
        }

    except APIGatewayError as exc:
        return _failure(
            str(exc),
            400,
            "INVALID_REQUEST",
            request_id,
        )

    except Exception:
        return _failure(
            "Unable to validate API request.",
            500,
            "GATEWAY_ERROR",
            request_id,
        )


def record_gateway_request(
    validation_result: dict,
    status_code: int,
    response_time_ms: float = 0,
    request_size_bytes: int = 0,
    response_size_bytes: int = 0,
    error_category: Optional[str] = None,
) -> Optional[dict]:
    """
    Record a processed gateway request.

    Call this after the API operation finishes.
    Do not pass credentials or sensitive request content.
    """
    if not isinstance(validation_result, dict):
        raise APIGatewayError(
            "Invalid validation result."
        )

    if not validation_result.get("valid"):
        raise APIGatewayError(
            "Cannot record an unvalidated request."
        )

    authentication = validation_result.get(
        "authentication",
        {},
    )

    user = authentication.get("user")

    if not isinstance(user, dict):
        raise APIGatewayError(
            "Authenticated user information is missing."
        )

    try:
        return record_api_request(
            user_id=user["id"],
            api_key_id=user["api_key_id"],
            endpoint=validation_result["endpoint"],
            method=validation_result["method"],
            status_code=status_code,
            response_time_ms=response_time_ms,
            request_size_bytes=request_size_bytes,
            response_size_bytes=response_size_bytes,
            error_category=error_category,
        )

    except Exception as exc:
        raise APIGatewayError(
            "Unable to record API request."
        ) from exc


def process_api_result(
    validation_result: dict,
    data: Any = None,
    message: str = "Request completed successfully.",
    status_code: int = 200,
) -> dict:
    """
    Create a successful API response for a validated request.

    The actual API operation must be executed separately.
    """
    if not isinstance(validation_result, dict):
        raise APIGatewayError(
            "Invalid validation result."
        )

    if not validation_result.get("valid"):
        raise APIGatewayError(
            "Request has not passed gateway validation."
        )

    return create_api_response(
        success=True,
        message=message,
        data=data,
        status_code=status_code,
        request_id=validation_result["request_id"],
    )


def create_gateway_error(
    validation_result: Optional[dict],
    message: str,
    status_code: int = 400,
    error_code: str = "REQUEST_ERROR",
) -> dict:
    """Create a standardized API error response."""
    request_id = str(uuid4())

    if isinstance(validation_result, dict):
        request_id = validation_result.get(
            "request_id",
            request_id,
        )

    return _failure(
        message=message,
        status_code=status_code,
        error_code=error_code,
        request_id=request_id,
    )


def get_gateway_information() -> dict:
    """Return gateway configuration information."""
    return {
        "application": "JAK Data Analytics",
        "gateway": "JAK API Gateway",
        "version": "1.0.0",
        "authentication": "API Key",
        "authorization": "Permission Scopes",
        "usage_limits": True,
        "supported_methods": sorted(VALID_METHODS),
        "supported_scopes": sorted(VALID_SCOPES),
    }
