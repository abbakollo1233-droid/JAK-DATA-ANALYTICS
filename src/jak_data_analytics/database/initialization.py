"""
JAK Data Analytics
Database Initialization

Responsibilities:
- Register database models
- Create database tables
- Check database status
- List available tables
- Initialize the application database
"""

from sqlalchemy import inspect, text

from .connection import (
    get_engine,
    Base,
)

# Import models to register them with SQLAlchemy.
from . import models


# ==================================================
# INITIALIZE DATABASE
# ==================================================

def initialize_database():
    """
    Create all database tables defined in models.py.

    Existing tables and records are preserved.
    """

    try:

        engine = get_engine()

        Base.metadata.create_all(
            bind=engine
        )

        return {
            "success": True,
            "message": "Database initialized successfully.",
            "tables": get_database_tables()
        }

    except Exception as error:

        return {
            "success": False,
            "message": f"Database initialization failed: {error}",
            "tables": []
        }


# ==================================================
# GET DATABASE TABLES
# ==================================================

def get_database_tables():
    """
    Return the names of all existing database tables.
    """

    try:

        engine = get_engine()

        inspector = inspect(engine)

        return inspector.get_table_names()

    except Exception:

        return []


# ==================================================
# CHECK DATABASE CONNECTION
# ==================================================

def check_database_status():
    """
    Test the database connection and return its status.
    """

    try:

        engine = get_engine()

        with engine.connect() as connection:

            connection.execute(
                text("SELECT 1")
            )

        return {
            "connected": True,
            "message": "Database connection is active."
        }

    except Exception as error:

        return {
            "connected": False,
            "message": str(error)
        }


# ==================================================
# VERIFY REQUIRED TABLES
# ==================================================

def verify_database_tables():
    """
    Check whether all expected application tables exist.
    """

    expected_tables = [
        "users",
        "projects",
        "datasets",
        "analysis_jobs",
        "saved_dashboards",
        "reports",
        "activity_logs",
        "contact_messages",
    ]

    existing_tables = get_database_tables()

    missing_tables = [
        table
        for table in expected_tables
        if table not in existing_tables
    ]

    return {
        "valid": len(missing_tables) == 0,
        "expected_tables": expected_tables,
        "existing_tables": existing_tables,
        "missing_tables": missing_tables
    }


# ==================================================
# DATABASE SUMMARY
# ==================================================

def get_database_summary():
    """
    Return a summary of the current database.
    """

    status = check_database_status()

    tables = get_database_tables()

    verification = verify_database_tables()

    return {
        "connected": status["connected"],
        "message": status["message"],
        "table_count": len(tables),
        "tables": tables,
        "database_ready": verification["valid"],
        "missing_tables": verification["missing_tables"]
    }


# ==================================================
# DATABASE INITIALIZATION REPORT
# ==================================================

def get_initialization_report():
    """
    Return a detailed database initialization report.
    """

    summary = get_database_summary()

    return {
        "application": "JAK Data Analytics",
        "database_connected": summary["connected"],
        "database_ready": summary["database_ready"],
        "total_tables": summary["table_count"],
        "tables": summary["tables"],
        "missing_tables": summary["missing_tables"],
        "status": (
            "Ready"
            if summary["database_ready"]
            else "Incomplete"
        )
    }