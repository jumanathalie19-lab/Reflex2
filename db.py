import os
import psycopg2


DATABASE_URL = os.environ.get("DATABASE_URL")


def get_db_connection():
    if not DATABASE_URL:
        raise RuntimeError(
            "DATABASE_URL environment variable is not set."
        )

    try:
        return psycopg2.connect(DATABASE_URL)
    except psycopg2.Error as e:
        raise RuntimeError(
            f"Could not connect to PostgreSQL database: {e}"
        )
