"""MySQL connection and transaction helpers for the Phase 6 integration.

No connection is made at import time. SQL statements must use connector parameters.
"""
import os
from contextlib import contextmanager
from uuid import uuid4


def new_id(prefix):
    """Return a collision-resistant ID compatible with VARCHAR(40)."""
    if not prefix or len(prefix) > 8 or not prefix.isalnum():
        raise ValueError("ID prefix must be 1 to 8 alphanumeric characters")
    return prefix + uuid4().hex


class DatabaseConfigurationError(RuntimeError):
    """Required local database configuration is missing."""


def connection_config():
    password = os.environ.get("MYSQL_PASSWORD")
    if not password:
        raise DatabaseConfigurationError("MYSQL_PASSWORD must be configured in the environment or .env")
    return {
        "host": os.environ.get("MYSQL_HOST", "127.0.0.1"),
        "port": int(os.environ.get("MYSQL_PORT", "3306")),
        "user": os.environ.get("MYSQL_USER", "devuser"),
        "password": password,
        "database": os.environ.get("MYSQL_DATABASE", "aether_db"),
        "connection_timeout": 5,
    }


def connect():
    import mysql.connector
    return mysql.connector.connect(**connection_config())


@contextmanager
def transaction():
    """Commit all operations together, or roll back on any exception."""
    connection = connect()
    try:
        yield connection
        connection.commit()
    except BaseException:
        connection.rollback()
        raise
    finally:
        connection.close()
