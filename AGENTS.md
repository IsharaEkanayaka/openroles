# OpenRoles: project brief

## Goal
A personal tool that collects IT job postings from Sri Lankan job sites, stores them once, and sends me alerts for jobs matching my filters. Python. Useful first, simple always.

## How to work with me (tutor mode)
- I'm learning. Take ONE small step at a time.
- Before writing code: say what the step is, why it exists, and what files it touches. Wait for my OK.
- Explain new concepts briefly in plain language.
- Where sensible, let me write the key part myself and review it, instead of writing everything.
- Every step ships with a test. Don't move on until it passes.
- Do NOT add anything not in this brief (extra features, config systems, abstractions, new libraries). If you think something is missing, tell me instead of adding it.
- If a step needs a design change, stop and tell me. The design changes before the code does.

## Architecture
Shared half (runs once, for all users):
scheduler (every 6h) -> collectors (one per site) -> common Job record -> dedup -> job store (SQLite)

Per-user half (LATER, not now):
alerts (saved filters + destination) -> matcher -> deliveries -> exporters (Telegram first)

## Rules
- Collectors fetch and normalise only. They never filter and never know about users.
- Everything downstream of a collector must not care which site a job came from.
- One failing collector must never stop the others.
- Dedup is `UNIQUE (source, source_id)` in the DB. Inserts must be idempotent.
- Keep the raw payload of every job so parsers can be fixed and re-run later.
- Mark a job notified only AFTER the send succeeds.

## Job record
source, source_id, url, title, company, location, description, remote, job_type,
posted_at, collected_at, last_seen_at, status (open/closed), source_category, salary, raw

## Tables
- jobs (above, unique on source + source_id)
- collector_runs (source, started_at, finished_at, status, items_fetched, items_new, error)
- LATER: users, alerts, alert_deliveries

## Sources

### itpro.lk (verified against the live feed)
Feed: https://itpro.lk/rss/all/ (RSS 2.0, 25 items spanning about 3 days, ttl 30 min).
Each item has the full description, so never fetch individual job pages.

Field mapping, feed -> Job:
- source: constant "itpro"
- source_id: the number in <link>, e.g. /job/15722/... -> "15722"
- url: <link>
- title: <title> with the trailing " at {company}" removed
- company: <dc:creator>, stripped of whitespace
- location: <description>, which only contains "Location: X"; strip the "Location: " prefix
- job_type: parsed from <content:encoded>, the "Job Type:" line.
  Observed values: Full-time, Internship, Part-time, Contract.
  Map to my fixed set: full-time | part-time | contract | internship.
  Unknown value -> None, never invent one.
- description: the HTML in <content:encoded> after the "Description:" label
  (drop the Company / Location / Job Type lines and the trailing "Apply for this job" link)
- posted_at: <pubDate> (RFC 822, +0530), converted to UTC
- raw: the whole <item>

Known limits (do NOT work around these without asking me):
- remote = True only when location is exactly "Remote". Some jobs mention remote or hybrid
  only in the description. That's accepted for now. No work_mode field.
- salary: not a structured field; leave it None for itpro.
- source_category: not in the "all" feed; leave it None for now.
- Feed includes non-developer jobs (sales, project management). The collector must NOT
  filter them. Filtering belongs in alerts later.
- Dedup key is the job ID from the URL. Do not rely on feed ordering.

### rooster.jobs
Not investigated yet. Do not write this collector.

### topjobs.lk
Not investigated yet. Do not write this collector.

## Out of scope for now
Multi-user, dashboard/frontend, rooster and topjobs collectors, backfill, ML, deployment.

## Current state
Done: project skeleton, Job and CollectorRun models, db setup, config, health endpoint, tests.
Next: save the itpro feed as a test fixture, then write the itpro collector against it
(no network in tests).