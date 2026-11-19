"""
JAK Data Analytics - API Request Validation Service

Validates incoming API request data.

Features:
- Required field validation.
- String, number, integer and boolean validation.
- Email validation.
- URL validation.
- Date and datetime validation.
- Enumeration validation.
- Nested object validation.
- List validation.
- Pagination validation.
- Request payload size validation.
- Structured validation errors.

This service is framework-independent.

Security:
- Validation is not authorization.
- Never trust client-side validation alone.
- Apply request size limits at the HTTP server or gateway.
- Sanitize data before displaying it in HTML.
"""

from __future__ import annotations

import json
import math
import re

from datetime import date, datetime, timezone
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse


# ============================================================
# CONSTANTS
# ============================================================

DEFAULT_PAGE = 1
DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 200
MAX_PAYLOAD_SIZE = 1_000_000

EMAIL_PATTERN = re.compile(
    r"^[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+"
    r"@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+$"
)


# ============================================================
# VALIDATION RESULT
# ============================================================

def validation_result(
    valid: bool,
    errors: Optional[List[Dict[str, str]]] = None,
    data: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:

    errors = errors or []

    return {
        "valid": valid,
        "success": valid,
        "errors": errors,
        "error_count": len(errors),
        "data": data,
    }


def _add_error(
    errors: List[Dict[str, str]],
    field: str,
    message: str,
) -> None:

    errors.append({
        "field": field,
        "message": message,
    })


# ============================================================
# GENERAL HELPERS
# ============================================================

def _is_number(value: Any) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(value)
    )


def _is_integer(value: Any) -> bool:
    return (
        isinstance(value, int)
        and not isinstance(value, bool)
    )


def _check_required(
    data: Dict[str, Any],
    field: str,
    errors: List[Dict[str, str]],
) -> bool:

    if field not in data or data[field] is None:
        _add_error(
            errors,
            field,
            "This field is required.",
        )
        return False

    if isinstance(data[field], str) and not data[field].strip():
        _add_error(
            errors,
            field,
            "This field cannot be empty.",
        )
        return False

    return True


# ============================================================
# BASIC FIELD VALIDATORS
# ============================================================

def validate_string(
    value: Any,
    field: str = "value",
    required: bool = False,
    minimum_length: int = 0,
    maximum_length: int = 10000,
    pattern: Optional[str] = None,
    allow_empty: bool = False,
) -> List[Dict[str, str]]:

    errors = []

    if value is None:
        if required:
            _add_error(errors, field, "This field is required.")
        return errors

    if not isinstance(value, str):
        _add_error(errors, field, "Must be a string.")
        return errors

    if not allow_empty and not value.strip():
        _add_error(errors, field, "Cannot be empty.")
        return errors

    if len(value) < minimum_length:
        _add_error(
            errors,
            field,
            f"Must contain at least {minimum_length} characters.",
        )

    if len(value) > maximum_length:
        _add_error(
            errors,
            field,
            f"Cannot exceed {maximum_length} characters.",
        )

    if pattern is not None:
        try:
            if not re.fullmatch(pattern, value):
                _add_error(
                    errors,
                    field,
                    "Does not match the required format.",
                )
        except re.error:
            _add_error(
                errors,
                field,
                "Validator configuration contains an invalid pattern.",
            )

    return errors


def validate_integer(
    value: Any,
    field: str = "value",
    required: bool = False,
    minimum: Optional[int] = None,
    maximum: Optional[int] = None,
) -> List[Dict[str, str]]:

    errors = []

    if value is None:
        if required:
            _add_error(errors, field, "This field is required.")
        return errors

    if not _is_integer(value):
        _add_error(errors, field, "Must be an integer.")
        return errors

    if minimum is not None and value < minimum:
        _add_error(
            errors,
            field,
            f"Must be at least {minimum}.",
        )

    if maximum is not None and value > maximum:
        _add_error(
            errors,
            field,
            f"Cannot exceed {maximum}.",
        )

    return errors


def validate_number(
    value: Any,
    field: str = "value",
    required: bool = False,
    minimum: Optional[float] = None,
    maximum: Optional[float] = None,
) -> List[Dict[str, str]]:

    errors = []

    if value is None:
        if required:
            _add_error(errors, field, "This field is required.")
        return errors

    if not _is_number(value):
        _add_error(
            errors,
            field,
            "Must be a finite number.",
        )
        return errors

    if minimum is not None and value < minimum:
        _add_error(
            errors,
            field,
            f"Must be at least {minimum}.",
        )

    if maximum is not None and value > maximum:
        _add_error(
            errors,
            field,
            f"Cannot exceed {maximum}.",
        )

    return errors


def validate_boolean(
    value: Any,
    field: str = "value",
    required: bool = False,
) -> List[Dict[str, str]]:

    errors = []

    if value is None:
        if required:
            _add_error(errors, field, "This field is required.")
        return errors

    if not isinstance(value, bool):
        _add_error(errors, field, "Must be a boolean.")

    return errors


# ============================================================
# EMAIL VALIDATION
# ============================================================

def validate_email(
    email: Any,
    field: str = "email",
    required: bool = True,
) -> List[Dict[str, str]]:

    errors = []

    if email is None:
        if required:
            _add_error(errors, field, "Email is required.")
        return errors

    if not isinstance(email, str):
        _add_error(errors, field, "Email must be a string.")
        return errors

    email = email.strip()

    if not email:
        if required:
            _add_error(errors, field, "Email is required.")
        return errors

    if len(email) > 254:
        _add_error(
            errors,
            field,
            "Email address is too long.",
        )
        return errors

    if not EMAIL_PATTERN.fullmatch(email):
        _add_error(
            errors,
            field,
            "Enter a valid email address.",
        )

    return errors


# ============================================================
# URL VALIDATION
# ============================================================

def validate_url(
    url: Any,
    field: str = "url",
    required: bool = True,
    require_https: bool = False,
) -> List[Dict[str, str]]:

    errors = []

    if url is None:
        if required:
            _add_error(errors, field, "URL is required.")
        return errors

    if not isinstance(url, str):
        _add_error(errors, field, "URL must be a string.")
        return errors

    url = url.strip()

    if not url:
        if required:
            _add_error(errors, field, "URL is required.")
        return errors

    try:
        parsed = urlparse(url)

        allowed_schemes = (
            {"https"}
            if require_https
            else {"http", "https"}
        )

        if parsed.scheme.lower() not in allowed_schemes:
            _add_error(
                errors,
                field,
                "URL must use an allowed HTTP or HTTPS scheme.",
            )

        if not parsed.hostname:
            _add_error(
                errors,
                field,
                "URL must contain a hostname.",
            )

        if parsed.username or parsed.password:
            _add_error(
                errors,
                field,
                "URL must not contain embedded credentials.",
            )

    except ValueError:
        _add_error(
            errors,
            field,
            "Invalid URL format.",
        )

    return errors


# ============================================================
# DATE VALIDATION
# ============================================================

def validate_date(
    value: Any,
    field: str = "date",
    required: bool = False,
) -> List[Dict[str, str]]:

    errors = []

    if value is None:
        if required:
            _add_error(errors, field, "Date is required.")
        return errors

    if isinstance(value, datetime):
        _add_error(
            errors,
            field,
            "Expected a date without a time component.",
        )
        return errors

    if isinstance(value, date):
        return errors

    if not isinstance(value, str):
        _add_error(errors, field, "Invalid date format.")
        return errors

    try:
        date.fromisoformat(value)
    except ValueError:
        _add_error(
            errors,
            field,
            "Date must use YYYY-MM-DD format.",
        )

    return errors


def validate_datetime(
    value: Any,
    field: str = "datetime",
    required: bool = False,
    require_timezone: bool = True,
) -> List[Dict[str, str]]:

    errors = []

    if value is None:
        if required:
            _add_error(errors, field, "Datetime is required.")
        return errors

    if isinstance(value, datetime):
        parsed = value

    elif isinstance(value, str):
        try:
            parsed = datetime.fromisoformat(
                value.replace("Z", "+00:00")
            )
        except ValueError:
            _add_error(
                errors,
                field,
                "Datetime must use a valid ISO 8601 format.",
            )
            return errors

    else:
        _add_error(
            errors,
            field,
            "Datetime must be an ISO 8601 string or datetime object.",
        )
        return errors

    if require_timezone and parsed.tzinfo is None:
        _add_error(
            errors,
            field,
            "Datetime must include a timezone.",
        )

    return errors


# ============================================================
# ENUMERATION VALIDATION
# ============================================================

def validate_choice(
    value: Any,
    choices: List[Any],
    field: str = "value",
    required: bool = False,
    case_sensitive: bool = True,
) -> List[Dict[str, str]]:

    errors = []

    if value is None:
        if required:
            _add_error(errors, field, "This field is required.")
        return errors

    if not isinstance(choices, (list, tuple, set)):
        raise ValueError("Choices must be a list, tuple, or set.")

    if case_sensitive:
        valid = value in choices
    else:
        valid = (
            isinstance(value, str)
            and any(
                isinstance(choice, str)
                and value.lower() == choice.lower()
                for choice in choices
            )
        )

    if not valid:
        _add_error(
            errors,
            field,
            "Value must be one of the permitted choices.",
        )

    return errors


# ============================================================
# LIST VALIDATION
# ============================================================

def validate_list(
    value: Any,
    field: str = "items",
    required: bool = False,
    minimum_items: int = 0,
    maximum_items: int = 1000,
    allowed_item_type: Optional[type] = None,
) -> List[Dict[str, str]]:

    errors = []

    if value is None:
        if required:
            _add_error(errors, field, "This field is required.")
        return errors

    if not isinstance(value, list):
        _add_error(errors, field, "Must be a list.")
        return errors

    if len(value) < minimum_items:
        _add_error(
            errors,
            field,
            f"Must contain at least {minimum_items} items.",
        )

    if len(value) > maximum_items:
        _add_error(
            errors,
            field,
            f"Cannot contain more than {maximum_items} items.",
        )

    if allowed_item_type is not None:
        for index, item in enumerate(value):
            if not isinstance(item, allowed_item_type):
                _add_error(
                    errors,
                    f"{field}[{index}]",
                    f"Must be of type {allowed_item_type.__name__}.",
                )

    return errors


# ============================================================
# NESTED OBJECT VALIDATION
# ============================================================

def validate_object(
    value: Any,
    schema: Dict[str, Dict[str, Any]],
    field: str = "object",
) -> List[Dict[str, str]]:

    errors = []

    if not isinstance(value, dict):
        _add_error(
            errors,
            field,
            "Must be an object.",
        )
        return errors

    if not isinstance(schema, dict):
        raise ValueError("Schema must be a dictionary.")

    for field_name, rules in schema.items():

        if not isinstance(rules, dict):
            raise ValueError(
                f"Invalid validation rules for {field_name}."
            )

        field_value = value.get(field_name)

        field_type = rules.get("type", str)
        required = rules.get("required", False)

        if field_value is None:
            if required:
                _add_error(
                    errors,
                    f"{field}.{field_name}",
                    "This field is required.",
                )
            continue

        if field_type is str:
            field_errors = validate_string(
                field_value,
                field=f"{field}.{field_name}",
                minimum_length=rules.get("minimum_length", 0),
                maximum_length=rules.get("maximum_length", 10000),
            )

        elif field_type is int:
            field_errors = validate_integer(
                field_value,
                field=f"{field}.{field_name}",
                minimum=rules.get("minimum"),
                maximum=rules.get("maximum"),
            )

        elif field_type is float:
            field_errors = validate_number(
                field_value,
                field=f"{field}.{field_name}",
                minimum=rules.get("minimum"),
                maximum=rules.get("maximum"),
            )

        elif field_type is bool:
            field_errors = validate_boolean(
                field_value,
                field=f"{field}.{field_name}",
            )

        elif field_type is dict:
            field_errors = validate_object(
                field_value,
                rules.get("schema", {}),
                field=f"{field}.{field_name}",
            )

        else:
            raise ValueError(
                f"Unsupported schema type for {field_name}."
            )

        errors.extend(field_errors)

    if not rules_allow_extra_fields(schema):
        allowed_fields = set(schema.keys())

        for extra_field in value.keys() - allowed_fields:
            _add_error(
                errors,
                f"{field}.{extra_field}",
                "Unexpected field.",
            )

    return errors


def rules_allow_extra_fields(
    schema: Dict[str, Dict[str, Any]],
) -> bool:
    """
    Extra fields are rejected unless the schema explicitly
    declares allow_extra_fields=True.
    """

    return schema.get(
        "__options__",
        {},
    ).get("allow_extra_fields", False)


# ============================================================
# PAGINATION VALIDATION
# ============================================================

def validate_pagination(
    page: Any = DEFAULT_PAGE,
    page_size: Any = DEFAULT_PAGE_SIZE,
) -> Dict[str, Any]:

    errors = []

    errors.extend(
        validate_integer(
            page,
            field="page",
            required=True,
            minimum=1,
        )
    )

    errors.extend(
        validate_integer(
            page_size,
            field="page_size",
            required=True,
            minimum=1,
            maximum=MAX_PAGE_SIZE,
        )
    )

    if errors:
        return validation_result(False, errors)

    return validation_result(
        True,
        data={
            "page": page,
            "page_size": page_size,
            "offset": (page - 1) * page_size,
            "limit": page_size,
        },
    )


# ============================================================
# REQUEST PAYLOAD VALIDATION
# ============================================================

def validate_payload_size(
    payload: Any,
    maximum_bytes: int = MAX_PAYLOAD_SIZE,
) -> List[Dict[str, str]]:

    errors = []

    if (
        isinstance(maximum_bytes, bool)
        or not isinstance(maximum_bytes, int)
        or maximum_bytes < 1
    ):
        raise ValueError(
            "Maximum payload size must be a positive integer."
        )

    try:
        serialized = json.dumps(
            payload,
            ensure_ascii=False,
            default=str,
        )

        size = len(serialized.encode("utf-8"))

    except (TypeError, ValueError):
        _add_error(
            errors,
            "payload",
            "Payload cannot be serialized.",
        )
        return errors

    if size > maximum_bytes:
        _add_error(
            errors,
            "payload",
            f"Payload exceeds the maximum size of {maximum_bytes} bytes.",
        )

    return errors


# ============================================================
# GENERIC SCHEMA VALIDATION
# ============================================================

def validate_request(
    data: Dict[str, Any],
    schema: Dict[str, Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Validate a request dictionary against a simple schema.

    Supported types:
        string
        integer
        number
        boolean
        email
        url
        date
        datetime
        list
        object
    """

    if not isinstance(data, dict):
        return validation_result(
            False,
            [{
                "field": "request",
                "message": "Request data must be an object.",
            }],
        )

    if not isinstance(schema, dict):
        raise ValueError("Schema must be a dictionary.")

    errors = []

    for field, rules in schema.items():

        if field == "__options__":
            continue

        if not isinstance(rules, dict):
            raise ValueError(
                f"Invalid rules for field '{field}'."
            )

        required = rules.get("required", False)

        if field not in data or data[field] is None:
            if required:
                _add_error(
                    errors,
                    field,
                    "This field is required.",
                )
            continue

        value = data[field]
        field_type = rules.get("type", "string")

        if field_type == "string":
            field_errors = validate_string(
                value,
                field=field,
                minimum_length=rules.get("minimum_length", 0),
                maximum_length=rules.get("maximum_length", 10000),
                pattern=rules.get("pattern"),
                allow_empty=rules.get("allow_empty", False),
            )

        elif field_type == "integer":
            field_errors = validate_integer(
                value,
                field=field,
                minimum=rules.get("minimum"),
                maximum=rules.get("maximum"),
            )

        elif field_type == "number":
            field_errors = validate_number(
                value,
                field=field,
                minimum=rules.get("minimum"),
                maximum=rules.get("maximum"),
            )

        elif field_type == "boolean":
            field_errors = validate_boolean(
                value,
                field=field,
            )

        elif field_type == "email":
            field_errors = validate_email(
                value,
                field=field,
                required=False,
            )

        elif field_type == "url":
            field_errors = validate_url(
                value,
                field=field,
                required=False,
                require_https=rules.get("require_https", False),
            )

        elif field_type == "date":
            field_errors = validate_date(
                value,
                field=field,
            )

        elif field_type == "datetime":
            field_errors = validate_datetime(
                value,
                field=field,
                require_timezone=rules.get(
                    "require_timezone",
                    True,
                ),
            )

        elif field_type == "choice":
            field_errors = validate_choice(
                value,
                choices=rules.get("choices", []),
                field=field,
                case_sensitive=rules.get(
                    "case_sensitive",
                    True,
                ),
            )

        elif field_type == "list":
            field_errors = validate_list(
                value,
                field=field,
                minimum_items=rules.get("minimum_items", 0),
                maximum_items=rules.get("maximum_items", 1000),
            )

        elif field_type == "object":
            field_errors = validate_object(
                value,
                schema=rules.get("schema", {}),
                field=field,
            )

        else:
            raise ValueError(
                f"Unsupported validation type: {field_type}"
            )

        errors.extend(field_errors)

    if not rules_allow_extra_fields(schema):
        allowed_fields = {
            field
            for field in schema
            if field != "__options__"
        }

        for extra_field in data.keys() - allowed_fields:
            _add_error(
                errors,
                str(extra_field),
                "Unexpected field.",
            )

    return validation_result(
        valid=not errors,
        errors=errors,
        data=data if not errors else None,
    )


# ============================================================
# DATE RANGE VALIDATION
# ============================================================

def validate_date_range(
    start_date: Any,
    end_date: Any,
    allow_same_date: bool = True,
) -> Dict[str, Any]:

    errors = []

    start_errors = validate_date(
        start_date,
        field="start_date",
        required=True,
    )

    end_errors = validate_date(
        end_date,
        field="end_date",
        required=True,
    )

    errors.extend(start_errors)
    errors.extend(end_errors)

    if errors:
        return validation_result(False, errors)

    start = (
        start_date
        if isinstance(start_date, date)
        else date.fromisoformat(start_date)
    )

    end = (
        end_date
        if isinstance(end_date, date)
        else date.fromisoformat(end_date)
    )

    if start > end:
        _add_error(
            errors,
            "date_range",
            "Start date must be before end date.",
        )

    elif not allow_same_date and start == end:
        _add_error(
            errors,
            "date_range",
            "Start and end dates must be different.",
        )

    return validation_result(
        valid=not errors,
        errors=errors,
        data={
            "start_date": start.isoformat(),
            "end_date": end.isoformat(),
        } if not errors else None,
    )
