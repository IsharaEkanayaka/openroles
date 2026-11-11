from pathlib import Path

import httpx
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.collectors.itpro import collect, fetch_feed
from app.models import Base, CollectorRun, Job


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "itpro_software_engineering.xml"


def test_fetch_feed_returns_response_content() -> None:
    expected_content = FIXTURE_PATH.read_bytes()

    def handler(request: httpx.Request) -> httpx.Response:
        assert str(request.url) == "https://example.test/feed.xml"
        return httpx.Response(200, content=expected_content)

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        assert fetch_feed(client, url="https://example.test/feed.xml") == expected_content


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
        runs = session.query(CollectorRun).order_by(CollectorRun.id).all()

        assert len(runs) == 2
        assert runs[0].source == "itpro"
        assert runs[0].status == "ok"
        assert runs[0].items_fetched == 25
        assert runs[0].items_new == 25
        assert runs[0].finished_at is not None
        assert runs[0].error is None
