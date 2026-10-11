"""Persist manual recommendation inputs in PostgreSQL."""

import os


def save_text_submission(text: str, language: str) -> None:
    """Store a manual submission; fail clearly rather than silently dropping it."""
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise RuntimeError("Manual recommendations need PostgreSQL. Set DATABASE_URL on the server.")

    try:
        import psycopg
    except ImportError as exc:
        raise RuntimeError("PostgreSQL support is not installed. Install server/requirements.txt.") from exc

    with psycopg.connect(database_url) as connection:
        connection.execute(
            """CREATE TABLE IF NOT EXISTS recommendation_submissions (
                   id BIGSERIAL PRIMARY KEY,
                   text_input TEXT NOT NULL,
                   language VARCHAR(80) NOT NULL,
                   created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
               )"""
        )
        connection.execute(
            "INSERT INTO recommendation_submissions (text_input, language) VALUES (%s, %s)",
            (text, language),
        )
