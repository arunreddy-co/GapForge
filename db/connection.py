"""
Database connection management for GapForge.
Provides context managers connecting to the AlloyDB instance securely with guaranteed cleanup.
It also initializes the application settings from environment variables exactly once.
"""

from contextlib import contextmanager
from pydantic_settings import BaseSettings, SettingsConfigDict
import psycopg2


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    ALLOYDB_HOST: str
    ALLOYDB_DB: str
    ALLOYDB_USER: str
    ALLOYDB_PASSWORD: str
    ALLOYDB_PORT: int = 5432
    GOOGLE_CLOUD_PROJECT: str
    GOOGLE_CLOUD_LOCATION: str = "us-central1"
    GOOGLE_GENAI_USE_VERTEXAI: str = "TRUE"

    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8')


# Load settings exactly once at startup.
settings = Settings()


@contextmanager
def get_db_connection():
    """Get AlloyDB connection with guaranteed cleanup.
    
    Yields:
        psycopg2 connection object.
    Raises:
        RuntimeError: If connection fails.
    """
    conn = None
    try:
        conn = psycopg2.connect(
            host=settings.ALLOYDB_HOST,
            dbname=settings.ALLOYDB_DB,
            user=settings.ALLOYDB_USER,
            password=settings.ALLOYDB_PASSWORD,
            port=settings.ALLOYDB_PORT,
            connect_timeout=10,
            sslmode="require"
        )
        yield conn
        conn.commit()
    except psycopg2.Error as e:
        if conn:
            conn.rollback()
        raise RuntimeError(f"Database error: {e}") from e
    finally:
        if conn:
            conn.close()
