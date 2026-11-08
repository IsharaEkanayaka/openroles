import re
from xml.etree import ElementTree

from app.models import Job

NAMESPACES = {"dc": "http://purl.org/dc/elements/1.1/"}
JOB_ID_PATTERN = re.compile(r"/job/(\d+)(?:/|$)")


def parse_item(item: ElementTree.Element, source_category: str) -> Job:
    url = _required_text(item, "link")
    company = _required_text(item, "dc:creator", namespaces=NAMESPACES).strip()
    title = _required_text(item, "title")
    location = _parse_location(_required_text(item, "description"))

    return Job(
        source="itpro",
        source_id=_parse_source_id(url),
        url=url,
        title=_remove_company_from_title(title, company),
        company=company,
        location=location,
        remote=location == "Remote",
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


def _remove_company_from_title(title: str, company: str) -> str:
    suffix = f" at {company}"
    return title.removesuffix(suffix).strip()
