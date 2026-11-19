"""
JAK Data Analytics
Database Connection Manager

Supports:
- SQLite for local development
- PostgreSQL for production
- SQLAlchemy database engine
- Database sessions
- Safe session management
"""

from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import (
    declarative_base,
    sessionmaker,
)

from ..config.settings import DATABASE_URL


# --------------------------------------------------
# DATABASE CONFIGURATION
# --------------------------------------------------

Base = declarative_base()

_engine = None
_SessionFactory = None


# --------------------------------------------------
# CREATE DATABASE ENGINE
# --------------------------------------------------

def get_engine():
    """
    Create and return the SQLAlchemy database engine.

    The engine is created once and reused throughout
    the application.
    """

    global _engine

    if _engine is not None:
        return _engine

    database_url = DATABASE_URL

    if database_url.startswith("sqlite:///"):

        engine_options = {
            "connect_args": {
                "check_same_thread": False
            },
            "pool_pre_ping": True,
        }

    else:

        engine_options = {
            "pool_pre_ping": True,
            "pool_recycle": 1800,
        }

    _engine = create_engine(
        database_url,
        **engine_options
    )

    return _engine


# --------------------------------------------------
# DATABASE SESSION FACTORY
# --------------------------------------------------

def get_session_factory():
    """
    Return the SQLAlchemy session factory.
    """

    global _SessionFactory

    if _SessionFactory is None:

        _SessionFactory = sessionmaker(
            bind=get_engine(),
            autocommit=False,
            autoflush=False,
            expire_on_commit=False,
        )

    return _SessionFactory


# --------------------------------------------------
# GET DATABASE SESSION
# --------------------------------------------------

def get_db_session():
    """
    Create a database session.

    Usage:

        session = get_db_session()

        try:
            # Database operations
            session.commit()

        except Exception:
            session.rollback()
            raise

        finally:
            session.close()
    """

    SessionLocal = get_session_factory()

    return SessionLocal()


# --------------------------------------------------
# DATABASE SESSION CONTEXT MANAGER
# --------------------------------------------------

@contextmanager
def database_session():
    """
    Manage database sessions automatically.

    Automatically:
    - Commits successful operations
    - Rolls back failed operations
    - Closes the session
    """

    session = get_db_session()

    try:

        yield session

        session.commit()

    except Exception:

        session.rollback()

        raise

    finally:

        session.close()


# --------------------------------------------------
# DATABASE SESSION GENERATOR
# --------------------------------------------------

def get_db():
    """
    Yield a database session and close it afterward.

    Useful for services and dependency-based workflows.
    """

    session = get_db_session()

    try:

        yield session

    finally:

        session.close()


# --------------------------------------------------
# TEST DATABASE CONNECTION
# --------------------------------------------------

def test_database_connection():
    """
    Check whether the database connection works.

    Returns:
        tuple: (success, message)
    """

    from sqlalchemy import text

    try:

        engine = get_engine()

        with engine.connect() as connection:

            connection.execute(
                text("SELECT 1")
            )

        return (
            True,
            "Database connection successful."
        )

    except Exception as error:

        return (
            False,
            f"Database connection failed: {error}"
        )


# --------------------------------------------------
# CLOSE DATABASE ENGINE
# --------------------------------------------------

def close_database():

    global _engine
    global _SessionFactory

    if _engine is not None:

        _engine.dispose()

        _engine = None

    _SessionFactory = None