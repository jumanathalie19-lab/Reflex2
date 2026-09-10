import os
import psycopg2


DATABASE_URL = os.environ.get("postgresql://postgres:[%Nathalie@2005.%]@db.dbdfngspeaqydrmbqyts.supabase.co:5432/postgres")


def get_connection():
    if not DATABASE_URL:
        raise RuntimeError(
            "DATABASE_URL environment variable is not set."
        )

    try:
        return psycopg2.connect(postgresql://postgres:[%Nathalie@2005.%]@db.dbdfngspeaqydrmbqyts.supabase.co:5432/postgres)
    except psycopg2.Error as e:
        raise RuntimeError(
            f"Could not connect to PostgreSQL database: {e}"
        )
