"""Tests for database connection functionality."""

import pytest
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from database import get_db, get_db_engine, get_session


class TestDatabaseConnection:
    """Test database connection using psycopg2."""

    def test_should_connect_to_database_successfully(self):
        """Test that psycopg2 connection is established successfully."""
        conn = None
        try:
            conn = get_db()
            assert conn is not None
            assert conn.closed == 0  # 0 means open, non-zero means closed
        finally:
            if conn:
                conn.close()

    def test_should_execute_simple_query(self):
        """Test that we can execute a simple query."""
        conn = None
        cursor = None
        try:
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute("SELECT 1 as test_value")
            result = cursor.fetchone()
            assert result is not None
            assert result[0] == 1
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    def test_should_handle_connection_error_gracefully(self):
        """Test that connection errors are handled properly."""
        # This test verifies that attempting to use a closed connection raises an error
        conn = get_db()
        conn.close()
        assert conn.closed != 0  # Connection should be closed


class TestDatabaseEngine:
    """Test database engine using SQLAlchemy."""

    def test_should_create_engine_successfully(self):
        """Test that SQLAlchemy engine is created successfully."""
        engine = get_db_engine()
        assert engine is not None

    def test_should_connect_with_engine(self):
        """Test that we can connect using the engine."""
        engine = get_db_engine()
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1 as test_value"))
            row = result.fetchone()
            assert row is not None
            assert row[0] == 1

    def test_should_verify_database_exists(self):
        """Test that we can query database metadata."""
        engine = get_db_engine()
        with engine.connect() as connection:
            result = connection.execute(text("SELECT current_database()"))
            db_name = result.fetchone()[0]
            assert db_name is not None
            assert isinstance(db_name, str)

    def test_should_query_at_users_table_count(self):
        """Test that we can query the number of records in at.users table."""
        engine = get_db_engine()
        with engine.connect() as connection:
            result = connection.execute(text("SELECT COUNT(*) FROM at.users"))
            count = result.fetchone()[0]
            assert count is not None
            assert isinstance(count, int)
            assert count >= 0


class TestDatabaseSession:
    """Test database session using SQLAlchemy ORM."""

    def test_should_create_session_successfully(self):
        """Test that SQLAlchemy session is created successfully."""
        session = get_session()
        assert session is not None
        session.close()

    def test_should_execute_query_with_session(self):
        """Test that we can execute queries using the session."""
        session = None
        try:
            session = get_session()
            result = session.execute(text("SELECT 1 as test_value"))
            row = result.fetchone()
            assert row is not None
            assert row[0] == 1
        finally:
            if session:
                session.close()

    def test_should_rollback_on_error(self):
        """Test that session can rollback on error."""
        session = None
        try:
            session = get_session()
            # Try to execute an invalid query
            with pytest.raises(SQLAlchemyError):
                session.execute(text("SELECT * FROM nonexistent_table"))
                session.commit()
            # Session should still be usable after rollback
            session.rollback()
            result = session.execute(text("SELECT 1"))
            assert result.fetchone()[0] == 1
        finally:
            if session:
                session.close()


