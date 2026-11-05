"""
LIA - PostgreSQL & Supabase Connection Module

This module provides database health check and ping functionality.
When the FastAPI server starts, this module tests the connection to your Supabase PostgreSQL instance
to ensure the database is reachable before any data ingestion or vector operations begin.
"""

import logging
import psycopg
from app.core.config import settings

# Initialize logger for beginner-friendly, formatted console logs
logger = logging.getLogger("lia")
logger.setLevel(logging.INFO)


def get_db_url() -> str:
    """
    Retrieves the PostgreSQL connection string.
    Checks SUPABASE_DB_URL first, then falls back to DATABASE_URL.
    """
    return settings.SUPABASE_DB_URL or settings.DATABASE_URL


def ping_database() -> bool:
    """
    Ping test for PostgreSQL / Supabase.

    What this function does:
    1. Checks if a database connection URL is configured in the environment (.env).
    2. Opens a lightweight connection to PostgreSQL.
    3. Runs 'SELECT 1;' — the standard, fastest SQL test query.
    4. Ensures the 'pgvector' extension is installed/available.
    5. Returns True if the database is online and ready, False otherwise.

    Beginner Note:
    - Running 'SELECT 1;' does not modify any data; it simply verifies:
      a) Your network connection to Supabase works.
      b) Your username and password are correct.
      c) The PostgreSQL database is accepting incoming queries.
    """
    db_url = get_db_url()

    # Step 1: Validate connection string existence
    if not db_url or "your-project-ref" in db_url or "your-password" in db_url:
        logger.warning("=" * 60)
        logger.warning("[DB PING FAILED] PostgreSQL connection URL is not configured.")
        logger.warning("Please update 'SUPABASE_DB_URL' in your .env file with your real Supabase connection string.")
        logger.warning("Example: postgresql://postgres.abcdef:mypassword@aws-0-us-east-1.pooler.supabase.com:6543/postgres")
        logger.warning("=" * 60)
        return False

    logger.info("=" * 60)
    logger.info("[DB PING] Connecting to PostgreSQL (Supabase)...")

    # Step 2: Attempt connection and execute ping query
    try:
        with psycopg.connect(db_url, connect_timeout=5) as connection:
            with connection.cursor() as cursor:
                # Test the connection with a quick query
                cursor.execute("SELECT 1;")
                result = cursor.fetchone()

                if result and result[0] == 1:
                    logger.info("[DB PING SUCCESS] PostgreSQL responded to 'SELECT 1;' successfully!")

                # Step 3: Check / enable the pgvector extension
                cursor.execute("CREATE EXTENSION IF NOT EXISTS vector;")
                connection.commit()
                logger.info("[DB PING SUCCESS] 'vector' extension is active and ready for RAG embeddings.")

        logger.info("[DB PING] Database health check completed: ONLINE.")
        logger.info("=" * 60)
        return True

    except psycopg.OperationalError as op_err:
        # OperationalError usually means wrong password, invalid host, or network timeout
        logger.error("=" * 60)
        logger.error(f"[DB PING ERROR] Could not connect to PostgreSQL: {op_err}")
        logger.error("Troubleshooting tips:")
        logger.error("1. Check if your internet connection is active.")
        logger.error("2. Verify that your Supabase password and project reference in .env are correct.")
        logger.error("3. If using Supabase Pooler (port 6543), verify connection pooling mode is enabled.")
        logger.error("=" * 60)
        return False

    except Exception as exc:
        # Any other unexpected database error
        logger.error("=" * 60)
        logger.error(f"[DB PING ERROR] Unexpected database error during ping: {exc}")
        logger.error("=" * 60)
        return False


if __name__ == "__main__":
    # Allows running this file directly for quick manual testing:
    # python -m app.db.pg_vector
    success = ping_database()
    print("Ping status:", "SUCCESS" if success else "FAILED")
