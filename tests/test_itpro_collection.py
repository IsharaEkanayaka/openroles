from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.collectors.itpro import collect
from app.models import Base, Job


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "itpro_software_engineering.xml"


def test_collect_saves_feed_jobs_and_reports_counts() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        assert collect(
            FIXTURE_PATH.read_bytes(),
            session,
            source_category="software-engineering",
        ) == (25, 25)
        assert collect(
            FIXTURE_PATH.read_bytes(),
            session,
            source_category="software-engineering",
        ) == (25, 0)
        assert session.query(Job).count() == 25
