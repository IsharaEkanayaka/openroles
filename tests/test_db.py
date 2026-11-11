from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db import save_jobs
from app.models import Base, Job


def test_save_jobs_deduplicates_by_source_and_source_id() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)

    first_job = Job(
        source="itpro",
        source_id="15717",
        title="Software Engineer",
        company="Example Ltd",
        url="https://itpro.lk/job/15717",
    )

    with Session(engine) as session:
        assert save_jobs(session, [first_job]) == 1
        assert save_jobs(session, [Job(
            source="itpro",
            source_id="15717",
            title="Updated title",
            company="Example Ltd",
            url="https://itpro.lk/job/15717",
        )]) == 0

        stored_job = session.query(Job).one()
        assert stored_job.title == "Software Engineer"
        assert stored_job.last_seen_at >= stored_job.collected_at
