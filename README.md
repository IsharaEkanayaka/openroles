# OpenRoles

OpenRoles collects job postings from multiple sources, deduplicates them, and
delivers matching alerts to users.

## Development

The project currently uses Python, FastAPI, SQLAlchemy, and SQLite.

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
python -m pytest
uvicorn app.main:app --reload
```

The first milestone only provides the application foundation and a health
endpoint. Collectors, job storage, scheduling, matching, and delivery will be
added as separate milestones.

The common job record is defined in `src/app/models/job.py`. It tracks source
identity, job details, collection timestamps, lifecycle status, optional
salary/category data, and the original source payload. Each job has a
source-specific `source_id`; the pair of `source` and `source_id` is unique so
the same posting is not stored twice from one source.