from datetime import datetime

import pytest
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import Base, Job


@pytest.fixture
def session() -> Session:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as database_session:
        yield database_session


def test_job_can_be_stored(session: Session) -> None:
    job = Job(
        source="rooster.jobs",
        source_id="job-123",
        title="Python Developer",
        company="Example Ltd",
        location="Colombo",
        description="Build useful software.",
        url="https://example.com/jobs/job-123",
        posted_at=datetime(2026, 11, 8),
    )

    session.add(job)
    session.commit()

    stored_job = session.get(Job, job.id)
    assert stored_job is not None
    assert stored_job.title == "Python Developer"
    assert stored_job.remote is False
    assert stored_job.status == "open"
    assert stored_job.collected_at is not None
    assert stored_job.last_seen_at is not None


def test_job_can_store_source_metadata(session: Session) -> None:
    job = Job(
        source="itpro",
        source_id="15587",
        title="Backend Developer",
        company="Example Ltd",
        url="https://example.com/jobs/15587",
        remote=True,
        source_category="IT",
        salary="LKR 200,000",
        raw='{"id": "15587"}',
    )

    session.add(job)
    session.commit()

    assert job.remote is True
    assert job.raw == '{"id": "15587"}'


def test_job_status_must_be_open_or_closed(session: Session) -> None:
    session.add(
        Job(
            source="itpro",
            source_id="15587",
            title="Backend Developer",
            company="Example Ltd",
            url="https://example.com/jobs/15587",
            status="unknown",
        )
    )

    with pytest.raises(IntegrityError):
        session.commit()


def test_source_and_source_id_must_be_unique(session: Session) -> None:
    common_fields = {
        "source": "rooster.jobs",
        "source_id": "job-123",
        "title": "Python Developer",
        "company": "Example Ltd",
        "url": "https://example.com/jobs/job-123",
    }
    session.add_all([Job(**common_fields), Job(**common_fields)])

    with pytest.raises(IntegrityError):
        session.commit()
