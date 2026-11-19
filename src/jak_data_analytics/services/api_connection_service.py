"""
JAK Data Analytics
External API Integration Service

Connects JAK to external REST APIs and converts
JSON responses into Pandas DataFrames.

Features:
- GET and POST requests
- API key authentication
- Bearer token authentication
- Custom headers
- Query parameters
- JSON response processing
- Pagination
- API connection testing
- DataFrame conversion
- Connection metadata

Security:
- Never logs API keys or access tokens.
- Uses request timeouts.
- Supports HTTPS.
- Does not execute remote code.
"""

import json
import time
from datetime import datetime, timezone
from urllib.parse import urlparse

import pandas as pd
import requests


# ---------------------------------------------------------
# CONFIGURATION
# ---------------------------------------------------------

DEFAULT_TIMEOUT = 30

MAX_TIMEOUT = 120

MAX_RESPONSE_SIZE_MB = 50

SUPPORTED_METHODS = {
    "GET",
    "POST",
}

SUPPORTED_AUTH_TYPES = {
    "none",
    "api_key",
    "bearer",
}

USER_AGENT = "JAK-Data-Analytics/1.0"


# ---------------------------------------------------------
# GENERAL UTILITIES
# ---------------------------------------------------------

def current_timestamp():
    """Return current UTC timestamp."""

    return datetime.now(
        timezone.utc
    ).isoformat()


def validate_url(url):
    """Validate an external API URL."""

    if not isinstance(url, str):
        raise ValueError(
            "API URL must be text."
        )

    url = url.strip()

    if not url:
        raise ValueError(
            "API URL is required."
        )

    parsed = urlparse(url)

    if parsed.scheme not in {"https", "http"}:
        raise ValueError(
            "Only HTTP and HTTPS URLs are supported."
        )

    if not parsed.hostname:
        raise ValueError(
            "Invalid API hostname."
        )

    if parsed.username or parsed.password:
        raise ValueError(
            "Credentials must not be embedded in the URL."
        )

    if parsed.scheme == "http":
        raise ValueError(
            "HTTPS is required for external API connections."
        )

    return url


def validate_timeout(timeout):
    """Validate request timeout."""

    timeout = int(timeout)

    if timeout < 1 or timeout > MAX_TIMEOUT:
        raise ValueError(
            f"Timeout must be between 1 and {MAX_TIMEOUT} seconds."
        )

    return timeout


def validate_method(method):
    """Validate HTTP request method."""

    method = str(method).upper().strip()

    if method not in SUPPORTED_METHODS:
        raise ValueError(
            f"Unsupported HTTP method: {method}"
        )

    return method


# ---------------------------------------------------------
# AUTHENTICATION
# ---------------------------------------------------------

def build_authentication(
    auth_type="none",
    api_key=None,
    token=None,
    api_key_header="X-API-Key",
):
    """
    Build authentication headers.

    Authentication values are used only for the
    current request and are not persisted.
    """

    auth_type = str(auth_type).lower().strip()

    if auth_type not in SUPPORTED_AUTH_TYPES:
        raise ValueError(
            "Unsupported authentication type."
        )

    headers = {}

    if auth_type == "api_key":

        if not api_key:
            raise ValueError(
                "API key is required."
            )

        if not api_key_header:
            raise ValueError(
                "API key header name is required."
            )

        headers[str(api_key_header)] = str(api_key)

    elif auth_type == "bearer":

        if not token:
            raise ValueError(
                "Bearer token is required."
            )

        headers["Authorization"] = (
            f"Bearer {token}"
        )

    return headers


# ---------------------------------------------------------
# REQUEST HEADERS
# ---------------------------------------------------------

def build_request_headers(
    custom_headers=None,
    auth_headers=None,
):
    """Combine standard and custom request headers."""

    headers = {
        "Accept": "application/json",
        "User-Agent": USER_AGENT,
    }

    if custom_headers:

        if not isinstance(custom_headers, dict):
            raise ValueError(
                "Custom headers must be a dictionary."
            )

        headers.update(custom_headers)

    if auth_headers:
        headers.update(auth_headers)

    return headers


# ---------------------------------------------------------
# RESPONSE VALIDATION
# ---------------------------------------------------------

def validate_response(response):
    """Validate an HTTP response."""

    if response.status_code < 200 or response.status_code >= 300:

        message = (
            f"API request failed with HTTP "
            f"{response.status_code}."
        )

        if response.status_code == 401:
            message += " Authentication failed."

        elif response.status_code == 403:
            message += " Access was denied."

        elif response.status_code == 404:
            message += " The requested endpoint was not found."

        elif response.status_code == 429:
            message += " API rate limit exceeded."

        elif response.status_code >= 500:
            message += " The external server encountered an error."

        raise RuntimeError(message)

    content_length = response.headers.get(
        "Content-Length"
    )

    if content_length:

        maximum_bytes = (
            MAX_RESPONSE_SIZE_MB * 1024 * 1024
        )

        if int(content_length) > maximum_bytes:
            raise ValueError(
                "API response exceeds the maximum allowed size."
            )

    if len(response.content) > (
        MAX_RESPONSE_SIZE_MB * 1024 * 1024
    ):
        raise ValueError(
            "API response exceeds the maximum allowed size."
        )

    return True


# ---------------------------------------------------------
# JSON PROCESSING
# ---------------------------------------------------------

def parse_json_response(response):
    """Convert an API response into Python data."""

    content_type = response.headers.get(
        "Content-Type",
        "",
    ).lower()

    if "json" not in content_type:
        raise ValueError(
            "API did not return a JSON response."
        )

    try:
        return response.json()

    except ValueError:
        raise ValueError(
            "Unable to decode API JSON response."
        )


def extract_json_records(
    response_data,
    records_path=None,
):
    """
    Extract records from a JSON response.

    records_path supports simple dictionary paths.

    Example:
        data
        results
        response.items
    """

    current = response_data

    if records_path:

        for key in str(records_path).split("."):

            if isinstance(current, dict):

                if key not in current:
                    raise ValueError(
                        f"JSON path not found: {key}"
                    )

                current = current[key]

            else:
                raise ValueError(
                    "JSON path cannot continue through a non-object value."
                )

    if isinstance(current, dict):
        return [current]

    if isinstance(current, list):
        return current

    raise ValueError(
        "API response does not contain tabular records."
    )


# ---------------------------------------------------------
# DATAFRAME CONVERSION
# ---------------------------------------------------------

def json_to_dataframe(
    response_data,
    records_path=None,
    flatten=True,
):
    """Convert JSON records into a Pandas DataFrame."""

    records = extract_json_records(
        response_data,
        records_path,
    )

    if not records:
        return pd.DataFrame()

    if not all(
        isinstance(item, dict)
        for item in records
    ):
        raise ValueError(
            "API records must contain JSON objects."
        )

    dataframe = pd.json_normalize(
        records,
        sep="_",
    ) if flatten else pd.DataFrame(records)

    dataframe.columns = [
        str(column)
        for column in dataframe.columns
    ]

    return dataframe


# ---------------------------------------------------------
# API REQUEST
# ---------------------------------------------------------

def make_api_request(
    url,
    method="GET",
    params=None,
    json_body=None,
    custom_headers=None,
    auth_type="none",
    api_key=None,
    token=None,
    api_key_header="X-API-Key",
    timeout=DEFAULT_TIMEOUT,
):
    """
    Execute a single API request.

    Returns:
        response_data
        response_metadata
    """

    url = validate_url(url)

    method = validate_method(method)

    timeout = validate_timeout(timeout)

    auth_headers = build_authentication(
        auth_type=auth_type,
        api_key=api_key,
        token=token,
        api_key_header=api_key_header,
    )

    headers = build_request_headers(
        custom_headers=custom_headers,
        auth_headers=auth_headers,
    )

    start_time = time.time()

    try:

        response = requests.request(
            method=method,
            url=url,
            params=params,
            json=json_body,
            headers=headers,
            timeout=timeout,
            allow_redirects=False,
            verify=True,
        )

        validate_response(response)

        response_data = parse_json_response(
            response
        )

        elapsed = round(
            time.time() - start_time,
            3,
        )

        metadata = {
            "url": url,
            "method": method,
            "status_code": response.status_code,
            "response_time_seconds": elapsed,
            "content_type": response.headers.get(
                "Content-Type"
            ),
            "retrieved_at": current_timestamp(),
        }

        return {
            "success": True,
            "data": response_data,
            "metadata": metadata,
        }

    except requests.exceptions.Timeout:
        raise RuntimeError(
            "API request timed out."
        )

    except requests.exceptions.ConnectionError:
        raise RuntimeError(
            "Could not connect to the API server."
        )

    except requests.exceptions.RequestException as error:
        raise RuntimeError(
            f"API request error: {error}"
        )


# ---------------------------------------------------------
# FETCH DATASET
# ---------------------------------------------------------

def fetch_api_dataset(
    url,
    method="GET",
    params=None,
    json_body=None,
    custom_headers=None,
    auth_type="none",
    api_key=None,
    token=None,
    api_key_header="X-API-Key",
    records_path=None,
    flatten=True,
    timeout=DEFAULT_TIMEOUT,
):
    """
    Retrieve API data and convert it into a DataFrame.
    """

    result = make_api_request(
        url=url,
        method=method,
        params=params,
        json_body=json_body,
        custom_headers=custom_headers,
        auth_type=auth_type,
        api_key=api_key,
        token=token,
        api_key_header=api_key_header,
        timeout=timeout,
    )

    dataframe = json_to_dataframe(
        response_data=result["data"],
        records_path=records_path,
        flatten=flatten,
    )

    result["dataframe"] = dataframe

    result["dataset_summary"] = {
        "row_count": len(dataframe),
        "column_count": len(dataframe.columns),
        "columns": list(dataframe.columns),
        "empty": dataframe.empty,
    }

    return result


# ---------------------------------------------------------
# PAGINATION
# ---------------------------------------------------------

def fetch_paginated_api_dataset(
    url,
    page_parameter="page",
    start_page=1,
    maximum_pages=10,
    page_size=None,
    page_size_parameter="limit",
    params=None,
    records_path=None,
    auth_type="none",
    api_key=None,
    token=None,
    api_key_header="X-API-Key",
    custom_headers=None,
    timeout=DEFAULT_TIMEOUT,
):
    """
    Fetch data from a page-number-based API.

    This function assumes the API uses page-number
    pagination. Cursor-based pagination requires
    a separate API-specific implementation.
    """

    url = validate_url(url)

    maximum_pages = int(maximum_pages)

    if maximum_pages < 1 or maximum_pages > 100:
        raise ValueError(
            "Maximum pages must be between 1 and 100."
        )

    all_records = []

    page_metadata = []

    for page in range(
        int(start_page),
        int(start_page) + maximum_pages,
    ):

        request_params = dict(
            params or {}
        )

        request_params[page_parameter] = page

        if page_size is not None:
            request_params[page_size_parameter] = int(
                page_size
            )

        result = make_api_request(
            url=url,
            method="GET",
            params=request_params,
            custom_headers=custom_headers,
            auth_type=auth_type,
            api_key=api_key,
            token=token,
            api_key_header=api_key_header,
            timeout=timeout,
        )

        records = extract_json_records(
            result["data"],
            records_path=records_path,
        )

        if not records:
            break

        all_records.extend(records)

        page_metadata.append({
            "page": page,
            "records": len(records),
            "status_code": result["metadata"]["status_code"],
        })

        if len(records) == 0:
            break

    dataframe = pd.json_normalize(
        all_records,
        sep="_",
    ) if all_records else pd.DataFrame()

    return {
        "success": True,
        "dataframe": dataframe,
        "metadata": {
            "url": url,
            "pages_fetched": len(page_metadata),
            "total_records": len(dataframe),
            "page_details": page_metadata,
            "retrieved_at": current_timestamp(),
        },
    }


# ---------------------------------------------------------
# CONNECTION TEST
# ---------------------------------------------------------

def test_api_connection(
    url,
    method="GET",
    params=None,
    custom_headers=None,
    auth_type="none",
    api_key=None,
    token=None,
    api_key_header="X-API-Key",
    timeout=DEFAULT_TIMEOUT,
):
    """Test whether an API endpoint is reachable."""

    try:

        result = make_api_request(
            url=url,
            method=method,
            params=params,
            custom_headers=custom_headers,
            auth_type=auth_type,
            api_key=api_key,
            token=token,
            api_key_header=api_key_header,
            timeout=timeout,
        )

        return {
            "success": True,
            "message": "API connection successful.",
            "metadata": result["metadata"],
        }

    except Exception as error:

        return {
            "success": False,
            "message": str(error),
            "metadata": None,
        }


# ---------------------------------------------------------
# CONNECTION CONFIGURATION
# ---------------------------------------------------------

def create_api_connection_config(
    name,
    url,
    method="GET",
    description="",
    records_path=None,
    auth_type="none",
    timeout=DEFAULT_TIMEOUT,
    params=None,
):
    """
    Create a reusable API configuration.

    Do not put API keys or bearer tokens in this
    configuration. Store credentials separately
    in a secure secrets manager.
    """

    if not str(name).strip():
        raise ValueError(
            "Connection name is required."
        )

    url = validate_url(url)

    method = validate_method(method)

    timeout = validate_timeout(timeout)

    if auth_type not in SUPPORTED_AUTH_TYPES:
        raise ValueError(
            "Unsupported authentication type."
        )

    if params is not None and not isinstance(params, dict):
        raise ValueError(
            "API parameters must be a dictionary."
        )

    return {
        "name": str(name).strip(),
        "url": url,
        "method": method,
        "description": str(description).strip(),
        "records_path": records_path,
        "auth_type": auth_type,
        "timeout": timeout,
        "params": params or {},
        "created_at": current_timestamp(),
        "updated_at": current_timestamp(),
    }


# ---------------------------------------------------------
# CONNECTION SUMMARY
# ---------------------------------------------------------

def get_api_dataset_summary(dataframe):
    """Generate a summary of an imported API dataset."""

    if not isinstance(dataframe, pd.DataFrame):
        raise ValueError(
            "Input must be a Pandas DataFrame."
        )

    return {
        "rows": len(dataframe),
        "columns": len(dataframe.columns),
        "column_names": list(dataframe.columns),
        "missing_cells": int(
            dataframe.isna().sum().sum()
        ),
        "duplicate_rows": int(
            dataframe.duplicated().sum()
        ),
        "memory_usage_bytes": int(
            dataframe.memory_usage(
                deep=True
            ).sum()
        ),
        "empty": dataframe.empty,
    }


# ---------------------------------------------------------
# API IMPORT REPORT
# ---------------------------------------------------------

def generate_api_import_report(
    connection_name,
    dataframe,
    request_metadata,
):
    """Generate a report about an API dataset import."""

    summary = get_api_dataset_summary(
        dataframe
    )

    return {
        "connection_name": connection_name,
        "imported_at": current_timestamp(),
        "request": request_metadata,
        "dataset": summary,
        "success": True,
    }
