import re
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from xml.etree import ElementTree

import httpx
from sqlalchemy.orm import Session

from app.db import save_jobs
from app.models import CollectorRun, Job

NAMESPACES = {
    "content": "http://purl.org/rss/1.0/modules/content/",
    "dc": "http://purl.org/dc/elements/1.1/",
}
JOB_ID_PATTERN = re.compile(r"/job/(\d+)(?:/|$)")
JOB_TYPE_PATTERN = re.compile(
    r"<strong>\s*Job Type:\s*</strong>\s*([^<]+)",
    re.IGNORECASE,
)
DESCRIPTION_PATTERN = re.compile(
    r"<strong>\s*Description:\s*</strong>\s*<br\s*/?>(.*?)(?:" 
    r"<a\b[^>]*>\s*Apply\s+for\s+this\s+job\s*</a>|$)",
    re.IGNORECASE | re.DOTALL,
)
JOB_TYPES = {
    "full-time": "full-time",
    "internship": "internship",
    "part-time": "part-time",
    "contract": "contract",
}
FEED_URL = "https://itpro.lk/rss/all/"


def fetch_feed(
    client: httpx.Client,
    *,
    url: str = FEED_URL,
) -> bytes:
    response = client.get(url)
    response.raise_for_status()
    return response.content


def parse_feed(feed_xml: str | bytes, source_category: str) -> list[Job]:
    root = ElementTree.fromstring(feed_xml)
    return [
        parse_item(item, source_category=source_category)
        for item in root.findall("./channel/item")
    ]


def collect(
    feed_xml: str | bytes,
    session: Session,
    source_category: str,
) -> tuple[int, int]:
    started_at = datetime.now(timezone.utc)
    jobs = parse_feed(feed_xml, source_category=source_category)
    items_fetched = len(jobs)
    items_new = save_jobs(session, jobs)
    session.add(
        CollectorRun(
            source="itpro",
            started_at=started_at,
            finished_at=datetime.now(timezone.utc),
            status="ok",
            items_fetched=items_fetched,
            items_new=items_new,
        )
    )
    session.commit()
    return items_fetched, items_new


def parse_item(item: ElementTree.Element, source_category: str) -> Job:
    url = _required_text(item, "link")
    company = _required_text(item, "dc:creator", namespaces=NAMESPACES).strip()
    title = _required_text(item, "title")
    location = _parse_location(_required_text(item, "description"))
    content = _required_text(item, "content:encoded", namespaces=NAMESPACES)
    posted_at = _parse_posted_at(_required_text(item, "pubDate"))

    return Job(
        source="itpro",
        source_id=_parse_source_id(url),
        url=url,
        title=_remove_company_from_title(title, company),
        company=company,
        location=location,
        remote=location == "Remote",
        job_type=_parse_job_type(content),
        description=_parse_description(content),
        posted_at=posted_at,
        source_category=source_category,
        raw=ElementTree.tostring(item, encoding="unicode"),
    )


def _required_text(
    item: ElementTree.Element,
    path: str,
    *,
    namespaces: dict[str, str] | None = None,
) -> str:
    value = item.findtext(path, namespaces=namespaces)
    if value is None or not value.strip():
        raise ValueError(f"itpro item is missing required field: {path}")
    return value


def _parse_source_id(url: str) -> str:
    match = JOB_ID_PATTERN.search(url)
    if match is None:
        raise ValueError(f"could not find itpro job id in URL: {url}")
    return match.group(1)


def _parse_location(value: str) -> str:
    prefix = "Location:"
    if not value.startswith(prefix):
        raise ValueError(f"unexpected itpro location value: {value}")
    return value.removeprefix(prefix).strip()


def _parse_job_type(content: str) -> str | None:
    match = JOB_TYPE_PATTERN.search(content)
    if match is None:
        return None
    return JOB_TYPES.get(match.group(1).strip().lower())


def _parse_description(content: str) -> str:
    match = DESCRIPTION_PATTERN.search(content)
    if match is None:
        raise ValueError("itpro item is missing a description section")
    return match.group(1).strip()


def _parse_posted_at(value: str) -> datetime:
    parsed = parsedate_to_datetime(value)
    if parsed is None:
        raise ValueError(f"could not parse itpro publication date: {value}")
    return parsed.astimezone(timezone.utc)


def _remove_company_from_title(title: str, company: str) -> str:
    suffix = f" at {company}"
    return title.removesuffix(suffix).strip()
