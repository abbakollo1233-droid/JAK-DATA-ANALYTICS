"""
JAK Data Analytics - API Response Service

Provides standard response structures for API endpoints.

Features:
- Standard success responses
- Paginated responses
- Response metadata
- Resource responses
- JSON-safe data conversion
- Consistent response envelopes
- Response validation
- Framework-independent implementation
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Any, Dict, List, Mapping, Optional
from uuid import UUID


API_RESPONSE_VERSION = "1.0"


@dataclass
class APIResponse:
    """Represents a standardised API response."""

    success: bool
    status_code: int
    message: str
    data: Any = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    errors: Optional[List[Dict[str, Any]]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert the response into a dictionary."""

        response = {
            "success": self.success,
            "status_code": self.status_code,
            "message": self.message,
            "data": self.data,
            "metadata": self.metadata,
        }

        if self.errors is not None:
            response["errors"] = self.errors

        return make_json_safe(response)

    def to_json(self, indent: Optional[int] = None) -> str:
        """Convert the response into JSON."""

        return json.dumps(
            self.to_dict(),
            ensure_ascii=False,
            indent=indent,
            allow_nan=False,
        )


def make_json_safe(value: Any) -> Any:
    """
    Convert common Python values into JSON-compatible values.

    This function does not attempt to expose private object attributes.
    """

    if value is None:
        return None

    if isinstance(value, (str, int, bool)):
        return value

    if isinstance(value, float):
        return value if math.isfinite(value) else None

    if isinstance(value, Decimal):
        return float(value) if value.is_finite() else None

    if isinstance(value, (datetime, date)):
        return value.isoformat()

    if isinstance(value, UUID):
        return str(value)

    if isinstance(value, Mapping):
        return {
            str(key): make_json_safe(item)
            for key, item in value.items()
        }

    if isinstance(value, (list, tuple, set)):
        return [make_json_safe(item) for item in value]

    if hasattr(value, "to_dict") and callable(value.to_dict):
        try:
            return make_json_safe(value.to_dict())
        except Exception:
            return str(value)

    # Support common NumPy scalar types without requiring NumPy.
    if hasattr(value, "item") and callable(value.item):
        try:
            return make_json_safe(value.item())
        except Exception:
            pass

    # Avoid exposing arbitrary object internals.
    return str(value)


def create_response_metadata(
    request_id: Optional[str] = None,
    api_version: Optional[str] = None,
    processing_time_ms: Optional[float] = None,
    extra: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Create standard metadata for an API response."""

    metadata = {
        "response_version": API_RESPONSE_VERSION,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    if request_id:
        metadata["request_id"] = str(request_id)

    if api_version:
        metadata["api_version"] = str(api_version)

    if processing_time_ms is not None:
        try:
            processing_time_ms = float(processing_time_ms)

            if (
                math.isfinite(processing_time_ms)
                and processing_time_ms >= 0
            ):
                metadata["processing_time_ms"] = round(
                    processing_time_ms,
                    3,
                )
        except (TypeError, ValueError):
            pass

    if extra:
        metadata["extra"] = make_json_safe(extra)

    return metadata


def build_success_response(
    data: Any = None,
    message: str = "Request completed successfully.",
    status_code: int = 200,
    request_id: Optional[str] = None,
    api_version: Optional[str] = None,
    processing_time_ms: Optional[float] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> APIResponse:
    """Build a standard successful response."""

    if not isinstance(status_code, int) or not 200 <= status_code < 300:
        raise ValueError("A successful response requires a 2xx status code.")

    response_metadata = create_response_metadata(
        request_id=request_id,
        api_version=api_version,
        processing_time_ms=processing_time_ms,
        extra=metadata,
    )

    return APIResponse(
        success=True,
        status_code=status_code,
        message=str(message),
        data=make_json_safe(data),
        metadata=response_metadata,
    )


def build_created_response(
    data: Any = None,
    message: str = "Resource created successfully.",
    **kwargs,
) -> APIResponse:
    """Build a 201 Created response."""

    return build_success_response(
        data=data,
        message=message,
        status_code=201,
        **kwargs,
    )


def build_no_content_response(
    message: str = "Request completed successfully.",
    **kwargs,
) -> APIResponse:
    """
    Build a successful response with no data.

    Uses a JSON response envelope with status code 200.
    """

    return build_success_response(
        data=None,
        message=message,
        status_code=200,
        **kwargs,
    )


def build_resource_response(
    resource: Any,
    resource_name: str,
    message: str = "Resource retrieved successfully.",
    **kwargs,
) -> APIResponse:
    """Build a response containing one named resource."""

    if not resource_name or not isinstance(resource_name, str):
        raise ValueError("A valid resource name is required.")

    return build_success_response(
        data={
            resource_name: make_json_safe(resource),
        },
        message=message,
        **kwargs,
    )


def build_collection_response(
    items: List[Any],
    collection_name: str = "items",
    message: str = "Records retrieved successfully.",
    **kwargs,
) -> APIResponse:
    """Build a response containing a collection of records."""

    if not isinstance(items, list):
        raise TypeError("Items must be provided as a list.")

    if not collection_name or not isinstance(collection_name, str):
        raise ValueError("A valid collection name is required.")

    return build_success_response(
        data={
            collection_name: make_json_safe(items),
            "count": len(items),
        },
        message=message,
        **kwargs,
    )


def build_paginated_response(
    items: List[Any],
    page: int,
    page_size: int,
    total_items: int,
    message: str = "Records retrieved successfully.",
    collection_name: str = "items",
    request_id: Optional[str] = None,
    api_version: Optional[str] = None,
    processing_time_ms: Optional[float] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> APIResponse:
    """
    Build a paginated API response.

    Page numbering starts at 1.
    """

    if not isinstance(items, list):
        raise TypeError("Items must be provided as a list.")

    if not isinstance(page, int) or isinstance(page, bool) or page < 1:
        raise ValueError("Page must be an integer greater than zero.")

    if (
        not isinstance(page_size, int)
        or isinstance(page_size, bool)
        or page_size < 1
    ):
        raise ValueError("Page size must be an integer greater than zero.")

    if (
        not isinstance(total_items, int)
        or isinstance(total_items, bool)
        or total_items < 0
    ):
        raise ValueError("Total items must be a non-negative integer.")

    if not collection_name or not isinstance(collection_name, str):
        raise ValueError("A valid collection name is required.")

    total_pages = math.ceil(total_items / page_size) if total_items else 0

    pagination = {
        "page": page,
        "page_size": page_size,
        "total_items": total_items,
        "total_pages": total_pages,
        "has_previous": page > 1 and total_pages > 0,
        "has_next": page < total_pages,
    }

    response_data = {
        collection_name: make_json_safe(items),
        "pagination": pagination,
    }

    return build_success_response(
        data=response_data,
        message=message,
        request_id=request_id,
        api_version=api_version,
        processing_time_ms=processing_time_ms,
        metadata=metadata,
    )


def build_error_response(
    message: str,
    status_code: int = 400,
    errors: Optional[List[Dict[str, Any]]] = None,
    request_id: Optional[str] = None,
    api_version: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> APIResponse:
    """
    Build a standard error response.

    Detailed errors should be sanitised before being passed here.
    Never include passwords, API keys, tokens, or other secrets.
    """

    if (
        not isinstance(status_code, int)
        or isinstance(status_code, bool)
        or not 400 <= status_code <= 599
    ):
        raise ValueError("An error response requires a 4xx or 5xx status code.")

    response_metadata = create_response_metadata(
        request_id=request_id,
        api_version=api_version,
        extra=metadata,
    )

    safe_errors = None

    if errors is not None:
        if not isinstance(errors, list):
            raise TypeError("Errors must be provided as a list.")

        safe_errors = make_json_safe(errors)

    return APIResponse(
        success=False,
        status_code=status_code,
        message=str(message),
        data=None,
        metadata=response_metadata,
        errors=safe_errors,
    )


def get_response_status(response: APIResponse) -> Dict[str, Any]:
    """Return a simple summary of an API response."""

    if not isinstance(response, APIResponse):
        raise TypeError("Expected an APIResponse instance.")

    return {
        "success": response.success,
        "status_code": response.status_code,
        "message": response.message,
    }


def validate_response(response: APIResponse) -> Dict[str, Any]:
    """Check whether a response follows the expected structure."""

    errors = []

    if not isinstance(response, APIResponse):
        return {
            "valid": False,
            "errors": ["Response must be an APIResponse instance."],
        }

    if not isinstance(response.success, bool):
        errors.append("The success field must be a boolean.")

    if not isinstance(response.status_code, int):
        errors.append("The status code must be an integer.")

    if not isinstance(response.message, str):
        errors.append("The message must be a string.")

    if not isinstance(response.metadata, dict):
        errors.append("Metadata must be a dictionary.")

    if response.success and not 200 <= response.status_code < 300:
        errors.append("Successful responses must use a 2xx status code.")

    if not response.success and not 400 <= response.status_code <= 599:
        errors.append("Error responses must use a 4xx or 5xx status code.")

    return {
        "valid": len(errors) == 0,
        "errors": errors,
    }


def response_to_json(
    response: APIResponse,
    indent: Optional[int] = None,
) -> str:
    """Convert an APIResponse object into JSON."""

    if not isinstance(response, APIResponse):
        raise TypeError("Expected an APIResponse instance.")

    return response.to_json(indent=indent)


def response_to_dict(response: APIResponse) -> Dict[str, Any]:
    """Convert an APIResponse object into a dictionary."""

    if not isinstance(response, APIResponse):
        raise TypeError("Expected an APIResponse instance.")

    return response.to_dict()


def create_pagination_links(
    page: int,
    total_pages: int,
    base_url: str,
    query_parameters: Optional[Dict[str, Any]] = None,
) -> Dict[str, Optional[str]]:
    """
    Generate previous, current, and next page links.

    The caller is responsible for URL encoding and validating base_url
    before exposing these links to clients.
    """

    if not isinstance(page, int) or isinstance(page, bool) or page < 1:
        raise ValueError("Page must be a positive integer.")

    if (
        not isinstance(total_pages, int)
        or isinstance(total_pages, bool)
        or total_pages < 0
    ):
        raise ValueError("Total pages must be a non-negative integer.")

    if not isinstance(base_url, str) or not base_url.strip():
        raise ValueError("A valid base URL is required.")

    parameters = dict(query_parameters or {})
    parameters.pop("page", None)

    def make_link(target_page: int) -> str:
        from urllib.parse import urlencode

        link_parameters = dict(parameters)
        link_parameters["page"] = target_page

        separator = "&" if "?" in base_url else "?"

        return (
            base_url
            + separator
            + urlencode(link_parameters, doseq=True)
        )

    return {
        "previous": (
            make_link(page - 1)
            if page > 1
            else None
        ),
        "current": make_link(page),
        "next": (
            make_link(page + 1)
            if page < total_pages
            else None
        ),
    }


# ---------------------------------------------------------
# BASIC USAGE EXAMPLES
# ---------------------------------------------------------

if __name__ == "__main__":

    # Example 1: Standard success response
    response = build_success_response(
        data={"name": "JAK Data Analytics"},
        message="Welcome to JAK Data Analytics.",
        request_id="REQ-001",
        api_version="v1",
    )

    print("SUCCESS RESPONSE:")
    print(response_to_json(response, indent=4))

    # Example 2: Paginated response
    records = [
        {"id": 1, "name": "Employee One"},
        {"id": 2, "name": "Employee Two"},
    ]

    paginated = build_paginated_response(
        items=records,
        page=1,
        page_size=10,
        total_items=25,
        collection_name="employees",
    )

    print("\nPAGINATED RESPONSE:")
    print(response_to_json(paginated, indent=4))

    # Example 3: Error response
    error = build_error_response(
        message="The requested dataset could not be found.",
        status_code=404,
        errors=[
            {
                "field": "dataset_id",
                "message": "Dataset does not exist.",
            }
        ],
    )

    print("\nERROR RESPONSE:")
    print(response_to_json(error, indent=4))

    # Example 4: Validate a response
    print("\nRESPONSE VALIDATION:")
    print(validate_response(response))
