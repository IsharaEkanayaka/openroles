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
- itpro.lk: RSS feed https://itpro.lk/rss/all/ (full description included, no HTML scraping).
  `remote` comes from location "Remote". `source_id` is the number in the job URL.
- rooster.jobs: not investigated yet.
- topjobs.lk: not investigated yet.

## Out of scope for now
Multi-user, dashboard/frontend, rooster and topjobs collectors, backfill, ML, deployment.

## Current state
Done: project skeleton, Job and CollectorRun models, db setup, config, health endpoint, tests.
Next: itpro collector, tested against a saved copy of the feed (no network in tests).