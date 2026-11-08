from pathlib import Path
from datetime import timezone
from xml.etree import ElementTree

from app.collectors.itpro import parse_feed, parse_item


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "itpro_software_engineering.xml"


def test_first_itpro_item_is_mapped_to_job() -> None:
    root = ElementTree.parse(FIXTURE_PATH).getroot()
    item = root.find("./channel/item")

    assert item is not None
    job = parse_item(item, source_category="software-engineering")

    assert job.source == "itpro"
    assert job.source_id == "15717"
    assert job.url.startswith("https://itpro.lk/job/15717/")
    assert job.title == "Software Engineer intern - January 2027 Intake"
    assert job.company == "Nippon IT and Educational Solution (NITES)"
    assert job.location == "Colombo"
    assert job.remote is False
    assert job.job_type == "internship"
    assert job.posted_at is not None
    assert job.posted_at.tzinfo == timezone.utc
    assert job.posted_at.isoformat() == "2026-11-07T13:24:57+00:00"
    assert job.description is not None
    assert "About NITES" in job.description
    assert "Apply for this job" not in job.description
    assert job.source_category == "software-engineering"
    assert job.raw is not None


def test_unknown_itpro_job_type_is_none() -> None:
    root = ElementTree.parse(FIXTURE_PATH).getroot()
    item = root.find("./channel/item")

    assert item is not None
    content = item.find("content:encoded", {"content": "http://purl.org/rss/1.0/modules/content/"})
    assert content is not None
    content.text = content.text.replace("Internship", "Temporary")

    job = parse_item(item, source_category="software-engineering")

    assert job.job_type is None


def test_entire_itpro_feed_is_mapped_to_jobs() -> None:
    jobs = parse_feed(
        FIXTURE_PATH.read_bytes(),
        source_category="software-engineering",
    )

    assert len(jobs) == 25
    assert jobs[0].source_id == "15717"
    assert all(job.source == "itpro" for job in jobs)
    assert all(job.source_category == "software-engineering" for job in jobs)
    assert len({job.source_id for job in jobs}) == len(jobs)
