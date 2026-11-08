from collections.abc import Iterator

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.config import get_settings


def create_database_engine() -> Engine:
    settings = get_settings()
    connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
    return create_engine(settings.database_url, connect_args=connect_args)


engine = create_database_engine()
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def get_db() -> Iterator[Session]:
    with SessionLocal() as session:
        yield session


def check_database_connection() -> None:
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))
