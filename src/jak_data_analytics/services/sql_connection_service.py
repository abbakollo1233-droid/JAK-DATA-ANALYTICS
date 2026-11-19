"""
JAK Data Analytics
SQL Database Integration Service

Connects JAK to supported SQL databases.

Supported databases:
- SQLite
- PostgreSQL
- MySQL

Features:
- Database connection testing
- SQLAlchemy engine creation
- Table discovery
- Schema discovery
- Read-only SELECT queries
- Parameterized query execution
- Pandas DataFrame conversion
- Query execution statistics

Security:
- Does not store database passwords.
- Supports parameterized queries.
- Rejects multiple SQL statements.
- Allows SELECT and read-only CTE queries only.
- Uses connection timeouts.
- Does not expose database credentials in reports.
"""

import re
import time
from datetime import datetime, timezone
from urllib.parse import quote_plus

import pandas as pd

from sqlalchemy import (
    create_engine,
    inspect,
    text,
)
from sqlalchemy.exc import SQLAlchemyError


# ---------------------------------------------------------
# CONFIGURATION
# ---------------------------------------------------------

SUPPORTED_DATABASES = {
    "sqlite",
    "postgresql",
    "mysql",
}

DEFAULT_TIMEOUT = 30

MAX_TIMEOUT = 120

MAX_QUERY_ROWS = 100000

SUPPORTED_QUERY_PREFIXES = {
    "SELECT",
    "WITH",
}


# ---------------------------------------------------------
# GENERAL UTILITIES
# ---------------------------------------------------------

def current_timestamp():
    """Return the current UTC timestamp."""

    return datetime.now(
        timezone.utc
    ).isoformat()


def validate_database_type(database_type):
    """Validate the database type."""

    database_type = str(
        database_type
    ).strip().lower()

    if database_type not in SUPPORTED_DATABASES:
        raise ValueError(
            f"Unsupported database type: {database_type}"
        )

    return database_type


def validate_timeout(timeout):
    """Validate database connection timeout."""

    timeout = int(timeout)

    if timeout < 1 or timeout > MAX_TIMEOUT:
        raise ValueError(
            f"Timeout must be between 1 and {MAX_TIMEOUT} seconds."
        )

    return timeout


# ---------------------------------------------------------
# DATABASE URL BUILDERS
# ---------------------------------------------------------

def build_sqlite_url(database_path):
    """Build a SQLite connection URL."""

    if not database_path:
        raise ValueError(
            "SQLite database path is required."
        )

    return f"sqlite:///{database_path}"


def build_postgresql_url(
    host,
    port,
    database,
    username,
    password,
):
    """Build a PostgreSQL connection URL."""

    required = {
        "host": host,
        "database": database,
        "username": username,
        "password": password,
    }

    missing = [
        key
        for key, value in required.items()
        if value is None or value == ""
    ]

    if missing:
        raise ValueError(
            f"Missing PostgreSQL settings: {missing}"
        )

    return (
        "postgresql+psycopg://"
        f"{quote_plus(str(username))}:"
        f"{quote_plus(str(password))}@"
        f"{host}:{int(port or 5432)}/"
        f"{quote_plus(str(database))}"
    )


def build_mysql_url(
    host,
    port,
    database,
    username,
    password,
):
    """Build a MySQL connection URL."""

    required = {
        "host": host,
        "database": database,
        "username": username,
        "password": password,
    }

    missing = [
        key
        for key, value in required.items()
        if value is None or value == ""
    ]

    if missing:
        raise ValueError(
            f"Missing MySQL settings: {missing}"
        )

    return (
        "mysql+pymysql://"
        f"{quote_plus(str(username))}:"
        f"{quote_plus(str(password))}@"
        f"{host}:{int(port or 3306)}/"
        f"{quote_plus(str(database))}"
        "?charset=utf8mb4"
    )


# ---------------------------------------------------------
# DATABASE ENGINE
# ---------------------------------------------------------

def create_database_engine(
    database_url,
    timeout=DEFAULT_TIMEOUT,
    read_only=False,
):
    """
    Create a SQLAlchemy database engine.

    The read_only option provides additional protection
    where supported by the database driver, but it does
    not replace database-level read-only permissions.
    """

    if not isinstance(database_url, str):
        raise ValueError(
            "Database URL must be text."
        )

    if not database_url.strip():
        raise ValueError(
            "Database URL is required."
        )

    timeout = validate_timeout(timeout)

    if database_url.startswith("sqlite:///"):

        connect_args = {
            "timeout": timeout,
            "check_same_thread": False,
        }

        if read_only:
            database_path = database_url.replace(
                "sqlite:///",
                "",
                1,
            )

            database_url = (
                "sqlite:///file:"
                f"{database_path}?mode=ro&uri=true"
            )

        engine = create_engine(
            database_url,
            connect_args=connect_args,
            pool_pre_ping=True,
        )

    else:

        engine = create_engine(
            database_url,
            pool_pre_ping=True,
            pool_recycle=1800,
            connect_args={
                "connect_timeout": timeout,
            },
        )

    return engine


# ---------------------------------------------------------
# CONNECTION TEST
# ---------------------------------------------------------

def test_database_connection(engine):
    """Test whether a database connection works."""

    try:

        start = time.time()

        with engine.connect() as connection:

            connection.execute(
                text("SELECT 1")
            )

        elapsed = round(
            time.time() - start,
            3,
        )

        return {
            "success": True,
            "message": "Database connection successful.",
            "response_time_seconds": elapsed,
            "tested_at": current_timestamp(),
        }

    except SQLAlchemyError as error:

        return {
            "success": False,
            "message": str(error),
            "response_time_seconds": None,
            "tested_at": current_timestamp(),
        }


# ---------------------------------------------------------
# DATABASE INFORMATION
# ---------------------------------------------------------

def get_database_information(engine):
    """Return basic database information."""

    try:

        with engine.connect() as connection:

            return {
                "database_type": (
                    engine.dialect.name
                ),
                "driver": (
                    engine.dialect.driver
                ),
                "database_name": (
                    engine.url.database
                ),
                "server_version": (
                    connection.dialect.server_version_info
                    if hasattr(connection, "dialect")
                    else None
                ),
                "retrieved_at": current_timestamp(),
            }

    except SQLAlchemyError as error:

        raise RuntimeError(
            f"Could not retrieve database information: {error}"
        )


# ---------------------------------------------------------
# TABLE DISCOVERY
# ---------------------------------------------------------

def get_database_tables(engine, schema=None):
    """Return tables available in a database."""

    try:

        inspector = inspect(engine)

        tables = inspector.get_table_names(
            schema=schema
        )

        return sorted(tables)

    except SQLAlchemyError as error:

        raise RuntimeError(
            f"Could not retrieve database tables: {error}"
        )


# ---------------------------------------------------------
# SCHEMA DISCOVERY
# ---------------------------------------------------------

def get_table_schema(
    engine,
    table_name,
    schema=None,
):
    """Retrieve column information for a table."""

    if not table_name:
        raise ValueError(
            "Table name is required."
        )

    inspector = inspect(engine)

    available_tables = inspector.get_table_names(
        schema=schema
    )

    if table_name not in available_tables:
        raise ValueError(
            f"Table does not exist: {table_name}"
        )

    columns = inspector.get_columns(
        table_name,
        schema=schema,
    )

    primary_key = inspector.get_pk_constraint(
        table_name,
        schema=schema,
    )

    primary_columns = set(
        primary_key.get("constrained_columns") or []
    )

    results = []

    for column in columns:

        results.append({
            "column_name": column["name"],
            "data_type": str(
                column["type"]
            ),
            "nullable": column.get(
                "nullable",
                True,
            ),
            "primary_key": (
                column["name"] in primary_columns
            ),
            "default": str(
                column.get("default")
            ) if column.get("default") is not None else None,
        })

    return pd.DataFrame(results)


# ---------------------------------------------------------
# SQL QUERY VALIDATION
# ---------------------------------------------------------

def validate_read_only_query(query):
    """
    Allow read-only SELECT and WITH queries.

    This is a defensive syntax check, not a complete
    SQL security boundary. Use a database account with
    SELECT-only permissions for external databases.
    """

    if not isinstance(query, str):
        raise ValueError(
            "SQL query must be text."
        )

    query = query.strip()

    if not query:
        raise ValueError(
            "SQL query cannot be empty."
        )

    if len(query) > 50000:
        raise ValueError(
            "SQL query is too long."
        )

    # Remove SQL comments for the initial inspection.
    cleaned = re.sub(
        r"/\*.*?\*/",
        " ",
        query,
        flags=re.DOTALL,
    )

    cleaned = re.sub(
        r"--[^\n]*",
        " ",
        cleaned,
    )

    cleaned = cleaned.strip()

    if not cleaned:
        raise ValueError(
            "SQL query cannot contain only comments."
        )

    # Reject multiple statements.
    without_trailing_semicolon = cleaned.rstrip(";")

    if ";" in without_trailing_semicolon:
        raise ValueError(
            "Multiple SQL statements are not allowed."
        )

    # Reject common write and administrative operations.
    forbidden = re.compile(
        r"\b("
        r"INSERT|UPDATE|DELETE|MERGE|REPLACE|"
        r"DROP|ALTER|CREATE|TRUNCATE|"
        r"GRANT|REVOKE|"
        r"ATTACH|DETACH|"
        r"PRAGMA|VACUUM|"
        r"CALL|EXEC|EXECUTE|"
        r"COPY|LOAD|"
        r"INTO\s+OUTFILE|"
        r"INTO\s+DUMPFILE"
        r")\b",
        re.IGNORECASE,
    )

    if forbidden.search(cleaned):
        raise ValueError(
            "This service only permits read-only SQL queries."
        )

    first_word = re.match(
        r"([A-Za-z]+)",
        cleaned,
    )

    if not first_word:
        raise ValueError(
            "Invalid SQL query."
        )

    keyword = first_word.group(1).upper()

    if keyword not in SUPPORTED_QUERY_PREFIXES:
        raise ValueError(
            "Only SELECT and read-only WITH queries are allowed."
        )

    return cleaned


# ---------------------------------------------------------
# QUERY EXECUTION
# ---------------------------------------------------------

def execute_read_query(
    engine,
    query,
    parameters=None,
    limit=MAX_QUERY_ROWS,
):
    """
    Execute a read-only SQL query.

    Parameters must be supplied separately using
    SQLAlchemy named bind parameters.

    Example:
        SELECT * FROM employees WHERE department = :department

        parameters = {"department": "IT"}
    """

    query = validate_read_only_query(
        query
    )

    if parameters is None:
        parameters = {}

    if not isinstance(parameters, dict):
        raise ValueError(
            "Query parameters must be a dictionary."
        )

    limit = int(limit)

    if limit < 1 or limit > MAX_QUERY_ROWS:
        raise ValueError(
            f"Result limit must be between 1 and {MAX_QUERY_ROWS}."
        )

    start = time.time()

    try:

        with engine.connect() as connection:

            result = connection.execute(
                text(query),
                parameters,
            )

            rows = result.fetchmany(
                limit + 1
            )

            columns = list(
                result.keys()
            )

        truncated = len(rows) > limit

        rows = rows[:limit]

        dataframe = pd.DataFrame(
            rows,
            columns=columns,
        )

        elapsed = round(
            time.time() - start,
            3,
        )

        return {
            "success": True,
            "dataframe": dataframe,
            "metadata": {
                "rows_returned": len(dataframe),
                "columns_returned": len(dataframe.columns),
                "execution_time_seconds": elapsed,
                "truncated": truncated,
                "row_limit": limit,
                "executed_at": current_timestamp(),
            },
        }

    except SQLAlchemyError as error:

        raise RuntimeError(
            f"SQL query failed: {error}"
        )


# ---------------------------------------------------------
# TABLE DATA PREVIEW
# ---------------------------------------------------------

def preview_table(
    engine,
    table_name,
    schema=None,
    limit=100,
):
    """Preview records from a table."""

    if not table_name:
        raise ValueError(
            "Table name is required."
        )

    tables = get_database_tables(
        engine,
        schema=schema,
    )

    if table_name not in tables:
        raise ValueError(
            f"Table does not exist: {table_name}"
        )

    limit = int(limit)

    if limit < 1 or limit > MAX_QUERY_ROWS:
        raise ValueError(
            "Invalid preview limit."
        )

    # Quote the identifier using the active SQL dialect.
    preparer = engine.dialect.identifier_preparer

    quoted_table = preparer.quote(
        table_name
    )

    if schema:
        quoted_schema = preparer.quote(
            schema
        )

        qualified_table = (
            f"{quoted_schema}.{quoted_table}"
        )

    else:
        qualified_table = quoted_table

    query = (
        f"SELECT * FROM {qualified_table} "
        f"LIMIT {limit}"
    )

    return execute_read_query(
        engine,
        query,
        limit=limit,
    )


# ---------------------------------------------------------
# DATABASE SUMMARY
# ---------------------------------------------------------

def get_database_summary(engine):
    """Generate a summary of the connected database."""

    tables = get_database_tables(
        engine
    )

    table_information = []

    for table_name in tables:

        schema = get_table_schema(
            engine,
            table_name,
        )

        table_information.append({
            "table_name": table_name,
            "column_count": len(schema),
            "columns": schema["column_name"].tolist(),
        })

    return {
        "database": get_database_information(
            engine
        ),
        "total_tables": len(tables),
        "tables": table_information,
        "generated_at": current_timestamp(),
    }


# ---------------------------------------------------------
# CONNECTION METADATA
# ---------------------------------------------------------

def create_connection_metadata(
    name,
    database_type,
    host=None,
    port=None,
    database=None,
    description="",
):
    """
    Create safe connection metadata.

    Do not include passwords, API keys or tokens.
    """

    database_type = validate_database_type(
        database_type
    )

    if not str(name).strip():
        raise ValueError(
            "Connection name is required."
        )

    return {
        "name": str(name).strip(),
        "database_type": database_type,
        "host": host,
        "port": port,
        "database": database,
        "description": str(description).strip(),
        "created_at": current_timestamp(),
        "updated_at": current_timestamp(),
        "status": "configured",
    }


# ---------------------------------------------------------
# CLOSE ENGINE
# ---------------------------------------------------------

def close_database_engine(engine):
    """Dispose of a SQLAlchemy engine."""

    if engine is not None:
        engine.dispose()

    return True


# ---------------------------------------------------------
# CONNECTION REPORT
# ---------------------------------------------------------

def generate_connection_report(
    connection_name,
    connection_result,
):
    """Generate a report without exposing credentials."""

    return {
        "connection_name": connection_name,
        "success": bool(
            connection_result.get("success")
        ),
        "message": connection_result.get(
            "message",
            "",
        ),
        "tested_at": current_timestamp(),
    }
