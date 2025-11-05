"""Database connection module for PostgreSQL."""
import os
from typing import Optional
import psycopg2
from psycopg2.extensions import connection as Connection
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

load_dotenv()


class DatabaseConnection:
    """Manages PostgreSQL database connections."""

    def __init__(self) -> None:
        """Initialize database connection parameters."""
        self.host = os.getenv("DB_HOST", "localhost")
        self.port = int(os.getenv("DB_PORT", "5432"))
        self.database = os.getenv("DB_NAME", "banking_app")
        self.user = os.getenv("DB_USER", "postgres")
        self.password = os.getenv("DB_PASSWORD", "postgres")
        self._connection: Optional[Connection] = None

    def connect(self) -> Connection:
        """
        Establish a connection to the PostgreSQL database.

        Returns:
            Connection: Active database connection.

        Raises:
            psycopg2.Error: If connection fails.
        """
        if self._connection is None or self._connection.closed:
            self._connection = psycopg2.connect(
                host=self.host,
                port=self.port,
                database=self.database,
                user=self.user,
                password=self.password,
                cursor_factory=RealDictCursor,
            )
        return self._connection

    def close(self) -> None:
        """Close the database connection if open."""
        if self._connection and not self._connection.closed:
            self._connection.close()
            self._connection = None

    def get_cursor(self) -> RealDictCursor:
        """
        Get a cursor for executing queries.

        Returns:
            RealDictCursor: Database cursor that returns dict-like results.
        """
        conn = self.connect()
        return conn.cursor()

    def __enter__(self) -> "DatabaseConnection":
        """Context manager entry."""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:  # type: ignore
        """Context manager exit."""
        self.close()


# Singleton instance
_db_connection: Optional[DatabaseConnection] = None


def get_db_connection() -> DatabaseConnection:
    """
    Get or create a singleton database connection.

    Returns:
        DatabaseConnection: The database connection instance.
    """
    global _db_connection
    if _db_connection is None:
        _db_connection = DatabaseConnection()
    return _db_connection
