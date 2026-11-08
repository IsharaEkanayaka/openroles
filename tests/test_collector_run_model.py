from datetime import datetime

import pytest
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import Base, CollectorRun


@pytest.fixture
def session() -> Session:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as database_session:
        yield database_session


def test_successful_collector_run_can_be_stored(session: Session) -> None:
    started_at = datetime(2026, 11, 8, 20, 30)
    finished_at = datetime(2026, 11, 8, 20, 31)
    run = CollectorRun(
        source="itpro",
        started_at=started_at,
        finished_at=finished_at,
        status="ok",
        items_fetched=25,
        items_new=4,
    )

    session.add(run)
    session.commit()

    stored_run = session.get(CollectorRun, run.id)
    assert stored_run is not None
    assert stored_run.source == "itpro"
    assert stored_run.items_fetched == 25
    assert stored_run.items_new == 4
    assert stored_run.error is None


def test_failed_collector_run_can_store_error(session: Session) -> None:
    run = CollectorRun(
        source="rooster.jobs",
        started_at=datetime(2026, 11, 8, 20, 30),
        status="error",
        error="Request timed out",
    )

    session.add(run)
    session.commit()

    assert run.finished_at is None
    assert run.error == "Request timed out"


def test_collector_run_status_must_be_ok_or_error(session: Session) -> None:
    session.add(
        CollectorRun(
            source="itpro",
            started_at=datetime(2026, 11, 8, 20, 30),
            status="running",
        )
    )

    with pytest.raises(IntegrityError):
        session.commit()
