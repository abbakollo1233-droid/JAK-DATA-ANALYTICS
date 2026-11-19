"""
JAK Data Analytics — API Documentation Service

Manages API endpoint documentation and generates
an OpenAPI-compatible specification.

Features:
- Endpoint registration
- HTTP method documentation
- Authentication documentation
- Permission scope documentation
- Request parameter definitions
- Request body definitions
- Response definitions
- OpenAPI specification generation
- JSON documentation export

Development implementation:
Endpoint definitions are stored in Streamlit session state.

Production recommendation:
Keep the API specification version-controlled and ensure
documented endpoints match the actual API routes.
"""

from __future__ import annotations

import json
import re

from copy import deepcopy
from datetime import datetime, timezone
from typing import Any, Optional


try:
    import streamlit as st
except ImportError:
    st = None


DOCUMENTATION_STORE = "jak_api_documentation"
DOCUMENTATION_INFO_STORE = "jak_api_documentation_info"


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


class APIDocumentationError(Exception):
    """Raised when API documentation operations fail."""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _get_store() -> dict:
    if st is None:
        raise APIDocumentationError(
            "Streamlit is required for the development documentation store."
        )

    if DOCUMENTATION_STORE not in st.session_state:
        st.session_state[DOCUMENTATION_STORE] = {}

    return st.session_state[DOCUMENTATION_STORE]


def _get_info() -> dict:
    if st is None:
        raise APIDocumentationError(
            "Streamlit is required for the development documentation store."
        )

    if DOCUMENTATION_INFO_STORE not in st.session_state:
        st.session_state[DOCUMENTATION_INFO_STORE] = {
            "title": "JAK Data Analytics API",
            "description": (
                "API services for JAK Data Analytics, "
                "including datasets, projects, analysis, and reports."
            ),
            "version": "1.0.0",
            "contact_email": None,
            "terms_of_service": None,
            "updated_at": _now(),
        }

    return st.session_state[DOCUMENTATION_INFO_STORE]


def _validate_text(
    value: str,
    field_name: str,
    maximum_length: int = 300,
    allow_empty: bool = False,
) -> str:
    if not isinstance(value, str):
        raise APIDocumentationError(
            f"{field_name} must be text."
        )

    value = value.strip()

    if not allow_empty and not value:
        raise APIDocumentationError(
            f"{field_name} is required."
        )

    if len(value) > maximum_length:
        raise APIDocumentationError(
            f"{field_name} cannot exceed {maximum_length} characters."
        )

    return value


def _validate_path(path: str) -> str:
    """Validate an API path."""
    path = _validate_text(
        path,
        "Endpoint path",
        maximum_length=300,
    )

    if not path.startswith("/"):
        raise APIDocumentationError(
            "API endpoint paths must start with '/'."
        )

    if "?" in path or "#" in path:
        raise APIDocumentationError(
            "Paths must not contain query strings or fragments."
        )

    if "//" in path:
        raise APIDocumentationError(
            "Paths cannot contain repeated slashes."
        )

    if not re.fullmatch(
        r"/[A-Za-z0-9_./{}\-]*",
        path,
    ):
        raise APIDocumentationError(
            "Endpoint path contains unsupported characters."
        )

    if ".." in path.split("/"):
        raise APIDocumentationError(
            "Endpoint path cannot contain parent-directory segments."
        )

    return path


def _validate_schema(schema: dict, depth: int = 0) -> dict:
    """
    Validate a basic JSON Schema structure.

    This is a lightweight structural check, not a complete
    JSON Schema validator.
    """
    if depth > 10:
        raise APIDocumentationError(
            "Schema nesting exceeds the maximum allowed depth."
        )

    if not isinstance(schema, dict):
        raise APIDocumentationError(
            "Schema definitions must be dictionaries."
        )

    allowed_types = {
        "object",
        "array",
        "string",
        "integer",
        "number",
        "boolean",
    }

    result = deepcopy(schema)

    schema_type = result.get("type")

    if schema_type is not None and schema_type not in allowed_types:
        raise APIDocumentationError(
            f"Unsupported schema type: {schema_type}"
        )

    properties = result.get("properties", {})

    if properties:
        if not isinstance(properties, dict):
            raise APIDocumentationError(
                "Schema properties must be a dictionary."
            )

        result["properties"] = {
            key: _validate_schema(value, depth + 1)
            for key, value in properties.items()
        }

    if "items" in result:
        result["items"] = _validate_schema(
            result["items"],
            depth + 1,
        )

    required = result.get("required", [])

    if not isinstance(required, list):
        raise APIDocumentationError(
            "Schema required fields must be a list."
        )

    if properties:
        unknown = set(required) - set(properties)

        if unknown:
            raise APIDocumentationError(
                "Required fields must exist in schema properties."
            )

    return result


def _validate_responses(responses: dict) -> dict:
    """Validate endpoint response documentation."""
    if not isinstance(responses, dict) or not responses:
        raise APIDocumentationError(
            "At least one response definition is required."
        )

    validated = {}

    for status_code, response in responses.items():
        code = str(status_code)

        if not code.isdigit() or not 100 <= int(code) <= 599:
            raise APIDocumentationError(
                f"Invalid response status code: {code}"
            )

        if not isinstance(response, dict):
            raise APIDocumentationError(
                "Each response definition must be a dictionary."
            )

        description = _validate_text(
            response.get("description", ""),
            "Response description",
            maximum_length=500,
        )

        item = {
            "description": description,
        }

        if "schema" in response:
            item["schema"] = _validate_schema(
                response["schema"]
            )

        validated[code] = item

    return validated


def _validate_parameters(parameters: list) -> list:
    """Validate documented endpoint parameters."""
    if not isinstance(parameters, list):
        raise APIDocumentationError(
            "Parameters must be supplied as a list."
        )

    validated = []

    allowed_locations = {
        "query",
        "path",
        "header",
        "cookie",
    }

    for parameter in parameters:
        if not isinstance(parameter, dict):
            raise APIDocumentationError(
                "Each parameter must be a dictionary."
            )

        name = _validate_text(
            parameter.get("name", ""),
            "Parameter name",
            maximum_length=100,
        )

        location = parameter.get("in", "query")

        if location not in allowed_locations:
            raise APIDocumentationError(
                f"Invalid parameter location: {location}"
            )

        description = _validate_text(
            parameter.get("description", ""),
            "Parameter description",
            maximum_length=500,
            allow_empty=True,
        )

        schema = _validate_schema(
            parameter.get(
                "schema",
                {"type": "string"},
            )
        )

        validated.append({
            "name": name,
            "in": location,
            "description": description,
            "required": bool(
                parameter.get(
                    "required",
                    location == "path",
                )
            ),
            "schema": schema,
        })

    return validated


def update_api_information(
    title: Optional[str] = None,
    description: Optional[str] = None,
    version: Optional[str] = None,
    contact_email: Optional[str] = None,
    terms_of_service: Optional[str] = None,
) -> dict:
    """Update the general API documentation information."""
    info = deepcopy(_get_info())

    if title is not None:
        info["title"] = _validate_text(
            title,
            "API title",
            maximum_length=150,
        )

    if description is not None:
        info["description"] = _validate_text(
            description,
            "API description",
            maximum_length=2000,
        )

    if version is not None:
        info["version"] = _validate_text(
            version,
            "API version",
            maximum_length=50,
        )

    if contact_email is not None:
        contact_email = _validate_text(
            contact_email,
            "Contact email",
            maximum_length=254,
        )

        if not re.fullmatch(
            r"[^@\s]+@[^@\s]+\.[^@\s]+",
            contact_email,
        ):
            raise APIDocumentationError(
                "Invalid contact email address."
            )

        info["contact_email"] = contact_email

    if terms_of_service is not None:
        info["terms_of_service"] = _validate_text(
            terms_of_service,
            "Terms of service URL",
            maximum_length=500,
        )

    info["updated_at"] = _now()

    st.session_state[DOCUMENTATION_INFO_STORE] = info

    return deepcopy(info)


def register_api_endpoint(
    path: str,
    method: str,
    summary: str,
    description: str = "",
    tags: Optional[list[str]] = None,
    parameters: Optional[list[dict]] = None,
    request_schema: Optional[dict] = None,
    responses: Optional[dict] = None,
    authenticated: bool = True,
    required_scope: Optional[str] = None,
    deprecated: bool = False,
) -> dict:
    """
    Register or update an API endpoint.

    Example:
        register_api_endpoint(
            path="/datasets",
            method="GET",
            summary="List datasets",
            required_scope="datasets:read",
            responses={
                "200": {
                    "description": "Datasets returned successfully."
                }
            }
        )
    """
    path = _validate_path(path)

    method = _validate_text(
        method,
        "HTTP method",
        maximum_length=10,
    ).upper()

    if method not in VALID_METHODS:
        raise APIDocumentationError(
            "Unsupported HTTP method."
        )

    summary = _validate_text(
        summary,
        "Endpoint summary",
        maximum_length=200,
    )

    description = _validate_text(
        description,
        "Endpoint description",
        maximum_length=2000,
        allow_empty=True,
    )

    if tags is None:
        tags = ["General"]

    if not isinstance(tags, list):
        raise APIDocumentationError(
            "Tags must be supplied as a list."
        )

    validated_tags = [
        _validate_text(tag, "Tag", maximum_length=50)
        for tag in tags
    ]

    validated_parameters = _validate_parameters(
        parameters or []
    )

    validated_request_schema = None

    if request_schema is not None:
        validated_request_schema = _validate_schema(
            request_schema
        )

    if responses is None:
        responses = {
            "200": {
                "description": "Request completed successfully."
            },
            "400": {
                "description": "Invalid request."
            },
        }

    validated_responses = _validate_responses(responses)

    if required_scope is not None:
        required_scope = _validate_text(
            required_scope,
            "Required permission scope",
            maximum_length=100,
        ).lower()

        if required_scope not in VALID_SCOPES:
            raise APIDocumentationError(
                "Unsupported permission scope."
            )

    if not isinstance(authenticated, bool):
        raise APIDocumentationError(
            "Authenticated must be True or False."
        )

    if not isinstance(deprecated, bool):
        raise APIDocumentationError(
            "Deprecated must be True or False."
        )

    if required_scope and not authenticated:
        raise APIDocumentationError(
            "A required permission scope needs authentication."
        )

    key = f"{method}:{path}"

    record = {
        "path": path,
        "method": method,
        "summary": summary,
        "description": description,
        "tags": validated_tags,
        "parameters": validated_parameters,
        "request_schema": validated_request_schema,
        "responses": validated_responses,
        "authenticated": authenticated,
        "required_scope": required_scope,
        "deprecated": deprecated,
        "updated_at": _now(),
    }

    _get_store()[key] = record

    return deepcopy(record)


def remove_api_endpoint(
    path: str,
    method: str,
) -> bool:
    """Remove an endpoint from the documentation registry."""
    path = _validate_path(path)

    method = _validate_text(
        method,
        "HTTP method",
        maximum_length=10,
    ).upper()

    key = f"{method}:{path}"

    return _get_store().pop(key, None) is not None


def get_api_endpoint(
    path: str,
    method: str,
) -> Optional[dict]:
    """Retrieve one documented endpoint."""
    path = _validate_path(path)

    method = _validate_text(
        method,
        "HTTP method",
        maximum_length=10,
    ).upper()

    record = _get_store().get(
        f"{method}:{path}"
    )

    return deepcopy(record) if record else None


def list_api_endpoints(
    tag: Optional[str] = None,
    method: Optional[str] = None,
    include_deprecated: bool = True,
) -> list[dict]:
    """List documented API endpoints."""
    results = []

    for record in _get_store().values():
        if tag and tag not in record["tags"]:
            continue

        if method:
            if record["method"] != method.upper():
                continue

        if (
            not include_deprecated
            and record["deprecated"]
        ):
            continue

        results.append(deepcopy(record))

    results.sort(
        key=lambda item: (
            item["path"],
            item["method"],
        )
    )

    return results


def _convert_response_schema(response: dict) -> dict:
    """Convert an internal response to OpenAPI format."""
    result = {
        "description": response["description"],
    }

    if "schema" in response:
        result["content"] = {
            "application/json": {
                "schema": response["schema"],
            }
        }

    return result


def generate_openapi_specification() -> dict:
    """Generate an OpenAPI 3.1-compatible specification."""
    info = _get_info()
    endpoints = list_api_endpoints()

    paths = {}

    for endpoint in endpoints:
        path = endpoint["path"]
        method = endpoint["method"].lower()

        if path not in paths:
            paths[path] = {}

        operation = {
            "summary": endpoint["summary"],
            "description": endpoint["description"],
            "tags": endpoint["tags"],
            "deprecated": endpoint["deprecated"],
            "responses": {
                code: _convert_response_schema(response)
                for code, response
                in endpoint["responses"].items()
            },
        }

        if endpoint["parameters"]:
            operation["parameters"] = (
                endpoint["parameters"]
            )

        if endpoint["request_schema"] is not None:
            operation["requestBody"] = {
                "required": True,
                "content": {
                    "application/json": {
                        "schema": endpoint["request_schema"],
                    }
                },
            }

        if endpoint["authenticated"]:
            operation["security"] = [
                {"ApiKeyAuth": []}
            ]

        paths[path][method] = operation

    specification = {
        "openapi": "3.1.0",
        "info": {
            "title": info["title"],
            "description": info["description"],
            "version": info["version"],
        },
        "servers": [
            {
                "url": "/api/v1",
                "description": "JAK Data Analytics API",
            }
        ],
        "paths": paths,
        "components": {
            "securitySchemes": {
                "ApiKeyAuth": {
                    "type": "apiKey",
                    "in": "header",
                    "name": "X-API-Key",
                    "description": (
                        "Provide your JAK API key "
                        "in the X-API-Key header."
                    ),
                }
            }
        },
    }

    if info.get("contact_email"):
        specification["info"]["contact"] = {
            "email": info["contact_email"]
        }

    if info.get("terms_of_service"):
        specification["info"]["termsOfService"] = (
            info["terms_of_service"]
        )

    return specification


def export_openapi_json(
    indent: int = 2,
) -> str:
    """Export the OpenAPI specification as JSON."""
    if (
        isinstance(indent, bool)
        or not isinstance(indent, int)
        or not 0 <= indent <= 8
    ):
        raise APIDocumentationError(
            "Indent must be between 0 and 8."
        )

    specification = generate_openapi_specification()

    return json.dumps(
        specification,
        indent=indent,
        ensure_ascii=False,
    )


def get_documentation_statistics() -> dict:
    """Return API documentation statistics."""
    endpoints = list_api_endpoints()

    methods = {}
    tags = set()

    authenticated = 0
    public = 0
    deprecated = 0

    for endpoint in endpoints:
        method = endpoint["method"]

        methods[method] = methods.get(method, 0) + 1

        tags.update(endpoint["tags"])

        if endpoint["authenticated"]:
            authenticated += 1
        else:
            public += 1

        if endpoint["deprecated"]:
            deprecated += 1

    return {
        "total_endpoints": len(endpoints),
        "authenticated_endpoints": authenticated,
        "public_endpoints": public,
        "deprecated_endpoints": deprecated,
        "methods": methods,
        "tags": sorted(tags),
        "last_updated": _get_info()["updated_at"],
    }


def clear_api_documentation() -> int:
    """Remove all registered endpoint documentation."""
    store = _get_store()

    count = len(store)

    store.clear()

    return count
