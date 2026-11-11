from collections.abc import Iterator
from datetime import datetime, timezone

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.config import get_settings
from app.models import Base, Job


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


def initialize_database() -> None:
    Base.metadata.create_all(bind=engine)


def save_jobs(session: Session, jobs: list[Job]) -> int:
    """Insert jobs and refresh the last-seen time for existing jobs."""
    now = datetime.now(timezone.utc)
    items_new = 0

    for job in jobs:
        existing_job = (
            session.query(Job)
            .filter_by(source=job.source, source_id=job.source_id)
            .one_or_none()
        )
        if existing_job is None:
            session.add(job)
            items_new += 1
        else:
            existing_job.last_seen_at = now

    session.commit()
    return items_new
