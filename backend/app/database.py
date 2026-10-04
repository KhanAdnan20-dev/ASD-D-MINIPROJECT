import psycopg
from psycopg import Connection

from app.config import get_settings


def get_connection() -> Connection:
    settings = get_settings()
    return psycopg.connect(
        host=settings.database_host,
        port=settings.database_port,
        dbname=settings.database_name,
        user=settings.database_user,
        password=settings.database_password.get_secret_value(),
    )