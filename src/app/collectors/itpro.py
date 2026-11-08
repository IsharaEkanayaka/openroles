import re
from xml.etree import ElementTree

from app.models import Job

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


def parse_item(item: ElementTree.Element, source_category: str) -> Job:
    url = _required_text(item, "link")
    company = _required_text(item, "dc:creator", namespaces=NAMESPACES).strip()
    title = _required_text(item, "title")
    location = _parse_location(_required_text(item, "description"))
    content = _required_text(item, "content:encoded", namespaces=NAMESPACES)

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


def _remove_company_from_title(title: str, company: str) -> str:
    suffix = f" at {company}"
    return title.removesuffix(suffix).strip()
