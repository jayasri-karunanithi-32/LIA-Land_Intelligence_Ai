"""
GitHub credential storage per Supabase user.

Stores encrypted GitHub tokens in the `github_connections` table
in the Supabase/Postgres database.  Creates the table automatically
on first use if it doesn't exist.

Schema:
    github_connections (
        user_id   TEXT PRIMARY KEY,   -- Supabase auth user UUID
        token     TEXT NOT NULL,       -- Fernet-encrypted GitHub token
        login     TEXT,                -- GitHub username
        method    TEXT,                -- 'oauth' | 'pat'
        scopes    TEXT,                -- comma-separated GitHub scopes
        created_at TIMESTAMPTZ DEFAULT now(),
        updated_at TIMESTAMPTZ DEFAULT now()
    )
"""

import logging
from typing import Optional

import psycopg

from app.core.config import settings
from app.core.github_crypto import encrypt_token, decrypt_token

logger = logging.getLogger("lia")

_DDL = """
CREATE TABLE IF NOT EXISTS github_connections (
    user_id    TEXT PRIMARY KEY,
    token      TEXT NOT NULL,
    login      TEXT,
    method     TEXT,
    scopes     TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
"""


def _conn():
    return psycopg.connect(settings.SUPABASE_DB_URL)


def ensure_table():
    """Create the github_connections table if it does not exist."""
    if not settings.SUPABASE_DB_URL:
        return
    try:
        with _conn() as conn:
            conn.execute(_DDL)
            conn.commit()
        logger.info("github_connections table ensured.")
    except Exception as exc:
        logger.error("Could not create github_connections table: %s", exc)


def save_connection(
    user_id: str,
    token: str,
    login: str,
    method: str,
    scopes: str,
):
    """Upsert an encrypted GitHub token for a Supabase user."""
    encrypted = encrypt_token(token)
    with _conn() as conn:
        conn.execute(
            """
            INSERT INTO github_connections (user_id, token, login, method, scopes, updated_at)
            VALUES (%s, %s, %s, %s, %s, now())
            ON CONFLICT (user_id) DO UPDATE
                SET token      = EXCLUDED.token,
                    login      = EXCLUDED.login,
                    method     = EXCLUDED.method,
                    scopes     = EXCLUDED.scopes,
                    updated_at = now()
            """,
            (user_id, encrypted, login, method, scopes),
        )
        conn.commit()


def get_connection(user_id: str) -> Optional[dict]:
    """Return the GitHub connection record for a user, with token decrypted."""
    with _conn() as conn:
        row = conn.execute(
            "SELECT token, login, method, scopes FROM github_connections WHERE user_id = %s",
            (user_id,),
        ).fetchone()
    if row is None:
        return None
    return {
        "token": decrypt_token(row[0]),
        "login": row[1],
        "method": row[2],
        "scopes": row[3],
    }


def delete_connection(user_id: str):
    """Remove a user's GitHub connection."""
    with _conn() as conn:
        conn.execute(
            "DELETE FROM github_connections WHERE user_id = %s",
            (user_id,),
        )
        conn.commit()


def connection_status(user_id: str) -> dict:
    """Return connection status without exposing the raw token."""
    with _conn() as conn:
        row = conn.execute(
            "SELECT login, method, scopes, updated_at FROM github_connections WHERE user_id = %s",
            (user_id,),
        ).fetchone()
    if row is None:
        return {"connected": False}
    return {
        "connected": True,
        "login": row[0],
        "method": row[1],
        "scopes": row[2],
        "connected_at": row[3].isoformat() if row[3] else None,
    }
